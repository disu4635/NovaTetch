import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db, RunRecord
from agent import WebAgent

router = APIRouter(prefix="/api/stories", tags=["stories"])


# ── Request / Response schemas ──────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    prompt: str


class AmbiguityOut(BaseModel):
    word: str
    category: str
    ieee_830_violation: str
    iso_25010_category: str
    suggestion: str
    context: str
    severity: str


class AnalyzeResponse(BaseModel):
    ambiguities: list[AmbiguityOut]


class Resolution(BaseModel):
    word: str
    category: str = ''
    analyst_resolution: str
    status: str  # "resolved" | "dismissed"


class GenerateRequest(BaseModel):
    prompt: str
    resolutions: list[Resolution] = []


class RunSummary(BaseModel):
    run_id: str
    prompt: str
    status: str
    created_at: datetime
    story_count: Optional[int] = None


class RunDetail(RunSummary):
    result: Optional[dict] = None
    error: Optional[str] = None


# ── Routes ───────────────────────────────────────────────────────────────────

@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_prompt(body: AnalyzeRequest):
    agent = WebAgent.get_instance()
    ambiguities = agent.analyze_ambiguities(body.prompt)
    return AnalyzeResponse(ambiguities=ambiguities)


@router.post("/generate", response_model=RunDetail)
def generate_stories(body: GenerateRequest, db: Session = Depends(get_db)):
    agent = WebAgent.get_instance()

    resolutions = [r.model_dump() for r in body.resolutions]

    # Create a pending record first
    import uuid
    temp_id = f"run-{uuid.uuid4().hex[:8]}"
    record = RunRecord(
        run_id=temp_id,
        prompt=body.prompt,
        status="pending",
    )
    db.add(record)
    db.commit()

    try:
        result = agent.generate_stories(body.prompt, resolutions)
        result_dict = result.model_dump(mode="json")

        record.run_id = result.pipeline_run_id
        record.status = "completed"
        record.result = json.dumps(result_dict, ensure_ascii=False, default=str)
        db.commit()

        return RunDetail(
            run_id=result.pipeline_run_id,
            prompt=body.prompt,
            status="completed",
            created_at=record.created_at,
            story_count=len(result.user_stories),
            result=result_dict,
        )

    except Exception as e:
        record.status = "failed"
        record.error = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs", response_model=list[RunSummary])
def list_runs(db: Session = Depends(get_db)):
    runs = db.query(RunRecord).order_by(RunRecord.created_at.desc()).limit(50).all()
    result = []
    for r in runs:
        story_count = None
        if r.result:
            try:
                data = json.loads(r.result)
                story_count = len(data.get("user_stories", []))
            except Exception:
                pass
        result.append(RunSummary(
            run_id=r.run_id,
            prompt=r.prompt,
            status=r.status,
            created_at=r.created_at,
            story_count=story_count,
        ))
    return result


@router.delete("/runs/{run_id}", status_code=204)
def delete_run(run_id: str, db: Session = Depends(get_db)):
    record = db.query(RunRecord).filter(RunRecord.run_id == run_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Run not found")
    db.delete(record)
    db.commit()


@router.get("/runs/{run_id}", response_model=RunDetail)
def get_run(run_id: str, db: Session = Depends(get_db)):
    record = db.query(RunRecord).filter(RunRecord.run_id == run_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Run not found")

    result_dict = None
    story_count = None
    if record.result:
        result_dict = json.loads(record.result)
        story_count = len(result_dict.get("user_stories", []))

    return RunDetail(
        run_id=record.run_id,
        prompt=record.prompt,
        status=record.status,
        created_at=record.created_at,
        story_count=story_count,
        result=result_dict,
        error=record.error,
    )
