"""Dibujo del mapa de calor con matplotlib: `Estilo` reúne las opciones y `dibujar` devuelve la figura.
"""
from __future__ import annotations

import hashlib
import io
import json
import logging
import re
import textwrap
import threading
from dataclasses import replace, dataclass, field
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.patheffects as pe  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import to_hex, to_rgb  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.collections import Collection
from matplotlib.patches import Circle, PathPatch, Rectangle
from matplotlib.text import Text  # noqa: E402
from matplotlib.path import Path as MPath  # noqa: E402
import shapely  # noqa: E402
from shapely import STRtree, affinity  # noqa: E402
from shapely.geometry import box  # noqa: E402
from shapely.ops import polylabel, unary_union  # noqa: E402

from . import geodatos as gd  # noqa: E402
from . import paletas as pal  # noqa: E402

logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
plt.rcParams["font.family"] = ["Arial", "Liberation Sans", "DejaVu Sans"]


@dataclass
class Estilo:
    # Qué se muestra
    nivel: str = "departamento"            # "departamento" | "municipio" | "region"
    deptos: list[str] = field(default_factory=list)   # vacío = todo el país
    municipios: list[str] = field(default_factory=list)  # "Depto|Municipio"; vacío = todos los de deptos
    regiones: list[str] = field(default_factory=list)    # nivel "region"; vacío = todas
    ciudad: str = "Bogotá"                 # nivel "ciudad": localidades o comunas
    ciudad_rural: bool = True              # incluir la zona rural (Sumapaz, corregimientos)
    divisiones: list[str] = field(default_factory=list)  # nivel "ciudad": las que se muestran; vacío = todas
    mostrar_depto_completo: bool = True  # ver todo el contexto o solo los elegidos
    mostrar_isla: bool = True  # San Andrés y Providencia en una esquina (todo el país)
    # Ampliación: lupa sobre algunos lugares pequeños del mapa
    ampliar: list[str] = field(default_factory=list)     # nombres de las unidades a ampliar
    ampliar_tam: float = 0.38
    ampliar_nombres: bool = True
    ampliar_forma: str = "cuadrada"         # "cuadrada" | "redonda"
    encuadre: str = "seleccion"            # "seleccion" (acercar a lo elegido) | "pais"
    mostrar_resto_pais: bool = True
    mostrar_vecinos: bool = False
    # Color del calor
    # "valor" | "zona_total" (calor por total de la zona) | "zona" | "zona_valor"
    relleno: str = "valor"
    zona_agregar: str = "suma"             # cómo se resume cada zona en "zona_total": "suma" | "promedio"
    zona_rol: str = "fuerte"  # "zona_valor": tono "fuerte" (mayor) o "suave" (menor)
    zona_escala: str = "global"  # "zona_valor": escala "global" o "por_zona"
    colores_zona: dict[str, str] = field(default_factory=dict)   # zona -> color de relleno
    # grupos distintos de Segmento: "lugar", "departamento" o "region"; "" = Segmento
    grupos_geo: str = ""
    colores: list[str] = field(default_factory=lambda: pal.colores_base("Violeta"))
    n_tonos: int = 8
    invertir: bool = False
    escala: str = "raiz"                   # "lineal" | "raiz" | "log" | "cuantiles"
    color_sin_dato: str | None = None      # None = tono más claro que el primero de la rampa
    color_contexto: str = "#E5E3DE"
    color_fondo: str = "#FFFFFF"
    color_vecinos: str | None = None       # otros países; None = un tono más claro que el contexto
    color_oceano: str | None = None        # mar (el rectángulo del mapa); None = el mismo color del fondo
    # borde_*: entre unidades; borde_depto_*: límites de departamento
    borde_color: str = "#FFFFFF"
    borde_grosor: float = 1.0
    borde_depto_color: str = "#FFFFFF"  # municipios y regiones
    borde_depto_grosor: float = 2.0
    contorno_area_color: str | None = None
    contorno_area_grosor: float = 2.0
    colores_grupo: dict[str, str] = field(default_factory=dict)  # grupo -> color de contorno
    contorno_grupo_grosor: float = 2.25
    # tipos de línea: ver TRAZOS
    estilo_borde: str = "continua"
    estilo_borde_depto: str = "continua"
    estilo_contorno_area: str = "continua"
    estilo_contorno_grupo: str = "continua"
    # Minimapa
    minimapa: bool = True
    minimapa_pos: str = "auto"             # "auto" | "sup-izq" | "sup-der" | "inf-izq" | "inf-der"
    minimapa_tam: float = 0.22
    # Leyenda
    leyenda: bool = True
    leyenda_titulo: str = "ESCALA"
    leyenda_extremos: str = "texto"        # "texto" | "valores"
    texto_menor: str = "MENOR"
    texto_mayor: str = "MAYOR"
    leyenda_tam: float = 13.0  # puntos; título y extremos de la leyenda
    extremos_tam: float = 11.0  # extremo izquierdo; el derecho usa los campos *_der
    extremos_tam_der: float = 11.0
    # Etiquetas sobre el mapa
    etiquetas: str = "ninguna"             # "ninguna" | "ranking" | "valor" | "nombre" | "nombre_valor"
    top_n: int = 5
    ranking_modo: str = "ambos"            # "mapa" (números) | "lista" (al lado) | "ambos"
    ranking_pos: str = "derecha"           # dónde va la lista: "derecha" | "izquierda" | "arriba" | "abajo"
    etiqueta_tam: float = 8.0
    valor_junto: str = "debajo"            # con «nombre y valor»: "debajo" | "lado" | "parentesis"
    color_marcador: str | None = None      # None = el tono más oscuro de la rampa
    tipo_etiquetas: str = ""  # tipografía de etiquetas y lista del ranking
    color_etiquetas: str | None = None     # None = el color automático
    # lista del ranking (fuera del mapa): su propio texto
    tam_lista: float = 10.0
    estilo_lista: list[str] = field(default_factory=list)
    tipo_lista: str = ""
    color_lista: str | None = None
    # nombres de los lugares ampliados en la lupa: su propio texto
    tam_amp: float = 8.0
    estilo_amp: list[str] = field(default_factory=list)
    tipo_amp: str = ""
    color_amp: str | None = None
    # Números
    decimales: int = 0
    sufijo: str = ""
    # Texto y tamaño
    titulo: str = ""
    subtitulo: str = ""
    fuente_nota: str = ""
    # estilo de cada texto: lista con "negrita", "cursiva" y/o "subrayado"
    estilo_titulo: list[str] = field(default_factory=lambda: ["negrita"])
    estilo_subtitulo: list[str] = field(default_factory=list)
    estilo_nota: list[str] = field(default_factory=list)
    estilo_leyenda: list[str] = field(default_factory=lambda: ["negrita"])
    estilo_etiquetas: list[str] = field(default_factory=list)
    estilo_extremos: list[str] = field(default_factory=list)   # texto izquierdo de los extremos de la leyenda
    estilo_extremos_der: list[str] = field(default_factory=list)
    titulo_tam: float = 17.0  # tamaños en puntos
    subtitulo_tam: float = 11.5
    nota_tam: float = 8.0
    # color de cada texto; None = automático según el fondo
    color_titulo: str | None = None
    color_subtitulo: str | None = None
    color_nota: str | None = None
    color_leyenda: str | None = None       # título de la leyenda y nombres de los segmentos
    color_extremos: str | None = None
    color_extremos_der: str | None = None
    # espacio extra en puntos (puede ser negativo) antes de cada elemento
    esp_titulo: float = 0.0                # sobre el título
    esp_subtitulo: float = 0.0             # entre el título y el subtítulo
    esp_leyenda: float = 0.0               # entre el mapa y la leyenda
    esp_leyenda_extremos: float = 0.0  # entre la escala y el extremo izquierdo
    esp_leyenda_extremos_der: float = 0.0  # ídem, extremo derecho
    esp_nota: float = 0.0                  # sobre la nota
    # Idioma ("es" | "en") y tipografía ("arial" | "calibri" | "times" | "georgia")
    idioma: str = "es"
    fuente: str = "arial"
    # tipografía de cada texto; vacío = la general
    tipo_titulo: str = ""
    tipo_subtitulo: str = ""
    tipo_nota: str = ""
    tipo_leyenda: str = ""
    tipo_extremos: str = ""
    tipo_extremos_der: str = ""
    # Elementos cartográficos: barra de escala en km y flecha del norte
    escala_km: bool = False
    norte: bool = False
    # Resumen de los datos y si va en la imagen
    resumen: bool = False
    resumen_items: list[str] = field(default_factory=lambda: ["total", "promedio", "max_min", "mayores"])
    resumen_n: int = 5
    resumen_en_imagen: bool = True
    tam_resumen: float = 9.0  # tamaño del resumen (su título, 18 % más)
    estilo_resumen: list[str] = field(default_factory=list)
    tipo_resumen: str = ""
    color_resumen: str | None = None
    ancho_pulgadas: float = 7.0
    proporcion: str = "auto"               # "auto" | "cuadrado" | "vertical" | "horizontal"
    dpi: int = 200


def formato(v: float, decimales=0, sufijo="") -> str:
    """Número con punto de miles y coma decimal (estilo colombiano)."""
    t = f"{v:,.{decimales}f}".replace(",", "§").replace(".", ",").replace("§", ".")
    return t + sufijo


TEXTOS = {
    "es": {"top": "TOP", "escala_zona": "Cada escala va de menor (izquierda) a mayor (derecha)",
           "por_zona": ", comparando dentro de cada segmento", "total": "Total", "promedio": "Promedio",
           "lugares": "Lugares con dato", "max": "Mayor", "min": "Menor", "mayores": "Mayores", "menores": "Menores",
           "del_total": "del total", "resumen": "RESUMEN"},
    "en": {"top": "TOP", "escala_zona": "Each scale goes from lower (left) to higher (right)",
           "por_zona": ", compared within each segment", "total": "Total", "promedio": "Average",
           "lugares": "Places with data", "max": "Maximum", "min": "Minimum", "mayores": "Top", "menores": "Bottom",
           "del_total": "of total", "resumen": "SUMMARY"},
}
# Tipografías con sustitutas de métrica parecida para Linux y la nube
FUENTES = {"arial": ["Arial", "Liberation Sans", "DejaVu Sans"],
           "calibri": ["Calibri", "Carlito", "Liberation Sans", "DejaVu Sans"],
           "times": ["Times New Roman", "Liberation Serif", "DejaVu Serif"],
           "georgia": ["Georgia", "Gelasio", "Liberation Serif", "DejaVu Serif"]}
