# NovaTetch — QualityAI Requirements Refiner

Herramienta de análisis inteligente de requerimientos de software. Toma un requerimiento escrito en lenguaje natural, detecta ambigüedades según los estándares **IEEE 830** e **ISO 25010**, las presenta al analista para resolverlas, y genera **historias de usuario estructuradas** con criterios de aceptación verificables en formato Given/When/Then.

---

## ¿Cómo funciona?

El pipeline sigue cuatro pasos:

```
Requerimiento → Detección de ambigüedades → Resolución (HITL) → RAG + LLM → Historias de usuario
```

1. **Detección de ambigüedades** — un analizador léxico identifica palabras vagas (`rápido`, `seguro`, `gestionar`, `usuarios`, etc.) que violan propiedades de IEEE 830 (verificabilidad, completitud, no ambigüedad).

2. **Human-in-the-Loop (HITL)** — si se detectan ambigüedades, la interfaz las presenta una por una. El analista puede aceptar la sugerencia automática, escribir su propia resolución, o descartarla. Esto elimina suposiciones del LLM.

3. **RAG (Retrieval-Augmented Generation)** — el sistema busca en una base de conocimiento de 50 historias de usuario de referencia las más similares al requerimiento, usando embeddings vectoriales. Esas historias se inyectan en el prompt como modelos de calidad.

4. **Generación y validación** — el LLM genera las historias en JSON, el sistema las valida contra un esquema Pydantic (Contract A). Si hay errores, reintenta hasta 3 veces con feedback automático.

---

## Stack

| Capa | Tecnología |
|---|---|
| Frontend | React 19 + TypeScript + Tailwind CSS v4 + Vite |
| Backend | FastAPI + Python 3.13 |
| LLM | Groq API — `llama-3.3-70b-versatile` |
| Embeddings | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` |
| Vector DB | ChromaDB (persistente) |
| Base de datos | SQLite (historial de ejecuciones) |
| Iconos | Lucide React |

---

## Requisitos previos

- Python 3.13+
- Node 22+
- Una API key de Groq → [console.groq.com](https://console.groq.com)

---

## Instalación y arranque

### 1. Clonar el repositorio

```bash
git clone <url-del-repo>
cd NovaTetch
```

### 2. Backend

```bash
cd backend
cp .env.example .env
# Editar .env y poner tu GROQ_API_KEY

pip install -r requirements.txt
uvicorn main:app --reload
```

El backend queda disponible en `http://localhost:8000`.

> La primera vez que arranca descarga el modelo de embeddings (~120 MB). Las ejecuciones siguientes son inmediatas porque la knowledge base ya está indexada en `knowledge_base_data_multilingual/`.

### 3. Frontend

```bash
# En otra terminal, desde la raíz del proyecto
cd frontend
npm install
npm run dev
```

El frontend queda disponible en `http://localhost:5173`.

---

## Estructura del proyecto

```
NovaTetch/
├── backend/
│   ├── main.py                  # Entrada FastAPI, CORS, startup
│   ├── agent.py                 # WebAgent — orquesta todo el pipeline
│   ├── database.py              # SQLite con SQLAlchemy (historial)
│   ├── routers/
│   │   └── stories.py           # Endpoints REST
│   ├── .env.example
│   └── requirements.txt
│
├── frontend/
│   └── src/
│       ├── App.tsx              # Máquina de estados de la UI
│       ├── api/client.ts        # Cliente HTTP hacia el backend
│       ├── components/
│       │   ├── PromptForm.tsx       # Formulario de entrada
│       │   ├── AmbiguityResolver.tsx # Pantalla HITL
│       │   ├── StoryCard.tsx        # Tarjeta expandible por historia
│       │   └── RunHistory.tsx       # Historial de ejecuciones
│       └── types/index.ts       # Tipos TypeScript compartidos
│
├── src/                         # Módulo de IA (núcleo)
│   ├── ambiguity_detector.py    # Detector IEEE 830 / ISO 25010
│   ├── contract_a.py            # Esquema Pydantic de salida
│   └── ...
│
├── knowledge_base_stories.json  # 50 historias de referencia (fuente)
├── knowledge_base_data_multilingual/  # ChromaDB (vectores indexados)
├── agente_v4_hitl.py            # Versión CLI del agente (consola)
└── requirements.txt
```

---

## API

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/api/stories/analyze` | Detecta ambigüedades en el prompt |
| `POST` | `/api/stories/generate` | Genera historias de usuario |
| `GET` | `/api/stories/runs` | Lista los últimos 50 runs |
| `GET` | `/api/stories/runs/{run_id}` | Detalle de un run |
| `DELETE` | `/api/stories/runs/{run_id}` | Elimina un run del historial |

---

## Base de conocimiento

La knowledge base contiene **50 historias de usuario de referencia** de 8 proyectos de distinto dominio, usadas como ejemplos de calidad por el LLM durante la generación:

| Proyecto | Dominio |
|---|---|
| Katary360 | Gestión de proyectos, seguimiento de tiempo, calidad |
| MediConnect | Historia clínica, agendamiento médico, farmacia |
| CampusDigital | Matrícula, contenido académico, calificaciones |
| StockControl Pro | Inventario, alertas de stock, ventas |
| RestaurantOS | Pedidos, cocina, facturación, gestión de mesas |
| TalentHub | Nómina, vacaciones, reclutamiento, evaluación |
| BancoDigital App | Transferencias, crédito, prevención de fraude |
| LogiTrack | Despachos, rastreo, entregas, logística |

Para agregar historias propias, edita `knowledge_base_stories.json` con el mismo formato y borra la carpeta `knowledge_base_data_multilingual/` — se regenera sola al arrancar el backend.

---

## Variables de entorno

| Variable | Descripción |
|---|---|
| `GROQ_API_KEY` | API key de Groq (obligatoria) |
