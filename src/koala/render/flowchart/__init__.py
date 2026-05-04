"""Placeholder para el render de `flowchart`.

Para implementarlo, este paquete debe contener:
- `profiles.py`: registra `RenderProfile` por layout y tipografias propias en
  `RenderProfileCatalog` (ver `render/tree/profiles.py` como ejemplo).
- `roles.py`: mapea roles de nodo (decision, process, data, ...) a slots de
  paleta universales (`focus`, `main`, `note`, ...). El render consulta
  `ThemeConfig.style_for(slot)`.
- `svg_render.py`: pipeline SVG que reciba un `SvgRenderRequest` y retorne
  `RenderResult(document_type="flowchart", ...)`.

`__init__.py` debe importar `profiles` para que la registracion ocurra al
cargar el paquete.
"""
