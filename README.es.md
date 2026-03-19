# Koala

🇪🇸 Español | 🇺🇸 [English](https://github.com/gabdiasalejandro/Koala/blob/main/README.md)

Koala es un DSL para generar diagramas a partir de texto estructurado.

La idea central del proyecto es simple: un mismo archivo fuente debe poder renderizarse en múltiples layouts y estilos sin reescribir el contenido.

## Uso rápido

Koala se puede usar de dos formas:

- como herramienta CLI mediante el comando instalado `koala`
- como librería de Python mediante `import koala`
- punto de implementación: [src/koala/cli.py](https://github.com/gabdiasalejandro/Koala/blob/main/src/koala/cli.py)
- repositorio: [github.com/gabdiasalejandro/Koala](https://github.com/gabdiasalejandro/Koala)

Instalación desde PyPI:

```bash
pip install koala-diagrams==1.2.1
```

Si prefieres una instalación aislada para usar el CLI:

```bash
pipx install koala-diagrams==1.2.1
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
koala layouts
koala typographies
koala compile docs/examples/tree.txt --layout tree
koala compile docs/examples/radial.txt --layout radial --theme jungle --size square
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
    layout="radial",
    theme="academic",
    size="square",
    text_align="left",
)

text_result = koala.compile_text(
    """
    1 Tema central
    Explicación principal.

    1.1 Primera rama
    Detalle de apoyo.
    """,
    layout="tree",
    theme="academic",
    base_dir="docs/examples",
    output_name="inline_demo",
)

print(file_result.output_svg)
print(text_result.output_svg)

context = koala.inspect_text("1 Root\nBody.\n", layout="tree", theme="academic")
validated = koala.validate_text("1 Root\nBody.\n", layout="tree", theme="academic", strict=True)

print(len(context.parsed.node_index))
print(len(validated.parsed.warnings))
```

Inputs aceptados por `koala.compile(path, **config)`:

- `path`: archivo fuente `.txt` o `.docx` a compilar
- `layout`: uno de `tree`, `synoptic`, `synoptic_boxes`, `radial`
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
- `base_dir`: directorio base para resolver rutas relativas de salida y metadata como `@output-dir`
- `output_name`: nombre base del archivo de salida cuando `output` no es explícito

Inputs aceptados por `koala.inspect_text(text, **config)` y `koala.validate_text(text, **config)`:

- `text`: contenido DSL de Koala en crudo
- `layout`, `theme`, `typography`, `size`, `text_align`, `show_node_numbers`
- `use_user_config` y `user_config`
- `strict`: solo para `validate_text(...)`; lanza `koala.ValidationError` si existen warnings del parser

Subcomandos disponibles:

- `compile`: renderiza un archivo fuente a SVG
- `inspect`: muestra metadata, warnings y settings resueltos
- `validate`: valida parseo y settings; con `--strict` falla si hay warnings
- `themes`: lista themes disponibles
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
default_show_node_numbers = true
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
- `koala.compile_text(...)` escribe por default en `<base_dir o cwd>/concept_map.<layout>.svg`
- si pasas `output_name="demo"` a `koala.compile_text(...)`, el archivo por default será `<base_dir o cwd>/demo.<layout>.svg`
- `koala.inspect_text(...)` y `koala.validate_text(...)` no escriben archivos; solo resuelven y retornan contexto

## Documentación

- [docs/syntax.md](https://github.com/gabdiasalejandro/Koala/blob/main/docs/syntax.md): sintaxis del DSL, metadata y reglas de precedencia
- [docs/tutorial.md](https://github.com/gabdiasalejandro/Koala/blob/main/docs/tutorial.md): guía práctica de autoría con ejemplos, themes y sugerencias de uso
- [docs/layouts.md](https://github.com/gabdiasalejandro/Koala/blob/main/docs/layouts.md): comportamiento de layouts y reglas geométricas
- [docs/architecture.md](https://github.com/gabdiasalejandro/Koala/blob/main/docs/architecture.md): estructura actual del paquete, flujo de API y pipeline de render
- [docs/examples/tree.txt](https://github.com/gabdiasalejandro/Koala/blob/main/docs/examples/tree.txt): ejemplo mínimo tipo tree
- [docs/examples/radial.txt](https://github.com/gabdiasalejandro/Koala/blob/main/docs/examples/radial.txt): ejemplo mínimo tipo radial
