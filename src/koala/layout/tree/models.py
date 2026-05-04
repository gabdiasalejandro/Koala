"""Modelos de layout especificos del tipo de documento `tree`.

`TreeLayoutKind` es el conjunto cerrado de layouts soportados por `tree`. Cada
tipo de documento define el suyo en `koala.layout.<tipo>.models`. La capa
shared trabaja con `str` opaco y delega la validacion al registry del tipo.
"""

from typing import Literal


TreeLayoutKind = Literal["tree", "synoptic", "synoptic_boxes", "radial"]
