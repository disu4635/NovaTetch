---
name: NovaTetch — QualityAI Requirements Refiner
description: Herramienta de análisis inteligente de requerimientos que convierte ambigüedad en estructura verificable.
colors:
  surface-deep: "#020617"
  surface-base: "#0f172a"
  surface-raised: "#1e293b"
  border-default: "#334155"
  border-subtle: "#1e293b"
  text-primary: "#ffffff"
  text-secondary: "#e2e8f0"
  text-muted: "#94a3b8"
  text-faint: "#64748b"
  inference-violet: "#7c3aed"
  inference-violet-hover: "#8b5cf6"
  inference-violet-soft: "#a78bfa"
  inference-violet-ghost: "#1e1040"
  pipeline-emerald: "#10b981"
  pipeline-emerald-soft: "#34d399"
  risk-critical: "#ef4444"
  risk-high: "#ea580c"
  risk-medium: "#ca8a04"
  risk-low: "#15803d"
typography:
  display:
    fontFamily: "system-ui, -apple-system, sans-serif"
    fontSize: "1.875rem"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-0.01em"
  headline:
    fontFamily: "system-ui, -apple-system, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 600
    lineHeight: 1.4
  body:
    fontFamily: "system-ui, -apple-system, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: "system-ui, -apple-system, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 500
    letterSpacing: "0.02em"
  mono:
    fontFamily: "ui-monospace, SFMono-Regular, 'Cascadia Code', monospace"
    fontSize: "0.75rem"
    fontWeight: 700
rounded:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  full: "9999px"
spacing:
  xs: "8px"
  sm: "12px"
  md: "16px"
  lg: "24px"
  xl: "40px"
components:
  button-primary:
    backgroundColor: "{colors.inference-violet}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.md}"
    padding: "12px 24px"
  button-primary-hover:
    backgroundColor: "{colors.inference-violet-hover}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.md}"
    padding: "12px 24px"
  button-sm:
    backgroundColor: "{colors.inference-violet}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.sm}"
    padding: "8px 16px"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.text-muted}"
    rounded: "{rounded.sm}"
    padding: "6px 8px"
  card-default:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.text-secondary}"
    rounded: "{rounded.lg}"
    padding: "24px"
  input-default:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.text-secondary}"
    rounded: "{rounded.md}"
    padding: "16px"
  badge-accent:
    backgroundColor: "{colors.inference-violet-ghost}"
    textColor: "{colors.inference-violet-soft}"
    rounded: "{rounded.full}"
    padding: "2px 10px"
---

# Design System: NovaTetch

## 1. Overview

**Creative North Star: "The Clarity Engine"**

NovaTetch existe para hacer una cosa: convertir lo ambiguo en lo preciso. El sistema visual refleja este proceso. No hay decoración. Cada elemento está donde está porque cumple una función en el pipeline de análisis. La interfaz no compite con el contenido — la jerarquía del análisis habla, la chrome se calla.

El tema es oscuro por razones concretas: los analistas que usan esta herramienta trabajan en entornos técnicos, con múltiples pantallas, a menudo por horas. Un fondo oscuro reduce la fatiga visual y crea contraste para las señales de estado (riesgo crítico, validado, en proceso). El modo claro existe como ciudadano de primera clase para ambientes distintos, no como afterthought.

La densidad es deliberada. El sistema no esconde información detrás de tooltips ni la pagina artificialmente. Los datos están visibles, organizados en jerarquía. La profundidad se construye con capas de opacidad sobre una paleta de slate — sin sombras, sin glassmorphism, sin efectos que no aporten información.

**Key Characteristics:**
- Plano por diseño: sin sombras, profundidad solo por opacidad y borde
- El acento violet aparece en menos del 15% de cualquier pantalla — su escasez es su fuerza
- El emerald solo marca el flujo de éxito/codegen; nunca compite con el violet
- Tipografía del sistema: sin fuentes personalizadas cargadas, velocidad sobre expresividad
- Estado del pipeline siempre inequívoco: el usuario nunca duda en qué fase está

## 2. Colors: The Slate-to-Void Palette

Una paleta construida sobre un ramp de slate profundo, con un único acento de propósito semántico y colores de estado funcionales.

### Primary
- **Inference Violet** (`#7c3aed`): el único color que inicia acciones. Botones primarios, indicadores de progreso, badges de IDs. Aparece cuando la IA actúa o cuando el analista puede actuar. Su scarcity es intencional.
- **Inference Violet Hover** (`#8b5cf6`): estado hover del acento principal. Un paso más claro en el mismo ramp.
- **Inference Violet Soft** (`#a78bfa`): texto y iconos de acento sobre fondos oscuros. Labels de badges, iconos en contexto coloreado.

