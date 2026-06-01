"""Code Generator Pipeline (M3-V3) — adaptado para web.

Pipeline completo: RAG generación de código + análisis estático (radon/complexipy/bandit)
+ trazabilidad CMMI L3 + branch coverage (pytest-cov).

Entrada : dict del Contract B (GherkinTestSuite revisado)
Salida  : dict del Contract C (CodeGenerationResult)

Función principal: run_codegen(contract_b_data, progress_cb) → dict
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import uuid
import warnings
from pathlib import Path
from typing import Callable

warnings.filterwarnings("ignore")

from dotenv import load_dotenv
from groq import Groq
from sentence_transformers import SentenceTransformer
import chromadb

BACKEND_PATH = Path(__file__).parent
NOVATECH_ROOT = BACKEND_PATH.parent
if str(NOVATECH_ROOT) not in sys.path:
    sys.path.insert(0, str(NOVATECH_ROOT))

from src.contract_b import GherkinFeature, GherkinTestSuite
from src.contract_c import (
    CodeGenerationResult,
    ComplexityBand,
    CoverageReport,
    FunctionMetrics,
    GeneratedCodeModule,
    GeneratedTest,
    MeasurementStatus,
    QualityCharacteristic,
    QualityCharacteristicResult,
    QualityReport,
    ScenarioTraceability,
    SecurityFinding,
    SecuritySeverity,
    TestTraceability,
    TraceabilityMatrix,
    TraceabilityStatus,
)

load_dotenv(BACKEND_PATH / ".env")

_KB_CODE_PATH = NOVATECH_ROOT / "knowledge_base_code_patterns"
_CODE_PATTERNS_PATH = NOVATECH_ROOT / "examples" / "knowledge_base" / "katary_code_patterns.json"

_kb_code_cache: dict = {}


# ============================================================
# PASO 1 — Inicializar KB de patrones de código (RAG)
# ============================================================

def _inicializar_kb_codigo(progress_cb: Callable[[str], None] | None = None):
    if "modelo" in _kb_code_cache:
        return _kb_code_cache["modelo"], _kb_code_cache["collection"]

    if progress_cb:
        progress_cb("Cargando modelo de embeddings para generación de código...")

    modelo = SentenceTransformer("all-MiniLM-L6-v2")
    client = chromadb.PersistentClient(path=str(_KB_CODE_PATH))
    collection = client.get_or_create_collection(
        name="katary_code_patterns",
        metadata={"hnsw:space": "cosine"},
    )

    if collection.count() == 0:
        if progress_cb:
            progress_cb("Indexando patrones de código Katary en ChromaDB...")
        with open(_CODE_PATTERNS_PATH, "r", encoding="utf-8") as f:
            patterns = json.load(f)

        textos = [
            f"{p['domain']}. {p['code_pattern_typical']}. {p['katary_context']}"
            for p in patterns
        ]
        embeddings = modelo.encode(textos).tolist()
        collection.add(
            ids=[p["id"] for p in patterns],
            embeddings=embeddings,
            documents=textos,
            metadatas=[
                {
                    "domain": p["domain"],
                    "quality_practices": json.dumps(p["quality_practices"], ensure_ascii=False),
                    "typical_functions": json.dumps(p["typical_functions"], ensure_ascii=False),
                    "common_smells": json.dumps(p["common_smells"], ensure_ascii=False),
                    "lessons_learned_katary": p["lessons_learned_katary"],
                }
                for p in patterns
            ],
        )

    _kb_code_cache["modelo"] = modelo
    _kb_code_cache["collection"] = collection
    return modelo, collection


# ============================================================
# PASO 2 — Buscar patrones similares (Retrieval)
# ============================================================

def _buscar_patrones(modelo, collection, feature: GherkinFeature, top_k: int = 3):
    nombres_escenarios = " ".join(s.name for s in feature.scenarios)
    consulta = f"{feature.name}. {feature.description}. {nombres_escenarios}"
    query_embedding = modelo.encode([consulta]).tolist()

    resultados = collection.query(query_embeddings=query_embedding, n_results=top_k)
    patrones = []
    for idx in range(len(resultados["ids"][0])):
        meta = resultados["metadatas"][0][idx]
        patrones.append({
            "id": resultados["ids"][0][idx],
            "domain": meta["domain"],
            "quality_practices": json.loads(meta["quality_practices"]),
            "typical_functions": json.loads(meta["typical_functions"]),
            "common_smells": json.loads(meta["common_smells"]),
            "lessons_learned_katary": meta["lessons_learned_katary"],
            "similitud": 1 - resultados["distances"][0][idx],
        })
    return patrones


# ============================================================
# PASO 3 — Construir prompt enriquecido con RAG
# ============================================================

def _construir_prompt(feature: GherkinFeature, patrones: list[dict]) -> tuple[str, str]:
    bloques_kb = []
    for p in patrones:
        bloques_kb.append(
            f"--- Patron: {p['domain']} (similitud {p['similitud']:.2f}) ---\n"
            f"Practicas de calidad: {', '.join(p['quality_practices'])}\n"
            f"Funciones tipicas: {', '.join(p['typical_functions'])}\n"
            f"Smells comunes a evitar: {', '.join(p['common_smells'])}\n"
            f"Leccion aprendida en Katary: {p['lessons_learned_katary']}\n"
        )
    contexto_kb = "\n".join(bloques_kb)

    system_prompt = (
        "Eres un generador de codigo Python. Recibes una feature con escenarios "
        "Gherkin y debes devolver UNICAMENTE un objeto JSON con esta estructura, "
        "sin texto antes ni despues, sin bloques de markdown:\n"
        "{\n"
        '  "modules": [\n'
        '    {"filename": "<archivo.py>", "source_code": "<codigo>", "description": "<que hace>"}\n'
        "  ],\n"
        '  "tests": [\n'
        '    {"test_name": "<nombre>", "source_code": "<codigo>", '
        '"target_module": "<archivo.py>", "scenario_ids": ["<AC-XXX>"]}\n'
        "  ]\n"
        "}\n\n"
        "IMPORTANTE:\n"
        "- Cada test debe incluir el decorator @pytest.mark.scenario(<id>) donde <id> es el "
        "  acceptance_criterion_id del escenario que ese test verifica.\n"
        "- El campo scenario_ids debe coincidir exactamente con los IDs entre corchetes en el prompt.\n"
        "- Usa el contexto de patrones Katary como guia de calidad y estilo.\n"
        "- Aplica guard clauses, type hints y early returns.\n"
        "- CC < 10 por funcion, CogC < 15."
    )

    bloques_escenarios = []
    for s in feature.scenarios:
        pasos = "\n".join(f"  {step.keyword} {step.text}" for step in s.steps)
        bloques_escenarios.append(
            f"Escenario [{s.acceptance_criterion_id}] {s.name}\n{pasos}"
        )
    escenarios_txt = "\n\n".join(bloques_escenarios)

    user_message = (
        f"CONTEXTO DE PATRONES KATARY (RAG):\n{contexto_kb}\n\n"
        f"FEATURE A IMPLEMENTAR:\n"
        f"Nombre: {feature.name}\n"
        f"Descripcion: {feature.description}\n"
        f"User Story: {feature.user_story_id}\n\n"
        f"ESCENARIOS:\n{escenarios_txt}\n\n"
        f"Genera el codigo Python que implementa esta feature y los tests Pytest. "
        f"En cada test, agrega @pytest.mark.scenario('<AC-XXX>') con los IDs entre "
        f"corchetes de arriba, y ponlos tambien en scenario_ids."
    )

    return system_prompt, user_message


# ============================================================
# PASO 4 — Llamar a Groq
# ============================================================

def _generar_con_groq(client: Groq, system_prompt: str, user_message: str) -> str:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.0,
        seed=42,
        max_tokens=4000,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content


# ============================================================
# PASO 5 — Parsear respuesta del LLM
# ============================================================

def _parsear_respuesta(raw_text: str, feature: GherkinFeature):
    texto = raw_text.strip()
    if texto.startswith("```"):
        texto = texto.split("\n", 1)[1] if "\n" in texto else texto[3:]
    if texto.endswith("```"):
        texto = texto.rsplit("```", 1)[0]

    inicio = texto.find("{")
    fin = texto.rfind("}")
    if inicio == -1 or fin == -1 or fin <= inicio:
        raise ValueError("No se encontró JSON válido en la respuesta del LLM")
    data = json.loads(texto[inicio:fin + 1])

    modulos: list[GeneratedCodeModule] = []
    for item in data.get("modules", []):
        modulos.append(GeneratedCodeModule(
            filename=item["filename"],
            source_code=item["source_code"],
            description=item.get("description", ""),
            user_story_id=feature.user_story_id,
        ))

    tests: list[GeneratedTest] = []
    for item in data.get("tests", []):
        tests.append(GeneratedTest(
            test_name=item["test_name"],
            source_code=item["source_code"],
            target_module=item.get("target_module", ""),
            scenario_ids=item.get("scenario_ids", []),
        ))

    return modulos, tests


# ============================================================
# PASO 6 — Análisis estático: radon, complexipy, bandit
# ============================================================

def _volcar_codigo(modulos: list[GeneratedCodeModule]) -> Path:
    tmp_dir = Path(tempfile.mkdtemp(prefix="novatech_codegen_"))
    for modulo in modulos:
        (tmp_dir / modulo.filename).write_text(modulo.source_code, encoding="utf-8")
    return tmp_dir


def _ejecutar_radon(code_dir: Path) -> dict:
    res_cc = subprocess.run(
        [sys.executable, "-m", "radon", "cc", "-j", str(code_dir)],
        capture_output=True, text=True,
    )
    cc_data = json.loads(res_cc.stdout) if res_cc.stdout.strip() else {}

    res_mi = subprocess.run(
        [sys.executable, "-m", "radon", "mi", "-j", str(code_dir)],
        capture_output=True, text=True,
    )
    mi_data = json.loads(res_mi.stdout) if res_mi.stdout.strip() else {}

    return {
        "cc": {Path(k).name: v for k, v in cc_data.items()},
        "mi": {Path(k).name: v for k, v in mi_data.items()},
    }


def _ejecutar_complexipy(code_dir: Path) -> dict:
    subprocess.run(
        ["complexipy", "--output-format", "json", "--quiet", str(code_dir)],
        cwd=str(code_dir), capture_output=True, text=True,
    )
    results_path = code_dir / "complexipy-results.json"
    if not results_path.exists():
        return {}
    lista = json.loads(results_path.read_text(encoding="utf-8"))
    resultado: dict[str, dict[str, int]] = {}
    for item in lista:
        resultado.setdefault(item["file_name"], {})[item["function_name"]] = item["complexity"]
    return resultado


def _ejecutar_bandit(code_dir: Path) -> list[SecurityFinding]:
    res = subprocess.run(
        ["bandit", "-r", "-f", "json", str(code_dir)],
        capture_output=True, text=True,
    )
    if not res.stdout.strip():
        return []
    try:
        data = json.loads(res.stdout)
    except json.JSONDecodeError:
        return []
    findings: list[SecurityFinding] = []
    for issue in data.get("results", []):
        try:
            sev = SecuritySeverity(issue["issue_severity"].lower())
        except ValueError:
            sev = SecuritySeverity.LOW
        findings.append(SecurityFinding(
            test_id=issue["test_id"],
            severity=sev,
            module=Path(issue["filename"]).name,
            line_number=issue["line_number"],
            description=issue["issue_text"],
        ))
    return findings


def _construir_function_metrics(radon_data: dict, complexipy_data: dict) -> list[FunctionMetrics]:
    metrics: list[FunctionMetrics] = []
    for archivo, entradas in radon_data.get("cc", {}).items():
        entradas_planas = []
        for entrada in entradas:
            if entrada.get("type") == "class":
                entradas_planas.extend(entrada.get("methods", []))
            else:
                entradas_planas.append(entrada)

        for entrada in entradas_planas:
            if entrada.get("type") not in ("function", "method"):
                continue
            nombre = entrada["name"]
            cc = entrada["complexity"]
            try:
                banda = ComplexityBand(entrada["rank"])
            except ValueError:
                banda = ComplexityBand.E

            cogc = complexipy_data.get(archivo, {}).get(nombre, 0)
            metrics.append(FunctionMetrics(
                function_name=nombre,
                module=archivo,
                cyclomatic_complexity=cc,
                cognitive_complexity=cogc,
                cc_band=banda,
                nesting_depth=0,
                exceeds_threshold=(cc >= 10) or (cogc >= 15),
            ))
    return metrics


def _clasificar_iso_25010(
    function_metrics: list[FunctionMetrics],
    security_findings: list[SecurityFinding],
    maintainability_index: float | None,
) -> list[QualityCharacteristicResult]:
    exceeding = sum(1 for fm in function_metrics if fm.exceeds_threshold)
    high_findings = sum(1 for f in security_findings if f.severity == SecuritySeverity.HIGH)
    mi_ok = maintainability_index is not None and maintainability_index >= 20

    mantenibilidad_verdict = (
        f"pass: 0 funciones sobre umbral, MI={maintainability_index} >= 20"
        if exceeding == 0 and mi_ok
        else f"fail: {exceeding} función(es) sobre umbral, MI={maintainability_index}"
    )
    seg_verdict = (
        "pass: sin hallazgos de Bandit"
        if not security_findings
        else f"fail: {len(security_findings)} hallazgo(s), {high_findings} de severidad HIGH"
    )

    return [
        QualityCharacteristicResult(
            characteristic=QualityCharacteristic.MAINTAINABILITY,
            status=MeasurementStatus.MEASURED,
            metrics_used=["radon cc", "complexipy", "radon mi"],
            verdict=mantenibilidad_verdict,
        ),
        QualityCharacteristicResult(
            characteristic=QualityCharacteristic.SECURITY,
            status=MeasurementStatus.MEASURED,
            metrics_used=["bandit"],
            verdict=seg_verdict,
        ),
        QualityCharacteristicResult(
            characteristic=QualityCharacteristic.FUNCTIONAL_SUITABILITY,
            status=MeasurementStatus.MEASURED,
            metrics_used=["pytest-cov"],
            verdict="Medido via branch coverage en pytest (V3).",
        ),
        QualityCharacteristicResult(
            characteristic=QualityCharacteristic.RELIABILITY,
            status=MeasurementStatus.REQUIRES_HUMAN_JUDGMENT,
            metrics_used=[],
            verdict="Manejo de errores y casos límite requieren revisión humana.",
        ),
        QualityCharacteristicResult(
            characteristic=QualityCharacteristic.PERFORMANCE_EFFICIENCY,
            status=MeasurementStatus.NOT_APPLICABLE,
            metrics_used=[],
            verdict="Característica de runtime; análisis estático no la mide.",
        ),
        QualityCharacteristicResult(
            characteristic=QualityCharacteristic.COMPATIBILITY,
            status=MeasurementStatus.NOT_APPLICABLE,
            metrics_used=[],
            verdict="Depende del entorno de integración; fuera del alcance.",
        ),
        QualityCharacteristicResult(
            characteristic=QualityCharacteristic.PORTABILITY,
            status=MeasurementStatus.NOT_APPLICABLE,
            metrics_used=[],
            verdict="Depende del entorno destino; fuera del alcance.",
        ),
        QualityCharacteristicResult(
            characteristic=QualityCharacteristic.USABILITY,
            status=MeasurementStatus.NOT_APPLICABLE,
            metrics_used=[],
            verdict="Necesita usuarios reales; no aplica a código backend.",
        ),
    ]


# ============================================================
# PASO 7 — Trazabilidad CMMI L3
# ============================================================

def _extraer_scenario_ids(contract_b: GherkinTestSuite) -> dict[str, str]:
    scenarios = {}
    for feature in contract_b.features:
        for sc in feature.scenarios:
            scenarios[sc.acceptance_criterion_id] = sc.name
    return scenarios


def _extraer_markers(tests: list[GeneratedTest]) -> dict[str, list[str]]:
    MARKER_RE = re.compile(r'@pytest\.mark\.scenario\(["\']([^"\']+)["\']\)')

    resultado: dict[str, list[str]] = {}
    for test in tests:
        declarados = list(test.scenario_ids or [])
        en_codigo = MARKER_RE.findall(test.source_code or "")

        def limpiar(sid: str) -> str:
            return sid.strip().strip("[]")

        ids = {limpiar(s) for s in declarados + en_codigo if s and limpiar(s)}
        resultado[test.test_name] = sorted(ids)
    return resultado


def _construir_trazabilidad(
    scenarios: dict[str, str],
    test_markers: dict[str, list[str]],
) -> TraceabilityMatrix:
    forward: list[ScenarioTraceability] = []
    orphan_scenarios: list[str] = []
    for sid, nombre in scenarios.items():
        cubriendo = sorted(t for t, ids in test_markers.items() if sid in ids)
        estado = TraceabilityStatus.COVERED if cubriendo else TraceabilityStatus.ORPHAN_FORWARD
        if not cubriendo:
            orphan_scenarios.append(sid)
        forward.append(ScenarioTraceability(
            scenario_id=sid,
            scenario_name=nombre,
            covering_tests=cubriendo,
            status=estado,
        ))

    backward: list[TestTraceability] = []
    orphan_tests: list[str] = []
    for test_name, ids in test_markers.items():
        justifican = sorted(s for s in ids if s in scenarios)
        estado = TraceabilityStatus.COVERED if justifican else TraceabilityStatus.ORPHAN_BACKWARD
        if not justifican:
            orphan_tests.append(test_name)
        backward.append(TestTraceability(
            test_name=test_name,
            justifying_scenarios=justifican,
            status=estado,
        ))

    total_sc = len(scenarios) or 1
    total_t = len(test_markers) or 1
    req_cov = (total_sc - len(orphan_scenarios)) / total_sc * 100
    test_just = (total_t - len(orphan_tests)) / total_t * 100

    return TraceabilityMatrix(
        forward=forward,
        backward=backward,
        requirements_coverage_pct=round(req_cov, 2),
        tests_justified_pct=round(test_just, 2),
        orphan_scenarios=orphan_scenarios,
        orphan_tests=orphan_tests,
        cmmi_l3_compliant=(not orphan_scenarios) and (not orphan_tests),
    )


# ============================================================
# PASO 8 — Branch coverage con pytest-cov
# ============================================================

def _medir_coverage(code_dir: Path, tests: list[GeneratedTest]) -> CoverageReport:
    for test in tests:
        nombre = test.test_name if test.test_name.startswith("test_") else f"test_{test.test_name}"
        if not nombre.endswith(".py"):
            nombre = f"{nombre}.py"
        wrapper = (
            "import sys\nfrom pathlib import Path\n"
            "sys.path.insert(0, str(Path(__file__).parent))\n\n"
            + test.source_code
        )
        (code_dir / nombre).write_text(wrapper, encoding="utf-8")

    (code_dir / "conftest.py").write_text(
        "def pytest_configure(config):\n"
        '    config.addinivalue_line("markers", "scenario(id): vincula un test a un escenario")\n',
        encoding="utf-8",
    )

    cov_json = code_dir / "coverage.json"
    subprocess.run(
        [
            sys.executable, "-m", "pytest",
            str(code_dir),
            f"--cov={code_dir}",
            "--cov-branch",
            f"--cov-report=json:{cov_json}",
            "-q", "--tb=no",
        ],
        capture_output=True, text=True, cwd=str(code_dir),
    )

    if not cov_json.exists():
        return CoverageReport(branch_coverage_pct=0.0, line_coverage_pct=0.0,
                              meets_threshold=False, uncovered_modules=[])

    data = json.loads(cov_json.read_text(encoding="utf-8"))
    totals = data.get("totals", {})
    line_pct = totals.get("percent_covered", 0.0)
    n_branches = totals.get("num_branches", 0)
    covered_branches = totals.get("covered_branches", 0)
    branch_pct = (covered_branches / n_branches * 100) if n_branches > 0 else line_pct

    uncovered: list[str] = []
    for filepath, fdata in data.get("files", {}).items():
        f_totals = fdata.get("summary", {})
        f_branches = f_totals.get("num_branches", 0)
        f_covered = f_totals.get("covered_branches", 0)
        f_pct = (f_covered / f_branches * 100) if f_branches > 0 else f_totals.get("percent_covered", 0.0)
        if f_pct < 80:
            uncovered.append(Path(filepath).name)

    return CoverageReport(
        branch_coverage_pct=round(branch_pct, 2),
        line_coverage_pct=round(line_pct, 2),
        meets_threshold=branch_pct >= 80,
        uncovered_modules=uncovered,
    )


# ============================================================
# PIPELINE PRINCIPAL
# ============================================================

def run_codegen(
    contract_b_data: dict,
    progress_cb: Callable[[str], None] | None = None,
) -> dict:
    """Ejecuta el pipeline completo V3 y retorna el Contract C como dict."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY no encontrada en el entorno")

    contract_b = GherkinTestSuite(**contract_b_data)
    groq_client = Groq(api_key=api_key)

    if progress_cb:
        progress_cb("Inicializando KB de patrones de código...")
    modelo, collection = _inicializar_kb_codigo(progress_cb)

    todos_modulos: list[GeneratedCodeModule] = []
    todos_tests: list[GeneratedTest] = []

    total_features = len(contract_b.features)
    for i, feature in enumerate(contract_b.features, 1):
        if progress_cb:
            progress_cb(f"Generando código ({i}/{total_features}): {feature.name[:60]}...")

        patrones = _buscar_patrones(modelo, collection, feature, top_k=3)
        system_prompt, user_message = _construir_prompt(feature, patrones)

        try:
            raw = _generar_con_groq(groq_client, system_prompt, user_message)
            modulos, tests = _parsear_respuesta(raw, feature)
            todos_modulos.extend(modulos)
            todos_tests.extend(tests)
        except (json.JSONDecodeError, KeyError, ValueError):
            continue

    if not todos_modulos:
        raise RuntimeError("El LLM no generó ningún módulo de código")

    if progress_cb:
        progress_cb("Ejecutando análisis estático (radon, complexipy, bandit)...")

    code_dir = _volcar_codigo(todos_modulos)

    try:
        radon_data = _ejecutar_radon(code_dir)
        complexipy_data = _ejecutar_complexipy(code_dir)
        security_findings = _ejecutar_bandit(code_dir)
        function_metrics = _construir_function_metrics(radon_data, complexipy_data)
        mi_values = [v["mi"] for v in radon_data.get("mi", {}).values()]
        mi_avg = round(sum(mi_values) / len(mi_values), 2) if mi_values else None
        iso_coverage = _clasificar_iso_25010(function_metrics, security_findings, mi_avg)
        exceeding = sum(1 for fm in function_metrics if fm.exceeds_threshold)
        quality_report = QualityReport(
            function_metrics=function_metrics,
            maintainability_index=mi_avg,
            security_findings=security_findings,
            iso_25010_coverage=iso_coverage,
            functions_exceeding_threshold=exceeding,
        )
    except Exception:
        quality_report = None

    if progress_cb:
        progress_cb("Construyendo matriz de trazabilidad CMMI L3...")

    scenarios = _extraer_scenario_ids(contract_b)
    test_markers = _extraer_markers(todos_tests)
    traceability_matrix = _construir_trazabilidad(scenarios, test_markers)

    if progress_cb:
        progress_cb("Midiendo branch coverage con pytest-cov...")

    try:
        coverage_report = _medir_coverage(code_dir, todos_tests)
    except Exception:
        coverage_report = CoverageReport(
            branch_coverage_pct=0.0, line_coverage_pct=0.0,
            meets_threshold=False, uncovered_modules=[],
        )

    resultado = CodeGenerationResult(
        pipeline_run_id=f"cg-{uuid.uuid4().hex[:8]}",
        agent_version="0.3.0-v3-trazabilidad",
        source_contract_b_id=contract_b.pipeline_run_id,
        generated_code=todos_modulos,
        generated_tests=todos_tests,
        quality_report=quality_report,
        traceability_matrix=traceability_matrix,
        coverage_report=coverage_report,
        total_modules=len(todos_modulos),
        total_tests=len(todos_tests),
    )

    if progress_cb:
        progress_cb(
            f"Completado: {resultado.total_modules} módulos, "
            f"{resultado.total_tests} tests, "
            f"coverage {coverage_report.branch_coverage_pct:.1f}%"
        )

    return resultado.model_dump(mode="json")
