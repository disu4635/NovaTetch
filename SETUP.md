# NovaTech — QualityAI Requirements Refiner

## Requisitos
- Python 3.13+
- Node 22+
- Groq API key (obtener en console.groq.com)

## Backend

```bash
cd backend
cp .env.example .env
# Poner tu GROQ_API_KEY en .env

pip install -r requirements.txt
uvicorn main:app --reload
# Corre en http://localhost:8000
```

La primera vez descarga el modelo de embeddings (~120MB) e indexa la knowledge base.

## Frontend

```bash
cd frontend
npm install
npm run dev
# Corre en http://localhost:5173
```

## Estructura de la API

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | /api/stories/analyze | Detecta ambigüedades en el prompt |
| POST | /api/stories/generate | Genera historias de usuario |
| GET  | /api/stories/runs | Lista los últimos 50 runs |
| GET  | /api/stories/runs/{run_id} | Detalle de un run |
| GET  | /health | Health check |

## Modelo de embeddings
`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
(ChromaDB collection: `katary_sgc_multilingual` en `../qualityai-modulo1/knowledge_base_data_multilingual`)