### Secondary
- **Pipeline Emerald** (`#10b981`): exclusivo para el flujo codegen y estados de éxito completado. Señala que el pipeline cerró correctamente. Nunca aparece junto a violet como acento competidor.
- **Pipeline Emerald Soft** (`#34d399`): versión legible del emerald sobre fondos oscuros. Estado "Completado" en historial.

### Neutral
- **Surface Deep** (`#020617`): fondo raíz. El void. Gradiente del canvas principal.
- **Surface Base** (`#0f172a`): fondo del body y el header sticky. El default de toda superficie que no está elevada.
- **Surface Raised** (`#1e293b`): tarjetas, inputs, paneles. La capa sobre la base.
- **Border Default** (`#334155`): bordes de tarjetas y divisores.
- **Text Primary** (`#ffffff`): headings de primer nivel, botones, elementos críticos.
- **Text Secondary** (`#e2e8f0`): body text, contenido de cards, texto de historia.
- **Text Muted** (`#94a3b8`): labels de campo, metadatos, texto de apoyo.
- **Text Faint** (`#64748b`): timestamps, IDs secundarios, notas de contexto.

### Status (funcionales, no decorativos)
- **Risk Critical** (`#ef4444`): errores del sistema, riesgo crítico ISO 25010.
- **Risk High** (`#ea580c`): riesgo alto.
- **Risk Medium** (`#ca8a04`): riesgo medio, suposiciones hechas por el LLM.
- **Risk Low** (`#15803d`): riesgo bajo, coberturas satisfactorias.

### Named Rules
**La Regla del Acento Único.** Inference Violet (`#7c3aed`) es el único color que puede iniciar una acción. Si un botón no es la acción principal, no lleva violet. Los botones secundarios son ghost (transparente con texto muted) o destructivos (red). No existe un "botón secundario azul" ni un "botón de apoyo verde".

**La Regla de la Señal Funcional.** Los colores de estado (risk-critical, risk-high, risk-medium, risk-low, pipeline-emerald) son informativos, no decorativos. Nunca se usan para dar "variedad visual" a una página que no está mostrando datos de estado.

## 3. Typography

**Body Font:** system-ui, -apple-system, sans-serif (fuente del sistema operativo)
**Mono Font:** ui-monospace, SFMono-Regular, 'Cascadia Code', monospace

**Character:** La herramienta usa la fuente del sistema intencionalmente. Velocidad de carga, coherencia con el entorno técnico del usuario, sin fricción de descarga de fuentes. La jerarquía se construye con peso y tamaño, no con expresividad tipográfica. El mono se reserva para IDs, criterios de aceptación tipo código, y valores de datos — marca claramente qué es "dato del sistema" versus "texto natural".

### Hierarchy

- **Display** (700, 1.875rem/30px, lh 1.2): el único h2 de pantalla — "Transforma requerimientos en historias de usuario". Solo aparece en el estado idle de la app. Una ocurrencia por sesión.
- **Headline** (600, 1.125rem/18px, lh 1.4): títulos de sección y paneles importantes ("Ambigüedades detectadas", "Revisión de calidad"). Máximo 2-3 por pantalla.
- **Title** (600, 1rem/16px, lh 1.4): título de tarjeta, nombre de historia de usuario. El nivel más denso del contenido.
- **Body** (400, 0.875rem/14px, lh 1.6): texto de contenido, descripciones, narrativa de historia (Como / Quiero / Para que). Max-width implícita de ~70ch para bloques de texto largo.
- **Label** (500, 0.75rem/12px, ls 0.02em): metadatos, conteos, timestamps, nombres de campo. Muted por defecto.
- **Mono** (700, 0.75rem/12px): IDs de historia (US-001), IDs de criterio (AC-001), valores de datos de prueba, valores límite. Siempre en `text-violet-400` cuando representa un identificador del sistema.

### Named Rules
**La Regla del Mono Semántico.** La fuente monoespaciada no es decorativa. Se usa solo cuando el contenido ES un dato del sistema: un ID, un valor de test, un límite numérico. El texto narrativo — aunque sea técnico — va en la fuente del sistema.

## 4. Elevation

Este sistema es plano por diseño, sin excepciones. No existen `box-shadow` en ningún componente. La profundidad se construye exclusivamente a través de capas de opacidad sobre la paleta de slate:

