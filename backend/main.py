from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import init_db
from routers.stories import router as stories_router
from routers.quality import router as quality_router

app = FastAPI(title="NovaTech - QualityAI", version="2.0.0")

# PDFs de actas disponibles como archivos estáticos en /quality_files/
_QUALITY_OUTPUT = Path(__file__).parent / "quality_output"
_QUALITY_OUTPUT.mkdir(exist_ok=True)
app.mount("/quality_files", StaticFiles(directory=str(_QUALITY_OUTPUT)), name="quality_files")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stories_router)
app.include_router(quality_router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}
