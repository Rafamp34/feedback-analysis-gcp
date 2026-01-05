# -*- coding: utf-8 -*-
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from database import FeedbackDatabase
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import os
from dotenv import load_dotenv
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import uuid

# Google Cloud APIs
from google.cloud import language_v1
from google.cloud import speech_v1
from google.cloud import vision

# Dialogflow (opcional - el chatbot funciona sin él)
try:
    from google.cloud import dialogflow
    DIALOGFLOW_AVAILABLE = True
except ImportError:
    DIALOGFLOW_AVAILABLE = False
    print("⚠️  Dialogflow no disponible - Chatbot funcionará en modo simple")

# Cargar variables de entorno
load_dotenv()

# Inicializar FastAPI
app = FastAPI(
    title="Sistema de Análisis de Feedback",
    description="Análisis multimodal con Google Cloud + Chatbot",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Archivos estáticos y templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Configurar encoding UTF-8 para respuestas
from starlette.responses import Response
Response.charset = "utf-8"

# Inicializar clientes de Google Cloud
language_client = language_v1.LanguageServiceClient()
speech_client = speech_v1.SpeechClient()
vision_client = vision.ImageAnnotatorClient()

# Cliente de Dialogflow
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
LANGUAGE_CODE = "es"

# Instanciar base de datos
db = FeedbackDatabase("feedback_analytics.db")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Página principal"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/health")
async def health():
    """Verificar que el servidor funciona"""
    apis = ["Natural Language", "Speech-to-Text", "Vision"]
    if DIALOGFLOW_AVAILABLE:
        apis.append("Dialogflow")
    
    return {
        "status": "ok",
        "apis": apis,
        "chatbot": "enabled",
        "chatbot_mode": "advanced" if DIALOGFLOW_AVAILABLE else "simple"
    }


