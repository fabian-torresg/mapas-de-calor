"""mapacalor: mapas de calor de Colombia por departamento, municipio, región o ciudad. Autor: Fabián Torres."""
from . import geodatos, paletas
from .datos import detectar_columnas, emparejar, leer_archivo, plantilla
from .render import Estilo, categorias, dibujar, exportar

__author__ = "Fabián Torres"
__all__ = ["Estilo", "categorias", "dibujar", "exportar", "emparejar", "plantilla", "detectar_columnas", "leer_archivo",
           "geodatos", "paletas"]
