"""Web-friendly wrapper for the RequirementsRefinerAgent.

Replaces the interactive console HITL with a two-step API:
  1. analyze(prompt)  → returns detected ambiguities
  2. generate(prompt, resolutions) → runs RAG + LLM + validation, returns stories
"""

import json
import os
import sys
import uuid
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

# Add NovaTetch root to sys.path so src/ is importable
NOVATECH_PATH = Path(__file__).parent.parent
if str(NOVATECH_PATH) not in sys.path:
    sys.path.insert(0, str(NOVATECH_PATH))

from dotenv import load_dotenv
from groq import Groq
from pydantic import ValidationError
from sentence_transformers import SentenceTransformer
import chromadb

from src.ambiguity_detector import AmbiguityDetector
from src.contract_a import (
    AcceptanceCriterion,
    AmbiguityResolution,
    RefinedRequirements,
    UserStory,
    Priority,
    StoryType,
)

load_dotenv()

EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
LLM_MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """Eres un Analista de Requerimientos Senior de Katary Software (CMMI-DEV L3, 19 años).
Transforma requerimientos ambiguos en historias de usuario estructuradas (IEEE 830 / ISO 25010).

{kb_context}

## FORMATO JSON OBLIGATORIO
Responde SOLO con JSON válido, sin texto ni markdown. Estructura:
{{"project_context": "resumen", "user_stories": [
  {{"id": "US-001", "title": "mín 10 chars", "story_type": "functional|non_functional|technical",
    "priority": "critical|high|medium|low", "as_a": "rol", "i_want": "acción", "so_that": "beneficio",
    "acceptance_criteria": [
      {{"id": "AC-001", "description": "mín 20 chars", "given": "precondición concreta",
        "when": "acción específica", "then": "resultado verificable con tiempos",
        "test_data_examples": [{{"campo": "val", "expected": "resultado"}}],
        "is_negative_case": false, "boundary_values": ["mín", "máx"]}}],
    "business_rules": [], "dependencies": [], "ui_elements": [], "api_endpoints": [],
    "ambiguities_resolved": [
      {{"original_text": "texto ambiguo", "issue": "por qué", "resolution": "valores concretos", "assumption_made": true}}]
  }}]}}

## REGLAS
1. IDs: US-001, AC-001 (3 dígitos). ACs secuenciales globales
2. Cada criterio: given/when/then con datos concretos, mín 2 test_data_examples
3. Por cada caso positivo, incluir 1 criterio negativo (is_negative_case: true)
4. Detectar y resolver ambigüedades con valores concretos en ambiguities_resolved
5. Responde SOLO JSON"""