FUENTES["firma"] = ["Great Vibes", "Georgia", "Liberation Serif", "DejaVu Serif"]    # manuscrita, incluida en datos/fuentes (SIL OFL)
FUENTES["sans"], FUENTES["serif"] = FUENTES["arial"], FUENTES["times"]  # nombres anteriores
_FUENTE_FIRMA = Path(__file__).resolve().parent.parent / "datos" / "fuentes" / "GreatVibes-Regular.ttf"
if _FUENTE_FIRMA.exists():
    font_manager.fontManager.addfont(str(_FUENTE_FIRMA))


def colores_texto(color_fondo: str) -> dict:
    """Colores automáticos de los textos: oscuros sobre fondo claro y claros sobre oscuro."""
    if pal.es_oscuro(color_fondo):
        return {"titulo": "#F1F5F9", "sub": "#B6C2D0", "leyenda": "#DCE4EE", "suave": "#9FB0C3", "resumen": "#C8D3E0"}
    return {"titulo": "#26302E", "sub": "#6B7572", "leyenda": "#3A4A47", "suave": "#8A9490", "resumen": "#4A5553"}


def _txt(e) -> dict:
    """Colores de los textos: los elegidos por quien usa la app o, si no hay, los automáticos."""
    tx = colores_texto(e.color_fondo)
    tx = {**tx, "nota": tx["suave"], "extremos": tx["suave"], "extremos_der": tx["suave"]}
    propios = {"titulo": e.color_titulo, "sub": e.color_subtitulo, "nota": e.color_nota, "leyenda": e.color_leyenda,
               "extremos": e.color_extremos, "extremos_der": e.color_extremos_der}
    return {**tx, **{k: v for k, v in propios.items() if v}}


def _tx(e, clave):
    return TEXTOS.get(e.idioma, TEXTOS["es"])[clave]


def calcular_resumen(p: dict, e: Estilo) -> dict | None:
    """Total, promedio, mayor, menor y los N mayores y menores con su % del total (por segmento si aplica)."""
    u = p["u"]
    nombre_col = {"municipio": "municipio", "region": "region", "ciudad": "division"}.get(e.nivel, "departamento")
    if e.relleno == "zona_total" and p.get("zonas_tot") is not None and len(p["zonas_tot"]):
        serie = p["zonas_tot"].astype(float)
    else:
        con = u[u.valor.notna()]
        if con.empty:
            return None
        etiqueta = con[nombre_col].astype(str)
        if e.nivel == "municipio" and con.departamento.nunique() > 1:
            etiqueta = etiqueta + " (" + con.departamento + ")"
        serie = pd.Series(con.valor.values, index=etiqueta.values).astype(float)
    total = float(serie.sum())
    orden = serie.sort_values(ascending=False)
    pct = (lambda v: 100 * v / total) if total else (lambda v: float("nan"))
    n = max(1, int(e.resumen_n))
    return {"total": total, "promedio": float(serie.mean()), "n": int(len(serie)),
            "max": (orden.index[0], float(orden.iloc[0])), "min": (orden.index[-1], float(orden.iloc[-1])),
            "mayores": [(k, float(v), pct(v)) for k, v in orden.head(n).items()],
            "menores": [(k, float(v), pct(v)) for k, v in orden.tail(n).iloc[::-1].items()]}


def lineas_resumen(r: dict, e: Estilo) -> list[str]:
    """Texto del resumen, una línea por bloque, según lo que se haya elegido mostrar."""
    f = lambda v: formato(v, e.decimales, e.sufijo)  # noqa: E731
    lin = []
    cab = []
    if "total" in e.resumen_items:
        cab.append(f"{_tx(e, 'total')}: {f(r['total'])}")
    if "promedio" in e.resumen_items:
        cab.append(f"{_tx(e, 'promedio')}: {f(r['promedio'])}")
    if cab:
        cab.append(f"{_tx(e, 'lugares')}: {r['n']}")
        lin.append("   ·   ".join(cab))
    if "max_min" in e.resumen_items:
        lin.append(f"{_tx(e, 'max')}: {r['max'][0]} ({f(r['max'][1])})   ·   "
                   f"{_tx(e, 'min')}: {r['min'][0]} ({f(r['min'][1])})")
    con_pct = "porcentaje" in e.resumen_items
    for clave in ("mayores", "menores"):
        if clave in e.resumen_items:
            partes = [f"{i}. {k} {f(v)}" + (f" ({formato(pc, 1)} %)" if con_pct and pd.notna(pc) else "")
                      for i, (k, v, pc) in enumerate(r[clave], start=1)]
            lin.append(f"{_tx(e, clave)}: " + "   ".join(partes))
    return lin


def _fuente(estilo, tipo: str = "") -> dict:
    """Negrita, cursiva y tipografía para matplotlib; el subrayado se dibuja aparte."""
    estilo = estilo or []
    datos = {"fontweight": "bold" if "negrita" in estilo else "normal",
             "fontstyle": "italic" if "cursiva" in estilo else "normal"}
    if tipo in FUENTES:
        datos["fontfamily"] = FUENTES[tipo]
    return datos


def _subrayar(fig, textos):
    """Dibuja una línea bajo cada texto marcado como subrayado (matplotlib no lo trae de fábrica)."""
    if not textos:
        return
    fig.canvas.draw()  # fija la posición de los ejes antes de medir los textos
    r = fig.canvas.get_renderer()
    inv = fig.transFigure.inverted()
    for t in textos:
        if not t.get_text().strip():
            continue
        bb = t.get_window_extent(r)
        (x0, y0), (x1, _) = inv.transform([(bb.x0, bb.y0), (bb.x1, bb.y0)])
        alto = bb.height / fig.dpi / fig.get_figheight()
        lineas = t.get_text().count("\n") + 1
        y = y0 + alto / lineas * 0.12
        fig.add_artist(Line2D([x0, x1], [y, y], transform=fig.transFigure, color=t.get_color(),
                              linewidth=max(t.get_fontsize() / 15, 0.6), zorder=t.get_zorder() + 0.1,
                              solid_capstyle="butt"))


def _ruta(geom) -> MPath:
    partes = list(geom.geoms) if geom.geom_type == "MultiPolygon" else [geom]
    verts, codes = [], []
    for p in partes:
        for anillo in [p.exterior, *p.interiors]:
            xy = np.asarray(anillo.coords)
            verts.extend(xy)
            codes.extend([MPath.MOVETO] + [MPath.LINETO] * (len(xy) - 2) + [MPath.CLOSEPOLY])
    return MPath(verts, codes)


# tipos de línea: patrón de trazo y punta (múltiplos del grosor)
TRAZOS = {"continua": ("-", "butt"), "guiones": ((0, (4, 2)), "butt"), "espaciada": ((0, (4, 5)), "butt"),
          "circulos": ((0, (0.01, 2.6)), "round"), "puntos": ((0, (1, 1.6)), "butt"), "guion_punto": ((0, (6, 2, 1, 2)), "butt")}


def _trazo(nombre: str) -> dict:
    """Argumentos de matplotlib para dibujar una línea con el tipo elegido."""
    estilo, punta = TRAZOS.get(nombre, TRAZOS["continua"])
    return {"linestyle": estilo, "capstyle": punta}


def _contorno_interior(ax, geom, color, grosor, tipo="continua"):
    """Contorno hacia adentro del límite: se traza al doble de ancho y se recorta con la propia figura."""
    if geom is None or geom.is_empty:
        return
    recorte = PathPatch(_ruta(geom), transform=ax.transData, facecolor="none", edgecolor="none")
    ax.add_patch(recorte)
    capas = (("white", 2 * (grosor + 0.75)), (color, 2 * grosor)) if tipo == "continua" else ((color, 2 * grosor),)
    for c, lw in capas:  # sin franja blanca en los punteados: taparía los huecos
        gpd.GeoSeries([geom.boundary], crs=gd.CRS).plot(ax=ax, color=c, linewidth=lw, joinstyle="round", zorder=4,
                                                        **(_trazo("continua") if c == "white" else _trazo(tipo)))
        ax.collections[-1].set_clip_path(recorte)


_UNIONES: dict = {}
_CERROJO = threading.RLock()


def _huella(serie) -> str:
    return hashlib.md5(b"".join(shapely.to_wkb(np.asarray(serie))), usedforsecurity=False).hexdigest()


def _unir(geometrias, margen: float = 0.0):
    """Unión de geometrías (con margen), en memoria: unir el país entero tarda segundos."""
    serie = geometrias.geometry if hasattr(geometrias, "geometry") else geometrias
    huella = _huella(serie)
    with _CERROJO:
        for clave in ((huella, 0.0), (huella, round(margen, 3))):
            if clave not in _UNIONES:
                if len(_UNIONES) > 60:
                    _UNIONES.pop(next(iter(_UNIONES)))
                union = serie.union_all() if clave[1] == 0.0 else _UNIONES[(huella, 0.0)].buffer(clave[1])
                shapely.prepare(union)
                _UNIONES[clave] = union
    return _UNIONES[(huella, round(margen, 3))] if margen else _UNIONES[(huella, 0.0)]


def precalentar():
    """Deja lista la vista inicial (departamentos): la unión del país y un dibujo de prueba."""
    deptos = gd.departamentos()
    continente = deptos[deptos.departamento != gd.ISLA_INSULAR]
    union = _unir(continente)
    huella = _huella(deptos.geometry)
    with _CERROJO:
        if (huella, 0.0) not in _UNIONES:  # el país es el continente más la isla: no se vuelve a unir
            todo = union.union(deptos[deptos.departamento == gd.ISLA_INSULAR].geometry.union_all())
            shapely.prepare(todo)
            _UNIONES[(huella, 0.0)] = todo
    plt.close(dibujar(None, Estilo(nivel="departamento", dpi=40))[0])


def precalentar_resto():
    """Prepara en segundo plano lo que piden las vistas por municipio y región."""
    def tarea():
        try:
            gd.regiones()
            municipios = gd.municipios()
            _unir(municipios[municipios.departamento.isin(gd.lista_departamentos(incluir_insular=False))])
        except Exception:
            logging.getLogger(__name__).exception("No se pudo precalentar la vista por municipio")
    threading.Thread(target=tarea, daemon=True, name="precalentar").start()


