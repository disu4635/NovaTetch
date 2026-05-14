"""Router de calidad: agentes V3 (Test Architect) + V4 (Risk Matrix) + PDF."""

import json
import threading
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db, QualityRun, RunRecord

router = APIRouter(prefix="/api/quality", tags=["quality"])

OUTPUT_DIR = Path(__file__).parent.parent / "quality_output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Progreso en memoria (transitorio — se pierde al reiniciar el servidor)
_progress: dict[str, str] = {}


# ── Schemas ──────────────────────────────────────────────────────────────────

class StartQualityResponse(BaseModel):
    quality_run_id: str


class QualityStatusResponse(BaseModel):
    quality_run_id: str
    run_id: str
    status: str
    progress_msg: Optional[str] = None
    contract_b: Optional[dict] = None
    error: Optional[str] = None


class ScenarioDecision(BaseModel):
    scenario_name: str
    action: str                          # "accepted" | "reclassified" | "comment"
    new_quality_characteristic: Optional[str] = None
    reason: Optional[str] = None


class SubmitReviewRequest(BaseModel):
    reviewer: str
    decisions: list[ScenarioDecision] = []
    feedback: Optional[str] = None
    review_status: str = "approved"      # "approved" | "rejected" | "needs_changes"
    use_llm_risk: bool = True


class ReviewResult(BaseModel):
    quality_run_id: str
    pdf_available: bool
    pdf_url: Optional[str] = None
    risk_matrix: Optional[dict] = None
    reviewed_contract_b: Optional[dict] = None


class QualityForRunResponse(BaseModel):
    found: bool
    quality_run_id: Optional[str] = None
    status: Optional[str] = None
    has_review: bool = False
    contract_b: Optional[dict] = None
    risk_matrix: Optional[dict] = None
    pdf_url: Optional[str] = None


# ── Background task ──────────────────────────────────────────────────────────

def _run_v3_background(quality_run_id: str, contract_a_data: dict):
    """Ejecuta el agente V3 en un hilo separado y guarda el resultado en la DB."""
    from database import SessionLocal
    from quality_agent_v3 import run_quality_v3

    def _progress_cb(msg: str):
        _progress[quality_run_id] = msg
        # Persistir el mensaje en DB para durabilidad
        db = SessionLocal()
        try:
            qr = db.query(QualityRun).filter(QualityRun.quality_run_id == quality_run_id).first()
            if qr:
                qr.progress_msg = msg
                db.commit()
        finally:
            db.close()

    db = SessionLocal()
    try:
        contract_b_data = run_quality_v3(contract_a_data, progress_cb=_progress_cb)
        qr = db.query(QualityRun).filter(QualityRun.quality_run_id == quality_run_id).first()
        if qr:
            qr.status = "completed"
            qr.contract_b_json = json.dumps(contract_b_data, ensure_ascii=False, default=str)
            qr.progress_msg = f"Completado: {contract_b_data.get('total_scenarios', 0)} escenarios generados."
            db.commit()
        _progress.pop(quality_run_id, None)
    except Exception as exc:
        db.rollback()
        qr = db.query(QualityRun).filter(QualityRun.quality_run_id == quality_run_id).first()
        if qr:
            qr.status = "failed"
            qr.error = str(exc)
            db.commit()
        _progress.pop(quality_run_id, None)
    finally:
        db.close()


# ── Routes ───────────────────────────────────────────────────────────────────

