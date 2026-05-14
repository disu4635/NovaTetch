"""Agente V4 — Risk Matrix Generator (ISO/IEC 25010).

Toma el Contract B (dict) y genera una matriz de riesgos clasificada
según ISO/IEC 25010 con recomendaciones accionables.

Dos capas:
  1. Determinista — calcula riesgos estructurales desde el JSON sin LLM.
  2. LLM (Groq) — enriquece con análisis semántico y recomendaciones narrativas.
"""

import json
import os
from datetime import datetime

from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent / ".env")

_UMBRAL_LIGERO = 5

_QC_IMPACTO_ALTO: dict[str, str] = {
    "security": (
        "Sistemas sin cobertura de seguridad exponen datos de usuarios, credenciales "
        "y sesiones. Regulaciones como OWASP Top 10, ISO 27001 y normativas de "
        "protección de datos (GDPR, Ley 1581 CO) exigen controles mínimos."
    ),
    "functional_suitability": (
        "La lógica de negocio sin cobertura produce comportamientos incorrectos "
        "que afectan directamente la confiabilidad del producto ante el cliente."
    ),
    "reliability": (
        "Sin pruebas de confiabilidad, el sistema puede fallar silenciosamente "
        "ante errores de red, timeouts o caídas de servicios dependientes."
    ),
    "usability": (
        "Errores de usabilidad no detectados generan fricción en el usuario final "
        "y aumentan la tasa de abandono y los tickets de soporte."
    ),
    "performance_efficiency": (
        "Sin pruebas de rendimiento no se detectan cuellos de botella hasta que "
        "el sistema está en producción bajo carga real."
    ),
    "compatibility": (
        "La falta de pruebas de compatibilidad puede hacer el sistema inutilizable "
        "en entornos del cliente (navegadores, SO, integraciones)."
    ),
    "maintainability": (
        "Baja cobertura de mantenibilidad dificulta detectar código frágil que "
        "aumentará el costo de cambios futuros."
    ),
    "portability": (
        "Sin pruebas de portabilidad, el despliegue en nuevos entornos "
        "puede generar regresiones no anticipadas."
    ),
}

NIVEL_COLOR_HEX = {
    "CRITICO": "#a42e2e",
    "ALTO":    "#c4622d",
    "MEDIO":   "#7a6a1a",
    "BAJO":    "#1a7a3c",
}


def _calcular_nivel_riesgo(qc: str, n_escenarios: int, total_escenarios: int) -> str:
    es_alto_impacto = qc in {"security", "functional_suitability", "reliability", "usability"}
    pct = (n_escenarios / total_escenarios * 100) if total_escenarios > 0 else 0

    if n_escenarios == 0:
        return "CRITICO" if es_alto_impacto else "ALTO"
    if n_escenarios < _UMBRAL_LIGERO:
        return "ALTO" if es_alto_impacto else "MEDIO"
    if pct < 10.0:
        return "MEDIO"
    return "BAJO"


def _identificar_riesgos_estructurales(suite_data: dict) -> list[dict]:
    cobertura: dict[str, int] = suite_data.get("coverage_by_characteristic", {})
    total = sum(cobertura.values()) or 1

    escenarios_por_qc: dict[str, list[str]] = {qc: [] for qc in cobertura}
    for feature in suite_data.get("features", []):
        for sc in feature.get("scenarios", []):
            qc_sc = sc.get("quality_characteristic", "functional_suitability")
            if qc_sc in escenarios_por_qc:
                escenarios_por_qc[qc_sc].append(sc.get("name", ""))

    orden_qc = [
        "functional_suitability", "performance_efficiency", "security",
        "usability", "reliability", "compatibility",
        "maintainability", "portability",
    ]

    riesgos = []
    for qc in orden_qc:
        n = cobertura.get(qc, 0)
        pct = n / total * 100
        nivel = _calcular_nivel_riesgo(qc, n, total)

        if n == 0:
            desc = (
                f"La característica '{qc}' no tiene ningún escenario de prueba. "
                f"Este hueco implica que no hay validación automatizable de esta "
                f"dimensión de calidad en el suite actual."
            )
            rec_base = (
                f"Generar al menos 3 escenarios que cubran casos positivos, "
                f"negativos y de borde para '{qc}'."
            )
        elif n < _UMBRAL_LIGERO:
            desc = (
                f"La característica '{qc}' tiene cobertura ligera ({n} escenario(s), "
                f"{pct:.1f}% del suite). Puede haber casos de uso no cubiertos."
            )
            rec_base = (
                f"Ampliar la cobertura de '{qc}' revisando criterios de aceptación "
                f"que impliquen esta dimensión. Aplicar EP/BVA sobre los ACs relevantes."
            )
        elif pct < 10.0:
            desc = (
                f"La característica '{qc}' tiene {n} escenario(s) ({pct:.1f}% del suite). "
                f"La cobertura existe pero puede ser insuficiente."
            )
            rec_base = (
                f"Evaluar si los {n} escenarios de '{qc}' cubren los casos críticos. "
                f"Considerar agregar escenarios de borde o de falla."
            )
        else:
            desc = (
                f"La característica '{qc}' tiene cobertura adecuada ({n} escenarios, "
                f"{pct:.1f}% del suite). Riesgo residual bajo."
            )
            rec_base = (
                f"Mantener la cobertura actual de '{qc}'. Revisar en cada sprint "
                f"que los nuevos ACs mantengan o mejoren esta proporción."
            )

        riesgos.append({
            "qc":                    qc,
            "n_escenarios":          n,
            "pct_total":             round(pct, 1),
            "nivel":                 nivel,
            "descripcion_riesgo":    desc,
            "contexto_impacto":      _QC_IMPACTO_ALTO.get(qc, ""),
            "recomendacion_base":    rec_base,
            "enriquecido_llm":       False,
            "recomendacion_llm":     "",
            "escenarios_existentes": escenarios_por_qc.get(qc, []),
        })

    return riesgos


