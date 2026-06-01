"""Contract C: Code Generator → Functional Tester.

Define el schema de salida del Agente 3 (Code Generator).
Transforma el Contract B (escenarios Gherkin del Test Architect) en código
Python + tests Pytest, acompañado de un Quality Report estructurado por
característica ISO 25010, una matriz de trazabilidad CMMI L3 y un reporte
de cobertura.

Principios de diseño:
- Cada escenario del Contract B debe ser cubierto por al menos un test
  (trazabilidad bidireccional — ningún huérfano).
- El código generado se mide objetivamente: CC, CogC, MI, hallazgos de
  seguridad. El agente NO finge medir lo que no puede medir — declara
  MEASURED / REQUIRES_HUMAN_JUDGMENT / NOT_APPLICABLE (anti checkbox-compliance).
- La matriz de trazabilidad vive DENTRO del contrato, no como anexo externo.
  Es la evidencia auditable que reemplaza al Excel manual de la certificación.
- El bucle de revisión humana del desarrollador senior vive DENTRO del
  contrato (ReviewMetadata). Cubre lo que las métricas no miden: naming,
  design intent, code smells subjetivos.

Evolución del schema a lo largo del módulo (patrón V1→V4):
- V1: GeneratedCodeModule + GeneratedTest. Sin métricas, sin trazabilidad,
      sin coverage. El "Contract C ingenuo".
- V2: agrega QualityReport (CC/CogC/MI por función + Bandit + ISO 25010).
- V3: agrega TraceabilityMatrix + CoverageReport.
- V4: agrega ReviewMetadata (HITL del desarrollador senior).

Versión 0.1.0:
- Schema base completo. Los campos de V2/V3/V4 son Optional y quedan en None
  en las versiones tempranas del agente — se pueblan progresivamente.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ============================================================
# ENUMS
# ============================================================
class QualityCharacteristic(str, Enum):
    """Las 8 características de calidad de producto según ISO/IEC 25010:2011.

    En M2 estas etiquetas se aplicaban a CASOS DE PRUEBA. En M3 se aplican
    al PRODUCTO: cada métrica del Quality Report reporta a una de estas
    características. Mismo estándar, entidad clasificada distinta.
    """

    FUNCTIONAL_SUITABILITY = "functional_suitability"  # ¿hace lo que debe?
    PERFORMANCE_EFFICIENCY = "performance_efficiency"  # ¿rendimiento adecuado?
    COMPATIBILITY = "compatibility"                    # ¿funciona en distintos entornos?
    USABILITY = "usability"                            # ¿es fácil de usar?
    RELIABILITY = "reliability"                        # ¿es estable y resiliente?
    SECURITY = "security"                              # ¿está protegido?
    MAINTAINABILITY = "maintainability"                # ¿es fácil de modificar?
    PORTABILITY = "portability"                        # ¿se puede mover de entorno?


class MeasurementStatus(str, Enum):
    """Estado de medición de una característica ISO 25010 en el Quality Report.

    El agente M3 declara honestamente qué puede medir y qué no. Esto es la
    defensa contra el 'checkbox compliance' (marcar todo en verde sin evidencia).
    """

    MEASURED = "measured"                                  # medido con herramienta objetiva
    REQUIRES_HUMAN_JUDGMENT = "requires_human_judgment"     # necesita el revisor senior (V4)
    NOT_APPLICABLE = "not_applicable"                       # fuera del alcance del análisis estático


class ComplexityBand(str, Enum):
    """Bandas de complejidad de radon para Cyclomatic Complexity.

    A: 1-5 simple | B: 6-10 moderado | C: 11-20 complejo
    D: 21-50 muy complejo | E: >50 no mantenible
    """

    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"


class TraceabilityStatus(str, Enum):
    """Estado de un nodo en la matriz de trazabilidad bidireccional.

    Un escenario sin test es huérfano forward. Un test sin escenario es
    huérfano backward. CMMI L3 exige cero huérfanos en ambas direcciones.
    """

    COVERED = "covered"                  # tiene al menos una conexión
    ORPHAN_FORWARD = "orphan_forward"     # escenario sin ningún test
    ORPHAN_BACKWARD = "orphan_backward"   # test sin ningún escenario


class SecuritySeverity(str, Enum):
    """Severidad de un hallazgo de seguridad (Bandit)."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ReviewStatus(str, Enum):
    """Estado de revisión del Contract C por parte del desarrollador senior.

    El bucle Human-in-the-Loop está formalizado dentro del contrato: el
    desarrollador senior debe aprobar antes de que el código avance al
    Módulo 4 (Functional Tester).
    """

    PENDING_REVIEW = "pending_review"  # recién generado, aún no revisado
    APPROVED = "approved"              # aprobado, listo para Módulo 4
    REJECTED = "rejected"              # rechazado, no avanza al Módulo 4
    NEEDS_CHANGES = "needs_changes"    # aprobación condicional con cambios