@router.post("/start/{run_id}", response_model=StartQualityResponse)
def start_quality_analysis(
    run_id: str,
    db: Session = Depends(get_db),
):
    """Inicia el análisis V3 sobre el Contract A de un run existente."""
    record = db.query(RunRecord).filter(RunRecord.run_id == run_id).first()
    if not record or record.status != "completed" or not record.result:
        raise HTTPException(status_code=404, detail="Run no encontrado o no completado")

    try:
        contract_a_data = json.loads(record.result)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="No se pudo leer el Contract A del run")

    quality_run_id = f"qr-{uuid.uuid4().hex[:8]}"
    qr = QualityRun(
        quality_run_id=quality_run_id,
        run_id=run_id,
        status="running",
        progress_msg="Iniciando análisis de calidad...",
    )
    db.add(qr)
    db.commit()

    _progress[quality_run_id] = "Iniciando análisis de calidad..."

    t = threading.Thread(
        target=_run_v3_background,
        args=(quality_run_id, contract_a_data),
        daemon=True,
    )
    t.start()

    return StartQualityResponse(quality_run_id=quality_run_id)


@router.get("/status/{quality_run_id}", response_model=QualityStatusResponse)
def get_quality_status(quality_run_id: str, db: Session = Depends(get_db)):
    """Retorna el estado actual del análisis de calidad (para polling)."""
    qr = db.query(QualityRun).filter(QualityRun.quality_run_id == quality_run_id).first()
    if not qr:
        raise HTTPException(status_code=404, detail="Quality run no encontrado")

    contract_b = None
    if qr.status == "completed" and qr.contract_b_json:
        contract_b = json.loads(qr.contract_b_json)

    progress_msg = _progress.get(quality_run_id) or qr.progress_msg

    return QualityStatusResponse(
        quality_run_id=quality_run_id,
        run_id=qr.run_id,
        status=qr.status,
        progress_msg=progress_msg,
        contract_b=contract_b,
        error=qr.error,
    )