- **Nivel 0 — Void** (`surface-deep`): el fondo del canvas. Nunca contiene elementos directamente.
- **Nivel 1 — Base** (`surface-base`): el plano de trabajo. El header sticky, el body.
- **Nivel 2 — Raised** (`surface-raised` / `bg-slate-800/40`—`/60`): tarjetas, inputs, paneles. La opacidad varía: 40% para contenedores secundarios, 50-60% para contenedores primarios.
- **Nivel 3 — Emphasized** (`bg-slate-900/50`): bloques de contenido dentro de una tarjeta (la narrativa de historia, los criterios Gherkin dentro de un card). Más oscuro que el contenedor padre.

Los bordes (`border-slate-700`) actúan como divisores de nivel, no como decoración.

**La Regla de la Tinta Sin Sombra.** Si el diseño necesita una sombra para "parecer elevado", el problema real es que la jerarquía de superficie está mal construida. Resolver con opacidad y borde, nunca con `box-shadow`.

## 5. Components

### Buttons
Táctiles y directos. Sin bordes redondeados extremos, sin gradientes.

- **Shape:** Gently rounded (12px) para botones primarios; mildly rounded (8px) para botones pequeños e inline.
- **Primary** (`bg-violet-600`, texto blanco, padding 12px 24px, rounded 12px): para la única acción posible en el estado actual del pipeline. Máximo uno visible por vez.
- **Primary Small** (`bg-violet-600`, padding 8px 16px, rounded 8px): botones dentro de cards o paneles (ej. "Iniciar análisis de calidad", "Descargar acta PDF").
- **Ghost / Destructive** (transparente, texto `text-muted`, hover `text-red-400` + `bg-red-500/10`): acciones secundarias como eliminar del historial. Invisible hasta hover; `group-hover:opacity-100`.
- **Hover:** `bg-violet-500` — un paso más claro. Transición `transition-colors` de 150ms.
- **Disabled:** `opacity-50`, `cursor-not-allowed`. No cambios estructurales.
- **Loading state:** spinner inline (h-4 w-4, border-2 border-white border-t-transparent, animate-spin) con label descriptivo ("Analizando...", "Generando historias...").

### Cards / Containers
El contenedor estándar del sistema. No nested.

- **Corner Style:** Suavemente redondeado (16px / rounded-2xl) para contenedores primarios; moderadamente redondeado (12px / rounded-xl) para contenedores secundarios y badges de estado.
- **Background:** `bg-slate-800/40` (40% opacidad) para la mayoría de los paneles; `bg-slate-800/50` y `/60` para inputs y áreas de mayor énfasis.
- **Shadow Strategy:** Ninguna. Ver Elevation.
- **Border:** `border border-slate-700` para contenedores neutros; `border-violet-500/30` para paneles en contexto del pipeline principal; `border-emerald-500/30` para paneles de éxito/codegen.
- **Internal Padding:** 24px (`p-6`) para paneles de sección; 20px (`p-5`) para cards de historial y resultado; 16px (`p-4`) para bloques de contenido anidado.

**La Regla de Sin Anidación Decorativa.** Los cards no se anidan para crear jerarquía visual. El bloque interno que muestra la narrativa "Como / Quiero / Para que" usa `bg-slate-900/50` (tono más oscuro) para señalar su naturaleza de contenido, no un card dentro de un card. La diferencia entre contenedor y contenido es de color y opacidad, no de borde y elevación repetidos.

### Inputs / Fields
- **Style:** `border border-slate-700`, `bg-slate-800/60`, `rounded-xl` (12px), padding 16px.
- **Text:** `text-slate-100`, placeholder `placeholder-slate-500`.
- **Focus:** `focus:outline-none focus:ring-2 focus:ring-violet-500` — el anillo violet es la única señal de foco activo. Sin cambio de borde ni de fondo.
- **Disabled:** heredado del botón padre que controla el estado.
- **Small variant** (inline, dentro de cards de ambigüedad): `border-slate-600`, `bg-slate-900/60`, `rounded-lg` (8px), padding 8px 12px.

### Badges / Chips
- **Priority / Status badges:** `rounded-full`, padding `px-2 py-0.5`, `text-xs font-medium`, con `border` y variantes por semántica (red/orange/amber/slate para prioridad; blue/purple/cyan para tipo de historia).
- **ID badges:** `rounded-lg`, `bg-violet-500/20`, `text-violet-300`, `border border-violet-500/30`, fuente mono — el tratamiento especial para identificadores del sistema.
- **Count badges:** `rounded-full`, `bg-violet-500/20`, `text-violet-300` — conteo de ambigüedades en el heading del resolver.

