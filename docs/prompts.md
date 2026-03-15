# Koala DSL generation guide (for LLMs)

Koala is a DSL used to generate structured conceptual diagrams.

Your job is to output **valid Koala syntax** that can be rendered into SVG diagrams.

Follow the rules and examples carefully.

Output **only Koala DSL**.

---

# Core Concept

A Koala document describes a **hierarchy of concepts**.

Hierarchy is defined using **numeric identifiers**.

Example hierarchy:

1
1.1
1.1.1
2
2.1

The numbering defines the tree structure.

---

# Node Syntax

A node has two parts:

<number> <title>
<body text>

Example:

1 Machine Learning
Field of AI focused on learning from data.

Guidelines:

- Titles should be **short and conceptual**
- Move explanations to the **body text**

Good:

1 Photosynthesis
Process used by plants to convert light into energy.

Bad:

1 Photosynthesis is the process by which plants convert sunlight into chemical energy...

---

# Relationships

Relationships can optionally be declared.

Syntax:

verb -> <node>

Example:

explains -> 1.1 Supervised learning
includes -> 1.2 Unsupervised learning

---

# Semantic Kinds

Nodes may declare an optional semantic type.

Syntax:

kind:: <node>

Example:

focus:: 1 Central Concept
hl:: 1.1 Important concept
soft:: 1.2 Secondary detail
main:: 1 Root concept

Available kinds:

main
focus
hl
note
warn
soft

Meaning:

main → root concept of the diagram  
focus → major conceptual sections  
hl → important concepts  
note → tangential explanations  
warn → warnings or common mistakes  
soft → secondary information  

Rules:

- Usually **only one main node**
- Kinds should be **sparse**
- Most nodes **should not use a kind**

---

# Metadata

Metadata appears at the top of the document.

Example:

@layout tree
@theme jungle
@size a4
@show-node-numbers false

Available layouts:

tree
synoptic
synoptic_boxes
radial

Available themes:

default
terracotta
jungle

---

# Structural Limits (IMPORTANT)

Follow these limits to ensure diagrams render correctly.

## Tree
Maximum siblings of root: **3**

Maximum siblings at bottom: **8**

Maximum depth: **7**

Recommended depth: **5**

Recommended total nodes: **12–24**
---

## Synoptic / Synoptic Boxes

Maximum siblings per parent: **11**

Maximum depth: **5**

Recommended total nodes: **12–24**

---

## Radial

Maximum first-level branches: **9**

Maximum depth: **4**

Radial diagrams work best when branches have **similar size**.

Recommended total nodes: **12–20**

---

# Writing Guidelines

Prefer **conceptual titles**.

Move explanations to the **body text**.

Avoid long paragraphs.

Soft limit:

Maximum **65 words per node**.

Do not use **lists inside node text**.

---

# Preferred Conceptual Structure

Most diagrams should follow this structure:

main concept  
major sections  
details

Example:

main:: 1 Ecosystem
System formed by living organisms and their environment.

hl:: 1.1 Producers
Organisms that create energy from sunlight.

hl:: 1.2 Consumers
Organisms that feed on others.

hl:: 1.3 Decomposers
Break down organic matter.

---

# Example Diagram (Tree)

@layout tree
@theme jungle
@size a4
@show-node-numbers false

main:: 1 Administración financiera
Disciplina que estudia cómo se obtienen, administran y utilizan los recursos monetarios dentro de una organización con el objetivo de generar valor y mejorar la toma de decisiones económicas.

focus:: organiza -> 1.1 Definición de finanzas y administración financiera
Explica los conceptos básicos relacionados con el manejo del dinero y la gestión financiera en las empresas.

define -> 1.1.1 Finanzas
Estudian la obtención, administración e inversión del dinero en personas, empresas y gobiernos.

hl:: aplica -> 1.1.2 Administración financiera
Consiste en planear, dirigir y controlar los recursos financieros para maximizar el valor de la empresa.

focus:: organiza -> 1.2 Áreas de las finanzas
Conjunto de campos de estudio que analizan distintos aspectos del uso del dinero en la economía y las organizaciones.

hl:: incluye -> 1.2.1 Administración financiera empresarial
Área que gestiona el capital dentro de las organizaciones y apoya la toma de decisiones económicas.

soft:: conecta -> 1.2.1.1 Mercados de capitales
Espacios donde se compran y venden instrumentos financieros como acciones y bonos.

explica -> 1.2.1.1.1 Función de los mercados
Permiten transferir recursos entre inversionistas y empresas que necesitan financiamiento.

hl:: analiza -> 1.2.2 Inversiones
Estudian cómo asignar recursos financieros para obtener beneficios futuros.

clasifica -> 1.2.2.1 Tipos de inversiones
Distinguen entre inversiones productivas y financieras según el activo o el plazo.

describe -> 1.2.2.1.1 Instrumentos de inversión
Incluyen acciones, bonos y otros títulos que generan rendimientos y presentan diferentes niveles de riesgo.

focus:: define -> 1.3 Metas de la administración financiera
Establecen los objetivos que orientan la gestión del dinero dentro de la empresa.

hl:: busca -> 1.3.1 Maximización del valor empresarial
Objetivo principal que consiste en incrementar la riqueza de los accionistas mediante decisiones financieras eficientes.

explica -> 1.3.1.1 Importancia de las decisiones financieras
Las decisiones sobre inversión, financiamiento y administración del capital determinan el crecimiento y la estabilidad económica de la empresa.

focus:: organiza -> 1.4 Otros conceptos clave
Elementos complementarios que apoyan la gestión y el control de las finanzas empresariales.

hl:: controla -> 1.4.1 Administración del presupuesto
Proceso de planificación y control de los ingresos y gastos de una organización.

gestiona -> 1.4.1.1 Facturación y pagos
Registro de ventas y cumplimiento de obligaciones financieras con proveedores y otras entidades.

hl:: analiza -> 1.4.1.2 Proyecciones financieras e indicadores
Estimaciones y medidas utilizadas para evaluar el desempeño económico de la empresa.

describe -> 1.4.1.2.1 Estados financieros
Documentos contables como el balance general, el estado de resultados y el flujo de efectivo que muestran la situación económica de la organización.

---

# Generation Strategy

Before writing the final DSL:

1. Plan the hierarchy mentally.
2. Ensure numbering is sequential.
3. Ensure depth does not exceed limits.
4. Then write the final DSL.

Do not show the planning step.

Output only valid Koala DSL.
