# Koala

🇪🇸 Español | 🇺🇸 [English](README.md)

Koala es un DSL para generar diagramas a partir de texto estructurado.

La idea central del proyecto es simple: un mismo archivo fuente debe poder renderizarse en múltiples layouts y estilos sin reescribir el contenido.

## Capacidades actuales

- Parsear árboles conceptuales jerárquicos desde `.txt` y `.docx`
- Renderizar el mismo documento como `tree`, `synoptic`, `synoptic_boxes` o `radial`
- Aplicar presets de tema y tipografía
- Elegir tamaño de página desde el CLI
- Leer metadata opcional directamente desde el archivo fuente con `@...`
- Ajustar la escena final al SVG de salida

## Resumen de sintaxis

Los nodos usan numeración jerárquica:

- `1`, `2`, `3` son raíces
- `1.1`, `1.2` son hijos de `1`
- `1.1.1` es hijo de `1.1`
- `0` es una super-raíz opcional

Ejemplo:

```text
1 Plataforma DSL
Define el concepto principal.

organiza -> 1.1 Core
Contiene parser, modelos y validaciones.

renderiza -> 1.2 Render
Genera la salida SVG.
```

Tipo semántico opcional:

```text
hl:: 1.2 Tabla Usuarios
hl:: contiene -> 1.2.1 Clave foránea
note:: 1.3 Nota
focus:: 1.4 Idea principal
```

Kinds integrados disponibles actualmente:

- universales: `note`, `warn`, `soft`
- propios del theme: `main`, `hl`, `focus`

`main` está pensado principalmente para la raíz del diagrama. Cuando la raíz usa `main::`, los themes integrados le dan un tratamiento más prominente y un borde más grueso.

Themes integrados disponibles actualmente:

- `default`
- `terracotta`
- `jungle`
- `frutal`
- `academic`

Metadata opcional:

```text
@layout tree
@theme terracotta
@typography default
@text-align justify
@size square
@show-node-numbers false
@output-dir output/metadata_demo
```

La metadata es opcional y sigue esta precedencia:

1. flag explícito del CLI
2. metadata dentro del archivo fuente
3. defaults internos

El alineado del texto de nodos ahora es `left` por default. Si quieres justificado, usa `@text-align justify`.

Para la sintaxis completa, ver [docs/syntax.md](/home/yaldapika/dev/koala/docs/syntax.md).

## Uso

Punto de entrada principal:

- [main.py](/home/yaldapika/dev/koala/main.py)

Ejemplos:

```bash
./.venv/bin/python main.py --layout tree
./.venv/bin/python main.py --layout synoptic
./.venv/bin/python main.py --layout synoptic_boxes
./.venv/bin/python main.py --layout radial
./.venv/bin/python main.py --input mocks/metadata_demo.txt
./.venv/bin/python main.py --layout tree --theme terracotta --size square
```

Opciones actuales del CLI:

- `--layout`: `tree`, `synoptic`, `synoptic_boxes`, `radial`
- `--input`: archivo `.txt` o `.docx`
- `--output-dir`: carpeta de salida
- `--theme`: preset de tema
- `--typography`: preset tipográfico
- `--size`: preset de página, actualmente `a4`, `a4_landscape`, `square`

Presets actuales de página:

- `a4`: `210 x 297 mm`
- `a4_landscape`: `297 x 210 mm`
- `square`: `210 x 210 mm`

Salida:

- `output/concept_map_<layout>.svg`

## Layouts

Layouts soportados actualmente:

- `tree`: jerarquía top-down con ancho adaptativo en padres y ajuste consciente de la página
- `synoptic`: cuadro sinóptico con corchetes y sin labels de relación
- `synoptic_boxes`: cuadro sinóptico con recuadros y labels de relación
- `radial`: mapa mental con disposición desde el centro

Para detalles de implementación, ver [docs/layouts.md](/home/yaldapika/dev/koala/docs/layouts.md).

## Arquitectura

El proyecto está dividido en tres capas:

- `core/`: parsing, modelos del DSL y carga de entrada
- `layout/`: medición compartida y un motor geométrico por layout
- `render/`: resolución de themes, contexto de render, ajuste a página y backend SVG

La separación de responsabilidades es:

- `core` entiende el lenguaje
- `layout` calcula geometría y conectores
- `render` resuelve presentación y dibuja la escena