def _centro(geom):
    g = max(geom.geoms, key=lambda p: p.area) if geom.geom_type == "MultiPolygon" else geom
    try:
        return polylabel(g, tolerance=200)
    except Exception:
        return g.representative_point()


def _indices_tono(v: pd.Series, n: int, escala: str) -> pd.Series:
    """Posición de cada valor en la rampa (0 = más claro, n-1 = más oscuro)."""
    if v.empty:
        return v.astype(int)
    vmin, vmax = v.min(), v.max()
    if vmax == vmin:
        return pd.Series(n - 1, index=v.index)
    if escala == "cuantiles":
        rk = v.rank(method="average", pct=True)
        return ((rk - rk.min()) / (rk.max() - rk.min()) * n).clip(upper=n - 1e-9).astype(int)
    if escala == "log":
        desp = 1 - vmin if vmin <= 0 else 0
        x = np.log10(v + desp)
        t = (x - x.min()) / (x.max() - x.min())
    elif escala == "raiz":   # realza las diferencias entre valores bajos
        t = np.sqrt((v - vmin) / (vmax - vmin))
    else:
        t = (v - vmin) / (vmax - vmin)
    return (t * n).clip(upper=n - 1e-9).astype(int)


def _grupo_geografico(u: pd.DataFrame, e: Estilo) -> pd.Series:
    """Grupo de cada unidad cuando se colorea por lugar, departamento o región (no por Segmento)."""
    nombre_col = {"municipio": "municipio", "region": "region", "ciudad": "division"}.get(e.nivel, "departamento")
    if e.grupos_geo == "departamento" and "departamento" in u:
        return u["departamento"].astype(str)
    if e.grupos_geo == "region" and "departamento" in u:
        return u["departamento"].map(gd.REGION_DE).fillna("Insular").astype(str)
    if e.nivel == "municipio":  # hay municipios con el mismo nombre en varios departamentos
        return (u["municipio"] + " (" + u["departamento"] + ")").astype(str)
    return u[nombre_col].astype(str)


def categorias(tabla: pd.DataFrame | None, e: Estilo, paleta: list[str], semilla: int = 0) -> dict[str, str]:
    """Color automático de cada grupo; dos grupos vecinos nunca repiten color y `semilla` cambia el reparto."""
    e = replace(e, relleno="zona", colores_zona={}, colores_grupo={}, leyenda=False)
    u = preparar(tabla, e)["u"]
    g = u["grupo"].astype("string").str.strip()
    ok = g.notna() & (g != "") & (g.str.lower() != "nan")
    if not ok.any():
        return {}
    geo = gpd.GeoDataFrame({"g": g[ok].astype(str).to_numpy()}, geometry=u.geometry[ok].to_numpy(), crs=gd.CRS)
    grupos = list(dict.fromkeys(geo.g))
    geoms = list(geo.dissolve(by="g").loc[grupos].geometry.buffer(150))     # el margen cierra rendijas entre vecinos
    i_a, i_b = STRtree(geoms).query(geoms, predicate="intersects")
    vecinos = [set() for _ in grupos]
    for a, b in zip(i_a, i_b, strict=False):
        if a != b:
            vecinos[a].add(int(b))
    return dict(zip(grupos, pal.colorear_grafo(vecinos, pal.ampliar(paleta, len(grupos)), semilla), strict=False))


def _colorear(u: pd.DataFrame, e: Estilo, tonos: list):
    """Pone en `u["fill"]` el color de cada unidad. Devuelve (con color, valores de leyenda, totales por zona)."""
    con = u.valor.notna()
    u["fill"] = e.color_sin_dato or pal.aclarar(tonos[0], 0.65)
    valores_ley = u.loc[con, "valor"]          # valores que resume la leyenda
    zonas_tot = None
    if e.relleno == "zona_total":
        # cada zona se resume y todos sus lugares llevan ese tono
        z = u.grupo.astype("string").str.strip()
        tiene = z.notna() & (z != "") & (z.str.lower() != "nan")
        ag = (lambda x: x.sum(min_count=1)) if e.zona_agregar == "suma" else "mean"
        zonas_tot = u[tiene].groupby(z[tiene])["valor"].agg(ag).dropna()
        if len(zonas_tot):
            idxz = _indices_tono(zonas_tot, e.n_tonos, e.escala)
            enz = tiene & z.isin(zonas_tot.index)
            u.loc[enz, "fill"] = z[enz].map(idxz).map(lambda i: tonos[i])
            con = enz
            valores_ley = zonas_tot
    elif e.relleno in ("zona", "zona_valor"):
        # un color por zona; en "zona_valor" el tono sigue el valor
        u["fill"] = e.color_sin_dato or "#F1F0EC"
        z = u.grupo.astype("string").str.strip()
        tiene = z.notna() & z.isin(list(e.colores_zona))
        if e.relleno == "zona":
            u.loc[tiene, "fill"] = z[tiene].map(e.colores_zona)
        else:
            # cada zona tiene su escala, a partir de su color
            if e.zona_escala == "por_zona":
                partes = [_indices_tono(u.loc[tiene & con & (z == g), "valor"], e.n_tonos, e.escala)
                          for g in z[tiene].unique()]
                idx = pd.concat(partes) if partes else pd.Series(dtype=int)
            else:
                idx = _indices_tono(u.loc[tiene & con, "valor"], e.n_tonos, e.escala)
            rampas = {g: pal.tonos(pal.rampa_un_color(c, fuerte=e.zona_rol == "fuerte"), e.n_tonos)
                      for g, c in e.colores_zona.items()}
            for i in u.index[tiene]:
                r = rampas[z[i]]
                u.at[i, "fill"] = r[idx[i]] if i in idx.index else pal.aclarar(r[0], 0.5)
        con = tiene
    elif con.any():
        idx = _indices_tono(u.loc[con, "valor"], e.n_tonos, e.escala)
        u.loc[con, "fill"] = idx.map(lambda i: tonos[i])
    return con, valores_ley, zonas_tot


def preparar(tabla: pd.DataFrame, e: Estilo) -> dict:
    """Une los datos con las geometrías del área elegida y calcula el color de cada unidad."""
    otros = None  # los no elegidos van de contexto
    incluir_isla = False
    if e.nivel == "ciudad":
        dep, mun = gd.CIUDADES[e.ciudad]
        deptos_sel = [dep]
        u = gd.ciudades()
        u = u[(u.ciudad == e.ciudad) & (e.ciudad_rural | ~u.rural)].copy()
        if e.divisiones:
            elegido = u.division.isin(e.divisiones)
            otros, u = u[~elegido].copy(), u[elegido].copy()     # el resto de la ciudad va de contexto
        llave = ["division"]
    elif e.nivel == "region":
        regs = e.regiones or gd.lista_regiones()
        deptos_sel = [d for d, r in gd.REGION_DE.items() if r in regs]
        u = gd.regiones()
        u = u[u.region.isin(regs)].copy()
        llave = ["region"]
    elif e.nivel == "municipio":
        deptos_sel = e.deptos or gd.lista_departamentos(incluir_insular=False)
        u = gd.municipios()
        u = u[u.departamento.isin(deptos_sel)].copy()
        if e.municipios:
            elegido = (u.departamento + "|" + u.municipio).isin(set(e.municipios))
            otros, u = u[~elegido], u[elegido].copy()
        llave = ["departamento", "municipio"]
    else:
        deptos_sel = e.deptos or gd.lista_departamentos(incluir_insular=False)
        incluir_isla = e.mostrar_isla and not e.deptos  # todo el país: la isla va en un recuadro
        u = gd.departamentos()
        u = u[u.departamento.isin(deptos_sel + ([gd.ISLA_INSULAR] if incluir_isla else []))].copy()
        llave = ["departamento"]
    if tabla is not None and len(tabla):
        cols = llave + ["valor"] + (["grupo"] if "grupo" in tabla else [])
        u = u.merge(tabla[cols], on=llave, how="left")
    else:
        u["valor"] = np.nan
    if "grupo" not in u:
        u["grupo"] = pd.NA
    if e.grupos_geo:
        u["grupo"] = _grupo_geografico(u, e)
    fuera = 0
    if tabla is not None and len(tabla):
        fuera = int((~tabla.set_index(llave).index.isin(u.set_index(llave).index)).sum())

    tonos = pal.tonos(e.colores, e.n_tonos, e.invertir)
    con, valores_ley, zonas_tot = _colorear(u, e, tonos)
    return {"u": u, "tonos": tonos, "deptos_sel": deptos_sel, "fuera": fuera, "con_dato": int(con.sum()),
            "otros": otros, "valores_ley": valores_ley, "zonas_tot": zonas_tot, "isla": incluir_isla}


def _limites(geoms, margen=0.05):
    minx, miny, maxx, maxy = geoms.total_bounds
    W, H = maxx - minx, maxy - miny
    m = margen * max(W, H)
    return (minx - m, maxx + m), (miny - m, maxy + m)


def dibujar(tabla: pd.DataFrame | None, e: Estilo):
    """Devuelve (figura, info). Un valor infinito en la tabla cuenta como «sin dato»."""
    if tabla is not None and "valor" in tabla and not np.isfinite(tabla["valor"].astype(float).fillna(0)).all():
        tabla = tabla.assign(valor=tabla["valor"].astype(float).where(np.isfinite(tabla["valor"].astype(float))))
    with plt.rc_context({"font.family": FUENTES.get(e.fuente, FUENTES["sans"])}):
        return _dibujar(tabla, e)


_POR_DEFECTO_EN = {"ESCALA": "SCALE", "SEGMENTO": "SEGMENT", "MENOR": "LOWER", "MAYOR": "HIGHER"}
_NOMBRE_COL = {"municipio": "municipio", "region": "region", "ciudad": "division"}


def _pulg(puntos: float) -> float:
    return puntos / 72


@dataclass
class _Escena:
    """Qué se dibuja: datos preparados, capas geográficas y encuadre."""
    e: Estilo
    p: dict
    u: pd.DataFrame
    u_ax: pd.DataFrame
    tonos: list
    isla: pd.DataFrame | None
    pais: gpd.GeoDataFrame
    pais_cont: gpd.GeoDataFrame
    area_deptos: gpd.GeoDataFrame
    solo_algunos: bool
    solo_munis: bool
    es_ciudad: bool
    nombre_col: str
    tx: dict
    area: object = None
    xlim: tuple = (0.0, 1.0)
    ylim: tuple = (0.0, 1.0)


