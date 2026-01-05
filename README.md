# 🧠 Sistema de Análisis de Feedback Multimodal

Sistema automatizado para el análisis de reseñas de clientes mediante **Inteligencia Artificial en la nube (Google Cloud AI)**, con soporte **multimodal** (texto, audio e imágenes), **almacenamiento persistente** y **chatbot interactivo** para consulta de resultados.

---

## 🎯 Descripción del Proyecto

Este proyecto consiste en el desarrollo de una aplicación web que permite a empresas de comercio electrónico analizar automáticamente el feedback de sus clientes a partir de distintos formatos de entrada (texto, voz e imagen).

El sistema procesa la información utilizando servicios de **Google Cloud AI**, almacena los resultados de forma persistente en una base de datos **SQLite**, y ofrece un **chatbot integrado** que permite consultar estadísticas, categorías y feedback reciente de forma conversacional.

---

## ✨ Características Principales

- ✅ **Análisis de Texto**
  - Detección de sentimiento
  - Extracción de entidades
  - Clasificación automática por categorías

- ✅ **Análisis de Audio**
  - Transcripción automática de voz a texto
  - Análisis de sentimiento del contenido transcrito

- ✅ **Análisis de Imágenes**
  - Detección de rostros
  - Inferencia de emociones
  - Identificación de objetos y texto en imágenes

- ✅ **Análisis Multimodal**
  - Combinación de resultados de texto, audio e imagen
  - Cálculo de un sentimiento final consolidado

- ✅ **Chatbot Integrado**
  - Consulta de estadísticas en tiempo real
  - Visualización de feedback reciente
  - Consulta de categorías y distribución de sentimientos
  - Funciona con o sin Dialogflow

- ✅ **Base de Datos Persistente**
  - Almacenamiento histórico de feedback
  - Estadísticas agregadas diarias
  - Persistencia tras reinicios

---

## 🔧 APIs de Google Cloud Utilizadas

| API | Función |
|----|--------|
| Natural Language API | Sentimiento y entidades |
| Speech-to-Text API | Transcripción de audio |
| Vision API | Análisis visual |
| Dialogflow (opcional) | Chatbot avanzado |

---

## 🗄️ Base de Datos

El sistema utiliza **SQLite** como base de datos persistente.

Archivo generado:
```
feedback_analytics.db
```

---

## 📋 Requisitos

- Python 3.9+
- Cuenta Google Cloud
- Git

---

## 🚀 Instalación

```bash
git clone <tu-repositorio>
cd feedback-analysis-gcp
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

## 🔐 Variables de Entorno

Archivo `.env`:

```env
GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json
GOOGLE_CLOUD_PROJECT_ID=analisis-inteligente
```

---

## ▶️ Ejecución

```bash
uvicorn app:app --reload
```

- App: http://localhost:8000
- Docs: http://localhost:8000/docs

---

## 👨‍💻 Autor

- **Nombre**: Rafael Moncayo Pérez
- **Centro**: DigitechFP
- **Asignatura**: Programación de Inteligencia Artificial
- **Fecha**: Enero 2026