class WebAgent:
    """Agent wrapper adapted for web API (no console input)."""

    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise RuntimeError("GROQ_API_KEY not set in environment")
            cls._instance = cls(api_key)
        return cls._instance

    def __init__(self, groq_api_key: str):
        self.groq_client = Groq(api_key=groq_api_key)
        self.ambiguity_detector = AmbiguityDetector()

        kb_data_path = str(NOVATECH_PATH / "knowledge_base_data_multilingual")
        stories_path = str(NOVATECH_PATH / "knowledge_base_stories.json")

        self._init_embeddings()
        self._init_chromadb(kb_data_path, stories_path)

    def _init_embeddings(self):
        print(f"Loading embedding model: {EMBEDDING_MODEL}")
        self.embedder = SentenceTransformer(EMBEDDING_MODEL)
        print("Embedding model ready")

    def _init_chromadb(self, kb_path: str, stories_path: str):
        client = chromadb.PersistentClient(path=kb_path)
        self.collection = client.get_or_create_collection(
            name="katary_sgc_multilingual",
            metadata={"hnsw:space": "cosine"},
        )
        if self.collection.count() == 0:
            self._load_stories(stories_path)
        else:
            print(f"Knowledge base ready: {self.collection.count()} stories")

    def _load_stories(self, stories_path: str):
        print("Indexing stories into ChromaDB...")
        with open(stories_path, "r", encoding="utf-8") as f:
            stories = json.load(f)

        textos = [s["texto"] for s in stories]
        embeddings = self.embedder.encode(textos).tolist()

        self.collection.add(
            ids=[s["id"] for s in stories],
            embeddings=embeddings,
            documents=textos,
            metadatas=[{
                "dominio": s.get("dominio", "general"),
                "criterios": s.get("criterios", ""),
            } for s in stories],
        )
        print(f"Indexed {self.collection.count()} stories")

    def analyze_ambiguities(self, prompt: str) -> list[dict]:
        """Step 1: detect ambiguities and return them as dicts for the API."""
        ambiguities = self.ambiguity_detector.analyze(prompt)
        return [
            {
                "word": a.word,
                "category": a.category,
                "ieee_830_violation": a.ieee_830_violation,
                "iso_25010_category": a.iso_25010_category,
                "suggestion": a.suggestion,
                "context": a.context,
                "severity": a.severity,
            }
            for a in ambiguities
        ]

    def generate_stories(self, prompt: str, resolutions: list[dict]) -> RefinedRequirements:
        """Step 2: generate user stories using analyst-provided resolutions.

        resolutions: list of { word, analyst_resolution, status: 'resolved'|'dismissed' }
        """
        run_id = f"run-{uuid.uuid4().hex[:8]}"

        # Build ambiguity context from resolutions
        ambiguity_section = ""
        enriched_prompt = prompt
        if resolutions:
            ambiguity_section = self.ambiguity_detector.build_resolved_prompt_section(resolutions)
            clarifications = [
                f"- \"{r['word']}\": {r['analyst_resolution']}"
                for r in resolutions
                if r.get("status") == "resolved" and r.get("analyst_resolution")
            ]
            if clarifications:
                enriched_prompt = prompt + "\n\nACLARACIONES DEL ANALISTA:\n" + "\n".join(clarifications)

        # RAG search
        query_emb = self.embedder.encode([prompt]).tolist()
        results = self.collection.query(
            query_embeddings=query_emb,
            n_results=3,
            include=["documents", "metadatas", "distances"],
        )

        historias = []
        for i in range(len(results["ids"][0])):
            sim = 1 - results["distances"][0][i]
            historias.append({
                "id": results["ids"][0][i],
                "texto": results["documents"][0][i],
                "criterios": results["metadatas"][0][i].get("criterios", ""),
                "dominio": results["metadatas"][0][i].get("dominio", ""),
                "similitud": sim,
            })

        # Build prompt
        contexto = "## HISTORIAS DE REFERENCIA DEL SGC DE KATARY\n"
        contexto += "Usa estas historias como modelo de calidad y profundidad:\n\n"
        for i, h in enumerate(historias, 1):
            contexto += f"### Referencia {i} [{h['id']}] (similitud: {h['similitud']:.2f})\n"
            contexto += f"**Historia:** {h['texto']}\n"
            contexto += f"**Criterios:** {h['criterios']}\n"
            contexto += f"**Dominio:** {h['dominio']}\n\n"

        full_context = contexto + ("\n" + ambiguity_section if ambiguity_section else "")
        system_prompt = SYSTEM_PROMPT.format(kb_context=full_context)
        user_message = (
            f"Analiza el siguiente requerimiento y transfórmalo en historias "
            f"de usuario con el nivel de calidad de las referencias del SGC de Katary.\n\n"
            f"REQUERIMIENTO:\n{enriched_prompt}"
        )

        # Generate + validate with retries
        last_errors = []
        for attempt in range(1, 4):
            try:
                if attempt == 1:
                    raw = self._call_llm(system_prompt, user_message)
                else:
                    retry_msg = (
                        f"{user_message}\n\n## CORRECCIONES REQUERIDAS\n"
                        + "\n".join(f"{i}. {e}" for i, e in enumerate(last_errors, 1))
                        + "\n\nCorrige TODOS los errores. SOLO JSON."
                    )
                    raw = self._call_llm(system_prompt, retry_msg)

                raw_json = self._extract_json(raw)
                return self._build_result(raw_json, prompt, run_id)

            except (json.JSONDecodeError, ValueError) as e:
                last_errors = [str(e)]
            except ValidationError as e:
                last_errors = [err["msg"] for err in e.errors()]

        raise RuntimeError(
            f"Failed to generate valid JSON after 3 attempts. Last errors: {last_errors}"
        )

    def _call_llm(self, system_prompt: str, user_message: str) -> str:
        response = self.groq_client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.3,
            max_tokens=4000,
        )
        return response.choices[0].message.content

    def _extract_json(self, raw: str) -> dict:
        text = raw.strip()
        if "```json" in text:
            text = text.split("```json", 1)[1].rsplit("```", 1)[0]
        elif "```" in text:
            text = text.split("```", 1)[1].rsplit("```", 1)[0]
        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError("No valid JSON found in LLM response")
        return json.loads(text[start:end])

    def _build_result(self, raw_json: dict, original: str, run_id: str) -> RefinedRequirements:
        user_stories = []
        ac_counter = 0

        for story_data in raw_json.get("user_stories", []):
            criteria = []
            for ac_data in story_data.get("acceptance_criteria", []):
                ac_counter += 1
                criteria.append(AcceptanceCriterion(
                    id=ac_data.get("id", f"AC-{ac_counter:03d}"),
                    description=ac_data.get("description", ""),
                    given=ac_data.get("given", ""),
                    when=ac_data.get("when", ""),
                    then=ac_data.get("then", ""),
                    test_data_examples=ac_data.get("test_data_examples", []),
                    is_negative_case=ac_data.get("is_negative_case", False),
                    boundary_values=ac_data.get("boundary_values", []),
                ))

            ambiguities = [
                AmbiguityResolution(
                    original_text=a.get("original_text", ""),
                    issue=a.get("issue", ""),
                    resolution=a.get("resolution", ""),
                    assumption_made=a.get("assumption_made", False),
                )
                for a in story_data.get("ambiguities_resolved", [])
            ]

            try:
                story_type = StoryType(story_data.get("story_type", "functional"))
            except ValueError:
                story_type = StoryType.FUNCTIONAL

            try:
                priority = Priority(story_data.get("priority", "medium"))
            except ValueError:
                priority = Priority.MEDIUM

            user_stories.append(UserStory(
                id=story_data.get("id", f"US-{len(user_stories) + 1:03d}"),
                title=story_data.get("title", "Sin título"),
                story_type=story_type,
                priority=priority,
                as_a=story_data.get("as_a", ""),
                i_want=story_data.get("i_want", ""),
                so_that=story_data.get("so_that", ""),
                acceptance_criteria=criteria,
                business_rules=story_data.get("business_rules", []),
                dependencies=story_data.get("dependencies", []),
                ui_elements=story_data.get("ui_elements", []),
                api_endpoints=story_data.get("api_endpoints", []),
                ambiguities_resolved=ambiguities,
            ))

        if not user_stories:
            raise ValueError("LLM returned no user stories")

        total_ambiguities = sum(len(s.ambiguities_resolved) for s in user_stories)
        total_assumptions = sum(
            sum(1 for a in s.ambiguities_resolved if a.assumption_made)
            for s in user_stories
        )

        return RefinedRequirements(
            pipeline_run_id=run_id,
            agent_version="4.1.0",
            original_requirements_text=original,
            project_context=raw_json.get("project_context", ""),
            user_stories=user_stories,
            total_ambiguities_found=total_ambiguities,
            total_assumptions_made=total_assumptions,
            coverage_notes=raw_json.get("coverage_notes"),
        )
