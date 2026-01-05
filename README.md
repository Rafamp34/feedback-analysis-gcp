# 🧠 Sistema de Análisis de Feedback Multimodal

Sistema automatizado para analizar reseñas de productos usando **Google Cloud AI** con soporte para texto, audio e imágenes.

## 🎯 Descripción del Proyecto

Este sistema permite a empresas de e-commerce procesar feedback de clientes de manera multimodal, extrayendo información valiosa para mejorar productos y servicio al cliente.

### Características Principales

- ✅ **Análisis de Texto**: Detección de sentimiento, extracción de entidades y categorización
- ✅ **Transcripción de Audio**: Convierte grabaciones de voz a texto y las analiza
- ✅ **Análisis de Imágenes**: Detecta rostros, emociones y objetos en fotografías
- ✅ **Análisis Multimodal**: Combina múltiples fuentes para un resultado consolidado

## 🔧 APIs de Google Cloud Utilizadas

| API | Función | Uso |
|-----|---------|-----|
| **Natural Language API** | Análisis de sentimiento y entidades | Procesa texto y audio transcrito |
| **Speech-to-Text API** | Transcripción de audio | Convierte voz a texto |
| **Vision API** | Análisis visual | Detecta caras, emociones y objetos |

## 📋 Requisitos Previos

- Python 3.8+
- Cuenta de Google Cloud Platform
- Git

## 🚀 Instalación

### 1. Clonar el repositorio
```bash
git clone <tu-repositorio>
cd feedback-analysis-gcp
```

### 2. Crear entorno virtual
```bash
python -m venv venv

# En Windows
venv\Scripts\activate

# En Linux/Mac
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar Google Cloud
    

### 5. Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto:
```env
GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json
GOOGLE_CLOUD_PROJECT_ID=analisis-inteligente
```

### 6. Ejecutar la aplicación
```bash
python app.py
```

La aplicación estará disponible en:
- **Frontend**: http://localhost:8000
- **Documentación API**: http://localhost:8000/docs
- **Documentación alternativa**: http://localhost:8000/redoc

## 📁 Estructura del Proyecto
```
feedback-analysis-gcp/
├── app.py                          # Backend FastAPI
├── requirements.txt                # Dependencias Python
├── .env                           # Variables de entorno (no subir a git)
├── .gitignore                     # Archivos ignorados por git
├── service-account-key.json       # Credenciales GCP (no subir a git)
├── README.md                      # Este archivo
├── static/
│   ├── css/
│   │   └── style.css             # Estilos de la aplicación
│   ├── js/
│   │   └── script.js             # Lógica del frontend
│   └── img/
└── templates/
    └── index.html                # Interfaz web principal
```

## 💻 Uso de la Aplicación

### Análisis de Texto

1. Navega a la pestaña **Texto**
2. Escribe o pega la reseña del cliente
3. Haz clic en **Analizar Texto**
4. Revisa los resultados: sentimiento, entidades, categoría y recomendación

### Análisis de Audio

1. Navega a la pestaña **Audio**
2. Selecciona un archivo WAV (16kHz recomendado)
3. Haz clic en **Transcribir y Analizar**
4. Obtén la transcripción y análisis del contenido

**Nota**: Para convertir audio a WAV 16kHz, usa herramientas como:
- Online: https://online-audio-converter.com/

### Análisis de Imagen

1. Navega a la pestaña **Imagen**
2. Selecciona una imagen JPG/PNG
3. Haz clic en **Analizar Imagen**
4. Revisa rostros detectados, emociones y objetos

### Análisis Multimodal

1. Navega a la pestaña **Multimodal**
2. Proporciona al menos uno: texto, audio o imagen
3. Haz clic en **Análisis Completo**
4. Obtén un resultado consolidado de todas las fuentes

## 📊 API Endpoints

### `POST /api/analyze/text`
Analiza texto con Natural Language API

**Body**: `text` (form-data)

**Response**:
```json
{
  "success": true,
  "sentimiento": {
    "clasificacion": "positivo",
    "score": 0.85,
    "intensidad": 1.2
  },
  "entidades": [...],
  "categoria": "Electrónica",
  "recomendacion": "..."
}
```

### `POST /api/analyze/audio`
Transcribe y analiza audio

**Body**: `file` (multipart/form-data)

### `POST /api/analyze/image`
Analiza imágenes

**Body**: `file` (multipart/form-data)

### `POST /api/analyze/multimodal`
Análisis completo multimodal

**Body**: `text`, `audio_file`, `image_file` (opcionales, al menos uno requerido)

## 💰 Análisis de Costos

### Capa Gratuita (Mensual)

| API | Límite Gratuito | Precio después |
|-----|-----------------|----------------|
| Natural Language | 5,000 unidades | $1.00 / 1,000 |
| Speech-to-Text | 60 minutos | $0.006 / 15s |
| Vision | 1,000 unidades | $1.50 / 1,000 |

### Estimación para 1,000 reseñas/mes

Distribución: 60% texto, 25% audio (30s), 15% imágenes

| Recurso | Cantidad | Costo |
|---------|----------|-------|
| Natural Language | 850 análisis | Gratis + $0 |
| Speech-to-Text | 125 min | Gratis + $1.56 |
| Vision | 150 imágenes | Gratis |
| **TOTAL** | | **~$1.56/mes** |

Para **10,000 reseñas/mes**: **~$50-70/mes**

## 🐛 Solución de Problemas

### Error: "No such file or directory: service-account-key.json"
- Verifica que descargaste las credenciales de Google Cloud
- Asegúrate de que el archivo esté en la raíz del proyecto

### Error: "API not enabled"
- Ejecuta los comandos para habilitar las APIs
- Espera 1-2 minutos para que se propaguen los cambios

### Error en transcripción de audio
- Verifica que el audio sea WAV, 16kHz
- Usa un conversor de audio si es necesario

### Error: "Permission denied"
- Verifica que el service account tenga los roles correctos
- Revisa que las credenciales sean válidas

## 📸 Capturas de Pantalla

_(Agrega capturas de pantalla de tu aplicación funcionando)_


## 👨‍💻 Autor

- **Nombre**: Rafael Moncayo Pérez
- **Centro**: DigitechFP
- **Asignatura**: Programación de Inteligencia Artificial
- **Fecha**: Enero 2026


```

---

## 📂 Resumen de archivos que debes crear:
```
feedback-analysis-gcp/
├── app.py                    
├── requirements.txt           
├── .env                      
├── .env.example               
├── .gitignore               
├── README.md                 
├── static/
│   ├── css/
│   │   └── style.css        
│   └── js/
│       └── script.js        
└── templates/
    └── index.html           