@router.post("/review/{quality_run_id}", response_model=ReviewResult)
def submit_review(
    quality_run_id: str,
    body: SubmitReviewRequest,
    db: Session = Depends(get_db),
):
    """Aplica las decisiones del revisor al Contract B, genera riesgos y el PDF."""
    from quality_agent_v4_risk import generar_matriz_riesgos
    from quality_pdf import generar_acta_pdf
    from src.contract_b import (
        GherkinTestSuite, QualityCharacteristic, ReviewChange, ReviewStatus
    )

    qr = db.query(QualityRun).filter(QualityRun.quality_run_id == quality_run_id).first()
    if not qr:
        raise HTTPException(status_code=404, detail="Quality run no encontrado")
    if qr.status != "completed" or not qr.contract_b_json:
        raise HTTPException(status_code=400, detail="El análisis V3 aún no ha completado")

    suite_data = json.loads(qr.contract_b_json)
    suite = GherkinTestSuite(**suite_data)

    # Snapshot de la matriz antes de aplicar cambios
    matriz_original = deepcopy(suite.coverage_by_characteristic)

    # Indexar todos los escenarios por nombre para lookup rápido
    todos = [s for f in suite.features for s in f.scenarios]
    sc_by_name = {s.name: s for s in todos}

    change_history: list[ReviewChange] = []
    reclasificaciones = []

    valid_qc = {qc.value for qc in QualityCharacteristic}

    for dec in body.decisions:
        sc = sc_by_name.get(dec.scenario_name)
        if sc is None:
            continue

        if dec.action == "accepted":
            change_history.append(ReviewChange(
                reviewer=body.reviewer,
                action="accepted",
                notes=f"Escenario '{sc.name}': clasificación '{sc.quality_characteristic.value}' confirmada.",
            ))

        elif dec.action == "reclassified":
            new_qc_raw = dec.new_quality_characteristic or ""
            if new_qc_raw not in valid_qc:
                continue
            new_qc = QualityCharacteristic(new_qc_raw)
            if new_qc == sc.quality_characteristic:
                continue

            qc_anterior = sc.quality_characteristic.value
            sc.quality_characteristic = new_qc
            nuevo_tag = f"@iso-{new_qc.value.replace('_', '-')}"
            sc.tags = [t for t in sc.tags if not t.lower().startswith("@iso-")]
            if nuevo_tag not in sc.tags:
                sc.tags.append(nuevo_tag)

            change_history.append(ReviewChange(
                reviewer=body.reviewer,
                action="reclassified",
                notes=(
                    f"Escenario '{sc.name}': "
                    f"{qc_anterior} -> {new_qc.value}. Razon: {dec.reason or '(sin razón)'}"
                ),
            ))
            reclasificaciones.append({
                "nombre":     sc.name,
                "qc_antes":   qc_anterior,
                "qc_despues": new_qc.value,
                "razon":      dec.reason or "",
            })

        elif dec.action == "comment":
            change_history.append(ReviewChange(
                reviewer=body.reviewer,
                action="comment_added",
                notes=f"Escenario '{sc.name}': {dec.reason or '(sin comentario)'}",
            ))

    # Actualizar review metadata en el suite
    status_map = {
        "approved":      ReviewStatus.APPROVED,
        "rejected":      ReviewStatus.REJECTED,
        "needs_changes": ReviewStatus.NEEDS_CHANGES,
    }
    new_status = status_map.get(body.review_status, ReviewStatus.APPROVED)
    suite.review.review_status = new_status
    suite.review.approved_by = body.reviewer
    if new_status == ReviewStatus.APPROVED:
        suite.review.approved_at = datetime.now()
    if body.feedback:
        suite.review.analyst_feedback = body.feedback
    suite.review.change_history.extend(change_history)

    # Recalcular matriz de cobertura si hubo reclasificaciones
    if reclasificaciones:
        nueva_matriz = {qc.value: 0 for qc in QualityCharacteristic}
        for s in todos:
            nueva_matriz[s.quality_characteristic.value] += 1
        suite.coverage_by_characteristic = nueva_matriz

    # Construir resumen para el PDF
    n_aceptados  = sum(1 for c in change_history if c.action == "accepted")
    n_comentados = sum(1 for c in change_history if c.action == "comment_added")
    resumen = {
        "reviewer":          body.reviewer,
        "estado_final":      new_status.value,
        "n_total":           len(todos),
        "n_aceptados":       n_aceptados,
        "n_saltados":        max(0, len(todos) - len(body.decisions)),
        "n_comentados":      n_comentados,
        "reclasificaciones": reclasificaciones,
        "comentarios":       [],
        "deltas_matriz":     [],
        "feedback_global":   body.feedback or "",
        "hubo_cambios":      len(reclasificaciones) > 0,
    }

    # Generar matriz de riesgos V4
    reviewed_data = json.loads(suite.model_dump_json())
    matriz_riesgos = generar_matriz_riesgos(reviewed_data, usar_llm=body.use_llm_risk)

    # Guardar Contract B revisado con nombre determinístico (sin timestamp)
    json_path = OUTPUT_DIR / f"{quality_run_id}_reviewed.json"
    json_path.write_text(suite.model_dump_json(indent=2), encoding="utf-8")

    # Generar PDF con nombre determinístico para servir como archivo estático
    # El PDF va a quality_output/{quality_run_id}.pdf → accesible en /quality_files/{quality_run_id}.pdf
    pdf_data_path = OUTPUT_DIR / f"{quality_run_id}.json"  # proxy para que .with_suffix() dé el nombre correcto
    pdf_path = None
    pdf_url = None
    try:
        # Pasamos quality_run_id.json → generar_acta_pdf lo convierte a quality_run_id.pdf
        pdf_path = generar_acta_pdf(suite, pdf_data_path, resumen, matriz_riesgos)
        pdf_url = f"/quality_files/{quality_run_id}.pdf"
    except Exception:
        pass

    # Persistir en DB
    qr.contract_b_json   = json.dumps(reviewed_data, ensure_ascii=False, default=str)
    qr.risk_matrix_json  = json.dumps(matriz_riesgos, ensure_ascii=False, default=str)
    qr.pdf_path          = str(pdf_path) if pdf_path else None
    db.commit()

    return ReviewResult(
        quality_run_id=quality_run_id,
        pdf_available=pdf_path is not None and pdf_path.exists(),
        pdf_url=pdf_url,
        risk_matrix=matriz_riesgos,
        reviewed_contract_b=reviewed_data,
    )