# ============================================================
# CÓDIGO Y TESTS GENERADOS (V1+)
# ============================================================
class GeneratedCodeModule(BaseModel):
    """Un módulo de código Python generado por el agente.

    Representa un archivo .py con la implementación que satisface los
    escenarios del Contract B.
    """

    filename: str = Field(
        ...,
        description="Nombre del archivo (ej: 'auth.py')",
        min_length=3,
    )
    source_code: str = Field(
        ...,
        description="Código fuente Python completo del módulo",
        min_length=10,
    )
    description: str = Field(
        ...,
        description="Qué hace este módulo (narrativa breve)",
    )
    user_story_id: str = Field(
        ...,
        description="ID de la historia de usuario que implementa (ej: US-001)",
    )


class GeneratedTest(BaseModel):
    """Un test Pytest generado por el agente.

    CRÍTICO PARA TRAZABILIDAD: cada test referencia los escenarios del
    Contract B que verifica mediante `scenario_ids`. En el código real
    esto se materializa con @pytest.mark.scenario("SCN-XXX"). Un test sin
    scenario_ids es un huérfano backward.
    """

    test_name: str = Field(
        ...,
        description="Nombre de la función de test (ej: 'test_login_exitoso')",
        min_length=5,
    )
    source_code: str = Field(
        ...,
        description="Código fuente Python del test (incluye los markers)",
        min_length=10,
    )
    scenario_ids: list[str] = Field(
        default_factory=list,
        description=(
            "IDs de escenarios del Contract B que este test verifica. "
            "Se materializa con @pytest.mark.scenario(...). "
            "Lista vacía = test huérfano backward (viola trazabilidad CMMI L3)."
        ),
    )
    target_module: str = Field(
        ...,
        description="Archivo de código que este test ejercita (ej: 'auth.py')",
    )


# ============================================================
# QUALITY REPORT — métricas de calidad de código (V2+)
# ============================================================
class FunctionMetrics(BaseModel):
    """Métricas de complejidad de una función individual.

    CC y CogC mandan en la decisión por función (Tema 1). La brecha
    CogC - CC es la herramienta diagnóstica: brecha grande = anidamiento.
    """

    function_name: str = Field(..., description="Nombre de la función medida")
    module: str = Field(..., description="Archivo donde vive la función")
    cyclomatic_complexity: int = Field(
        ...,
        ge=1,
        description="Cyclomatic Complexity (radon cc). Umbral defendible: < 10",
    )
    cognitive_complexity: int = Field(
        ...,
        ge=0,
        description="Cognitive Complexity (complexipy). Umbral defendible: < 15",
    )
    cc_band: ComplexityBand = Field(
        ...,
        description="Banda de radon para el CC (A-E)",
    )
    nesting_depth: int = Field(
        default=0,
        ge=0,
        description="Profundidad máxima de anidamiento. Umbral defendible: <= 3",
    )
    exceeds_threshold: bool = Field(
        default=False,
        description="True si CC >= 10 o CogC >= 15 (requiere refactor o excepción documentada)",
    )


class SecurityFinding(BaseModel):
    """Un hallazgo de seguridad reportado por Bandit sobre el código generado."""

    test_id: str = Field(..., description="ID de la regla Bandit (ej: B602)")
    severity: SecuritySeverity = Field(..., description="Severidad del hallazgo")
    module: str = Field(..., description="Archivo donde se encontró")
    line_number: int = Field(..., ge=1, description="Línea del hallazgo")
    description: str = Field(..., description="Descripción del problema de seguridad")


class QualityCharacteristicResult(BaseModel):
    """Resultado de una característica ISO 25010 en el Quality Report.

    Cada una de las 8 características tiene una fila. El campo `status`
    declara honestamente si el agente la midió, si necesita juicio humano,
    o si está fuera de alcance. Esto evita el checkbox compliance.
    """

    characteristic: QualityCharacteristic = Field(
        ...,
        description="La característica ISO 25010 evaluada",
    )
    status: MeasurementStatus = Field(
        ...,
        description="MEASURED / REQUIRES_HUMAN_JUDGMENT / NOT_APPLICABLE",
    )
    metrics_used: list[str] = Field(
        default_factory=list,
        description="Métricas/herramientas que sustentan este resultado (ej: ['radon cc', 'complexipy'])",
    )
    verdict: Optional[str] = Field(
        default=None,
        description="Veredicto breve: 'pass', 'fail', o explicación si REQUIRES_HUMAN_JUDGMENT / NOT_APPLICABLE",
    )