@app.post("/api/analyze/text")
async def analyze_text(text: str = Form(...)):
    """Analiza texto con Google Natural Language API"""
    try:
        document = language_v1.Document(
            content=text,
            type_=language_v1.Document.Type.PLAIN_TEXT,
            language="es"
        )
        
        sentiment_response = language_client.analyze_sentiment(
            request={"document": document}
        )
        
        sentiment = sentiment_response.document_sentiment
        score = sentiment.score
        magnitude = sentiment.magnitude
        
        if score > 0.25:
            label = "positivo"
            emoji = "😊"
        elif score < -0.25:
            label = "negativo"
            emoji = "😞"
        else:
            label = "neutral"
            emoji = "😐"
        
        entities_response = language_client.analyze_entities(
            request={"document": document}
        )
        
        entities = []
        for entity in entities_response.entities[:10]:
            tipo = "OTRO"
            if entity.type_ == language_v1.Entity.Type.PERSON:
                tipo = "PERSONA"
            elif entity.type_ == language_v1.Entity.Type.LOCATION:
                tipo = "LUGAR"
            elif entity.type_ == language_v1.Entity.Type.ORGANIZATION:
                tipo = "ORGANIZACIÓN"
            elif entity.type_ == language_v1.Entity.Type.CONSUMER_GOOD:
                tipo = "PRODUCTO"
            elif entity.type_ == language_v1.Entity.Type.EVENT:
                tipo = "EVENTO"
            
            entities.append({
                "nombre": entity.name,
                "tipo": tipo,
                "relevancia": round(entity.salience, 2)
            })
        
        try:
            classification_response = language_client.classify_text(
                request={"document": document}
            )
            
            if classification_response.categories:
                categoria = classification_response.categories[0].name
                categoria = categoria.split('/')[-1].replace('_', ' ').title()
            else:
                categoria = "General"
        except:
            categoria = categorizar_manual(text)
        
        if label == "positivo":
            recomendacion = "Cliente satisfecho! Considerar para testimonios"
        elif label == "negativo":
            recomendacion = "URGENTE: Cliente insatisfecho, contactar inmediatamente"
        else:
            recomendacion = "Feedback neutral, hacer seguimiento"
        
        # Guardar en base de datos
        db.add_feedback({
            "id": str(uuid.uuid4()),
            "tipo": "texto",
            "sentimiento": label,
            "score": round(score, 2),
            "magnitude": round(magnitude, 2),
            "categoria": categoria,
            "texto": text,
            "entidades": entities
        })

        
        return {
            "success": True,
            "sentimiento": {
                "clasificacion": label,
                "emoji": emoji,
                "score": round(score, 2),
                "intensidad": round(magnitude, 2)
            },
            "entidades": entities,
            "categoria": categoria,
            "recomendacion": recomendacion
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.post("/api/analyze/audio")
async def analyze_audio(file: UploadFile = File(...)):
    """Transcribe audio con Speech-to-Text y analiza el contenido"""
    try:
        audio_content = await file.read()
        audio = speech_v1.RecognitionAudio(content=audio_content)
        
        config = speech_v1.RecognitionConfig(
            encoding=speech_v1.RecognitionConfig.AudioEncoding.LINEAR16,
            audio_channel_count=2,
            language_code="es-ES",
            enable_automatic_punctuation=True
        )
        
        response = speech_client.recognize(config=config, audio=audio)
        
        if not response.results:
            raise HTTPException(
                status_code=400,
                detail="No se pudo transcribir el audio. Asegúrate de que sea WAV con voz clara."
            )
        
        transcripcion = ""
        confidencias = []
        
        for result in response.results:
            transcripcion += result.alternatives[0].transcript + " "
            confidencias.append(result.alternatives[0].confidence)
        
        transcripcion = transcripcion.strip()
        confianza_promedio = sum(confidencias) / len(confidencias)
        
        document = language_v1.Document(
            content=transcripcion,
            type_=language_v1.Document.Type.PLAIN_TEXT,
            language="es"
        )
        
        sentiment_response = language_client.analyze_sentiment(
            request={"document": document}
        )
        sentiment = sentiment_response.document_sentiment
        
        if sentiment.score > 0.25:
            label = "positivo"
        elif sentiment.score < -0.25:
            label = "negativo"
        else:
            label = "neutral"
        
        # Guardar en base de datos
        db.add_feedback({
            "id": str(uuid.uuid4()),
            "tipo": "audio",
            "sentimiento": label,
            "score": round(sentiment.score, 2),
            "texto": transcripcion,
            "audio_confianza": round(confianza_promedio, 2)
        })
        
        return {
            "success": True,
            "transcripcion": transcripcion,
            "confianza_audio": round(confianza_promedio, 2),
            "sentimiento": {
                "clasificacion": label,
                "score": round(sentiment.score, 2)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.post("/api/analyze/image")
async def analyze_image(file: UploadFile = File(...)):
    """Analiza imágenes con Vision API"""
    try:
        image_content = await file.read()
        image = vision.Image(content=image_content)
        
        face_response = vision_client.face_detection(image=image)
        faces = face_response.face_annotations
        
        likelihood_map = {
            vision.Likelihood.VERY_UNLIKELY: 0.1,
            vision.Likelihood.UNLIKELY: 0.3,
            vision.Likelihood.POSSIBLE: 0.5,
            vision.Likelihood.LIKELY: 0.7,
            vision.Likelihood.VERY_LIKELY: 0.9
        }
        
        caras_info = []
        if faces:
            for face in faces[:3]:
                emociones = {
                    "alegria": likelihood_map.get(face.joy_likelihood, 0),
                    "tristeza": likelihood_map.get(face.sorrow_likelihood, 0),
                    "enojo": likelihood_map.get(face.anger_likelihood, 0),
                    "sorpresa": likelihood_map.get(face.surprise_likelihood, 0)
                }
                
                emocion_dominante = max(emociones.items(), key=lambda x: x[1])
                
                caras_info.append({
                    "emociones": emociones,
                    "emocion_principal": emocion_dominante[0]
                })
        
        labels_response = vision_client.label_detection(image=image, max_results=10)
        labels = labels_response.label_annotations
        
        objetos = []
        for label in labels:
            objetos.append({
                "nombre": label.description,
                "confianza": round(label.score, 2)
            })
        
        text_response = vision_client.text_detection(image=image)
        texts = text_response.text_annotations
        
        texto_detectado = texts[0].description if texts else ""
        
        sentimiento_imagen = "neutral"
        if caras_info:
            if caras_info[0]["emocion_principal"] == "alegria":
                sentimiento_imagen = "positivo"
            elif caras_info[0]["emocion_principal"] in ["tristeza", "enojo"]:
                sentimiento_imagen = "negativo"
        
        # Guardar en base de datos
        db.add_feedback({
            "id": str(uuid.uuid4()),
            "tipo": "imagen",
            "sentimiento": sentimiento_imagen,
            "score": 0,
            "rostros": len(faces),
            "objetos": objetos
        })
        
        return {
            "success": True,
            "caras": {
                "cantidad": len(faces),
                "detalles": caras_info
            },
            "objetos": objetos,
            "texto": texto_detectado[:200] if texto_detectado else "",
            "sentimiento_visual": sentimiento_imagen
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.post("/api/analyze/multimodal")
async def analyze_multimodal(
    text: Optional[str] = Form(None),
    audio_file: Optional[UploadFile] = File(None),
    image_file: Optional[UploadFile] = File(None)
):
    """Análisis completo multimodal"""
    try:
        if not any([text, audio_file, image_file]):
            raise HTTPException(
                status_code=400,
                detail="Debes enviar al menos texto, audio o imagen"
            )
        
        resultado = {
            "success": True,
            "apis_usadas": []
        }
        
        sentimientos = []
        
        if text and text.strip():
            resultado["apis_usadas"].append("Natural Language")
            text_result = await analyze_text(text=text)
            resultado["analisis_texto"] = text_result
            sentimientos.append(text_result["sentimiento"]["score"])
        
        if audio_file:
            resultado["apis_usadas"].append("Speech-to-Text")
            audio_result = await analyze_audio(file=audio_file)
            resultado["analisis_audio"] = audio_result
            sentimientos.append(audio_result["sentimiento"]["score"])
        
        if image_file:
            resultado["apis_usadas"].append("Vision")
            image_result = await analyze_image(file=image_file)
            resultado["analisis_imagen"] = image_result
            
            if image_result["sentimiento_visual"] == "positivo":
                sentimientos.append(0.7)
            elif image_result["sentimiento_visual"] == "negativo":
                sentimientos.append(-0.7)
        
        if sentimientos:
            promedio = sum(sentimientos) / len(sentimientos)
            
            if promedio > 0.25:
                sentimiento_final = "positivo"
                recomendacion = "Feedback positivo en múltiples canales. Cliente satisfecho!"
            elif promedio < -0.25:
                sentimiento_final = "negativo"
                recomendacion = "ALERTA: Feedback negativo detectado. Contactar YA!"
            else:
                sentimiento_final = "neutral"
                recomendacion = "Feedback mixto. Revisar comentarios."
            
            resultado["resultado_final"] = {
                "sentimiento": sentimiento_final,
                "score_promedio": round(promedio, 2),
                "canales_analizados": len(sentimientos),
                "recomendacion": recomendacion
            }
        
        return resultado
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# =====================================================
# CHATBOT ENDPOINTS CON DIALOGFLOW
# =====================================================

@app.post("/api/chatbot/webhook")
async def dialogflow_webhook(request: Request):
    """Webhook para Dialogflow - Maneja fulfillment"""
    try:
        req = await request.json()
        
        intent_name = req.get("queryResult", {}).get("intent", {}).get("displayName", "")
        parameters = req.get("queryResult", {}).get("parameters", {})
        
        response_text = handle_intent(intent_name, parameters)
        
        return JSONResponse(content={
            "fulfillmentText": response_text
        })
        
    except Exception as e:
        return JSONResponse(content={
            "fulfillmentText": f"Lo siento, ocurrió un error: {str(e)}"
        })


@app.post("/api/chatbot/message")
async def chatbot_message(message: str = Form(...), session_id: str = Form(default="default")):
    """Endpoint directo para el chatbot (sin Dialogflow configurado)"""
    try:
        # Si no hay Dialogflow configurado, usar respuestas predefinidas
        response = generate_simple_response(message)
        
        return {
            "success": True,
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/api/chatbot/stats")
async def get_stats():
    """Obtener estadísticas para el chatbot"""
    try:
        stats = db.get_statistics()
        categories = db.get_categories()
        recent = db.get_recent_feedback(limit=5)
        
        return {
            "success": True,
            "statistics": stats,
            "categories": categories,
            "recent_feedback": recent
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


def handle_intent(intent_name: str, parameters: Dict[str, Any]) -> str:
    """Maneja diferentes intents de Dialogflow"""
    
    if "estadisticas" in intent_name.lower() or "stats" in intent_name.lower():
        stats = db.get_statistics()
        return f"""📊 Estadísticas actuales:
        
• Total de feedback: {stats['total']}
• Positivos: {stats['positivos']} ({stats['porcentaje_positivos']}%)
• Negativos: {stats['negativos']} ({stats['porcentaje_negativos']}%)
• Neutrales: {stats['neutrales']}
• Score promedio: {stats['score_promedio']}

¿Necesitas más información?"""
    
    elif "categorias" in intent_name.lower() or "categories" in intent_name.lower():
        categories = db.get_categories()
        if not categories:
            return "No hay categorías registradas aún. Analiza más feedback para ver las categorías."
        
        cat_text = "📁 Distribución de categorías:\n\n"
        for cat, count in categories.items():
            cat_text += f"• {cat}: {count} feedback\n"
        return cat_text
    
    elif "reciente" in intent_name.lower() or "recent" in intent_name.lower():
        recent = db.get_recent_feedback(limit=3)
        if not recent:
            return "No hay feedback reciente registrado."
        
        text = "📝 Últimos 3 feedback:\n\n"
        for idx, f in enumerate(recent, 1):
            text += f"{idx}. {f.get('sentimiento', 'N/A').upper()} - {f.get('tipo', 'N/A')}\n"
        return text
    
    elif "ayuda" in intent_name.lower() or "help" in intent_name.lower():
        return """🤖 Puedo ayudarte con:

• Ver estadísticas generales
• Consultar categorías de feedback
• Mostrar feedback reciente
• Explicar cómo funcionan las APIs
• Dar recomendaciones

¿Qué te gustaría saber?"""
    
    elif "apis" in intent_name.lower():
        return """☁️ Usamos estas APIs de Google Cloud:

1. **Natural Language API**: Analiza sentimiento y entidades en texto
2. **Speech-to-Text API**: Convierte audio a texto
3. **Vision API**: Detecta rostros, emociones y objetos en imágenes
4. **Dialogflow**: Yo! El chatbot inteligente 🤖

¿Quieres saber más sobre alguna?"""
    
    else:
        return "Entiendo tu pregunta. ¿Podrías reformularla? Puedo ayudarte con estadísticas, categorías, feedback reciente y más."


def generate_simple_response(message: str) -> str:
    """Genera respuestas simples sin Dialogflow configurado"""
    message = message.lower()
    
    # ESTADÍSTICAS - con y sin tildes
    if any(word in message for word in ["estadística", "estadisticas", "estadística", "estadísticas", "stats", "números", "numeros", "cuántos", "cuantos", "datos", "total"]):
        stats = db.get_statistics()
        
        if stats['total'] == 0:
            return """📊 Estadísticas actuales:

Aún no hay feedback analizado. 

¡Comienza analizando texto, audio o imágenes en las pestañas superiores!"""
        
        return f"""📊 Estadísticas actuales:

• Total de feedback: {stats['total']} 
• Positivos: {stats['positivos']} ({stats['porcentaje_positivos']}%)
• Negativos: {stats['negativos']} ({stats['porcentaje_negativos']}%)
• Neutrales: {stats['neutrales']}
• Score promedio: {stats['score_promedio']}

💡 Tip: Analiza más feedback para obtener mejores insights!"""
    
    # CATEGORÍAS - con y sin tildes
    elif any(word in message for word in ["categoría", "categorias", "categoría", "categorías", "category", "tipo", "tipos", "clasificación", "clasificacion"]):
        categories = db.get_categories()
        
        if not categories:
            return """📁 Categorías:

Aún no hay categorías detectadas. 

Analiza más feedback para que el sistema identifique automáticamente las categorías de productos o servicios mencionados."""
        
        text = "📁 Categorías detectadas:\n\n"
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            text += f"• {cat}: {count} feedback\n"
        
        text += f"\n📈 Total de categorías: {len(categories)}"
        return text
    
    # FEEDBACK RECIENTE - con y sin tildes
    elif any(word in message for word in ["reciente", "recientes", "último", "ultimos", "últimos", "ultimo", "recent", "nuevo", "nuevos"]):
        recent = db.get_recent_feedback(limit=5)
        
        if not recent:
            return """📝 Feedback reciente:

No hay feedback registrado todavía.

¡Usa las pestañas superiores para analizar texto, audio o imágenes!"""
        
        text = f"📝 Últimos {len(recent)} feedback analizados:\n\n"
        for idx, f in enumerate(recent, 1):
            sentimiento = f.get('sentimiento', 'N/A').upper()
            tipo = f.get('tipo', 'N/A').capitalize()
            emoji = "😊" if sentimiento == "POSITIVO" else "😞" if sentimiento == "NEGATIVO" else "😐"
            text += f"{idx}. {emoji} {sentimiento} - Tipo: {tipo}\n"
        
        return text
    
    # AYUDA / HOLA
    elif any(word in message for word in ["hola", "ayuda", "help", "qué puedes", "que puedes", "hola", "buenas", "buenos", "hey"]):
        return """👋 ¡Hola! Soy tu asistente de feedback.

Puedo ayudarte con:
• 📊 Estadísticas generales del feedback
• 📁 Ver categorías detectadas
• 📝 Consultar feedback reciente
• ☁️ Información sobre las APIs de Google Cloud

💬 Escribe tu pregunta o usa los botones de abajo."""
    
    # APIs / TECNOLOGÍA
    elif any(word in message for word in ["api", "apis", "google", "cloud", "tecnología", "tecnologia", "cómo funciona", "como funciona"]):
        return """☁️ Google Cloud AI - Tecnología utilizada:

1. **Natural Language API**
   📝 Analiza sentimiento y extrae entidades del texto

2. **Speech-to-Text API**
   🎤 Convierte grabaciones de voz a texto

3. **Vision API**
   👁️ Detecta rostros, emociones y objetos en imágenes

4. **Chatbot (yo)**
   🤖 ¡Tu asistente inteligente!

🔗 Todo integrado con FastAPI + Python"""
    
    # SENTIMIENTO
    elif any(word in message for word in ["sentimiento", "positivo", "negativo", "neutral", "cómo van", "como van"]):
        stats = db.get_statistics()
        
        if stats['total'] == 0:
            return "Aún no hay análisis de sentimiento. ¡Analiza feedback primero!"
        
        if stats['porcentaje_positivos'] > 60:
            resumen = "¡Excelente! La mayoría del feedback es positivo 😊"
        elif stats['porcentaje_negativos'] > 40:
            resumen = "⚠️ Atención: Hay bastante feedback negativo"
        else:
            resumen = "El feedback está balanceado"
        
        return f"""😊 Análisis de Sentimiento:

{resumen}

• Positivos: {stats['porcentaje_positivos']}%
• Negativos: {stats['porcentaje_negativos']}%
• Score promedio: {stats['score_promedio']}"""
    
    # NO ENTENDIDO
    else:
        return """🤔 No estoy seguro de entender tu pregunta.

Intenta preguntar sobre:
• 📊 "Muéstrame las estadísticas"
• 📁 "¿Qué categorías tengo?"
• 📝 "Feedback reciente"
• ☁️ "¿Qué APIs usas?"

O usa los botones de sugerencias abajo 👇"""


def categorizar_manual(text):
    """Categorizar texto manualmente"""
    text = text.lower()
    
    if any(word in text for word in ["auriculares", "teléfono", "laptop", "tablet"]):
        return "Electrónica"
    elif any(word in text for word in ["camisa", "zapatos", "ropa", "vestido"]):
        return "Ropa"
    elif any(word in text for word in ["comida", "restaurante", "sabor"]):
        return "Alimentos"
    elif any(word in text for word in ["entrega", "envío", "paquete"]):
        return "Logística"
    else:
        return "General"


if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("🚀 Iniciando servidor con CHATBOT...")
    print("📖 Docs: http://localhost:8000/docs")
    print("🌐 App: http://localhost:8000")
    print(f"🤖 Chatbot: {'Modo Avanzado (Dialogflow)' if DIALOGFLOW_AVAILABLE else 'Modo Simple (Sin Dialogflow)'}")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000)