@router.get("/for-run/{run_id}", response_model=QualityForRunResponse)
def get_quality_for_run(run_id: str, db: Session = Depends(get_db)):
    """Retorna el quality run más reciente completado para un run de historias."""
    qr = (
        db.query(QualityRun)
        .filter(QualityRun.run_id == run_id, QualityRun.status == "completed")
        .order_by(QualityRun.created_at.desc())
        .first()
    )
    if not qr:
        return QualityForRunResponse(found=False)

    contract_b = json.loads(qr.contract_b_json) if qr.contract_b_json else None
    risk_matrix = json.loads(qr.risk_matrix_json) if qr.risk_matrix_json else None

    pdf_url = None
    if qr.pdf_path:
        pdf_file = Path(qr.pdf_path)
        if pdf_file.exists():
            pdf_url = f"/quality_files/{qr.quality_run_id}.pdf"

    return QualityForRunResponse(
        found=True,
        quality_run_id=qr.quality_run_id,
        status=qr.status,
        has_review=risk_matrix is not None,
        contract_b=contract_b,
        risk_matrix=risk_matrix,
        pdf_url=pdf_url,
    )


def _resumen_desde_suite(suite) -> dict:
    """Reconstruye el dict resumen mínimo desde el historial del suite."""
    acciones = suite.review.change_history
    return {
        "reviewer":          suite.review.approved_by or "",
        "estado_final":      suite.review.review_status.value,
        "n_total":           suite.total_scenarios,
        "n_aceptados":       sum(1 for c in acciones if c.action == "accepted"),
        "n_saltados":        0,
        "n_comentados":      sum(1 for c in acciones if c.action == "comment_added"),
        "reclasificaciones": [],
        "comentarios":       [],
        "deltas_matriz":     [],
        "feedback_global":   suite.review.analyst_feedback or "",
        "hubo_cambios":      any(c.action == "reclassified" for c in acciones),
    }


def _generar_pdf(qr: QualityRun, db) -> Path:
    """Genera (o regenera) el PDF de un quality run y actualiza la DB."""
    from quality_pdf import generar_acta_pdf
    from src.contract_b import GherkinTestSuite

    if not qr.contract_b_json:
        raise HTTPException(status_code=400, detail="Sin datos del Contract B para generar el PDF")

    suite = GherkinTestSuite(**json.loads(qr.contract_b_json))
    matriz_riesgos = json.loads(qr.risk_matrix_json) if qr.risk_matrix_json else None
    resumen = _resumen_desde_suite(suite)

    pdf_data_path = OUTPUT_DIR / f"{qr.quality_run_id}.json"
    pdf_path = generar_acta_pdf(suite, pdf_data_path, resumen, matriz_riesgos)

    qr.pdf_path = str(pdf_path)
    db.commit()
    return pdf_path


@router.get("/download/{quality_run_id}")
def download_pdf(quality_run_id: str, db: Session = Depends(get_db)):
    """Descarga el PDF. Si el archivo no existe lo regenera automáticamente."""
    qr = db.query(QualityRun).filter(QualityRun.quality_run_id == quality_run_id).first()
    if not qr:
        raise HTTPException(status_code=404, detail="Quality run no encontrado")
    if not qr.risk_matrix_json:
        raise HTTPException(status_code=400, detail="La revisión aún no fue completada")

    pdf_path = Path(qr.pdf_path) if qr.pdf_path else None

    if not pdf_path or not pdf_path.exists():
        try:
            pdf_path = _generar_pdf(qr, db)
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Error al generar el PDF: {exc}")

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=f"acta_calidad_{quality_run_id}.pdf",
        headers={"Content-Disposition": f'attachment; filename="acta_calidad_{quality_run_id}.pdf"'},
    )
