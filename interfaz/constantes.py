"""Constantes de la interfaz: formatos, tipografías, opciones y textos fijos."""
from __future__ import annotations


FORMATOS = ["png", "jpg", "tiff", "svg", "pdf"]


FORMATOS_IMAGEN = ["png", "jpg", "tiff"]  # dependen de la resolución


FORMATOS_DATOS = {"csv": "CSV", "xlsx": "Excel", "json": "JSON", "parquet": "Parquet", "geojson": "GeoJSON"}


DPI_VISTA = 200  # resolución fija de la vista previa


COLA_MAX = 20


ICONO_ESTILO = {"Negrita": "**N**", "Cursiva": ":material/format_italic:", "Subrayado": ":material/format_underlined:"}


AYUDA_ESPACIO = ("Espacio extra, en puntos, antes del elemento: sobre el título, entre el título y el subtítulo, entre el "
                 "mapa y la leyenda o entre el mapa y la nota. Un valor negativo lo acerca al elemento anterior.")


TIPOGRAFIAS = {"Arial": "arial", "Calibri": "calibri", "Times New Roman": "times", "Georgia": "georgia"}


FUENTE_TEXTOS = (("tit", "tit"), ("tit", "sub"), ("tit", "nota"), ("ley", "ley"), ("ley", "ext"), ("ley", "extd"),
                 ("etq", "etq"), ("etq", "lista"), ("res", "res"))   # (sección, texto) de cada tipografía


# anchos de las columnas de la tabla subida
ANCHO_COLUMNA = {"Ciudad": 100, "Departamento": 150, "Municipio": 170, "Región": 120, "Departamentos": 220,
                 "Localidad o comuna": 200, "Valor": 90, "Segmento": 120, "Estado": 250, "Corregir": 90}


# el departamento hace de segmento
CALCULO_GEO = {"departamento": {}, "municipio": {"Dentro de cada departamento": "departamento"},
               "region": {}, "ciudad": {}}


CALCULOS = {"Por lugar": "valor", "Dentro de cada segmento": "zona_valor", "Según el total de cada segmento": "zona_total"}


TITULO_GRUPO = {"": "SEGMENTO", "lugar": "LUGAR", "departamento": "DEPARTAMENTO", "region": "REGIÓN"}


RAYAS = ["#8A8F98"]  # "Personalizada" no tiene colores fijos


UN_TONO = "Un solo tono, de claro a oscuro."


DIVERGENTE = "Dos extremos con centro claro. Para valores que se desvían en ambos sentidos."


PALETA_INFO = {  # texto de ayuda de cada paleta
    "Personalizada": "Colores propios, de 1 a 10.", "Mapa de calor": "Amarillo, naranja y rojo.",
    "Azul marino": UN_TONO, "Violeta": UN_TONO, "Turquesa": UN_TONO, "Ámbar": UN_TONO, "Esmeralda": UN_TONO,
    "Océano": UN_TONO, "Coral": UN_TONO, "Fucsia": UN_TONO, "Grafito": UN_TONO,
    "Viridis": "Escala uniforme, legible con daltonismo.", "Magma": "Escala uniforme, de negro a amarillo claro.",
    "Cividis": "Escala uniforme, diseñada para daltonismo.",
    "Rojo → Azul (divergente)": DIVERGENTE, "Café → Verde (divergente)": DIVERGENTE,
    "Vivos": "Colores intensos y variados.", "Suaves": "Tonos pastel.", "Alto contraste": "Colores oscuros, bien "
                                                                                          "diferenciados entre sí.",
    "Tierra": "Tonos naturales.", "Apta para daltónicos": "Distinguibles con daltonismo.",
}


RES_OPC = {"total": "Total", "promedio": "Promedio", "max_min": "Mayor y menor", "mayores": "Los mayores",
           "menores": "Los menores", "porcentaje": "Porcentaje del total"}


TIPOS_LINEA = {"continua": "─────", "guiones": "╌╌╌╌", "espaciada": "─ ─ ─ ─", "circulos": "● ● ● ● ●", "puntos": "■ ■ ■ ■ ■",
               "guion_punto": "─ • ─ • ─"}  # muestra de cada tipo de línea


AYUDA_SEG = ("Opcional. Agrupa lugares bajo un mismo nombre (zonas, vendedores, canales, sedes o tipos de cliente). "
              "Cada segmento puede colorearse o delimitarse con una línea (secciones Colores y Líneas y límites). Si "
              "solo hay segmentos, Valor puede quedar vacío.")
