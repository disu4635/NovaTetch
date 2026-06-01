"""Router de generación de código: pipeline V3 + revisión HITL senior."""

import io
import json
import threading
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db, CodeGenRun, QualityRun

router = APIRouter(prefix="/api/codegen", tags=["codegen"])

_progress: dict[str, str] = {}


# ── Schemas ──────────────────────────────────────────────────────────────────

class StartCodegenResponse(BaseModel):
    codegen_run_id: str


class CodegenStatusResponse(BaseModel):
    codegen_run_id: str
    quality_run_id: str
    status: str
    progress_msg: Optional[str] = None
    contract_c: Optional[dict] = None
    error: Optional[str] = None


class ModuleAction(BaseModel):
    module_name: str
    action: str                    # "accepted" | "smell_flagged" | "skipped"
    notes: Optional[str] = None


class SubmitCodeReviewRequest(BaseModel):
    reviewer: str
    module_actions: list[ModuleAction] = []
    verdict: str = "approved"      # "approved" | "rejected" | "needs_changes"
    feedback: Optional[str] = None


class CodeReviewResult(BaseModel):
    codegen_run_id: str
    reviewed_contract_c: dict


class CodegenForQualityResponse(BaseModel):
    found: bool
    codegen_run_id: Optional[str] = None
    status: Optional[str] = None
    has_review: bool = False
    contract_c: Optional[dict] = None


# ── Background task ──────────────────────────────────────────────────────────

def _run_codegen_background(codegen_run_id: str, contract_b_data: dict):
    from database import SessionLocal
    from codegen_agent import run_codegen

    def _progress_cb(msg: str):
        _progress[codegen_run_id] = msg
        db = SessionLocal()
        try:
            cr = db.query(CodeGenRun).filter(CodeGenRun.codegen_run_id == codegen_run_id).first()
            if cr:
                cr.progress_msg = msg
                db.commit()
        finally:
            db.close()

    db = SessionLocal()
    try:
        contract_c_data = run_codegen(contract_b_data, progress_cb=_progress_cb)
        cr = db.query(CodeGenRun).filter(CodeGenRun.codegen_run_id == codegen_run_id).first()
        if cr:
            cr.status = "completed"
            cr.contract_c_json = json.dumps(contract_c_data, ensure_ascii=False, default=str)
            cr.progress_msg = (
                f"Completado: {contract_c_data.get('total_modules', 0)} módulos, "
                f"{contract_c_data.get('total_tests', 0)} tests"
            )
            db.commit()
        _progress.pop(codegen_run_id, None)
    except Exception as exc:
        db.rollback()
        cr = db.query(CodeGenRun).filter(CodeGenRun.codegen_run_id == codegen_run_id).first()
        if cr:
            cr.status = "failed"
            cr.error = str(exc)
            db.commit()
        _progress.pop(codegen_run_id, None)
    finally:
        db.close()


# ── Routes ───────────────────────────────────────────────────────────────────

@router.post("/start/{quality_run_id}", response_model=StartCodegenResponse)
def start_codegen(quality_run_id: str, db: Session = Depends(get_db)):
    """Inicia el pipeline V3 usando el Contract B revisado de un quality run."""
    qr = db.query(QualityRun).filter(QualityRun.quality_run_id == quality_run_id).first()
    if not qr or qr.status != "completed" or not qr.contract_b_json:
        raise HTTPException(status_code=404, detail="Quality run no encontrado o sin Contract B")

    contract_b_data = json.loads(qr.contract_b_json)

    codegen_run_id = f"cg-{uuid.uuid4().hex[:8]}"
    cr = CodeGenRun(
        codegen_run_id=codegen_run_id,
        quality_run_id=quality_run_id,
        run_id=qr.run_id,
        status="running",
        progress_msg="Iniciando generación de código...",
    )
    db.add(cr)
    db.commit()

    _progress[codegen_run_id] = "Iniciando generación de código..."

    t = threading.Thread(
        target=_run_codegen_background,
        args=(codegen_run_id, contract_b_data),
        daemon=True,
    )
    t.start()

    return StartCodegenResponse(codegen_run_id=codegen_run_id)


@router.get("/status/{codegen_run_id}", response_model=CodegenStatusResponse)
def get_codegen_status(codegen_run_id: str, db: Session = Depends(get_db)):
    cr = db.query(CodeGenRun).filter(CodeGenRun.codegen_run_id == codegen_run_id).first()
    if not cr:
        raise HTTPException(status_code=404, detail="Codegen run no encontrado")

    contract_c = None
    if cr.status == "completed" and cr.contract_c_json:
        contract_c = json.loads(cr.contract_c_json)

    return CodegenStatusResponse(
        codegen_run_id=codegen_run_id,
        quality_run_id=cr.quality_run_id,
        status=cr.status,
        progress_msg=_progress.get(codegen_run_id) or cr.progress_msg,
        contract_c=contract_c,
        error=cr.error,
    )