Para la arquitectura completa, ver [docs/architecture.md](/home/yaldapika/dev/koala/docs/architecture.md).

## Sugerencias para mejores resultados visuales

Estas recomendaciones son heurísticas prácticas para obtener diagramas más limpios con los motores actuales.

### Generales

- Mantén los títulos cortos y conceptuales; mueve la explicación al cuerpo
- Usa relaciones solo cuando aporten algo; demasiadas labels generan ruido
- Prefiere grupos de hermanos equilibrados cuando sea posible
- Divide párrafos muy largos en prosa más compacta; la medición actual trabaja por líneas y la escritura más apretada suele envolver mejor
- Usa metadata cuando un archivo esté pensado para renderizarse de una forma específica

### `tree`

- Funciona mejor para jerarquías clásicas y mapas explicativos
- Va muy bien cuando los niveles superiores son conceptuales y los inferiores concentran detalle
- Encaja especialmente bien con `a4_landscape` y `square`
- Si un padre tiene muchos hijos, conviene mantener los títulos hijos compactos para que el árbol conserve escala legible
- Si el mapa es poco profundo y muy ancho, `square` suele ayudar a densificar la composición

### `synoptic`

- Funciona mejor para clasificaciones agrupadas y estructuras tipo esquema
- Conviene usar títulos cortos y cuerpo muy ligero
- Da mejores resultados cuando cada nivel refina categorías
- `a4_landscape` sigue siendo el preset más seguro porque la geometría interna todavía está orientada a columnas
- No dependas de labels de relación; este layout las suprime a propósito

### `synoptic_boxes`

- Funciona bien para diagramas didácticos de izquierda a derecha o descomposición de procesos
- Conviene que cada grupo de hermanos sea conceptualmente paralelo
- Usa cuerpo corto o medio, no párrafos enormes
- `a4_landscape` sigue siendo el preset más seguro
- `square` ya está soportado, pero todavía no existe una heurística específica de compactación para ese aspect ratio
- Se sugiere una profundidad máxima menor a 4 

### `radial`

- Funciona mejor para un tema central con ramas relativamente equilibradas
- Intenta que las ramas de primer nivel tengan importancia y tamaño similares
- Evita una rama gigante y muchas ramas mínimas si quieres una composición circular limpia
- `square` y `a4_landscape` suelen dar el mejor balance
- Si la raíz es breve y los hijos tienen contenido rico, `radial` suele aprovechar muy bien la hoja

### Consejos por tamaño de página

#### `a4`

- Mejor para árboles altos o jerarquías más profundas verticalmente
- Útil cuando quieres más ritmo de lectura en pila
- Menos ideal para estructuras sinópticas muy anchas, salvo que el contenido sea compacto

#### `a4_landscape`

- Default actual
- Mejor preset generalista
- La opción más segura para `synoptic` y `synoptic_boxes`
- También funciona muy bien para documentos `tree` de anchura media

#### `square`

- Ideal cuando buscas una composición más densa y centrada
- Muy buena opción para `radial`
- Útil en `tree` cuando el contenido tendería a abrirse demasiado en horizontal
- Exige escritura más compacta para `synoptic` y `synoptic_boxes` mientras esos motores no tengan optimización específica por aspect ratio

## Ejemplos recomendados

- [mocks/concepts.txt](/home/yaldapika/dev/koala/mocks/concepts.txt)
- [mocks/metadata_demo.txt](/home/yaldapika/dev/koala/mocks/metadata_demo.txt)

## Estado actual

El proyecto ya es útil para:

- prototipado rápido de mapas conceptuales
- probar múltiples layouts desde el mismo contenido
- testear semántica visual con `kind::`
- distribuir mocks auto-descriptivos mediante metadata

Todavía hay espacio de mejora en:

- adaptación específica de `synoptic` y `synoptic_boxes` a páginas portrait y square
- aceptar markdown adentro para destacar conceptos en negritas
- evaluar crosed relationships entre nodos en la misma jerarquía o diferente (solo la flecha)
- aceptar saltos de línea en el texto del nodo
- mejorar la distribución de radial
- validaciones más fuertes
- pruebas visuales automatizadas
- facilitar su uso como DSL haciéndolo ejecutable de otras maneras sin depender de main.py
- añadir más temas, tipografías y tipos de conectores o hacerlo fácilmente configurable
- mejorar los corchetes de synoptic