_SYSTEM_RISK = """\
Eres un arquitecto de calidad de software experto en ISO/IEC 25010 y CMMI-DEV L3.
Recibes el análisis estructural de riesgos de un suite de pruebas BDD y tu tarea
es enriquecer cada riesgo con análisis semántico y recomendaciones concretas.

Responde ÚNICAMENTE con un JSON válido:
{
  "riesgos_enriquecidos": [
    {
      "qc": "<nombre exacto de la característica>",
      "analisis_impacto": "<2-3 oraciones sobre el impacto real en este producto>",
      "recomendacion_llm": "<recomendación concreta y priorizada, mínimo 2 acciones>",
      "criterios_exito": "<cómo saber que el riesgo está mitigado, 1-2 métricas>",
      "referencias_tecnicas": "<estándar, patrón o práctica de referencia>"
    }
  ]
}
Mantén el mismo orden y los mismos valores de "qc" que en el input.
"""


def _enriquecer_con_groq(riesgos: list[dict], suite_data: dict) -> list[dict]:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return riesgos

    try:
        from groq import Groq
    except ImportError:
        return riesgos

    pipeline_id = suite_data.get("pipeline_run_id", "desconocido")
    total = sum(suite_data.get("coverage_by_characteristic", {}).values())
    feature_names = [f.get("name", "") for f in suite_data.get("features", [])]
    contexto_producto = "; ".join(feature_names[:5]) or "no disponible"

    lineas = [
        f"Pipeline ID: {pipeline_id}",
        f"Total escenarios en el suite: {total}",
        f"Contexto del producto (features): {contexto_producto}",
        "",
        "Riesgos estructurales identificados:",
        "",
    ]
    for r in riesgos:
        lineas.append(f"- Característica: {r['qc']}")
        lineas.append(f"  Nivel de riesgo: {r['nivel']}")
        lineas.append(f"  Escenarios actuales: {r['n_escenarios']} ({r['pct_total']}% del suite)")
        lineas.append(f"  Descripción del riesgo: {r['descripcion_riesgo']}")
        if r["escenarios_existentes"]:
            muestra = r["escenarios_existentes"][:3]
            lineas.append(f"  Escenarios existentes (muestra): {'; '.join(muestra)}")
        lineas.append("")

    prompt_usuario = "\n".join(lineas)

    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": _SYSTEM_RISK},
                {"role": "user",   "content": prompt_usuario},
            ],
            temperature=0.2,
            seed=42,
            max_tokens=3000,
        )
        raw = response.choices[0].message.content.strip()
        if "```json" in raw:
            raw = raw.split("```json", 1)[1].rsplit("```", 1)[0]
        elif "```" in raw:
            raw = raw.split("```", 1)[1].rsplit("```", 1)[0]

        data = json.loads(raw)
        enriquecidos = data.get("riesgos_enriquecidos", [])
        enriq_por_qc = {e["qc"]: e for e in enriquecidos}
        for r in riesgos:
            if r["qc"] in enriq_por_qc:
                e = enriq_por_qc[r["qc"]]
                r["recomendacion_llm"]    = e.get("recomendacion_llm", "")
                r["analisis_impacto"]     = e.get("analisis_impacto", "")
                r["criterios_exito"]      = e.get("criterios_exito", "")
                r["referencias_tecnicas"] = e.get("referencias_tecnicas", "")
                r["enriquecido_llm"]      = True

    except Exception:
        pass

    return riesgos


def generar_matriz_riesgos(suite_data: dict, usar_llm: bool = True) -> dict:
    """Genera la matriz de riesgos completa para un Contract B.

    Args:
        suite_data: Dict del Contract B.
        usar_llm:   Si True, enriquece con Groq.

    Returns:
        Dict con pipeline_run_id, generado_en, total_escenarios, riesgos, resumen_ejecutivo.
    """
    pipeline_id = suite_data.get("pipeline_run_id", "desconocido")
    total = sum(suite_data.get("coverage_by_characteristic", {}).values())

    riesgos = _identificar_riesgos_estructurales(suite_data)

    if usar_llm:
        riesgos = _enriquecer_con_groq(riesgos, suite_data)

    conteo_final = {"CRITICO": 0, "ALTO": 0, "MEDIO": 0, "BAJO": 0}
    for r in riesgos:
        conteo_final[r["nivel"]] += 1

    return {
        "pipeline_run_id":  pipeline_id,
        "generado_en":      datetime.now().isoformat(),
        "total_escenarios": total,
        "enriquecido_llm":  usar_llm and any(r.get("enriquecido_llm") for r in riesgos),
        "riesgos":          riesgos,
        "resumen_ejecutivo": {
            "total_qc":         len(riesgos),
            "criticos":         conteo_final["CRITICO"],
            "altos":            conteo_final["ALTO"],
            "medios":           conteo_final["MEDIO"],
            "bajos":            conteo_final["BAJO"],
            "qc_sin_cobertura": [r["qc"] for r in riesgos if r["n_escenarios"] == 0],
        },
    }
