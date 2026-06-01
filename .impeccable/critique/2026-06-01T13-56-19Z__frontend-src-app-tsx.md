---
target: frontend/src/App.tsx
total_score: 19
p0_count: 3
p1_count: 4
timestamp: 2026-06-01T13-56-19Z
slug: frontend-src-app-tsx
---
## Design Health Score

| # | Heurística | Punt. | Problema clave |
|---|-----------|-------|----------------|
| 1 | Visibility of System Status | 3 | Sin indicador de paso N de M en el pipeline |
| 2 | Match System / Real World | 3 | "Agente V3 en ejecución" — nombre de código interno expuesto |
| 3 | User Control and Freedom | 2 | Sin navegación hacia atrás; "Nuevo análisis" destruye todo el trabajo |
| 4 | Consistency and Standards | 3 | Dos patrones de spinner; variaciones menores en radios de card |
| 5 | Error Prevention | 2 | Sin confirmación para borrar runs ni para "Nuevo análisis" en pipeline activo |
| 6 | Recognition Rather Than Recall | 3 | Sin indicador de qué sigue después de cada paso |
| 7 | Flexibility and Efficiency | 1 | Sin shortcuts de teclado; sin copiar historias; sin expandir todo |
| 8 | Aesthetic and Minimalist Design | 2 | Stats bar hero-metric + eyebrows uppercase en cada sección |
| 9 | Error Recovery | 2 | "Intentar de nuevo" destruye el estado — no reintenta |
| 10 | Help and Documentation | 1 | Sin ayuda contextual; sin explicación de términos técnicos |
| **Total** | | **22/40** | **Acceptable** |

## Anti-Patterns Verdict

**Rating: moderado.**

1. Stats bar como hero-metric (App.tsx:421–444, ScenarioReviewer.tsx:217–238)
2. Uppercase eyebrow en cada sección — AI grammar explícita
3. Página que acumula sin descartar (quality-done muestra todo simultáneamente)

Scan determinístico: 7 findings, 6 falsos positivos (ternarios), 1 válido (ScenarioReviewer.tsx:224 text-violet-400 en métrica).

## Priority Issues

**[P1] "Intentar de nuevo" destruye el estado**
Llama a handleReset() en lugar de reintentar el paso fallido. Para errores en calidad/codegen, el usuario pierde minutos de procesamiento.
Fix: Reintentar el paso fallido preservando run y currentPrompt. Cambiar label según comportamiento real.
Command: /impeccable harden

**[P1] Pipeline unidireccional sin back navigation**
Sin forma de volver al paso anterior sin "Nuevo análisis" que borra todo.
Fix: Separar "Cancelar operación" (preserva paso anterior) de "Nuevo análisis" (reset completo).
Command: /impeccable harden

**[P1] Sin confirmación para acciones destructivas durante pipeline activo**
"Nuevo análisis" y "Eliminar" sin confirmación cuando pipeline está activo.
Fix: Confirmation dialog cuando phase !== 'idle'.
Command: /impeccable harden

**[P2] Stats bar = hero-metric anti-pattern**
Historias/Criterios/Ambigüedades/Suposiciones como big-number + label. Listado en PRODUCT.md anti-references.
Fix: Inline badge o metadata junto a ID de ejecución.
Command: /impeccable quieter

**[P2] Uppercase eyebrow en cada sección**
text-xs uppercase tracking-wider como estructura de página en App.tsx, RunHistory, StoryCard, ScenarioReviewer, RiskMatrix.
Fix: Reservar uppercase para metadata inline; headings de sección con text-sm font-semibold sin uppercase.
Command: /impeccable polish

## Persona Red Flags

Alex (Power User): Sin Ctrl+Enter, sin copy-all, sin expand-all, sin keyboard shortcuts en HITL resolver.
Jordan (First-Timer): "Agente V3 en ejecución" no tiene significado. QualityPanel no es descubrible sin scroll. Sin onboarding.
Valentina (QA Analyst): No puede ver el requerimiento original en quality-review. Escenarios Gherkin sin contexto de historia. Campo reviewer sin validación.

## Minor Observations

- "Historial reciente" con uppercase tracking es redundante
- "Agente V3/V4" son nombres internos de código expuestos al usuario
- No persiste estado en vuelo entre recargas de página
- RiskMatrix usa opacity-80/70/60 sin tokens
- StoryCard usa SVG inline para chevron en vez de ChevronDown de Lucide
- Gradiente from-slate-950 via-slate-900 to-slate-950 innecesario con paleta plana

## Questions to Consider

- ¿Cuánto trabajo se pierde en promedio cuando falla en el paso 3 de 4?
- ¿El output del pipeline adónde va? ¿Existe export integrado como siguiente paso?
- ¿El analista vuelve a la misma sesión en días distintos? Si sí, el estado perdido al recargar sube a P1.
