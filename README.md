## Koala

DSL para generar diagramas a partir de texto estructurado.

El objetivo es tener una sintaxis suficientemente simple para que pueda ser escrita por personas o generada por LLMs, y a la vez una arquitectura que permita crecer hacia más layouts, más reglas de estilo y más dominios semánticos.

## Sintaxis base

Los nodos se definen con numeración jerárquica:

- `1`, `2`, `3` representan raíces.
- `1.1`, `1.2` representan hijos de `1`.
- `1.1.1` representa un hijo de `1.1`.

También se puede declarar una relación explícita antes del nodo usando `->` o `→`.

Ejemplo:

```text
1 Plataforma DSL
Define el concepto principal.

organiza -> 1.1 Core
Contiene parser, modelos y validaciones.

renderiza -> 1.2 Render
Genera SVG y PDF.
```

El texto debajo de cada encabezado se interpreta como cuerpo del nodo.

## Sintaxis `kind::`

Existe un prefijo semántico opcional para marcar el tipo del nodo:

```text
fr:: 1.2 Tabla Usuarios
```

Eso produce un nodo con `kind=fr`, lo que permite aplicar colores o estilos distintos desde la capa de render.

También puede combinarse con relaciones:

```text
contiene -> fr:: 1.2.1 Clave foránea
```

## Ejemplo recomendado

El ejemplo principal del proyecto está en [mocks/concepts.txt](/home/yaldapika/dev/koala/mocks/concepts.txt:1). Ese archivo está pensado para funcionar razonablemente bien en `tree`, `synoptic` y `radial`.

## Uso

La entrada principal es [main.py](/home/yaldapika/dev/koala/main.py:1) y ahora expone una CLI simple.

Ejemplos:

```bash
./.venv/bin/python main.py --layout tree
./.venv/bin/python main.py --layout synoptic
./.venv/bin/python main.py --layout radial
```

También soporta:

```bash
./.venv/bin/python main.py --layout radial --input mocks/concepts.txt --output-dir output
```

Parámetros disponibles:

- `--layout`: `tree`, `synoptic`, `radial`
- `--input`: archivo `.txt` o `.docx`
- `--output-dir`: carpeta donde se generan los resultados

La compilación genera ambos formatos:

- `output/concept_map_<layout>.svg`
- `output/concept_map_<layout>.pdf`

## Layouts soportados

Actualmente existen tres layouts:

- `tree`: disposición vertical top-down, útil para jerarquías clásicas.
- `synoptic`: disposición en columnas, útil para cuadros sinópticos.
- `radial`: disposición tipo mapa mental, con la raíz al centro y las ramas distribuidas alrededor.

En radial:

- La raíz se coloca en el centro.
- Los hijos de la raíz se reparten angularmente como una estrella.
- Las ramas más profundas determinan el radio total del diagrama.
- El motor intenta evitar solapes calculando separación radial y tangencial.

## Arquitectura

El proyecto está dividido en tres capas:

- `core/`: parsing, modelos del DSL y carga de archivos.
- `layout/`: cálculo geométrico de nodos y aristas.
- `render/`: traducción de la escena geométrica a SVG y PDF.

La separación de responsabilidades es:

- `core` entiende el lenguaje.
- `layout` decide posiciones según el tipo de layout.
- `render` dibuja la escena y aplica tema, tipografía y salida final.

## Carpeta `layout`

La carpeta `layout/` está organizada para crecer sin duplicación:

- [models.py](/home/yaldapika/dev/koala/layout/models.py:1): estructuras tipadas como `LayoutBox`, `LayoutEdge` y `LayoutScene`.
- [shared.py](/home/yaldapika/dev/koala/layout/shared.py:1): utilidades compartidas de medición, texto y helpers geométricos.
- [tree_layout.py](/home/yaldapika/dev/koala/layout/tree_layout.py:1): layout top-down.
- [synoptic_layout.py](/home/yaldapika/dev/koala/layout/synoptic_layout.py:1): layout de cuadro sinóptico.
- [radial_layout.py](/home/yaldapika/dev/koala/layout/radial_layout.py:1): layout tipo mapa mental.
- [registry.py](/home/yaldapika/dev/koala/layout/registry.py:1): registro de motores por tipo de layout.

Cada motor retorna una `LayoutScene` con:

- `boxes`: nodos ya medidos y posicionados.
- `edges`: aristas con geometría explícita.

Eso permite que los renderizadores no dependan de la matemática específica de cada layout.

## Capa de render

Los renderizadores están en:

- [svg_render.py](/home/yaldapika/dev/koala/render/svg_render.py:1)
- [pdf_render.py](/home/yaldapika/dev/koala/render/pdf_render.py:1)

Ambos consumen la misma `LayoutScene`, por lo que agregar un layout nuevo normalmente requiere tocar solo `layout/` y registrarlo en [registry.py](/home/yaldapika/dev/koala/layout/registry.py:1).

La configuración visual está centralizada en [defaults.py](/home/yaldapika/dev/koala/render/defaults.py:1), incluyendo:

- layout por defecto
- tamaños base
- paletas por `kind`
- ajustes específicos para radial

## Estado actual

Ya es una herramienta útil para:

- prototipar mapas conceptuales desde texto
- generar variantes visuales del mismo contenido
- probar estilos semánticos por tipo de nodo
- experimentar con distintos layouts sin rehacer el parser

Todavía hay espacio para refactorizar y pulir, sobre todo en:

- compactación más fina del radial
- reglas más ricas de sintaxis
- estilos por dominio
- validaciones más fuertes del DSL
- pruebas visuales automatizadas
