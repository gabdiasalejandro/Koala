# Tests

Estructura base de tests del proyecto:

- `unit/`: unit tests de funciones y módulos aislados.
- `structural/`: tests de estructura para validar invariantes del SVG y de la escena generada.
- `end_to_end/`: ejecución completa del pipeline con mocks reales y generación de SVGs.

Comando actual para correr el end to end:

```bash
./.venv/bin/python tests/end_to_end/code/run_e2e.py
```

El output generado queda en `tests/end_to_end/output/` y el manifiesto en `tests/end_to_end/e2e_manifest.json`.
