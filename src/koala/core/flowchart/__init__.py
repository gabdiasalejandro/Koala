"""Placeholder para el tipo de documento `flowchart`.

Para implementarlo, este paquete debe contener:
- `models.py`: modelos de dominio con roles semanticos por nodo (start, end,
  process, decision, data, ...).
- `parser.py`: parser del DSL de flowchart.
- `pipeline.py`: `FlowchartDocumentPipeline` que cumpla el protocolo descrito
  en `docs/architecture.md` ("Adding a new document type") y se registre en
  `koala.core.shared.registry`.

Los roles definidos aqui se mapean a slots de paleta universales en
`render/flowchart/` (ver "Themes, palette slots, and node roles" en la doc
de arquitectura).
"""
