"""Contract B: Test Architect → Code Generator.

Schema de salida del agente de calidad (V3).
Transforma criterios de aceptación en casos de prueba Gherkin (BDD)
completos, clasificados por ISO/IEC 25010.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ScenarioType(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    BOUNDARY = "boundary"
    EDGE_CASE = "edge_case"
    ERROR_HANDLING = "error_handling"


class QualityCharacteristic(str, Enum):
    FUNCTIONAL_SUITABILITY = "functional_suitability"
    PERFORMANCE_EFFICIENCY = "performance_efficiency"
    COMPATIBILITY = "compatibility"
    USABILITY = "usability"
    RELIABILITY = "reliability"
    SECURITY = "security"
    MAINTAINABILITY = "maintainability"
    PORTABILITY = "portability"


class ReviewStatus(str, Enum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_CHANGES = "needs_changes"


class ReviewChange(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    reviewer: str = Field(..., min_length=1)
    action: str = Field(...)
    notes: Optional[str] = Field(default=None)


class ReviewMetadata(BaseModel):
    review_status: ReviewStatus = Field(default=ReviewStatus.PENDING_REVIEW)
    version: int = Field(default=1, ge=1)
    approved_by: Optional[str] = Field(default=None)
    approved_at: Optional[datetime] = Field(default=None)
    analyst_feedback: Optional[str] = Field(default=None)
    change_history: list[ReviewChange] = Field(default_factory=list)


class GherkinStep(BaseModel):
    keyword: str = Field(..., pattern=r"^(Given|When|Then|And|But)$")
    text: str = Field(..., min_length=5)
    data_table: Optional[list[dict]] = Field(default=None)
    doc_string: Optional[str] = Field(default=None)


class ExamplesTable(BaseModel):
    headers: list[str] = Field(...)
    rows: list[list[str]] = Field(..., min_length=1)


class GherkinScenario(BaseModel):
    name: str = Field(..., min_length=10)
    scenario_type: ScenarioType = Field(default=ScenarioType.POSITIVE)
    quality_characteristic: QualityCharacteristic = Field(
        default=QualityCharacteristic.FUNCTIONAL_SUITABILITY
    )
    tags: list[str] = Field(default_factory=list)
    steps: list[GherkinStep] = Field(..., min_length=3)
    is_outline: bool = Field(default=False)
    examples: Optional[ExamplesTable] = Field(default=None)
    acceptance_criterion_id: str = Field(...)
    user_story_id: str = Field(...)


class GherkinFeature(BaseModel):
    name: str = Field(..., min_length=10)
    description: str = Field(...)
    tags: list[str] = Field(default_factory=list)
    background: Optional[list[GherkinStep]] = Field(default=None)
    scenarios: list[GherkinScenario] = Field(..., min_length=1)
    user_story_id: str = Field(...)


class CoverageMatrix(BaseModel):
    user_story_id: str
    criterion_id: str
    scenario_names: list[str] = Field(..., min_length=1)
    coverage_type: list[ScenarioType] = Field(...)
    quality_characteristics_covered: list[QualityCharacteristic] = Field(
        default_factory=list
    )


class GherkinTestSuite(BaseModel):
    pipeline_run_id: str = Field(...)
    agent_name: str = Field(default="test_architect")
    agent_version: str = Field(default="0.3.0-v3-iso25010")
    created_at: datetime = Field(default_factory=datetime.now)

    features: list[GherkinFeature] = Field(..., min_length=1)
    coverage_matrix: list[CoverageMatrix] = Field(...)

    review: ReviewMetadata = Field(default_factory=ReviewMetadata)

    total_scenarios: int = Field(default=0)
    total_positive: int = Field(default=0)
    total_negative: int = Field(default=0)
    total_boundary: int = Field(default=0)
    uncovered_criteria: list[str] = Field(default_factory=list)

    coverage_by_characteristic: dict[str, int] = Field(default_factory=dict)