### Navigation / Header
- **Style:** sticky, `border-b border-slate-800`, `bg-slate-900/80 backdrop-blur` — el backdrop blur es funcional aquí: preserva la legibilidad del header sobre contenido en scroll.
- **Brand mark:** `h-8 w-8 rounded-lg bg-violet-600` con icono `Cpu` blanco. El único uso de violet saturado en el chrome de la app.
- **Action link:** "Nuevo análisis" — `text-slate-400 hover:text-slate-200`, inline con icono `Plus`. Ghost, nunca button-shaped.

### Progress Spinners
- **Large** (`h-12 w-12`, `border-4 border-violet-500 border-t-transparent`, `animate-spin`): para fases de espera del pipeline (generando, analizando, running quality).
- **Small inline** (`h-4 w-4`, `border-2`, `animate-spin`): dentro de botones durante su propio estado loading.
- El spinner de éxito (codegen-submitting) usa `border-emerald-500` para señalar que el contexto es el pipeline de código.

### Story Cards (componente distintivo)
Acordeón de información estructurada. El primer item abre por defecto.

- **Header clickable:** full-width, `hover:bg-slate-700/30`, sin border-radius propio (hereda del contenedor). ID badge mono + título truncado + badges de prioridad/tipo + chevron animado.
- **Body expandido:** padding 24px, flex-col con gap 24px entre secciones (narrativa, criterios, reglas de negocio, ambigüedades resueltas).
- **Criterio negativo:** `border-red-500/30 bg-red-500/5` — único uso de rojo en el contenido de historia. Señal inmediata de caso de falla esperado.

## 6. Do's and Don'ts

### Do:
- **Do** usar `bg-violet-600` exclusivamente para el botón de la acción principal del paso actual del pipeline. Un botón primary por pantalla visible.
- **Do** usar `bg-slate-800/40` con `border border-slate-700` como el tratamiento estándar de contenedor. Es el default, no la excepción.
- **Do** representar todos los IDs del sistema (US-001, AC-001, run IDs) con fuente mono en `text-violet-400`. La tipografía diferencia "dato del sistema" de "texto natural".
- **Do** construir profundidad con tonos de slate y opacidad. Subir al siguiente nivel de superficie significa ir a un tono más oscuro de bg, no agregar sombra.
- **Do** mantener el emerald (`#10b981`) exclusivo del flujo codegen y éxito de pipeline. Es la señal visual de "completado", no un color de apoyo general.
- **Do** usar `transition-colors` de 150ms como duración estándar para hover states. Rápido y responsivo.
- **Do** incluir `cursor-pointer` explícito en todos los elementos interactivos que no son `<a>` o `<button>` nativo.

### Don't:
- **Don't** usar `box-shadow` en ningún componente. El sistema es plano; las sombras rompen el lenguaje de elevación por opacidad.
- **Don't** crear SaaS oscuro genérico con gradientes violet y glow effects — el cliché de "herramienta de IA 2024". Inference Violet es un color de acción funcional, no una marca de identidad para gradientes.
- **Don't** mostrar el dashboard con métricas enormes en hero (big-number + label + gradiente acento). La barra de estadísticas existe para contexto rápido, no como elemento de marketing interno.
- **Don't** usar uppercase tracking amplio en eyebrows encima de cada sección. Está permitido solo en labels de campo ("REQUERIMIENTO", "ID DE EJECUCIÓN") cuando son metadata, no como estructura visual de página.
- **Don't** usar glassmorphism. El `backdrop-blur` del header es la única excepción admitida, y existe por razón funcional (legibilidad en scroll), no decorativa.
- **Don't** anidar cards dentro de cards para crear jerarquía. El bloque de contenido interno usa tono de bg más oscuro (`bg-slate-900/50`), no un nuevo contenedor con border y padding propio.
- **Don't** usar gradientes de texto (`background-clip: text`). Cualquier texto con acento va en `text-violet-400` o `text-violet-300` sólido.
- **Don't** usar los colores de estado (risk-critical, risk-high, risk-medium, risk-low) para decoración visual. Solo aparecen cuando el dato que representan está en pantalla.
- **Don't** usar `border-left > 1px` como stripe decorativo en cards o items de lista. Los contenedores de ambigüedad usan color de fondo y borde completo como unidad, no rayas laterales.