@dataclass
class _Medidas:
    """Tamaños de la figura en pulgadas y fracciones de ella."""
    fig_w: float = 0.0
    fig_h: float = 0.0
    margen: float = 0.0
    mapa_w: float = 0.0
    ax_w: float = 0.0
    ax_h: float = 0.0
    m_in: float = 0.0
    lista_w: float = 0.0
    lista_h: float = 0.0
    lista_cols: int = 1
    lateral: bool = True
    con_lista: bool = False
    tam_ley: float = 0.0
    base: float = 0.0
    alto_nota: float = 0.0
    alto_res: float = 0.0
    pie: float = 0.17          # franja inferior reservada a la firma
    alto_tit: float = 0.0
    sep_tit: float = 0.0
    sep_sub: float = 0.0
    zonas_ley: list = field(default_factory=list)
    por_fila: int = 1
    filas_ley: int = 0
    esp_ley: float = 0.0
    esp_ley_ext: float = 0.0
    esp_ley_ext_der: float = 0.0
    res: dict | None = None
    lin_res: list = field(default_factory=list)
    esc_res: float = 1.0


def _preparar_escena(tabla: pd.DataFrame | None, e: Estilo) -> _Escena:
    if e.idioma == "en":
        e = replace(e, leyenda_titulo=_POR_DEFECTO_EN.get(e.leyenda_titulo, e.leyenda_titulo),
                    texto_menor=_POR_DEFECTO_EN.get(e.texto_menor, e.texto_menor),
                    texto_mayor=_POR_DEFECTO_EN.get(e.texto_mayor, e.texto_mayor))
    p = preparar(tabla, e)
    u = p["u"]
    if e.relleno in ("zona", "zona_valor") and u.grupo.nunique() > 20:
        e = replace(e, leyenda=False)            # con tantos grupos la leyenda no cabe ni se lee
    isla = u[u.departamento == gd.ISLA_INSULAR] if p["isla"] else None      # se dibuja aparte, en un recuadro
    pais = gd.departamentos()
    pais_cont = pais[pais.departamento != gd.ISLA_INSULAR]
    esc = _Escena(
        e=e, p=p, u=u, u_ax=u if isla is None else u.drop(isla.index), tonos=p["tonos"], isla=isla, pais=pais,
        pais_cont=pais_cont, area_deptos=pais[pais.departamento.isin(p["deptos_sel"])],
        solo_algunos=p["otros"] is not None and len(p["otros"]) > 0, solo_munis=False, es_ciudad=e.nivel == "ciudad",
        nombre_col=_NOMBRE_COL.get(e.nivel, "departamento"), tx=_txt(e))
    esc.solo_munis = esc.solo_algunos and not e.mostrar_depto_completo      # solo los municipios elegidos
    if esc.es_ciudad:
        esc.area = u if (esc.solo_munis or not esc.solo_algunos) else pd.concat([u, p["otros"]])
    else:
        esc.area = u if esc.solo_munis else esc.area_deptos
    esc.xlim, esc.ylim = _limites(pais_cont if e.encuadre == "pais" else esc.area)
    if e.encuadre == "pais" and gd.ISLA_INSULAR in p["deptos_sel"]:
        esc.xlim, esc.ylim = _limites(pais)
    return esc


