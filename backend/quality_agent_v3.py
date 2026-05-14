"""Agente V3 — Test Architect con clasificación ISO/IEC 25010.

Versión web del agente V3: acepta un dict del Contract A y retorna
el Contract B como dict. Diseñado para ser llamado como función
desde el router de calidad.
"""

import json
import os
import sys
import uuid
import warnings
from collections import Counter
from pathlib import Path
from typing import Callable

warnings.filterwarnings("ignore")

from dotenv import load_dotenv
from groq import Groq
from pydantic import ValidationError
from sentence_transformers import SentenceTransformer
import chromadb

BACKEND_PATH = Path(__file__).parent
NOVATECH_ROOT = BACKEND_PATH.parent
if str(NOVATECH_ROOT) not in sys.path:
    sys.path.insert(0, str(NOVATECH_ROOT))

from src.contract_a import AcceptanceCriterion, RefinedRequirements, UserStory
from src.contract_b import (
    CoverageMatrix,
    GherkinFeature,
    GherkinScenario,
    GherkinStep,
    GherkinTestSuite,
    QualityCharacteristic,
    ScenarioType,
)

load_dotenv(BACKEND_PATH / ".env")

_KB_PATH = NOVATECH_ROOT / "knowledge_base_test_patterns"
_PATTERNS_PATH = NOVATECH_ROOT / "examples" / "knowledge_base" / "katary_test_patterns.json"

_kb_cache: dict = {}


def _inicializar_kb(progress_cb: Callable[[str], None] | None = None):
    if "modelo" in _kb_cache:
        return _kb_cache["modelo"], _kb_cache["collection"]

    if progress_cb:
        progress_cb("Cargando modelo de embeddings para análisis de calidad...")

    modelo = SentenceTransformer("all-MiniLM-L6-v2")

    client = chromadb.PersistentClient(path=str(_KB_PATH))
    collection = client.get_or_create_collection(
        name="katary_test_patterns",
        metadata={"hnsw:space": "cosine"},
    )

    if collection.count() == 0:
        if progress_cb:
            progress_cb("Indexando patrones de testing Katary...")
        with open(_PATTERNS_PATH, "r", encoding="utf-8") as f:
            patterns = json.load(f)

        textos = [
            f"{p['domain']}. {p['ac_pattern_typical']}. {p['katary_context']}"
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
                    "techniques_used": ", ".join(p["techniques_used"]),
                    "typical_scenarios": json.dumps(p["typical_scenarios"], ensure_ascii=False),
                    "lessons_learned_katary": p["lessons_learned_katary"],
                }
                for p in patterns
            ],
        )

    _kb_cache["modelo"] = modelo
    _kb_cache["collection"] = collection
    return modelo, collection