@router.post("/review/{codegen_run_id}", response_model=CodeReviewResult)
def submit_code_review(
    codegen_run_id: str,
    body: SubmitCodeReviewRequest,
    db: Session = Depends(get_db),
):
    """Aplica las decisiones del revisor senior al Contract C."""
    from src.contract_c import (
        CodeGenerationResult, ReviewChange, ReviewStatus,
    )

    cr = db.query(CodeGenRun).filter(CodeGenRun.codegen_run_id == codegen_run_id).first()
    if not cr:
        raise HTTPException(status_code=404, detail="Codegen run no encontrado")
    if cr.status != "completed" or not cr.contract_c_json:
        raise HTTPException(status_code=400, detail="El pipeline aún no ha completado")

    resultado = CodeGenerationResult(**json.loads(cr.contract_c_json))

    # Registrar acciones por módulo
    for action in body.module_actions:
        if action.action == "skipped":
            continue
        resultado.review.change_history.append(ReviewChange(
            reviewer=body.reviewer,
            action=action.action,
            target=action.module_name,
            notes=action.notes,
        ))

    # Aplicar veredicto global
    v = body.verdict.lower()
    if v in ("approved", "aprobar", "aprobado"):
        resultado.review.review_status = ReviewStatus.APPROVED
        resultado.review.approved_by = body.reviewer
        resultado.review.approved_at = datetime.now()
        accion = "approved"
    elif v in ("rejected", "rechazar", "rechazado"):
        resultado.review.review_status = ReviewStatus.REJECTED
        accion = "rejected"
    else:
        resultado.review.review_status = ReviewStatus.NEEDS_CHANGES
        resultado.review.version += 1
        accion = "changes_requested"

    if body.feedback:
        resultado.review.reviewer_feedback = body.feedback

    resultado.review.change_history.append(ReviewChange(
        reviewer=body.reviewer,
        action=accion,
        notes=body.feedback or f"Veredicto final: {accion}",
    ))

    reviewed_data = json.loads(resultado.model_dump_json())
    cr.contract_c_json = json.dumps(reviewed_data, ensure_ascii=False, default=str)
    db.commit()

    # Regenerar el PDF ejecutivo incluyendo los datos del código (Sección 8)
    try:
        from quality_pdf import generar_acta_pdf
        from src.contract_b import GherkinTestSuite

        qr = db.query(QualityRun).filter(QualityRun.quality_run_id == cr.quality_run_id).first()
        if qr and qr.contract_b_json:
            suite_b = GherkinTestSuite(**json.loads(qr.contract_b_json))
            risk_matrix = json.loads(qr.risk_matrix_json) if qr.risk_matrix_json else None

            acciones_b = suite_b.review.change_history
            resumen_b = {
                "reviewer":          suite_b.review.approved_by or "",
                "estado_final":      suite_b.review.review_status.value,
                "n_total":           suite_b.total_scenarios,
                "n_aceptados":       sum(1 for c in acciones_b if c.action == "accepted"),
                "n_saltados":        0,
                "n_comentados":      sum(1 for c in acciones_b if c.action == "comment_added"),
                "reclasificaciones": [],
                "comentarios":       [],
                "deltas_matriz":     [],
                "feedback_global":   suite_b.review.analyst_feedback or "",
                "hubo_cambios":      any(c.action == "reclassified" for c in acciones_b),
            }

            from pathlib import Path as _Path
            _OUTPUT_DIR = _Path(__file__).parent.parent / "quality_output"
            pdf_data_path = _OUTPUT_DIR / f"{qr.quality_run_id}.json"
            new_pdf = generar_acta_pdf(
                suite_b, pdf_data_path, resumen_b, risk_matrix,
                contract_c_data=reviewed_data,
            )
            qr.pdf_path = str(new_pdf)
            db.commit()
    except Exception:
        pass  # Si falla la regeneración del PDF no rompemos el flujo principal

    return CodeReviewResult(
        codegen_run_id=codegen_run_id,
        reviewed_contract_c=reviewed_data,
    )


@router.get("/for-quality-run/{quality_run_id}", response_model=CodegenForQualityResponse)
def get_codegen_for_quality_run(quality_run_id: str, db: Session = Depends(get_db)):
    """Retorna el codegen run más reciente para un quality run (para restaurar estado)."""
    cr = (
        db.query(CodeGenRun)
        .filter(CodeGenRun.quality_run_id == quality_run_id, CodeGenRun.status == "completed")
        .order_by(CodeGenRun.created_at.desc())
        .first()
    )
    if not cr:
        return CodegenForQualityResponse(found=False)

    contract_c = json.loads(cr.contract_c_json) if cr.contract_c_json else None

    has_review = False
    if contract_c:
        review = contract_c.get("review", {})
        has_review = review.get("review_status") not in ("pending_review", None)

    return CodegenForQualityResponse(
        found=True,
        codegen_run_id=cr.codegen_run_id,
        status=cr.status,
        has_review=has_review,
        contract_c=contract_c,
    )


@router.get("/download/{codegen_run_id}")
def download_code(codegen_run_id: str, db: Session = Depends(get_db)):
    """Descarga el código generado como ZIP."""
    cr = db.query(CodeGenRun).filter(CodeGenRun.codegen_run_id == codegen_run_id).first()
    if not cr or not cr.contract_c_json:
        raise HTTPException(status_code=404, detail="Código no disponible")

    data = json.loads(cr.contract_c_json)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for mod in data.get("generated_code", []):
            zf.writestr(f"src/{mod['filename']}", mod["source_code"])
        for test in data.get("generated_tests", []):
            nombre = test["test_name"]
            if not nombre.startswith("test_"):
                nombre = f"test_{nombre}"
            if not nombre.endswith(".py"):
                nombre = f"{nombre}.py"
            zf.writestr(f"tests/{nombre}", test["source_code"])
        # conftest.py
        zf.writestr(
            "tests/conftest.py",
            "def pytest_configure(config):\n"
            '    config.addinivalue_line("markers", "scenario(id): vincula un test a un escenario")\n',
        )
        # metadata
        meta = {
            "pipeline_run_id": data.get("pipeline_run_id"),
            "agent_version": data.get("agent_version"),
            "source_contract_b_id": data.get("source_contract_b_id"),
            "total_modules": data.get("total_modules"),
            "total_tests": data.get("total_tests"),
        }
        zf.writestr("metadata.json", json.dumps(meta, indent=2))

    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="codigo_{codegen_run_id}.zip"'},
    )