def _columnas_lista(esc: _Escena, ax_w: float) -> tuple[int, float]:
    """Columnas y alto de la lista del ranking cuando va arriba o abajo del mapa."""
    e, p, u = esc.e, esc.p, esc.u
    n_lista = min(e.top_n, p["con_dato"])
    if e.relleno == "zona_total" and p["zonas_tot"] is not None and len(p["zonas_tot"]):
        nombres = [str(x) for x in p["zonas_tot"].sort_values(ascending=False).index[:e.top_n]]
    else:
        nombres = [str(x) for x in u[u.valor.notna()].sort_values("valor", ascending=False)[esc.nombre_col].head(e.top_n)]
    letra = e.tam_lista * 0.52 / 72                       # ancho medio de una letra, en pulgadas
    ancho_item = 0.45 + letra * (max((len(x) for x in nombres), default=8) + 7) + 0.3
    cols = max(1, min(n_lista, int(ax_w // ancho_item)))
    cols = -(-n_lista // -(-n_lista // cols)) if n_lista else 1      # sin columnas vacías
    return cols, 0.72 + max(0.2, 0.3 * e.tam_lista / 10.5) * -(-n_lista // cols)


def _alto_leyenda(esc: _Escena, m: _Medidas) -> float:
    e = esc.e
    if m.zonas_ley:
        alto = (0.55 + (0.42 if e.relleno == "zona_valor" else 0.28) * m.filas_ley
                + (0.22 if e.relleno == "zona_valor" else 0) + m.esp_ley) if e.leyenda else 0.12
    elif e.leyenda and esc.p["con_dato"]:
        alto = 1.05 + m.esp_ley + max(m.esp_ley_ext, m.esp_ley_ext_der)
    else:
        alto = 0.12
    return max(alto, 0.12)


def _calcular_medidas(esc: _Escena) -> _Medidas:
    """Tamaños de la figura y de cada bloque; ajusta el encuadre."""
    e, p, u = esc.e, esc.p, esc.u
    m = _Medidas()
    m.con_lista = e.etiquetas == "ranking" and e.ranking_modo in ("lista", "ambos") and p["con_dato"] > 0
    m.m_in = 0.03 * e.ancho_pulgadas
    m.ax_w = e.ancho_pulgadas - 2 * m.m_in
    m.lateral = e.ranking_pos in ("derecha", "izquierda")
    m.lista_w = 3.0 if m.con_lista and m.lateral else 0
    if m.con_lista and not m.lateral:
        m.lista_cols, m.lista_h = _columnas_lista(esc, m.ax_w)
    m.fig_w = e.ancho_pulgadas + m.lista_w
    m.margen = (m.m_in + (m.lista_w if e.ranking_pos == "izquierda" else 0)) / m.fig_w    # margen izquierdo
    m.mapa_w = m.ax_w / m.fig_w
    xlim, ylim = esc.xlim, esc.ylim
    forma = (ylim[1] - ylim[0]) / (xlim[1] - xlim[0])
    forma = {"cuadrado": 1.0, "vertical": 1.25, "horizontal": 9 / 16}.get(e.proporcion, min(max(forma, 0.62), 1.45))
    m.ax_h = m.ax_w * forma
    if e.relleno in ("zona", "zona_valor"):
        presentes = set(u.grupo.dropna().astype(str).str.strip())
        m.zonas_ley = [z for z in e.colores_zona if z in presentes]
    m.por_fila = max(1, min(2 if e.relleno == "zona_valor" else 4, len(m.zonas_ley)))
    m.filas_ley = -(-len(m.zonas_ley) // m.por_fila)
    m.esp_ley, m.esp_ley_ext = _pulg(e.esp_leyenda), _pulg(e.esp_leyenda_extremos)
    m.esp_ley_ext_der = _pulg(e.esp_leyenda_extremos_der)
    m.tam_ley = _alto_leyenda(esc, m)
    alto_tit = _pulg(e.titulo_tam) * 1.45 if e.titulo else 0
    alto_sub = _pulg(e.subtitulo_tam) * 1.6 if e.subtitulo else 0
    m.sep_tit = _pulg(e.esp_titulo) if (e.titulo or e.subtitulo) else 0
    m.sep_sub = _pulg(e.esp_subtitulo) if (e.titulo and e.subtitulo) else 0
    m.alto_tit = alto_tit
    alto_bloque_tit = max(alto_tit + alto_sub + 0.12 + m.sep_tit + m.sep_sub, 0.05)
    m.alto_nota = max(_pulg(e.nota_tam) * 2.4 + _pulg(e.esp_nota), _pulg(e.nota_tam)) if e.fuente_nota else 0
    m.res = calcular_resumen(p, e) if e.resumen else None
    if m.res and e.resumen_en_imagen:
        ancho_chars = int(m.ax_w * 72 / (e.tam_resumen * 0.5))      # caracteres que caben a ese tamaño
        for linea in lineas_resumen(m.res, e):
            m.lin_res += textwrap.wrap(linea, ancho_chars) or [""]
    m.esc_res = e.tam_resumen / 8.5
    m.alto_res = (0.36 * m.esc_res + 0.19 * m.esc_res * len(m.lin_res)) if m.lin_res else 0
    m.fig_h = m.ax_h + m.tam_ley + alto_bloque_tit + m.alto_nota + m.alto_res + m.lista_h + m.pie
    m.base = m.pie + m.alto_nota + m.alto_res  # firma, resumen y nota, bajo la leyenda
    # se amplía el encuadre en el eje que sobre, sin deformar
    ancho, alto = xlim[1] - xlim[0], ylim[1] - ylim[0]
    cx, cy = sum(xlim) / 2, sum(ylim) / 2
    if ancho / alto < m.ax_w / m.ax_h:
        ancho = alto * m.ax_w / m.ax_h
    else:
        alto = ancho * m.ax_h / m.ax_w
    esc.xlim, esc.ylim = (cx - ancho / 2, cx + ancho / 2), (cy - alto / 2, cy + alto / 2)
    return m


def _capas_contexto(ax, esc: _Escena):
    """Vecinos, resto del país y municipios de contexto. Devuelve el municipio de la ciudad (o None)."""
    e, p = esc.e, esc.p
    base_mun = None
    if (e.mostrar_vecinos or e.color_oceano) and len(gd.vecinos()):  # con mar propio, el vecino no se pinta de mar
        gd.vecinos().plot(ax=ax, color=e.color_vecinos or pal.aclarar(e.color_contexto, 0.45), edgecolor="white",
                          linewidth=0.8, zorder=0)
    if esc.es_ciudad:
        dep, mun = gd.CIUDADES[e.ciudad]
        caja = box(esc.xlim[0], esc.ylim[0], esc.xlim[1], esc.ylim[1]).buffer((esc.xlim[1] - esc.xlim[0]) * 0.5)
        m_all = gd.municipios()
        m_all = m_all[m_all.intersects(caja)]
        base_mun = m_all[(m_all.departamento == dep) & (m_all.municipio == mun)]
        if e.mostrar_resto_pais:
            m_all.drop(base_mun.index).plot(ax=ax, color=e.color_contexto, edgecolor="white", linewidth=0.8, zorder=1)
        if not esc.solo_munis:
            base_mun.plot(ax=ax, color=pal.aclarar(e.color_contexto, 0.5), edgecolor="none", zorder=1.5)
    elif e.mostrar_resto_pais:
        resto = esc.pais[~esc.pais.departamento.isin(p["deptos_sel"])]
        resto.plot(ax=ax, color=e.color_contexto, edgecolor="white", linewidth=1, zorder=1)
    if esc.solo_algunos and not esc.solo_munis:
        p["otros"].plot(ax=ax, color=pal.aclarar(e.color_contexto, 0.35), edgecolor="white", linewidth=0.4, zorder=1)
    return base_mun


def _capas_unidades(ax, esc: _Escena, base_mun):
    """Unidades con su color, líneas de borde y contornos de grupo y de área."""
    e, u_ax = esc.e, esc.u_ax
    rellenos = u_ax["fill"].tolist()      # lista y no Serie: geopandas 1.2 alinea una Serie por etiqueta de índice
    u_ax.plot(ax=ax, color=rellenos, edgecolor=rellenos, linewidth=0.3, zorder=2)   # sin rendijas entre polígonos
    if e.nivel != "region" and e.borde_grosor > 0:
        u_ax.boundary.plot(ax=ax, color=e.borde_color, linewidth=e.borde_grosor, zorder=2.5, **_trazo(e.estilo_borde))
    if e.nivel in ("municipio", "region") and e.borde_depto_grosor > 0 and not esc.solo_munis:
        esc.area_deptos.boundary.plot(ax=ax, color=e.borde_depto_color, linewidth=e.borde_depto_grosor, zorder=3,
                                      **_trazo(e.estilo_borde_depto))
    if esc.es_ciudad and e.borde_depto_grosor > 0 and not esc.solo_munis:
        base_mun.boundary.plot(ax=ax, color=e.borde_depto_color, linewidth=e.borde_depto_grosor, zorder=3,
                               **_trazo(e.estilo_borde_depto))
    if e.nivel == "region" and e.borde_grosor > 0:          # líneas entre regiones, encima de los departamentos
        u_ax.boundary.plot(ax=ax, color=e.borde_color, linewidth=e.borde_grosor, zorder=3.5, **_trazo(e.estilo_borde))
    grupos = [g for g in u_ax.grupo.dropna().unique() if str(g).strip() and g in e.colores_grupo]
    for g in grupos:
        geom = u_ax[u_ax.grupo == g].geometry.union_all().buffer(80).buffer(-80)
        _contorno_interior(ax, geom, e.colores_grupo[g], e.contorno_grupo_grosor, e.estilo_contorno_grupo)
    if e.contorno_area_color:
        _contorno_interior(ax, _unir(esc.area).buffer(80).buffer(-80),
                           e.contorno_area_color, e.contorno_area_grosor, e.estilo_contorno_area)


def _crear_mapa(fig, esc: _Escena, m: _Medidas):
    """Ejes del mapa con sus capas."""
    e = esc.e
    # la lista de abajo va entre el mapa y la leyenda
    base_mapa = m.tam_ley + m.base + (m.lista_h if e.ranking_pos == "abajo" else 0)
    ax = fig.add_axes([m.margen, base_mapa / m.fig_h, m.mapa_w, m.ax_h / m.fig_h])
    ax.set_facecolor(e.color_fondo)
    base_mun = _capas_contexto(ax, esc)
    _capas_unidades(ax, esc, base_mun)
    ax.set_xlim(*esc.xlim)
    ax.set_ylim(*esc.ylim)
    ax.set_aspect("equal")
    ax.axis("off")
    if e.color_oceano and e.color_oceano.lower() != e.color_fondo.lower():
        ax.add_patch(Rectangle((esc.xlim[0], esc.ylim[0]), esc.xlim[1] - esc.xlim[0], esc.ylim[1] - esc.ylim[0],
                               facecolor=e.color_oceano, edgecolor="none", zorder=-5))
    return ax


def _marcadores_ranking(ax, esc: _Escena, top: pd.DataFrame, color_marc: str):
    """Círculo numerado sobre cada lugar del ranking."""
    e = esc.e
    k = (esc.xlim[1] - esc.xlim[0]) / 900   # desplazamiento de la sombra, proporcional al encuadre
    for i, (_, r) in enumerate(top.iterrows(), start=1):
        if esc.isla is not None and r.get("departamento") == gd.ISLA_INSULAR:
            continue                                  # el archipiélago está fuera del encuadre
        c = _centro(r.geometry)
        d = e.etiqueta_tam * 2.6
        ax.scatter([c.x + 3 * k], [c.y - 3 * k], s=(d + 2) ** 2, color="black", alpha=0.18, linewidth=0, zorder=6)
        ax.scatter([c.x], [c.y], s=d ** 2, color=color_marc, edgecolor="white", linewidth=1.5, zorder=7)
        ax.text(c.x, c.y, str(i), color="white" if pal.es_oscuro(color_marc) else "#222",
                ha="center", va="center_baseline", fontsize=e.etiqueta_tam * 1.3, fontweight="bold", zorder=8)


def _textos_sobre_el_mapa(ax, esc: _Escena) -> list:
    """Valor, nombre o ambos sobre cada lugar. Devuelve los textos subrayados."""
    e, u_ax, nombre_col = esc.e, esc.u_ax, esc.nombre_col
    subrayar = []
    if e.etiquetas not in ("valor", "nombre", "nombre_valor"):
        return subrayar
    filas = u_ax if e.etiquetas == "nombre" else u_ax[u_ax.valor.notna()]
    halo = [pe.withStroke(linewidth=2.6, foreground="white")]
    for _, r in filas.iterrows():
        c = _centro(r.geometry)
        if e.etiquetas == "valor":
            txt = formato(r.valor, e.decimales, e.sufijo)
        elif e.etiquetas == "nombre":
            txt = r[nombre_col]
        else:
            v = formato(r.valor, e.decimales, e.sufijo)
            txt = {"lado": f"{r[nombre_col]} {v}", "parentesis": f"{r[nombre_col]} ({v})"}.get(
                e.valor_junto, f"{r[nombre_col]}\n{v}")
        t = ax.text(c.x, c.y, txt, ha="center", va="center", fontsize=e.etiqueta_tam,
                    color=e.color_etiquetas or "#1F2A28", linespacing=1.1, path_effects=halo, zorder=8,
                    **_fuente(e.estilo_etiquetas, e.tipo_etiquetas))
        if "subrayado" in e.estilo_etiquetas:
            subrayar.append(t)
    return subrayar


def _etiquetas(fig, ax, esc: _Escena, m: _Medidas) -> list:
    """Marcadores del ranking, etiquetas sobre el mapa y lista del ranking. Devuelve los textos subrayados."""
    e, p, u = esc.e, esc.p, esc.u
    color_marc = e.color_marcador or esc.tonos[-1]
    con = u[u.valor.notna()]
    nombre_col = esc.nombre_col
    rk, rk_nombre = con, nombre_col
    if e.relleno == "zona_total" and p["zonas_tot"] is not None and len(p["zonas_tot"]):
        # el ranking es de zonas con su total
        zz = u[u.grupo.astype("string").str.strip().isin(p["zonas_tot"].index)].copy()
        zz["grupo"] = zz.grupo.astype(str).str.strip()
        rk = zz.dissolve(by="grupo", as_index=False)[["grupo", "geometry"]]
        rk["valor"] = rk.grupo.map(p["zonas_tot"])
        rk_nombre = "grupo"
    top = rk.sort_values("valor", ascending=False).head(e.top_n) if e.etiquetas == "ranking" else rk.iloc[:0]
    if e.etiquetas == "ranking" and len(con) and e.ranking_modo in ("mapa", "ambos"):
        _marcadores_ranking(ax, esc, top, color_marc)
    subrayar = _textos_sobre_el_mapa(ax, esc)
    if m.con_lista and len(top):
        varios = rk_nombre == "municipio" and top.departamento.nunique() > 1
        if m.lateral:
            x0 = (m.m_in + m.ax_w + 0.25) / m.fig_w if e.ranking_pos == "derecha" else m.m_in / m.fig_w
            caja = dict(x0=x0, ancho=(m.lista_w - 0.35) / m.fig_w, y0=(m.tam_ley + m.base) / m.fig_h, alto=m.ax_h / m.fig_h,
                        alto_in=m.ax_h, ancho_in=m.lista_w - 0.35, cols=1)
        else:
            sep = 0.22         # aire entre la lista y el mapa
            y0 = (m.tam_ley + m.base + (0 if e.ranking_pos == "abajo" else m.ax_h + sep)) / m.fig_h
            caja = dict(x0=m.margen, ancho=m.mapa_w, y0=y0, alto=(m.lista_h - sep) / m.fig_h, alto_in=m.lista_h - sep,
                        ancho_in=m.ax_w, cols=m.lista_cols)
        subrayar += _lista_ranking(fig, top, rk_nombre, varios, color_marc, e, **caja)
    return subrayar


def _titulos(fig, esc: _Escena, m: _Medidas, subrayar: list):
    e, tx = esc.e, esc.tx
    yt = 1 - (0.12 + m.sep_tit) / m.fig_h
    if e.titulo:
        t = fig.text(m.margen, yt, e.titulo, fontsize=e.titulo_tam, color=tx["titulo"], va="top",
                     **_fuente(e.estilo_titulo, e.tipo_titulo))
        if "subrayado" in e.estilo_titulo:
            subrayar.append(t)
        yt -= (m.alto_tit + m.sep_sub) / m.fig_h
    if e.subtitulo:
        t = fig.text(m.margen, yt, e.subtitulo, fontsize=e.subtitulo_tam, color=tx["sub"], va="top",
                     **_fuente(e.estilo_subtitulo, e.tipo_subtitulo))
        if "subrayado" in e.estilo_subtitulo:
            subrayar.append(t)


def _leyenda_zonas(fig, esc: _Escena, m: _Medidas, subrayar: list):
    """Leyenda de segmentos: un cuadro de color por zona (o su escala, en «zona_valor»)."""
    e, tx = esc.e, esc.tx

    def yin(pulgadas):
        return pulgadas / m.fig_h
    top = m.base + m.tam_ley - 0.12 - m.esp_ley
    if e.leyenda_titulo:
        t = fig.text(m.margen, yin(top), e.leyenda_titulo, fontsize=e.leyenda_tam, color=tx["leyenda"], va="top",
                     **_fuente(e.estilo_leyenda, e.tipo_leyenda))
        if "subrayado" in e.estilo_leyenda:
            subrayar.append(t)
    col_w = m.mapa_w / m.por_fila
    paso = 0.42 if e.relleno == "zona_valor" else 0.28
    for k, zname in enumerate(m.zonas_ley):
        fila, col = divmod(k, m.por_fila)
        yy = yin(top - 0.42 - fila * paso)
        xx = m.margen + col * col_w
        etiqueta = zname if len(zname) <= 22 else zname[:21] + "…"
        if e.relleno == "zona_valor":
            fig.text(xx, yy + yin(0.04), etiqueta, fontsize=9.5, color=tx["leyenda"], va="bottom")
            r = pal.tonos(pal.rampa_un_color(e.colores_zona[zname], fuerte=e.zona_rol == "fuerte"), e.n_tonos)
            ancho = col_w * (0.98 if m.por_fila == 1 else 0.9) / len(r)
            for j, c in enumerate(r):
                fig.patches.append(Rectangle((xx + j * ancho, yy - yin(0.12)), ancho * 0.96, yin(0.13),
                                             transform=fig.transFigure, color=c))
        else:
            fig.patches.append(Rectangle((xx, yy - yin(0.07)), yin(0.18) * m.fig_h / m.fig_w, yin(0.16),
                                         transform=fig.transFigure, color=e.colores_zona[zname]))
            fig.text(xx + 0.26 / m.fig_w, yy, etiqueta, fontsize=9.5, color=tx["leyenda"], va="center")
    if e.relleno == "zona_valor":
        fig.text(m.margen, yin(top - 0.42 - m.filas_ley * paso + 0.05), _tx(e, "escala_zona")
                 + (_tx(e, "por_zona") if e.zona_escala == "por_zona" else ""),
                 fontsize=9, color=tx["suave"], va="center")


def _leyenda_escala(fig, esc: _Escena, m: _Medidas, subrayar: list):
    """Leyenda de la escala de color, con sus extremos."""
    e, tx = esc.e, esc.tx

    def yin(pulgadas):
        return pulgadas / m.fig_h
    lx, w, h = m.margen, m.mapa_w / len(esc.tonos), yin(0.16)
    ly = yin(m.base + 0.42 + max(m.esp_ley_ext, m.esp_ley_ext_der))
    if e.leyenda_titulo:
        t = fig.text(lx, ly + h + yin(0.16), e.leyenda_titulo, fontsize=e.leyenda_tam, color=tx["leyenda"],
                     **_fuente(e.estilo_leyenda, e.tipo_leyenda))
        if "subrayado" in e.estilo_leyenda:
            subrayar.append(t)
    for i, c in enumerate(esc.tonos):
        fig.patches.append(Rectangle((lx + i * w, ly), w * 0.98, h, transform=fig.transFigure, color=c))
    if e.leyenda_extremos == "valores":
        v = esc.p["valores_ley"]
        izq, der = formato(v.min(), e.decimales, e.sufijo), formato(v.max(), e.decimales, e.sufijo)
    else:
        izq, der = e.texto_menor, e.texto_mayor
    for x, txt, ha, esp_lado, tam_lado, color_lado, estilo_lado, tipo_lado in (
            (lx, izq, "left", m.esp_ley_ext, e.extremos_tam, tx["extremos"], e.estilo_extremos, e.tipo_extremos),
            (m.margen + m.mapa_w, der, "right", m.esp_ley_ext_der, e.extremos_tam_der, tx["extremos_der"],
             e.estilo_extremos_der, e.tipo_extremos_der)):
        t = fig.text(x, ly - yin(0.26 + esp_lado), txt, fontsize=tam_lado, color=color_lado, ha=ha,
                     **_fuente(estilo_lado, tipo_lado))
        if "subrayado" in estilo_lado:
            subrayar.append(t)


def _pie(fig, esc: _Escena, m: _Medidas, subrayar: list):
    """Resumen de los datos y nota al pie."""
    e, tx = esc.e, esc.tx
    if m.lin_res:
        y0 = m.base - 0.12
        fig.text(m.margen, y0 / m.fig_h, _tx(e, "resumen"), fontsize=e.tam_resumen * 1.18, color=tx["leyenda"], va="top",
                 **{**_fuente(e.estilo_resumen, e.tipo_resumen), "fontweight": "bold"})
        for k, linea in enumerate(m.lin_res):
            subrayar += _linea_con_rotulos(fig, m.margen, (y0 - (0.26 + 0.19 * k) * m.esc_res) / m.fig_h, linea,
                                           fontsize=e.tam_resumen, color=e.color_resumen or tx["resumen"], va="top",
                                           estilo=e.estilo_resumen, tipo=e.tipo_resumen)
    if e.fuente_nota:
        t = fig.text(m.margen, (m.pie + _pulg(e.nota_tam) * 0.7) / m.fig_h, e.fuente_nota, fontsize=e.nota_tam, color=tx["nota"],
                     **_fuente(e.estilo_nota, e.tipo_nota))
        if "subrayado" in e.estilo_nota:
            subrayar.append(t)


def _cartografia(ax, esc: _Escena, mini, amp, huella_amp) -> tuple:
    """Barra de escala y flecha del norte en esquinas libres. Devuelve sus esquinas."""
    e, xlim, ylim = esc.e, esc.xlim, esc.ylim
    ocupadas = {mini, amp} | ({"sup-izq"} if esc.isla is not None else set())
    esq_escala = esq_norte = None
    area = _unir(esc.u, (xlim[1] - xlim[0]) * 0.012)  # el área con margen: nada se dibuja encima
    if huella_amp is not None:
        area = area.union(huella_amp)
    if e.escala_km:
        esq = _esquina_libre(("inf-izq", "inf-der", "inf-cen", "sup-izq", "sup-der"), ocupadas, area,
                             lambda c: _caja_barra(xlim, ylim, c))
        _barra_escala(ax, xlim, ylim, esq)
        ocupadas.add(esq)
        esq_escala = esq
    if e.norte:
        esq = _esquina_libre(("sup-der", "sup-izq", "inf-der", "inf-izq"), ocupadas, area,
                             lambda c: _caja_norte(xlim, ylim, c))
        _flecha_norte(ax, xlim, ylim, esq)
        esq_norte = esq
    return esq_escala, esq_norte


_FIRMA = {"es": "Por Ft.", "en": "By Ft."}


def _firma(fig, esc: _Escena, m: _Medidas):
    """Firma casi imperceptible en la esquina inferior derecha: manuscrita, pequeña y apenas distinta del fondo."""
    e = esc.e
    base = "#F1F5F9" if pal.es_oscuro(e.color_fondo) else "#26302E"
    fig.text(1 - 0.09 / m.fig_w, 0.018 / m.fig_h, _FIRMA.get(e.idioma, _FIRMA["es"]), ha="right", va="bottom",
             fontsize=9, color=_mezclar(base, e.color_fondo, 0.8), **_fuente([], "firma"))


def _dibujar(tabla: pd.DataFrame | None, e: Estilo):
    esc = _preparar_escena(tabla, e)
    e, p, u = esc.e, esc.p, esc.u
    m = _calcular_medidas(esc)
    fig = plt.figure(figsize=(m.fig_w, m.fig_h), dpi=e.dpi, facecolor=e.color_fondo)
    fig.canvas.draw_idle = lambda *a, **k: None  # solo se dibuja al guardar (cada .plot() redibujaría todo)
    ax = _crear_mapa(fig, esc, m)
    subrayar = _etiquetas(fig, ax, esc, m)
    amp, huella_amp = None, None
    if e.ampliar:
        huella_amp = _ampliacion(ax, u, esc.pais, esc.nombre_col, esc.xlim, esc.ylim, m.ax_w, m.ax_h, e, esc.tonos, subrayar)
        amp = "lupa" if huella_amp is not None else None
    mini = None
    if e.minimapa and e.encuadre != "pais" and (len(p["deptos_sel"]) < len(esc.pais_cont) or esc.solo_algunos or esc.es_ciudad):
        mini = _minimapa(ax, esc.pais_cont, u, esc.xlim, esc.ylim, m.ax_w, m.ax_h, e, evitar=amp, tapado=huella_amp)
    if esc.isla is not None and len(esc.isla):  # San Andrés y Providencia, acercadas en el noroeste
        _islas_noroeste(ax, esc.isla, e, _unir(esc.pais_cont))
    _titulos(fig, esc, m, subrayar)
    if e.leyenda and m.zonas_ley:
        _leyenda_zonas(fig, esc, m, subrayar)
    elif e.leyenda and p["con_dato"]:
        _leyenda_escala(fig, esc, m, subrayar)
    _pie(fig, esc, m, subrayar)
    esq_escala, esq_norte = _cartografia(ax, esc, mini, amp, huella_amp)
    _firma(fig, esc, m)
    _subrayar(fig, subrayar)
    info = {"con_dato": p["con_dato"], "unidades": len(u), "fuera_del_area": p["fuera"],
            "minimapa": mini, "escala": esq_escala, "norte": esq_norte, "tonos": esc.tonos, "ampliacion": amp, "resumen": m.res,
            "cifras": calcular_resumen(p, replace(e, resumen_n=5))}
    return fig, info


def _islas_noroeste(ax, isla, e: Estilo, tierra):
    """San Andrés y Providencia, agrandadas y acercadas en el noroeste, sin marco ni nombre."""
    (x0, x1), (y0, y1) = ax.get_xlim(), ax.get_ylim()
    ancho, alto = x1 - x0, y1 - y0
    lx0, ly0, lx1, ly1 = tierra.bounds                # la silueta de Colombia: de ahí se mide la posición
    Wl, Hl = lx1 - lx0, ly1 - ly0
    geom = isla.geometry.iloc[0]
    islas = list(geom.geoms) if geom.geom_type == "MultiPolygon" else [geom]
    mayor = max(max(p.bounds[2] - p.bounds[0], p.bounds[3] - p.bounds[1]) for p in islas)
    k = 0.09 * min(ancho, alto) / mayor               # la isla mayor mide ~9 % del lado menor del mapa
    # las islas van de oeste a este, con un espacio entre ellas
    separacion = 0.12 * k * mayor
    grandes = [affinity.scale(p, k, k, origin=p.centroid) for p in sorted(islas, key=lambda p: p.centroid.x)]
    partes = [grandes[0]]
    bx0, by0, bx1, by1 = grandes[0].bounds
    x_libre = bx1 + separacion
    for g in grandes[1:]:
        gb = g.bounds
        dx = x_libre - gb[0]
        dy = (by0 + 0.7 * (by1 - by0)) - (gb[1] + gb[3]) / 2
        movida = affinity.translate(g, dx, dy)
        partes.append(movida)
        x_libre = movida.bounds[2] + separacion
    gx, gy = unary_union(partes).centroid.x, unary_union(partes).centroid.y
    margen = 0.012 * min(ancho, alto)
    elegido = None
    for fx, fy in ((0.10, 0.94), (0.09, 0.95), (0.08, 0.95), (0.07, 0.96), (0.06, 0.96), (0.05, 0.97)):
        cand = [affinity.translate(g, lx0 + fx * Wl - gx, ly0 + fy * Hl - gy) for g in partes]
        bx0, by0, bx1, by1 = unary_union(cand).bounds
        # que no se salga del marco del mapa
        dx = max(x0 + margen - bx0, 0) - max(bx1 - (x1 - margen), 0)
        dy = max(y0 + margen - by0, 0) - max(by1 - (y1 - margen), 0)
        cand = [affinity.translate(g, dx, dy) for g in cand]
        elegido = cand
        if not tierra.intersects(unary_union(cand).buffer(0.01 * min(ancho, alto))):
            break
    color = isla["fill"].iloc[0]
    gpd.GeoSeries(elegido, crs=gd.CRS).plot(ax=ax, color=color, edgecolor=color, linewidth=0.3, zorder=2)
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)


def _esquina_libre(candidatas, ocupadas, area, caja):
    """Primera esquina libre cuya caja no toque el área dibujada; si ninguna, la primera sin ocupar."""
    libres = [c for c in candidatas if c not in ocupadas]
    return next((c for c in libres if not area.intersects(caja(c))), libres[0] if libres else candidatas[0])


def _medidas_barra(xlim, ylim, esquina):
    """Posición y largo de la barra de escala: (x0, y0, largo, alto, km)."""
    dx, dy = xlim[1] - xlim[0], ylim[1] - ylim[0]
    objetivo = dx * 0.22 / 1000                   # unos 22 % del ancho, en km
    base = 10 ** np.floor(np.log10(objetivo))
    km = max(b * base for b in (1, 2, 5) if b * base <= objetivo) if objetivo >= 1 else round(objetivo, 1) or 0.5
    largo = km * 1000
    if esquina.endswith("cen"):
        x0 = (xlim[0] + xlim[1]) / 2 - largo / 2
    else:
        x0 = xlim[0] + dx * 0.04 if esquina.endswith("izq") else xlim[1] - dx * 0.04 - largo
    y0 = ylim[0] + dy * 0.035 if esquina.startswith("inf") else ylim[1] - dy * 0.035 - dy * 0.05
    return x0, y0, largo, dy * 0.012, km


def _caja_barra(xlim, ylim, esquina):
    """Rectángulo que ocupa la barra de escala con sus cifras."""
    dx, dy = xlim[1] - xlim[0], ylim[1] - ylim[0]
    x0, y0, largo, h, _ = _medidas_barra(xlim, ylim, esquina)
    return box(x0 - dx * 0.03, y0 - dy * 0.01, x0 + largo + dx * 0.04, y0 + dy * 0.055)


def _caja_norte(xlim, ylim, esquina):
    """Rectángulo que ocupa la flecha del norte con su letra."""
    dx, dy = xlim[1] - xlim[0], ylim[1] - ylim[0]
    x = xlim[0] + dx * 0.06 if esquina.endswith("izq") else xlim[1] - dx * 0.06
    y = ylim[1] - dy * 0.11 if esquina.startswith("sup") else ylim[0] + dy * 0.12
    return box(x - dx * 0.03, y - dy * 0.01, x + dx * 0.03, y + dy * 0.055 * 1.08 + dy * 0.045)


def _barra_escala(ax, xlim, ylim, esquina):
    """Barra de escala en kilómetros (el mapa está en metros, EPSG:3116)."""
    x0, y0, largo, h, km = _medidas_barra(xlim, ylim, esquina)
    for i in range(4):   # cuatro tramos alternados negro y blanco
        ax.add_patch(Rectangle((x0 + i * largo / 4, y0), largo / 4, h, facecolor="#26302E" if i % 2 == 0 else "white",
                               edgecolor="#26302E", linewidth=0.6, zorder=20))
    halo = [pe.withStroke(linewidth=2.2, foreground="white")]
    for frac, txt in ((0, "0"), (0.5, formato(km / 2, 0 if km / 2 >= 1 else 1)), (1, f"{formato(km, 0 if km >= 1 else 1)} km")):
        ax.text(x0 + largo * frac, y0 + h * 1.9, txt, ha="center", va="bottom", fontsize=7, color="#26302E",
                path_effects=halo, zorder=21)


def _flecha_norte(ax, xlim, ylim, esquina):
    """Flecha del norte sencilla."""
    dx, dy = xlim[1] - xlim[0], ylim[1] - ylim[0]
    x = xlim[0] + dx * 0.06 if esquina.endswith("izq") else xlim[1] - dx * 0.06
    y = ylim[1] - dy * 0.11 if esquina.startswith("sup") else ylim[0] + dy * 0.12
    alto, ancho = dy * 0.055, dx * 0.018
    ax.add_patch(plt.Polygon([(x, y + alto), (x - ancho, y), (x, y + alto * 0.28)], closed=True,
                             facecolor="#26302E", edgecolor="#26302E", linewidth=0.6, zorder=20))
    ax.add_patch(plt.Polygon([(x, y + alto), (x + ancho, y), (x, y + alto * 0.28)], closed=True,
                             facecolor="white", edgecolor="#26302E", linewidth=0.6, zorder=20))
    ax.text(x, y + alto * 1.08, "N", ha="center", va="bottom", fontsize=9, fontweight="bold", color="#26302E",
            path_effects=[pe.withStroke(linewidth=2.2, foreground="white")], zorder=21)


def _lista_ranking(fig, top, nombre_col, varios, color, e: Estilo, x0, ancho, y0, alto, alto_in, ancho_in, cols=1):
    """Lista 'TOP N' junto al mapa: en una columna a los lados y en varias arriba o abajo."""
    n = len(top)
    tx = _txt(e)
    ft = _fuente(e.estilo_lista, e.tipo_lista)
    axl = fig.add_axes([x0, y0, ancho, alto])
    axl.set_xlim(0, 1)
    axl.set_ylim(0, 1)
    axl.axis("off")
    cab = 0.34 / alto_in                       # espacio del encabezado (en fracción del alto)
    filas_n = -(-n // cols)
    paso = min(0.36 / alto_in, (1 - cab) / max(filas_n, 1)) if cols == 1 else max(0.2, 0.3 * e.tam_lista / 10.5) / alto_in
    fuente = max(5.5, min(e.tam_lista, paso * alto_in * 72 * 0.48))
    cw = 1 / cols                              # ancho de una columna (fracción del ancho)
    color_txt = e.color_lista or tx["titulo"]
    axl.text(0, 1, f"{_tx(e, 'top')} {n}", fontsize=max(fuente * 1.2, 9), color=e.color_lista or tx["leyenda"],
             va="top", **{**ft, "fontweight": "bold"})
    claro = "white" if pal.es_oscuro(color) else "#222"
    filas = []
    for i, (_, r) in enumerate(top.iterrows(), start=1):
        col, fila = divmod(i - 1, filas_n)
        base = col * cw
        y = 1 - cab - (fila + 0.5) * paso
        axl.scatter([base + 0.045 * cw], [y], s=(fuente * 2.0) ** 2, color=color, edgecolor="white", linewidth=1, clip_on=False)
        axl.text(base + 0.045 * cw, y, str(i), color=claro, ha="center", va="center_baseline", fontsize=fuente * 0.9,
                 fontweight="bold")
        nombre = str(r[nombre_col]) + (f" ({r.departamento})" if varios else "")
        valor_txt = formato(r.valor, e.decimales, e.sufijo)
        # caracteres entre número y valor (letra media ≈ 0,52 del tamaño)
        cabe = int(((ancho_in * cw) * 0.87 - len(valor_txt) * fuente * 0.6 / 72 - 0.1) / (fuente * 0.52 / 72))
        if len(nombre) > cabe:
            nombre = nombre[:max(cabe - 1, 4)].rstrip() + "…"
        filas.append((base, y, nombre, valor_txt))
    nombres = [axl.text(b + 0.13 * cw, y, nom, fontsize=fuente, color=color_txt, va="center", **ft) for b, y, nom, _ in filas]
    valores = [axl.text(b + cw, y, val, fontsize=fuente, color=color_txt, va="center", ha="right",
                        **{**ft, "fontweight": "bold"}) for b, y, _, val in filas]
    # los valores van junto al nombre más largo
    rend = fig.canvas.get_renderer()
    ancho_px = axl.get_window_extent(rend).width
    ancho_nom = max(t.get_window_extent(rend).width for t in nombres) / ancho_px
    ancho_val = max(t.get_window_extent(rend).width for t in valores) / ancho_px
    desp = min(cw * 0.98, 0.13 * cw + ancho_nom + 0.04 * cw + ancho_val)
    for t, (b, _, _, _) in zip(valores, filas, strict=False):
        t.set_x(b + desp)
    return nombres if "subrayado" in e.estilo_lista else []


def _linea_con_rotulos(fig, x, y, linea, estilo, tipo, **kw):
    """Línea del resumen con los rótulos en negrita. Devuelve los textos subrayados."""
    rend = fig.canvas.get_renderer()
    ancho_fig = fig.get_figwidth() * fig.dpi
    subrayados = []
    for parte in re.split(r"((?:^|·\s*)[^:·]+:)", linea):
        if not parte:
            continue
        es_rotulo = bool(re.fullmatch(r"(?:^|·\s*)[^:·]+:", parte))
        datos = {**_fuente(estilo, tipo), **({"fontweight": "bold"} if es_rotulo else {})}
        t = fig.text(x, y, parte, **datos, **kw)
        x += t.get_window_extent(rend).width / ancho_fig
        if "subrayado" in estilo:
            subrayados.append(t)
    return subrayados


def _mezclar(color, fondo, fraccion):
    """Color mezclado con el fondo en la fracción indicada (0 = el color, 1 = el fondo)."""
    a, b = np.array(to_rgb(color)), np.array(to_rgb(fondo))
    return to_hex(a * (1 - fraccion) + b * fraccion)


def _nombres_en_lupa(ins, sel, nombre_col: str, e: Estilo, subrayar: list):
    halo = [pe.withStroke(linewidth=2.2, foreground="white")]
    for _, r in sel.iterrows():
        c = _centro(r.geometry)
        t = ins.text(c.x, c.y, r[nombre_col], ha="center", va="center", fontsize=max(e.tam_amp, 4),
                     color=e.color_amp or "#1F2A28", path_effects=halo, zorder=5, **_fuente(e.estilo_amp, e.tipo_amp))
        if "subrayado" in e.estilo_amp:
            subrayar.append(t)


def _bordear_lupa(ins, e: Estilo, redonda: bool):
    """Recorta la lupa en círculo o le pone marco, según su forma."""
    if redonda:
        recorte = Circle((0.5, 0.5), 0.5, transform=ins.transAxes)
        ins.patch.set_visible(False)
        ins.add_patch(Circle((0.5, 0.5), 0.5, transform=ins.transAxes, facecolor=e.color_fondo, edgecolor="none", zorder=0))
        for a in ins.get_children():
            if isinstance(a, (Collection, Text)):
                a.set_clip_path(recorte)
        for b in ins.spines.values():
            b.set_visible(False)
        ins.add_patch(Circle((0.5, 0.5), 0.5, transform=ins.transAxes, fill=False, edgecolor="#3A4A47", linewidth=1.4,
                             zorder=20, clip_on=False))
    else:
        for b in ins.spines.values():
            b.set_edgecolor("#3A4A47")
            b.set_linewidth(1.4)


def _ampliacion(ax, u, pais, nombre_col, xlim, ylim, AX_W, AX_H, e: Estilo, tonos, subrayar):
    """Lupa sobre los lugares elegidos; atenúa el resto. Devuelve el área que cubre."""
    sel = u[u[nombre_col].isin(e.ampliar)]
    if sel.empty:
        return None
    redonda = e.ampliar_forma == "redonda"
    x0, y0, x1, y1 = sel.total_bounds
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    dx, dy = xlim[1] - xlim[0], ylim[1] - ylim[0]
    # contenido de la lupa: los lugares elegidos con margen (círculo mínimo o caja)
    if redonda:
        union = sel.geometry.union_all()
        c = shapely.minimum_bounding_circle(union).centroid
        cx, cy = c.x, c.y
        lado = 2 * shapely.minimum_bounding_radius(union) * 1.08 + 1500
    else:
        lado = max(x1 - x0, y1 - y0) * 1.1 + 1500
    BW = min(0.85, e.ampliar_tam)  # ancho de la lupa (fracción del mapa)
    BH = BW * AX_W / AX_H                  # cuadrada en la imagen
    mg = 0.01
    fx, fy = (cx - xlim[0]) / dx, (cy - ylim[0]) / dy
    px = min(max(fx - BW / 2, mg), 1 - BW - mg)     # centrada en los lugares; si no cabe, se acerca al borde
    py = min(max(fy - BH / 2, mg), 1 - BH - mg)
    # zona del mapa que tapa la lupa, en las coordenadas del mapa
    lcx, lcy = xlim[0] + (px + BW / 2) * dx, ylim[0] + (py + BH / 2) * dy
    rx, ry = BW * dx / 2, BH * dy / 2
    base = MPath.unit_circle() if redonda else MPath.unit_rectangle()
    centro = np.array([0.0, 0.0]) if redonda else np.array([0.5, 0.5])
    hueco = MPath((base.vertices - centro) * ([rx, ry] if redonda else [2 * rx, 2 * ry]) + [lcx, lcy], base.codes)
    marco = MPath([(xlim[0], ylim[0]), (xlim[0], ylim[1]), (xlim[1], ylim[1]), (xlim[1], ylim[0]), (xlim[0], ylim[0])],
                  # sentido contrario al hueco
                  [MPath.MOVETO, MPath.LINETO, MPath.LINETO, MPath.LINETO, MPath.CLOSEPOLY])
    ax.add_patch(PathPatch(MPath.make_compound_path(marco, hueco), facecolor=e.color_fondo, edgecolor="none",
                           alpha=0.55, zorder=2.95))
    ins = ax.inset_axes([px, py, BW, BH], zorder=12)
    ins.set_facecolor(e.color_fondo)
    zona = box(cx - lado, cy - lado, cx + lado, cy + lado)
    pais[pais.intersects(zona)].plot(ax=ins, color=e.color_contexto, edgecolor="white", linewidth=0.8)
    cerca = u[u.intersects(zona)]
    # los no ampliados se atenúan, menos que lo de fuera de la lupa
    elegido = cerca[nombre_col].isin(e.ampliar)
    tenue = [to_hex(c) if sel_ else _mezclar(c, e.color_fondo, 0.4) for c, sel_ in zip(cerca["fill"], elegido, strict=False)]
    cerca.plot(ax=ins, color=tenue, edgecolor=e.borde_color if e.borde_grosor > 0 else tenue,
               linewidth=max(e.borde_grosor, 0.3) * 1.2)
    if e.ampliar_nombres:
        _nombres_en_lupa(ins, sel, nombre_col, e, subrayar)
    ins.set_xlim(cx - lado / 2, cx + lado / 2)
    ins.set_ylim(cy - lado / 2, cy + lado / 2)
    ins.set_aspect("equal")
    ins.set_xticks([])
    ins.set_yticks([])
    ins.set_xlabel("")
    ins.set_ylabel("")
    _bordear_lupa(ins, e, redonda)
    return box(lcx - rx, lcy - ry, lcx + rx, lcy + ry)


def _minimapa(ax, pais, u, xlim, ylim, AX_W, AX_H, e: Estilo, evitar=None, tapado=None):
    """Mapa pequeño de Colombia con el área resaltada. En 'auto' busca una esquina que no tape el área."""
    cx0, cy0, cx1, cy1 = pais.total_bounds
    PAD = 0.06
    ix0, ix1 = cx0 - PAD * (cx1 - cx0), cx1 + PAD * (cx1 - cx0)
    iy0, iy1 = cy0 - PAD * (cy1 - cy0), cy1 + PAD * (cy1 - cy0)
    mg = 0.008
    region = _unir(u, (xlim[1] - xlim[0]) * 0.012)
    if tapado is not None:
        region = region.union(tapado)       # la lupa también cuenta como ocupada
    dx, dy = xlim[1] - xlim[0], ylim[1] - ylim[0]

    def libre(fx, fy, bw, bh):
        caja = box(xlim[0] + fx * dx, ylim[0] + fy * dy, xlim[0] + (fx + bw) * dx, ylim[0] + (fy + bh) * dy)
        return not region.intersects(caja)

    def esquinas(BW, BH):
        return {"sup-izq": (mg, 1 - BH - mg), "sup-der": (1 - BW - mg, 1 - BH - mg),
                "inf-izq": (mg, mg), "inf-der": (1 - BW - mg, mg)}

    tam = e.minimapa_tam
    if e.minimapa_pos == "auto":
        elegida = None
        for BW in (tam, tam * 0.85, tam * 0.7, tam * 0.55):
            BH = BW * AX_W * (iy1 - iy0) / (ix1 - ix0) / AX_H
            esq = esquinas(BW, BH)
            elegida = next((k for k, (fx, fy) in esq.items() if k != evitar and libre(fx, fy, BW, BH)), None)
            if elegida:
                break
        if not elegida:
            BW = tam
            BH = BW * AX_W * (iy1 - iy0) / (ix1 - ix0) / AX_H
            esq = esquinas(BW, BH)
            elegida = next(k for k in ("sup-der", "sup-izq", "inf-izq", "inf-der") if k != evitar)
    else:
        BW = tam
        BH = BW * AX_W * (iy1 - iy0) / (ix1 - ix0) / AX_H
        esq, elegida = esquinas(BW, BH), e.minimapa_pos
    fx, fy = esq[elegida]
    ins = ax.inset_axes([fx, fy, BW, BH], zorder=11)
    ins.set_facecolor("white")
    pais.plot(ax=ins, color=e.color_contexto, edgecolor="white", linewidth=0.25)
    u.plot(ax=ins, color=u["fill"].tolist(), edgecolor="none", linewidth=0)
    # si el área es muy pequeña frente al país, un punto marca dónde está
    ax0, ay0, ax1, ay1 = u.total_bounds
    if max(ax1 - ax0, ay1 - ay0) < 0.06 * max(cx1 - cx0, cy1 - cy0):
        c = _unir(u).centroid
        ins.scatter([c.x], [c.y], s=28, color=pal.tonos(e.colores, e.n_tonos, e.invertir)[-1],
                    edgecolor="white", linewidth=1, zorder=5)
    ins.set_xlim(ix0, ix1)
    ins.set_ylim(iy0, iy1)
    ins.set_aspect("equal")
    ins.set_xticks([])
    ins.set_yticks([])
    ins.set_xlabel("")
    ins.set_ylabel("")
    for b in ins.spines.values():
        b.set_edgecolor("#A8A59D")
        b.set_linewidth(0.6)
    return elegida


def exportar_geojson(tabla: pd.DataFrame | None, e: Estilo) -> bytes:
    """Unidades del área con valor, segmento y color, en GeoJSON (WGS84)."""
    u = preparar(tabla, e)["u"]
    llaves = [c for c in ("departamento", "municipio", "region", "ciudad", "division") if c in u]
    g = u[llaves + ["valor", "grupo", "fill", "geometry"]].rename(columns={"grupo": "segmento", "fill": "color"})
    g["segmento"] = g.segmento.astype(object).where(g.segmento.notna(), None)
    datos = json.loads(g.to_crs(4326).to_json(na="null", drop_id=True))
    datos["attribution"] = ("Límites: GADM 4.1 (uso académico y no comercial, https://gadm.org); localidades y comunas y "
                            "municipios recientes: © colaboradores de OpenStreetMap (ODbL).")
    return json.dumps(datos, ensure_ascii=False).encode("utf-8")


def exportar(fig, formato_archivo="png", dpi=None) -> bytes:
    buf = io.BytesIO()
    extra = {"jpg": {"pil_kwargs": {"quality": 95}}, "tiff": {"pil_kwargs": {"compression": "tiff_lzw"}}}.get(formato_archivo, {})
    fig.savefig(buf, format={"jpg": "jpeg"}.get(formato_archivo, formato_archivo), facecolor=fig.get_facecolor(),
                dpi=dpi or fig.dpi, **extra)
    return buf.getvalue()
