# End To End

Estructura:

- `code/`: runner y suite del test end to end
- `mocks/`: archivos fuente usados por la suite
- `output/`: SVGs generados agrupados por `theme` y luego por `text-align`

Comando:

```bash
./.venv/bin/python tests/end_to_end/code/run_e2e.py
```

El manifiesto queda en `tests/end_to_end/e2e_manifest.json`.

Cobertura actual del end to end:

- todos los `themes`
- todos los `layouts`
- `text-align left` y `text-align justify`
- `show-node-numbers` en `true` y `false`
- `page sizes` rotadas entre `a4`, `a4_landscape` y `square`