class QualityReport(BaseModel):
    """Reporte de calidad del código generado (V2+).

    Estructura el resultado del análisis estático: métricas por función,
    hallazgos de seguridad, y la cobertura de las 8 características ISO 25010.
    En V1 este campo del Contract C queda en None.
    """

    function_metrics: list[FunctionMetrics] = Field(
        default_factory=list,
        description="Métricas CC/CogC/nesting de cada función del código generado",
    )
    maintainability_index: Optional[float] = Field(
        default=None,
        description="Maintainability Index a nivel archivo (radon mi). Umbral radon: >= 20",
    )
    security_findings: list[SecurityFinding] = Field(
        default_factory=list,
        description="Hallazgos de Bandit sobre el código generado",
    )
    iso_25010_coverage: list[QualityCharacteristicResult] = Field(
        default_factory=list,
        description="Una fila por cada una de las 8 características ISO 25010",
    )
    functions_exceeding_threshold: int = Field(
        default=0,
        ge=0,
        description="Cuántas funciones superan CC >= 10 o CogC >= 15",
    )


# ============================================================
# TRAZABILIDAD CMMI L3 — matriz Contract B → Contract C (V3+)
# ============================================================
class ScenarioTraceability(BaseModel):
    """Lado forward de la matriz: un escenario del Contract B y sus tests."""

    scenario_id: str = Field(..., description="ID del escenario del Contract B (ej: SCN-001)")
    scenario_name: str = Field(..., description="Nombre descriptivo del escenario")
    covering_tests: list[str] = Field(
        default_factory=list,
        description="Nombres de los tests que cubren este escenario",
    )
    status: TraceabilityStatus = Field(
        ...,
        description="COVERED si tiene al menos un test; ORPHAN_FORWARD si no",
    )


class TestTraceability(BaseModel):
    """Lado backward de la matriz: un test y los escenarios que lo justifican."""

    test_name: str = Field(..., description="Nombre del test")
    justifying_scenarios: list[str] = Field(
        default_factory=list,
        description="IDs de escenarios que justifican la existencia de este test",
    )
    status: TraceabilityStatus = Field(
        ...,
        description="COVERED si justifica al menos un escenario; ORPHAN_BACKWARD si no",
    )


class TraceabilityMatrix(BaseModel):
    """Matriz de trazabilidad bidireccional Contract B → Contract C (V3+).

    Esta es la evidencia auditable CMMI L3 que reemplaza al Excel manual.
    Se regenera automáticamente cada vez que el agente ejecuta el pipeline.

    Regla maestra: cero huérfanos en ambas direcciones para cumplir L3.
    Many-to-many es válido (un test cubre varios escenarios, un escenario
    tiene varios tests). Solo los nodos aislados violan.
    """

    forward: list[ScenarioTraceability] = Field(
        default_factory=list,
        description="Escenarios del Contract B y los tests que los cubren",
    )
    backward: list[TestTraceability] = Field(
        default_factory=list,
        description="Tests y los escenarios que los justifican",
    )
    requirements_coverage_pct: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="% de escenarios con al menos un test (escenarios cubiertos / total)",
    )
    tests_justified_pct: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="% de tests con al menos un escenario (tests justificados / total)",
    )
    orphan_scenarios: list[str] = Field(
        default_factory=list,
        description="IDs de escenarios sin test (huérfanos forward) — debería estar vacío",
    )
    orphan_tests: list[str] = Field(
        default_factory=list,
        description="Nombres de tests sin escenario (huérfanos backward) — debería estar vacío",
    )
    cmmi_l3_compliant: bool = Field(
        default=False,
        description="True solo si NO hay huérfanos en ninguna dirección",
    )


# ============================================================
# COVERAGE REPORT — cobertura de código (V3+)
# ============================================================
class CoverageReport(BaseModel):
    """Reporte de cobertura de código del agente (V3+).

    Branch coverage es la métrica principal (el estándar de la industria).
    Line coverage se reporta solo como referencia, NO es compuerta.
    """

    branch_coverage_pct: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="% branch coverage (pytest-cov --cov-branch). Umbral M3: >= 80%",
    )
    line_coverage_pct: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="% line coverage. Solo referencia — NO es compuerta de calidad",
    )
    meets_threshold: bool = Field(
        default=False,
        description="True si branch_coverage_pct >= 80 (umbral de negocio M3)",
    )
    uncovered_modules: list[str] = Field(
        default_factory=list,
        description="Archivos con branch coverage por debajo del umbral",
    )