def _buscar_patrones(modelo, collection, ac: AcceptanceCriterion, top_k: int = 3):
    consulta = f"{ac.description}. Given {ac.given}. When {ac.when}. Then {ac.then}"
    emb = modelo.encode([consulta]).tolist()
    resultados = collection.query(
        query_embeddings=emb,
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
    patrones = []
    for i in range(len(resultados["ids"][0])):
        similitud = 1 - resultados["distances"][0][i]
        patrones.append({
            "id": resultados["ids"][0][i],
            "domain": resultados["metadatas"][0][i]["domain"],
            "typical_scenarios": json.loads(resultados["metadatas"][0][i]["typical_scenarios"]),
            "lessons_learned_katary": resultados["metadatas"][0][i]["lessons_learned_katary"],
            "techniques_used": resultados["metadatas"][0][i]["techniques_used"],
            "similitud": similitud,
        })
    return patrones


def _construir_prompt(ac: AcceptanceCriterion, story: UserStory, patrones: list[dict]) -> tuple[str, str]:
    contexto_kb = "## PATRONES DE TESTING DEL SGC KATARY\n"
    contexto_kb += "Usa estos patrones como referencia de calidad para tus escenarios:\n\n"
    for i, p in enumerate(patrones, 1):
        contexto_kb += f"### Patron {i} [{p['id']}] dominio: {p['domain']} (similitud: {p['similitud']:.2f})\n"
        contexto_kb += f"Tecnicas usadas tipicamente: {p['techniques_used']}\n"
        contexto_kb += "Escenarios tipicos:\n"
        for s in p["typical_scenarios"]:
            contexto_kb += f"   - {s}\n"
        contexto_kb += f"Leccion Katary: {p['lessons_learned_katary']}\n\n"

    instrucciones_heuristicas = (
        "## INSTRUCCIONES DE TESTING DISCIPLINADO (OBLIGATORIAS)\n\n"
        "Para el criterio de aceptacion recibido, aplica las siguientes tecnicas de caja negra:\n\n"
        "1. EQUIVALENCE PARTITIONING (EP): identifica clases equivalentes validas e invalidas.\n"
        "   Genera UN escenario por cada clase identificada.\n"
        "2. BOUNDARY VALUE ANALYSIS (BVA): si el AC menciona rangos numericos, genera 4 escenarios\n"
        "   adicionales con limite inferior, justo debajo del inferior, limite superior, justo encima.\n"
        "3. DECISION TABLES (DT): si el AC tiene multiples condiciones que se combinan, genera UN\n"
        "   escenario por cada combinacion relevante.\n\n"
        "Minimo: 1 escenario positivo + 1 por cada clase invalida + BVA/DT si aplica.\n"
        "NO te conformes con UN solo escenario por AC.\n"
    )

    instrucciones_iso25010 = (
        "## CLASIFICACION ISO/IEC 25010 (OBLIGATORIA)\n\n"
        "Por cada escenario asigna OBLIGATORIAMENTE el campo `quality_characteristic`:\n"
        "   - functional_suitability  (logica de negocio, validaciones, reglas)\n"
        "   - performance_efficiency  (tiempos de respuesta, carga concurrente)\n"
        "   - security                (autenticacion, autorizacion, bloqueo, cifrado)\n"
        "   - usability               (mensajes de error, accesibilidad, UI)\n"
        "   - reliability             (recuperacion de fallas, timeouts)\n"
        "   - compatibility           (navegadores, SO, formatos)\n"
        "   - maintainability         (rara vez aplica en BDD funcional)\n"
        "   - portability             (rara vez aplica en BDD funcional)\n"
    )

    system = (
        "Eres un Test Architect que convierte criterios de aceptacion en escenarios Gherkin (BDD)\n"
        "aplicando tecnicas de caja negra disciplinadas y clasificandolos segun ISO/IEC 25010.\n\n"
        f"{contexto_kb}\n{instrucciones_heuristicas}\n{instrucciones_iso25010}\n"
        "## FORMATO DE RESPUESTA OBLIGATORIO\n"
        "Devuelve UNICAMENTE un JSON valido:\n"
        '{"scenarios": [{"name": "nombre descriptivo (min 10 chars)", '
        '"scenario_type": "positive|negative|boundary|edge_case|error_handling", '
        '"quality_characteristic": "functional_suitability|performance_efficiency|security|'
        'usability|reliability|compatibility|maintainability|portability", '
        '"tags": ["@tag1"], "heuristic_applied": "EP|BVA|DT|general", '
        '"steps": [{"keyword": "Given", "text": "..."}, {"keyword": "When", "text": "..."}, '
        '{"keyword": "Then", "text": "..."}]}]}\n'
        "Cada step.text debe tener minimo 5 caracteres.\n"
    )

    user = (
        f"Historia de usuario: {story.title}\n"
        f"Como {story.as_a}, quiero {story.i_want}, para {story.so_that}.\n\n"
        f"Criterio de aceptacion {ac.id}:\n"
        f"   Descripcion: {ac.description}\n"
        f"   Given: {ac.given}\n"
        f"   When: {ac.when}\n"
        f"   Then: {ac.then}\n"
        f"   Caso negativo: {'Si' if ac.is_negative_case else 'No'}\n"
        f"   Test data examples: {ac.test_data_examples}\n"
        f"   Boundary values: {ac.boundary_values}\n\n"
        "Genera la LISTA de escenarios Gherkin aplicando EP, BVA y/o DT segun corresponda,\n"
        "y CLASIFICA cada escenario con su caracteristica ISO/IEC 25010."
    )

    return system, user


def _generar_con_groq(client: Groq, system_prompt: str, user_message: str) -> str:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.0,
        seed=42,
        max_tokens=2500,
    )
    return response.choices[0].message.content


def _parsear_escenarios(raw_text: str, ac: AcceptanceCriterion, story: UserStory) -> list[GherkinScenario]:
    text = raw_text.strip()
    if "```json" in text:
        text = text.split("```json", 1)[1].rsplit("```", 1)[0]
    elif "```" in text:
        text = text.split("```", 1)[1].rsplit("```", 1)[0]

    start = text.find("{")
    end = text.rfind("}") + 1
    data = json.loads(text[start:end])

    scenarios_data = data.get("scenarios", [])
    if not scenarios_data:
        raise ValueError(f"LLM no devolvio escenarios para AC {ac.id}")

    valid_qc_values = {qc.value for qc in QualityCharacteristic}
    scenarios = []
    for sd in scenarios_data:
        steps = [GherkinStep(keyword=s["keyword"], text=s["text"]) for s in sd["steps"]]

        tags = sd.get("tags", [])
        heuristica = sd.get("heuristic_applied", "general")
        if heuristica != "general" and f"@{heuristica.lower()}" not in [t.lower() for t in tags]:
            tags.append(f"@{heuristica.lower()}")

        qc_raw = sd.get("quality_characteristic", "functional_suitability")
        if qc_raw not in valid_qc_values:
            qc_raw = "functional_suitability"
        quality_characteristic = QualityCharacteristic(qc_raw)

        iso_tag = f"@iso-{quality_characteristic.value.replace('_', '-')}"
        if iso_tag not in [t.lower() for t in tags]:
            tags.append(iso_tag)

        scenarios.append(GherkinScenario(
            name=sd["name"],
            scenario_type=ScenarioType(sd.get("scenario_type", "positive")),
            quality_characteristic=quality_characteristic,
            tags=tags,
            steps=steps,
            acceptance_criterion_id=ac.id,
            user_story_id=story.id,
        ))
    return scenarios


