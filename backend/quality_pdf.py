"""Generación del acta PDF de revisión de calidad.

Produce un PDF firmable con:
- Encabezado institucional
- Decisión del analista
- Resumen de escenarios revisados
- Matriz de cobertura ISO 25010
- Matriz de riesgos ISO 25010
- Log de auditoría
- Espacio de firma
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

BACKEND_PATH = Path(__file__).parent
NOVATECH_ROOT = BACKEND_PATH.parent
if str(NOVATECH_ROOT) not in sys.path:
    sys.path.insert(0, str(NOVATECH_ROOT))

from src.contract_b import GherkinTestSuite, QualityCharacteristic, ReviewStatus
from quality_agent_v4_risk import NIVEL_COLOR_HEX

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        HRFlowable,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
    _REPORTLAB_OK = True
except ImportError:
    _REPORTLAB_OK = False


_COLOR_HEADER    = None
_COLOR_SUBHEADER = None
_COLOR_TABLE_HDR = None
_COLOR_ROW_ALT   = None
_COLOR_APPROVED  = None
_COLOR_REJECTED  = None
_COLOR_PENDING   = None

if _REPORTLAB_OK:
    _COLOR_HEADER    = colors.HexColor("#1a3a5c")
    _COLOR_SUBHEADER = colors.HexColor("#2e6da4")
    _COLOR_TABLE_HDR = colors.HexColor("#dce8f5")
    _COLOR_ROW_ALT   = colors.HexColor("#f4f8fc")
    _COLOR_APPROVED  = colors.HexColor("#1a7a3c")
    _COLOR_REJECTED  = colors.HexColor("#a42e2e")
    _COLOR_PENDING   = colors.HexColor("#7a6a1a")

_STATUS_COLOR_HEX = {
    "approved":       "#1a7a3c",
    "rejected":       "#a42e2e",
    "needs_changes":  "#7a6a1a",
    "pending_review": "#7a6a1a",
}

_STATUS_LABEL = {
    "approved":       "APROBADO",
    "rejected":       "RECHAZADO",
    "needs_changes":  "SOLICITUD DE CAMBIOS",
    "pending_review": "PENDIENTE DE REVISIÓN",
}


def _safe(texto) -> str:
    return (
        str(texto)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def generar_acta_pdf(
    suite: GherkinTestSuite,
    output_path: Path,
    resumen: dict,
    matriz_riesgos: dict | None = None,
) -> Path:
    """Genera el acta PDF. Retorna la ruta del PDF generado."""
    if not _REPORTLAB_OK:
        raise RuntimeError(
            "reportlab no está instalado. Ejecuta: pip install reportlab"
        )

    pdf_path = output_path.with_suffix(".pdf")
    base_styles = getSampleStyleSheet()

    s_titulo = ParagraphStyle("Titulo", parent=base_styles["Title"],
        fontSize=18, textColor=_COLOR_HEADER, spaceAfter=4, leading=22)
    s_subtitulo = ParagraphStyle("Subtitulo", parent=base_styles["Normal"],
        fontSize=10, textColor=_COLOR_SUBHEADER, spaceAfter=2)
    s_seccion = ParagraphStyle("Seccion", parent=base_styles["Heading2"],
        fontSize=12, textColor=_COLOR_SUBHEADER, spaceBefore=14, spaceAfter=4)
    s_normal = ParagraphStyle("Normal2", parent=base_styles["Normal"],
        fontSize=9, leading=13, spaceAfter=2)
    s_mono = ParagraphStyle("Mono", parent=base_styles["Code"],
        fontSize=8, leading=11, leftIndent=8, spaceAfter=1)

    status_val = suite.review.review_status.value
    s_estado = ParagraphStyle("Estado", parent=base_styles["Normal"],
        fontSize=14,
        textColor=colors.HexColor(_STATUS_COLOR_HEX.get(status_val, "#7a6a1a")),
        leading=18, spaceAfter=4)
    s_firma_label = ParagraphStyle("FirmaLabel", parent=base_styles["Normal"],
        fontSize=8, textColor=colors.HexColor("#555555"), leading=10)
    s_footer = ParagraphStyle("Footer", parent=base_styles["Normal"],
        fontSize=7, textColor=colors.HexColor("#888888"), leading=9)

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=2.5 * cm, rightMargin=2.5 * cm,
        topMargin=2.2 * cm, bottomMargin=2.5 * cm,
        title=f"Acta de Revisión — {suite.pipeline_run_id}",
        author=suite.review.approved_by or "pendiente",
        subject="Contract B — Revisión QA ISO 25010 / CMMI-DEV L3",
    )

    story = []
    emit = story.append

    # ── Encabezado ──────────────────────────────────────────────────────────
    emit(Paragraph("ACTA DE REVISIÓN DE CALIDAD", s_titulo))
    emit(Paragraph("Contract B — Matriz ISO 25010 / Auditoría CMMI-DEV L3", s_subtitulo))
    emit(HRFlowable(width="100%", thickness=2, color=_COLOR_HEADER, spaceAfter=10))

    meta_data = [
        ["Pipeline Run ID",     _safe(suite.pipeline_run_id)],
        ["Agente generador",    _safe(suite.agent_version)],
        ["Versión del suite",   str(suite.review.version)],
        ["Fecha de emisión",    datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
    ]
    meta_table = Table(meta_data, colWidths=[5 * cm, 11 * cm])
    meta_table.setStyle(TableStyle([
        ("FONTNAME",      (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
        ("FONTNAME",      (0, 0), (0, -1), "Helvetica-Bold"),
        ("TEXTCOLOR",     (0, 0), (0, -1), _COLOR_HEADER),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    emit(meta_table)
    emit(Spacer(1, 0.3 * cm))

    # ── 1. Decisión del analista ─────────────────────────────────────────────
    emit(Paragraph("1. DECISIÓN DEL ANALISTA", s_seccion))
    estado_label = _STATUS_LABEL.get(status_val, status_val.upper())
    emit(Paragraph(f"<b>Estado del suite:</b> {estado_label}", s_estado))

    decision_data = [
        ["Revisor / Analista QA", _safe(suite.review.approved_by or "(no registrado)")],
        ["Aprobado en",
         suite.review.approved_at.strftime("%Y-%m-%d %H:%M:%S") if suite.review.approved_at else "(no aplica)"],
        ["Feedback del analista",
         _safe(suite.review.analyst_feedback or "(sin comentarios adicionales)")],
    ]
    dt = Table(decision_data, colWidths=[5 * cm, 11 * cm])
    dt.setStyle(TableStyle([
        ("FONTNAME",      (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("FONTNAME",      (0, 0), (0, -1), "Helvetica-Bold"),
        ("BACKGROUND",    (0, 0), (-1, 0), _COLOR_TABLE_HDR),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("BOX",           (0, 0), (-1, -1), 0.5, colors.HexColor("#aaaaaa")),
        ("INNERGRID",     (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
    ]))
    emit(dt)

    # ── 2. Resumen de escenarios ─────────────────────────────────────────────
    emit(Paragraph("2. RESUMEN DE ESCENARIOS", s_seccion))
    acciones_log = suite.review.change_history
    n_aceptados      = sum(1 for c in acciones_log if c.action == "accepted")
    n_reclasificados = sum(1 for c in acciones_log if c.action == "reclassified")
    n_comentados     = sum(1 for c in acciones_log if c.action == "comment_added")

    resumen_data = [
        ["Total escenarios",             str(suite.total_scenarios)],
        ["Aceptados sin cambios",         str(n_aceptados)],
        ["Reclasificados por el analista",str(n_reclasificados)],
        ["Con comentarios",               str(n_comentados)],
    ]
    rt = Table(resumen_data, colWidths=[8 * cm, 8 * cm])
    rt.setStyle(TableStyle([
        ("FONTNAME",      (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("FONTNAME",      (0, 0), (0, -1), "Helvetica-Bold"),
        ("BACKGROUND",    (0, 0), (-1, 0), _COLOR_TABLE_HDR),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, _COLOR_ROW_ALT]),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("BOX",           (0, 0), (-1, -1), 0.5, colors.HexColor("#aaaaaa")),
        ("INNERGRID",     (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
    ]))
    emit(rt)

    # ── 3. Reclasificaciones ─────────────────────────────────────────────────
    emit(Paragraph("3. INTERVENCIÓN DEL ANALISTA", s_seccion))
    reclasifs = resumen.get("reclasificaciones", [])
    if reclasifs:
        emit(Paragraph(f"<b>Reclasificaciones ({len(reclasifs)} escenario(s))</b>", s_normal))
        rh = [
            Paragraph("<b>Escenario</b>", s_normal),
            Paragraph("<b>LLM clasificó como</b>", s_normal),
            Paragraph("<b>Analista corrigió a</b>", s_normal),
            Paragraph("<b>Justificación</b>", s_normal),
        ]
        rows = [rh]
        for r in reclasifs:
            rows.append([
                Paragraph(_safe(r["nombre"]),     s_mono),
                Paragraph(_safe(r["qc_antes"]),   s_mono),
                Paragraph(_safe(r["qc_despues"]), s_mono),
                Paragraph(_safe(r["razon"] or "—"), s_mono),
            ])
        tbl = Table(rows, colWidths=[3.8*cm, 3.5*cm, 3.5*cm, 5.2*cm])
        tbl.setStyle(TableStyle([
            ("FONTNAME",      (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE",      (0, 0), (-1, -1), 8),
            ("BACKGROUND",    (0, 0), (-1, 0), _COLOR_TABLE_HDR),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING",    (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("BOX",           (0, 0), (-1, -1), 0.5, colors.HexColor("#aaaaaa")),
            ("INNERGRID",     (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
        ]))
        emit(tbl)
        emit(Spacer(1, 0.2 * cm))
    else:
        emit(Paragraph(
            "El analista no introdujo ninguna reclasificación. "
            "La clasificación ISO 25010 original fue aceptada en su totalidad.",
            s_normal,
        ))

    # ── 4. Matriz de cobertura ISO 25010 ─────────────────────────────────────
    emit(Paragraph("4. MATRIZ DE COBERTURA ISO 25010 (post-revisión)", s_seccion))
    cobertura = suite.coverage_by_characteristic
    total_esc = sum(cobertura.values()) or 1

    mh = [
        Paragraph("<b>Característica ISO 25010</b>", s_normal),
        Paragraph("<b>Escenarios</b>", s_normal),
        Paragraph("<b>% del total</b>", s_normal),
    ]
    mrows = [mh]
    for qc in QualityCharacteristic:
        n = cobertura.get(qc.value, 0)
        pct = f"{n / total_esc * 100:.1f}%"
        mrows.append([
            Paragraph(_safe(qc.value), s_normal),
            Paragraph(str(n), s_normal),
            Paragraph(pct, s_normal),
        ])
    mrows.append([
        Paragraph("<b>TOTAL</b>", s_normal),
        Paragraph(f"<b>{sum(cobertura.values())}</b>", s_normal),
        Paragraph("<b>100%</b>", s_normal),
    ])
    row_colors = [
        ("BACKGROUND", (0, i), (-1, i), _COLOR_ROW_ALT if i % 2 == 0 else colors.white)
        for i in range(1, len(mrows) - 1)
    ]
    mt = Table(mrows, colWidths=[9 * cm, 3 * cm, 4 * cm])
    mt.setStyle(TableStyle([
        ("FONTNAME",      (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("BACKGROUND",    (0, 0), (-1, 0), _COLOR_TABLE_HDR),
        ("BACKGROUND",    (0, -1), (-1, -1), _COLOR_TABLE_HDR),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("BOX",           (0, 0), (-1, -1), 0.5, colors.HexColor("#aaaaaa")),
        ("INNERGRID",     (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
        ("ALIGN",         (1, 0), (2, -1), "CENTER"),
    ] + row_colors))
    emit(mt)

    # ── 5. Log de auditoría ──────────────────────────────────────────────────
    emit(Paragraph("5. LOG DE AUDITORÍA", s_seccion))
    if not acciones_log:
        emit(Paragraph("(Sin acciones registradas)", s_normal))
    else:
        lh = [
            Paragraph("<b>#</b>", s_normal),
            Paragraph("<b>Timestamp</b>", s_normal),
            Paragraph("<b>Revisor</b>", s_normal),
            Paragraph("<b>Acción</b>", s_normal),
            Paragraph("<b>Notas</b>", s_normal),
        ]
        lrows = [lh]
        for i, chg in enumerate(acciones_log, 1):
            ts = chg.timestamp.strftime("%Y-%m-%d %H:%M") if chg.timestamp else "—"
            lrows.append([
                Paragraph(str(i), s_mono),
                Paragraph(_safe(ts), s_mono),
                Paragraph(_safe(chg.reviewer), s_mono),
                Paragraph(_safe(chg.action), s_mono),
                Paragraph(_safe(chg.notes or ""), s_mono),
            ])
        alt = [("BACKGROUND", (0, i), (-1, i), _COLOR_ROW_ALT)
               for i in range(2, len(lrows), 2)]
        lt = Table(lrows, colWidths=[0.8*cm, 3.2*cm, 2.5*cm, 2.8*cm, 6.7*cm])
        lt.setStyle(TableStyle([
            ("FONTNAME",      (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE",      (0, 0), (-1, -1), 7.5),
            ("BACKGROUND",    (0, 0), (-1, 0), _COLOR_TABLE_HDR),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING",    (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("BOX",           (0, 0), (-1, -1), 0.5, colors.HexColor("#aaaaaa")),
            ("INNERGRID",     (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
        ] + alt))
        emit(lt)

    # ── 6. Matriz de riesgos ─────────────────────────────────────────────────
    emit(Spacer(1, 0.3 * cm))
    emit(Paragraph("6. MATRIZ DE RIESGOS ISO/IEC 25010", s_seccion))

    if matriz_riesgos is None:
        emit(Paragraph("Matriz de riesgos no disponible en esta sesión.", s_normal))
    else:
        res_riesgos = matriz_riesgos.get("resumen_ejecutivo", {})
        enriq       = matriz_riesgos.get("enriquecido_llm", False)
        fuente_rec  = "Groq / LLM (llama-3.3-70b)" if enriq else "Capa determinista"

        emit(Paragraph(
            f"Análisis sobre {matriz_riesgos.get('total_escenarios', '?')} escenarios. "
            f"Recomendaciones: <b>{_safe(fuente_rec)}</b>.",
            s_normal,
        ))
        emit(Spacer(1, 0.15 * cm))

        conteo_data = [
            [
                Paragraph(f"<b>{res_riesgos.get('criticos', 0)}</b>", s_normal),
                Paragraph(f"<b>{res_riesgos.get('altos', 0)}</b>",    s_normal),
                Paragraph(f"<b>{res_riesgos.get('medios', 0)}</b>",   s_normal),
                Paragraph(f"<b>{res_riesgos.get('bajos', 0)}</b>",    s_normal),
            ],
            [
                Paragraph("CRÍTICO", s_normal), Paragraph("ALTO", s_normal),
                Paragraph("MEDIO", s_normal),   Paragraph("BAJO", s_normal),
            ],
        ]
        ct = Table(conteo_data, colWidths=[4*cm, 4*cm, 4*cm, 4*cm])
        ct.setStyle(TableStyle([
            ("FONTNAME",      (0, 0), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, 0),  14),
            ("FONTSIZE",      (0, 1), (-1, 1),   8),
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1),  4),
            ("BOTTOMPADDING", (0, 0), (-1, -1),  4),
            ("BACKGROUND",    (0, 0), (0, -1), colors.HexColor(NIVEL_COLOR_HEX["CRITICO"])),
            ("BACKGROUND",    (1, 0), (1, -1), colors.HexColor(NIVEL_COLOR_HEX["ALTO"])),
            ("BACKGROUND",    (2, 0), (2, -1), colors.HexColor(NIVEL_COLOR_HEX["MEDIO"])),
            ("BACKGROUND",    (3, 0), (3, -1), colors.HexColor(NIVEL_COLOR_HEX["BAJO"])),
            ("TEXTCOLOR",     (0, 0), (-1, -1), colors.white),
        ]))
        emit(ct)
        emit(Spacer(1, 0.3 * cm))

        riesgo_header = [
            Paragraph("<b>Característica</b>",       s_normal),
            Paragraph("<b>Nivel</b>",                s_normal),
            Paragraph("<b>Esc.</b>",                 s_normal),
            Paragraph("<b>%</b>",                    s_normal),
            Paragraph("<b>Descripción del riesgo</b>", s_normal),
            Paragraph("<b>Recomendación</b>",        s_normal),
        ]
        riesgo_rows = [riesgo_header]
        for r in matriz_riesgos.get("riesgos", []):
            nivel     = r.get("nivel", "BAJO")
            nivel_hex = NIVEL_COLOR_HEX.get(nivel, "#1a7a3c")
            rec_texto = r.get("recomendacion_llm") or r.get("recomendacion_base", "")
            riesgo_rows.append([
                Paragraph(_safe(r.get("qc", "")), s_mono),
                Paragraph(f'<font color="{nivel_hex}"><b>{_safe(nivel)}</b></font>', s_mono),
                Paragraph(str(r.get("n_escenarios", 0)), s_mono),
                Paragraph(f"{r.get('pct_total', 0)}%", s_mono),
                Paragraph(_safe(r.get("descripcion_riesgo", "")[:150]), s_mono),
                Paragraph(_safe(rec_texto[:160]), s_mono),
            ])
        alt_r = [("BACKGROUND", (0, i), (-1, i), _COLOR_ROW_ALT)
                 for i in range(2, len(riesgo_rows), 2)]
        rrt = Table(riesgo_rows, colWidths=[3.2*cm, 1.6*cm, 0.9*cm, 0.8*cm, 5.2*cm, 4.3*cm])
        rrt.setStyle(TableStyle([
            ("FONTNAME",      (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE",      (0, 0), (-1, -1), 7.5),
            ("BACKGROUND",    (0, 0), (-1, 0), _COLOR_TABLE_HDR),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING",    (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("BOX",           (0, 0), (-1, -1), 0.5, colors.HexColor("#aaaaaa")),
            ("INNERGRID",     (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
        ] + alt_r))
        emit(rrt)

    # ── 7. Firmas ────────────────────────────────────────────────────────────
    emit(Spacer(1, 0.6 * cm))
    emit(Paragraph("7. FIRMAS", s_seccion))
    emit(Spacer(1, 0.5 * cm))

    linea = "_" * 38
    sp = Spacer(1, 0.1 * cm)
    firma_left = [
        Paragraph(linea, s_firma_label), sp,
        Paragraph("<b>Analista QA / Revisor</b>", s_firma_label),
        Paragraph(f"Nombre: {_safe(suite.review.approved_by or '________________________________')}", s_firma_label),
        Paragraph("Cargo: ________________________________", s_firma_label),
        Paragraph("Fecha: ________________________________", s_firma_label),
    ]
    firma_right = [
        Paragraph(linea, s_firma_label), sp,
        Paragraph("<b>Supervisor / Líder QA</b>", s_firma_label),
        Paragraph("Nombre: ________________________________", s_firma_label),
        Paragraph("Cargo: ________________________________", s_firma_label),
        Paragraph("Fecha: ________________________________", s_firma_label),
    ]
    firma_table = Table([[firma_left, firma_right]], colWidths=[8 * cm, 8 * cm])
    firma_table.setStyle(TableStyle([
        ("VALIGN",  (0, 0), (-1, -1), "TOP"),
        ("ALIGN",   (0, 0), (-1, -1), "LEFT"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    emit(firma_table)

    # ── Pie de página ────────────────────────────────────────────────────────
    emit(Spacer(1, 0.6 * cm))
    emit(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#aaaaaa"), spaceAfter=4))
    emit(Paragraph(
        f"Documento generado por NovaTetch QualityAI · "
        f"Emitido: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        s_footer,
    ))
    emit(Paragraph(
        "Este acta es evidencia de auditoría bajo CMMI-DEV L3. No modificar manualmente.",
        s_footer,
    ))

    doc.build(story)
    return pdf_path
