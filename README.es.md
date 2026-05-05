# Koala

🇪🇸 Español | 🇺🇸 [English](https://github.com/gabdiasalejandro/Koala/blob/main/README.md)

Koala es un DSL para generar diagramas a partir de texto estructurado.

La idea central del proyecto es simple: un mismo archivo fuente debe poder renderizarse en múltiples layouts y estilos sin reescribir el contenido. Hoy soporta mapas jerárquicos tipo `tree` y cuadros comparativos formales tipo `matrix`.

## Uso rápido

Koala se puede usar de dos formas:

- como herramienta CLI mediante el comando instalado `koala`
- como librería de Python mediante `import koala`
- punto de implementación: [src/koala/cli.py](https://github.com/gabdiasalejandro/Koala/blob/main/src/koala/cli.py)
- repositorio: [github.com/gabdiasalejandro/Koala](https://github.com/gabdiasalejandro/Koala)

Instalación desde PyPI:

```bash
pip install koala-diagrams==1.3.6
```

Si prefieres una instalación aislada para usar el CLI:

```bash
pipx install koala-diagrams==1.3.6
```

Instalación directa desde GitHub:

```bash
pip install "git+https://github.com/gabdiasalejandro/Koala.git"
```

Si quieres trabajar desde el repo durante desarrollo:

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/pip install -e . --no-build-isolation
PYTHONPATH=src ./.venv/bin/python -m koala themes
```

Uso desde CLI:

Usa `koala` cuando quieras compilar archivos `.txt` o `.docx` desde terminal.

Comandos básicos:

```bash
koala themes
koala types
koala layouts
koala typographies
koala compile docs/examples/tree.txt --type tree --layout tree
koala compile docs/examples/radial.txt --type tree --layout radial --theme jungle --size square
koala compile comparison.txt --type matrix --layout matrix --typography formal
koala export docs/examples/tree.txt --format png --quality high
koala export comparison.txt --type matrix --layout matrix --format png --quality medium
koala export docs/examples/tree.txt --format pdf --quality high
koala inspect docs/examples/tree.txt
koala validate docs/examples/radial.txt --strict
koala config-path
```

Uso como librería:

Usa `import koala` cuando quieras compilar diagramas desde otro programa Python y recibir un resultado estructurado.

```python
import koala

file_result = koala.compile(
    "docs/examples/radial.txt",
    type="tree",
    layout="radial",
    theme="academic",
    size="square",
    text_align="left",
)

svg_result = koala.render_text(
    """
    1 Tema central
    Explicación principal.

    1.1 Primera rama
    Detalle de apoyo.
    """,
    type="tree",
    layout="tree",
    theme="academic",
)

text_path = koala.save_text(
    "1 Root\nBody.\n",
    "docs/examples/inline_demo",
)

print(file_result.output_svg)
print(svg_result.svg)
print(text_path)

context = koala.inspect_text("1 Root\nBody.\n", layout="tree", theme="academic")
validated = koala.validate_text("1 Root\nBody.\n", type="tree", layout="tree", theme="academic", strict=True)

print(len(context.parsed.node_index))
print(len(validated.parsed.warnings))

png_result = koala.export_text(
    "main:: 1 Tema central\nExplicación principal.\n",
    type="tree",
    format="png",
    quality="high",
    layout="tree",
    theme="frutal",
)

pdf_result = koala.export_text(
    "main:: 1 Tema central\nExplicación principal.\n",
    type="tree",
    format="pdf",
    quality="high",
    layout="tree",
    theme="frutal",
)

print(png_result.media_type, len(png_result.content))
print(pdf_result.media_type, len(pdf_result.content))
```

Ejemplo mínimo de `matrix`:

```text
matrix:: Cuadro comparativo de formatos Koala
columns:: Criterio | Tree | Matrix
row:: Mejor uso | Mapas jerárquicos de conceptos | Comparación lado a lado con criterios constantes
row:: Lectura | De lo general a lo particular | Horizontal y orientada a decisión
footer:: Recomendación | Usa matrix cuando quieras presentar una conclusión comparativa.
```

Render:

```bash
koala compile comparison.txt --type matrix --layout matrix --theme academic --typography formal
koala export comparison.txt --type matrix --layout matrix --format pdf --quality high
```

En general conviene evitar `@show-node-numbers` dentro de la metadata del documento. Es mejor controlar esa preferencia desde flags de CLI, argumentos de librería o config de usuario, salvo que el archivo necesite dejar esa intención embebida explícitamente.

Inputs aceptados por `koala.compile(path, **config)`:

- `path`: archivo fuente `.txt` o `.docx` a compilar
- `type`: tipo de documento a parsear; `tree` o `matrix`; default `tree`
- `layout`: para `tree`, uno de `tree`, `synoptic`, `synoptic_boxes`, `radial`; para `matrix`, `matrix`
- `theme`: nombre de theme como `academic`, `frutal`, `terracotta`, `default`, `jungle`
- `typography`: nombre del preset tipográfico
- `size`: preset de tamaño como `a4`, `a4_landscape`, `square`
- `text_align`: `left` o `justify`
- `show_node_numbers`: fuerza mostrar u ocultar la numeración de nodos
- `output`: ruta final explícita del SVG
- `output_dir`: carpeta donde se escribirá el SVG
- `desktop`: envía la salida a `~/Desktop` cuando exista
- `use_user_config`: carga defaults desde la config de usuario
- `user_config`: permite pasar un objeto `KoalaUserConfig` ya cargado

Inputs aceptados por `koala.compile_text(text, **config)`:

- `text`: contenido DSL de Koala en crudo
- todas las claves de config aceptadas por `koala.compile(...)`
- `base_dir`: directorio base para resolver rutas relativas de salida
- `output_name`: nombre base del archivo de salida cuando `output` no es explícito
- esta función se mantiene por compatibilidad y sigue escribiendo SVG a disco

Inputs aceptados por `koala.inspect_text(text, **config)` y `koala.validate_text(text, **config)`:

- `text`: contenido DSL de Koala en crudo
- `type`, `layout`, `theme`, `typography`, `size`, `text_align`, `show_node_numbers`
- `use_user_config` y `user_config`
- `strict`: solo para `validate_text(...)`; lanza `koala.ValidationError` si existen warnings del parser

Inputs aceptados por `koala.render_text(text, **config)`:

- `text`: contenido DSL de Koala en crudo
- `type`, `layout`, `theme`, `typography`, `size`, `text_align`, `show_node_numbers`, `background`
- `use_user_config` y `user_config`
- no escribe archivos; el SVG serializado queda en `result.svg`

Inputs aceptados por `koala.export_text(text, format=..., **config)` y `koala.export_file(path, format=..., **config)`:

- `format`: `svg`, `png` o `pdf`
- `quality`: `medium` o `high` para PNG; PDF usa `high`
- `title`: título explícito para PDF; si se omite, Koala usa el primer nodo `main::` o la primera raíz
- `output`: ruta opcional para escribir el archivo además de retornar bytes
- `type`, `layout`, `theme`, `typography`, `size`, `text_align`, `show_node_numbers`, `background`
- retornan `ExportResult.content`, `ExportResult.media_type`, `ExportResult.extension` y `ExportResult.output_path` cuando se escribe archivo
- PNG se exporta directo desde el SVG canónico según calidad; PDF agrega marco profesional, márgenes, título y colores acordes al theme

Inputs aceptados por `koala.save_text(text, output, **config)`:

- `text`: contenido DSL de Koala en crudo
- `output`: ruta final del `.txt`; si no termina en `.txt`, Koala agrega la extensión
- `base_dir`: directorio base para resolver salidas relativas

Subcomandos disponibles:

- `compile`: renderiza un archivo fuente a SVG
- `export`: exporta un archivo fuente a SVG, PNG o PDF
- `inspect`: muestra metadata, warnings y settings resueltos
- `validate`: valida parseo y settings; con `--strict` falla si hay warnings
- `themes`: lista themes disponibles
- `types`: lista tipos de documento disponibles
- `layouts`: lista layouts disponibles
- `typographies`: lista presets tipográficos disponibles
- `config-path`: muestra la ruta esperada de la config de usuario

Config de usuario:

- ruta por default: `~/.config/koala/config.toml`
- ruta fallback: `~/.koala.toml`

Ejemplo:

```toml
[tool.koala]
default_layout = "tree"
default_theme = "academic"
default_typography = "default"
default_size = "a4_landscape"
default_text_align = "left"
default_show_node_numbers = false
default_output_mode = "next_to_input"
```

Claves soportadas:

- `default_layout`
- `default_theme`
- `default_typography`
- `default_size`
- `default_text_align`
- `default_show_node_numbers`
- `default_output_mode`: `next_to_input`, `desktop`, `cwd`
- `default_output_dir`

Comportamiento de salida:

- por default, la salida queda junto al archivo fuente con nombre `<input_stem>.<layout>.svg`
- `--output` escribe a una ruta SVG explícita
- `--output-dir` escribe en una carpeta concreta
- `--desktop` escribe en `~/Desktop` si existe; si no, cae de vuelta a la carpeta del input
- `koala.render_text(...)` no escribe archivos; retorna el SVG serializado en memoria
- `koala.export_text(...)` y `koala.export_file(...)` retornan bytes en memoria; si pasas `output`, también escriben el archivo
- `koala.compile_text(...)` escribe por default en `<base_dir o cwd>/concept_map.<layout>.svg`
- si pasas `output_name="demo"` a `koala.compile_text(...)`, el archivo por default será `<base_dir o cwd>/demo.<layout>.svg`
- `koala.save_text(...)` escribe texto DSL a un `.txt`
- `koala.inspect_text(...)` y `koala.validate_text(...)` no escriben archivos; solo resuelven y retornan contexto

Tipos de documento:

- `type="tree"` es el default y usa el DSL jerárquico actual
- `type="matrix"` usa sintaxis explícita de cuadro comparativo con `matrix::`, `columns::`, `row::` y `footer::`
- los layouts de `tree` son `tree`, `synoptic`, `synoptic_boxes` y `radial`
- el layout de `matrix` es `matrix`
- si el DSL no coincide con el `type` solicitado, Koala lanza `DocumentTypeMismatchError`
- la arquitectura interna está organizada por capas: `core/<type>`, `layout/<type>` y `render/<type>`
- `core/shared`, `layout/shared` y `render/shared` contienen config, themes, tipografía, tamaño de página, background y export compartidos para tipos actuales y futuros como `flowchart`

## Documentación

- [docs/syntax.md](https://github.com/gabdiasalejandro/Koala/blob/main/docs/syntax.md): sintaxis del DSL, metadata y reglas de precedencia
- [docs/tutorial.md](https://github.com/gabdiasalejandro/Koala/blob/main/docs/tutorial.md): guía práctica de autoría con ejemplos, themes y sugerencias de uso
- [docs/how-to-add-a-typography.md](https://github.com/gabdiasalejandro/Koala/blob/main/docs/how-to-add-a-typography.md): guía para agregar presets tipográficos y revisar SVG/PNG/PDF
- [docs/layouts.md](https://github.com/gabdiasalejandro/Koala/blob/main/docs/layouts.md): comportamiento de layouts y reglas geométricas
- [docs/architecture.md](https://github.com/gabdiasalejandro/Koala/blob/main/docs/architecture.md): estructura actual del paquete, flujo de API y pipeline de render
- [docs/examples/tree.txt](https://github.com/gabdiasalejandro/Koala/blob/main/docs/examples/tree.txt): ejemplo mínimo tipo tree
- [docs/examples/radial.txt](https://github.com/gabdiasalejandro/Koala/blob/main/docs/examples/radial.txt): ejemplo mínimo tipo radial
- [docs/prompts/](https://github.com/gabdiasalejandro/Koala/tree/main/docs/prompts): prompts listos para generar DSL por layout