def _calcular_matriz_cobertura(escenarios: list[GherkinScenario]) -> dict[str, int]:
    matriz = {qc.value: 0 for qc in QualityCharacteristic}
    contador = Counter(e.quality_characteristic.value for e in escenarios)
    matriz.update(contador)
    return matriz


def _construir_contract_b(
    contract_a: RefinedRequirements,
    scenarios_por_story: dict[str, list[GherkinScenario]],
) -> GherkinTestSuite:
    features = []
    for story in contract_a.user_stories:
        scenarios = scenarios_por_story.get(story.id, [])
        if not scenarios:
            continue
        features.append(GherkinFeature(
            name=story.title,
            description=f"Como {story.as_a}, quiero {story.i_want}, para {story.so_that}",
            user_story_id=story.id,
            scenarios=scenarios,
        ))

    coverage = []
    for story in contract_a.user_stories:
        for ac in story.acceptance_criteria:
            sc = [
                s for s in scenarios_por_story.get(story.id, [])
                if s.acceptance_criterion_id == ac.id
            ]
            if sc:
                coverage.append(CoverageMatrix(
                    user_story_id=story.id,
                    criterion_id=ac.id,
                    scenario_names=[s.name for s in sc],
                    coverage_type=[s.scenario_type for s in sc],
                    quality_characteristics_covered=list({s.quality_characteristic for s in sc}),
                ))

    all_scenarios = [s for f in features for s in f.scenarios]
    total_positive = sum(1 for s in all_scenarios if s.scenario_type == ScenarioType.POSITIVE)
    total_negative = sum(1 for s in all_scenarios if s.scenario_type == ScenarioType.NEGATIVE)
    total_boundary = sum(1 for s in all_scenarios if s.scenario_type == ScenarioType.BOUNDARY)
    matriz_iso = _calcular_matriz_cobertura(all_scenarios)

    return GherkinTestSuite(
        pipeline_run_id=f"v3-{uuid.uuid4().hex[:8]}",
        agent_version="0.3.0-v3-iso25010",
        features=features,
        coverage_matrix=coverage,
        total_scenarios=len(all_scenarios),
        total_positive=total_positive,
        total_negative=total_negative,
        total_boundary=total_boundary,
        coverage_by_characteristic=matriz_iso,
    )


def run_quality_v3(
    contract_a_data: dict,
    progress_cb: Callable[[str], None] | None = None,
) -> dict:
    """Ejecuta el pipeline V3 sobre el Contract A y retorna el Contract B como dict."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY no encontrada en el entorno")

    contract_a = RefinedRequirements(**contract_a_data)
    groq_client = Groq(api_key=api_key)
    modelo, collection = _inicializar_kb(progress_cb)

    total_stories = len(contract_a.user_stories)
    total_acs = sum(len(s.acceptance_criteria) for s in contract_a.user_stories)
    ac_procesados = 0
    scenarios_por_story: dict[str, list[GherkinScenario]] = {}

    for story in contract_a.user_stories:
        scenarios_por_story[story.id] = []
        for ac in story.acceptance_criteria:
            ac_procesados += 1
            if progress_cb:
                progress_cb(
                    f"Procesando AC {ac_procesados}/{total_acs}: {ac.description[:60]}..."
                )

            patrones = _buscar_patrones(modelo, collection, ac, top_k=3)
            system_prompt, user_message = _construir_prompt(ac, story, patrones)

            try:
                raw_response = _generar_con_groq(groq_client, system_prompt, user_message)
                escenarios = _parsear_escenarios(raw_response, ac, story)
                scenarios_por_story[story.id].extend(escenarios)
            except (json.JSONDecodeError, ValidationError, KeyError, ValueError):
                continue

    if progress_cb:
        progress_cb("Construyendo Contract B con matriz ISO 25010...")

    suite = _construir_contract_b(contract_a, scenarios_por_story)
    return suite.model_dump(mode="json")
