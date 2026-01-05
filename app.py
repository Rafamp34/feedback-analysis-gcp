from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import os
from dotenv import load_dotenv
from typing import Optional

# Google Cloud APIs
from google.cloud import language_v1
from google.cloud import speech_v1
from google.cloud import vision

# Cargar variables de entorno
load_dotenv()

# Inicializar FastAPI
app = FastAPI(
    title="Sistema de Análisis de Feedback",
    description="Análisis multimodal con Google Cloud",
    version="1.0.0"
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

# Inicializar clientes de Google Cloud
language_client = language_v1.LanguageServiceClient()
speech_client = speech_v1.SpeechClient()
vision_client = vision.ImageAnnotatorClient()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Página principal"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/health")
async def health():
    """Verificar que el servidor funciona"""
    return {
        "status": "ok",
        "apis": ["Natural Language", "Speech-to-Text", "Vision"]
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
        
        # Configuración que acepta estéreo (2 canales)
        config = speech_v1.RecognitionConfig(
            encoding=speech_v1.RecognitionConfig.AudioEncoding.LINEAR16,
            audio_channel_count=2,  # <-- AGREGAR ESTA LÍNEA (para estéreo)
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
        
        # Analizar el texto transcrito
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
        
        # 1. DETECTAR CARAS Y EMOCIONES
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
        
        # 2. DETECTAR OBJETOS
        labels_response = vision_client.label_detection(image=image, max_results=10)
        labels = labels_response.label_annotations
        
        objetos = []
        for label in labels:
            objetos.append({
                "nombre": label.description,
                "confianza": round(label.score, 2)
            })
        
        # 3. DETECTAR TEXTO (OCR)
        text_response = vision_client.text_detection(image=image)
        texts = text_response.text_annotations
        
        texto_detectado = texts[0].description if texts else ""
        
        # Sentimiento de la imagen
        sentimiento_imagen = "neutral"
        if caras_info:
            if caras_info[0]["emocion_principal"] == "alegria":
                sentimiento_imagen = "positivo"
            elif caras_info[0]["emocion_principal"] in ["tristeza", "enojo"]:
                sentimiento_imagen = "negativo"
        
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
        
        # Analizar texto
        if text and text.strip():
            resultado["apis_usadas"].append("Natural Language")
            text_result = await analyze_text(text=text)
            resultado["analisis_texto"] = text_result
            sentimientos.append(text_result["sentimiento"]["score"])
        
        # Analizar audio
        if audio_file:
            resultado["apis_usadas"].append("Speech-to-Text")
            audio_result = await analyze_audio(file=audio_file)
            resultado["analisis_audio"] = audio_result
            sentimientos.append(audio_result["sentimiento"]["score"])
        
        # Analizar imagen
        if image_file:
            resultado["apis_usadas"].append("Vision")
            image_result = await analyze_image(file=image_file)
            resultado["analisis_imagen"] = image_result
            
            if image_result["sentimiento_visual"] == "positivo":
                sentimientos.append(0.7)
            elif image_result["sentimiento_visual"] == "negativo":
                sentimientos.append(-0.7)
        
        # Resultado final
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
    print("🚀 Iniciando servidor...")
    print("📖 Docs: http://localhost:8000/docs")
    print("🌐 App: http://localhost:8000")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000)