# ============================================================
# REVIEW METADATA — HITL del desarrollador senior (V4+)
# ============================================================
class ReviewChange(BaseModel):
    """Una entrada en el historial de revisión del desarrollador senior.

    Cada acción (aprobar, rechazar, comentar, marcar code smell) genera un
    registro auditable para CMMI-DEV L3.
    """

    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Cuándo ocurrió la acción",
    )
    reviewer: str = Field(
        ...,
        description="Identificador del desarrollador senior que realizó la acción",
        min_length=1,
    )
    action: str = Field(
        ...,
        description="Acción: approved | rejected | comment_added | changes_requested | smell_flagged",
    )
    target: Optional[str] = Field(
        default=None,
        description="A qué aplica la acción (módulo, función, o test específico)",
    )
    notes: Optional[str] = Field(
        default=None,
        description="Notas del revisor. Lo que las métricas no ven: naming, design intent, smells",
    )


class ReviewMetadata(BaseModel):
    """Metadata del bucle de revisión humana del desarrollador senior (V4+).

    Formaliza al revisor senior como parte del contrato. Cubre lo que el
    análisis estático NO mide: legibilidad real, intención del diseño,
    code smells subjetivos, Functional Appropriateness. Sin esta aprobación
    el código NO debe avanzar al Módulo 4.
    """

    review_status: ReviewStatus = Field(
        default=ReviewStatus.PENDING_REVIEW,
        description="Estado actual de la revisión",
    )
    version: int = Field(
        default=1,
        ge=1,
        description="Versión del Contract C (incrementa cuando se solicitan cambios)",
    )
    approved_by: Optional[str] = Field(
        default=None,
        description="Identificador del desarrollador senior que aprobó",
    )
    approved_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp de la aprobación",
    )
    reviewer_feedback: Optional[str] = Field(
        default=None,
        description="Comentario libre del revisor sobre el código completo",
    )
    change_history: list[ReviewChange] = Field(
        default_factory=list,
        description="Historial de acciones del revisor para auditoría CMMI L3",
    )


# ============================================================
# CONTRACT C — el contrato completo
# ============================================================
class CodeGenerationResult(BaseModel):
    """Contract C: Salida del Agente 3 (Code Generator), entrada del Agente 4.

    Contiene el código Python generado, los tests Pytest, y — progresivamente
    según la versión del agente — el Quality Report, la matriz de trazabilidad
    y el reporte de cobertura. El campo `review` formaliza al desarrollador
    senior humano como parte del contrato.

    Campos por versión del agente:
    - V1 puebla: generated_code, generated_tests.
    - V2 agrega: quality_report.
    - V3 agrega: traceability_matrix, coverage_report.
    - V4 agrega: review (deja de ser el default PENDING_REVIEW).
    """

    # Metadata del pipeline
    pipeline_run_id: str = Field(..., description="ID único de la ejecución del pipeline")
    agent_name: str = Field(default="code_generator")
    agent_version: str = Field(default="0.1.0")
    created_at: datetime = Field(default_factory=datetime.now)

    # Trazabilidad de origen — qué Contract B se usó como entrada
    source_contract_b_id: str = Field(
        ...,
        description="pipeline_run_id del Contract B que alimentó esta generación",
    )

    # Código y tests generados (V1+)
    generated_code: list[GeneratedCodeModule] = Field(
        ...,
        description="Módulos de código Python generados",
        min_length=1,
    )
    generated_tests: list[GeneratedTest] = Field(
        ...,
        description="Tests Pytest generados (con markers de trazabilidad)",
        min_length=1,
    )

    # Quality Report — análisis estático (V2+, None en V1)
    quality_report: Optional[QualityReport] = Field(
        default=None,
        description="Reporte de calidad de código. V1 lo deja en None; V2+ lo puebla.",
    )

    # Trazabilidad CMMI L3 (V3+, None en V1/V2)
    traceability_matrix: Optional[TraceabilityMatrix] = Field(
        default=None,
        description="Matriz de trazabilidad bidireccional. V1/V2 la dejan en None; V3+ la puebla.",
    )

    # Cobertura de código (V3+, None en V1/V2)
    coverage_report: Optional[CoverageReport] = Field(
        default=None,
        description="Reporte de cobertura branch/line. V1/V2 lo dejan en None; V3+ lo puebla.",
    )

    # Bucle de revisión humana (HITL del desarrollador senior, V4+)
    review: ReviewMetadata = Field(
        default_factory=ReviewMetadata,
        description=(
            "Metadata del bucle de revisión humana. Por defecto inicia en "
            "PENDING_REVIEW; el desarrollador senior lo actualiza vía CLI en V4."
        ),
    )

    # Métricas resumen
    total_modules: int = Field(default=0, ge=0)
    total_tests: int = Field(default=0, ge=0)
