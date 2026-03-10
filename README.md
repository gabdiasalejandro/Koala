## Este proyecto es un DSL que tiene por objetivo generar diagramas a partir de texto 

Utiliza una sintaxis simple y para poder ser utilizado tanto por humanos como por LLM's 

Para marcar los nódos del diagrama se utilizan prefijos numéricos, los enteros se toman como raíz (ej. 1, 2)

Para determinar la profundidad de los nodos se usan puntos decimales, por ejemplo,
para escribir un nodo que funcione como hijo de la raíz uno usamos 1.1, 1.2 si se busca un segundo hijo y así sucesivamente.

Si es necesario que haya relaciones entre estas (palabras conectoras) se hace uso de el texto conector seguido de "->"
antes del número identificador del nodo.

El texto se agrega debajo del título y el número y se renderiza como cuerpo del nodo.

También existe un prefijo semántico opcional para el tipo de nodo: `kind::`.
Esto permite aplicar estilos diferentes por layout/render. Ejemplo:

```text
fr:: 1.2 Tabla Usuarios
```

Con ese marcador, el nodo se parsea con `kind=fr` y puede colorearse con otra paleta.

Ejemplo de sintaxis:
-------------------------------------------------------------------------------------------------------------------
    1 Célula
    La célula es la unidad básica de los seres vivos. Todos los organismos están formados por una o más células.

    1.1 Tipos de células
    Existen dos tipos principales de células según la presencia de núcleo definido y la organización interna.

    1.1.1 Procariotas
    No tienen núcleo definido y su material genético se encuentra disperso en el citoplasma. Son más simples y generalmente más pequeñas.

    1.1.2 Eucariotas
    Poseen núcleo y diversos organelos membranosos. Forman organismos unicelulares y multicelulares más complejos.

    tienen → 1.1.2.1 Núcleo
    El núcleo protege el material genético y coordina funciones importantes de la célula.

    contiene → 1.1.2.1.1 ADN
    El ADN almacena la información hereditaria necesaria para el funcionamiento y la reproducción celular.

    1.2 Estructuras básicas
    Además del núcleo, muchas células presentan membrana plasmática, citoplasma y distintos organelos especializados.

    1.2.1 Membrana plasmática
    Delimita la célula y regula el intercambio de sustancias con el entorno.

    1.2.2 Citoplasma
    Es el medio interno donde ocurren múltiples reacciones químicas y donde se encuentran suspendidos los organelos.
---------------------------------------------------------------------------------------------------------------------


## Arquitectura
Ahora está dividido en 3 capas principales:

- `core/`: parser, modelos del DSL y carga de archivos (`io.py`).
- `layout/`: motor de cálculo geométrico (`conceptual_topdown.py`) y modelos/configuración de layout/tema (`models.py`).
- `layout/`: motor de cálculo geométrico (`conceptual_topdown.py`), modelos de layout/tema (`models.py`) y registro de motores (`registry.py`).
- `render/`: salidas concretas (`svg_mvp.py`, `pdf_mvp.py`) con una configuración centralizada (`defaults.py`).

La idea de escalabilidad es:

- Agregar nuevos layouts (`synoptic`, `radial`) como motores en `layout/` sin duplicar lógica de render.
- Agregar sintaxis nueva en `core/parser.py` sin tocar geometría.
- Agregar reglas de color/estilo por `kind` en `render/defaults.py` (ej: `fr` para diagramas de DB).
