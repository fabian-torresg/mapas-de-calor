"""Geometrías de Colombia: municipios, departamentos y países vecinos.

Municipios y departamentos: GADM 4.1 (uso no comercial, sin redistribución): se descarga la primera vez a
datos/geometrias/. Vecinos: Natural Earth. Localidades y comunas: OpenStreetMap (© colaboradores, ODbL).
"""
from __future__ import annotations

import re
import shutil
import time
import unicodedata
import urllib.request
import zipfile
from functools import lru_cache
from pathlib import Path

import geopandas as gpd
import pandas as pd
from pyogrio.errors import DataSourceError
from shapely.geometry import MultiPolygon

RAIZ = Path(__file__).resolve().parent.parent
DIR_GEO = RAIZ / "datos" / "geometrias"
GADM_ZIP = DIR_GEO / "gadm41_COL_2.json.zip"
GADM_URL = "https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_COL_2.json.zip"
VECINOS_GEOJSON = DIR_GEO / "paises_vecinos.geojson"
CIUDADES_GEOJSON = DIR_GEO / "ciudades_osm.geojson"   # localidades y comunas, de OpenStreetMap (ODbL)
NUEVOS_GEOJSON = DIR_GEO / "municipios_nuevos_osm.geojson"   # municipios posteriores a GADM, de OpenStreetMap (ODbL)
CATALOGO_CSV =RAIZ / "datos" / "catalogo" / "municipios.csv"

CRS = "EPSG:3116"  # MAGNA-SIRGAS / Colombia Bogotá: metros, sin deformar el país
SIMPLIFICAR_M = 60  # tolerancia de simplificación (m)
ISLA_INSULAR = "San Andrés y Providencia"

# Nombres comunes que se escriben en lugar del oficial
ALIAS_DEPTO = {
    "BOGOTA": "Bogotá D.C.", "BOGOTADC": "Bogotá D.C.", "DISTRITOCAPITAL": "Bogotá D.C.",
    "VALLE": "Valle del Cauca", "GUAJIRA": "La Guajira", "NORTESANTANDER": "Norte de Santander",
    "SANANDRES": ISLA_INSULAR, "SANANDRESPROVIDENCIAYSANTACATALINA": ISLA_INSULAR,
    "ARCHIPIELAGODESANANDRESPROVIDENCIAYSANTACATALINA": ISLA_INSULAR,
}
ALIAS_MUNI = {
    ("Valle del Cauca", "CALI"): "Santiago de Cali",
    ("Bolívar", "CARTAGENA"): "Cartagena de Indias",
    ("Bolívar", "MOMPOX"): "Mompós",
    ("Norte de Santander", "CUCUTA"): "San José de Cúcuta",
    ("Cundinamarca", "FUSA"): "Fusagasugá",
    ("Bogotá D.C.", "BOGOTA"): "Bogotá D.C.",
    ("Bogotá D.C.", "BOGOTADC"): "Bogotá D.C.",
}

# Regiones naturales: atajo para elegir varios departamentos
REGIONES = {
    "Caribe": ["Atlántico", "Bolívar", "Cesar", "Córdoba", "La Guajira", "Magdalena", "Sucre"],
    "Andina": ["Antioquia", "Bogotá D.C.", "Boyacá", "Caldas", "Cundinamarca", "Huila",
               "Norte de Santander", "Quindío", "Risaralda", "Santander", "Tolima"],
    "Pacífica": ["Cauca", "Chocó", "Nariño", "Valle del Cauca"],
    "Orinoquía": ["Arauca", "Casanare", "Meta", "Vichada"],
    "Amazonía": ["Amazonas", "Caquetá", "Guainía", "Guaviare", "Putumayo", "Vaupés"],
    "Eje Cafetero": ["Caldas", "Quindío", "Risaralda"],
    "Insular": [ISLA_INSULAR],
}


# Regiones naturales sin solaparse: cada departamento en una
REGIONES_NATURALES = {k: v for k, v in REGIONES.items() if k != "Eje Cafetero"}
REGION_DE = {d: r for r, ds in REGIONES_NATURALES.items() for d in ds}


def norm(s) -> str:
    """Clave para comparar nombres: sin tildes, sin espacios ni signos, en mayúsculas."""
    s = unicodedata.normalize("NFD", str(s))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return "".join(c for c in s.upper() if c.isalnum())


def _zip_valido(ruta: Path) -> bool:
    """El archivo es un zip legible, con contenido y sin entradas dañadas."""
    try:
        with zipfile.ZipFile(ruta) as z:
            return bool(z.namelist()) and z.testzip() is None
    except (zipfile.BadZipFile, OSError):
        return False


def asegurar_gadm(ruta: Path = GADM_ZIP, intentos: int = 3) -> Path:
    """Descarga GADM si falta o está dañado (reintentos, tiempo máximo y verificación)."""
    if ruta.exists():
        if _zip_valido(ruta):
            return ruta
        ruta.unlink()           # copia truncada o dañada: se vuelve a descargar
    ruta.parent.mkdir(parents=True, exist_ok=True)
    tmp = ruta.with_suffix(".part")
    for intento in range(intentos):
        try:
            # URL fija con https
            with urllib.request.urlopen(GADM_URL, timeout=60) as resp, open(tmp, "wb") as f:   # noqa: S310  # nosec B310
                esperado = int(resp.headers.get("Content-Length") or 0)
                shutil.copyfileobj(resp, f)
            if esperado and tmp.stat().st_size != esperado:
                raise OSError("Descarga incompleta de GADM.")
            if not _zip_valido(tmp):
                raise OSError("El archivo descargado de GADM no es válido.")
            tmp.replace(ruta)
            return ruta
        except OSError:
            tmp.unlink(missing_ok=True)
            if intento == intentos - 1:
                raise
            time.sleep(2 * (intento + 1))
    return ruta


def _leer_gadm() -> gpd.GeoDataFrame:
    """Lee GADM; si no se puede leer, lo descarta y avisa con OSError."""
    ruta = asegurar_gadm()
    try:
        return gpd.read_file(ruta)
    except DataSourceError as error:
        ruta.unlink(missing_ok=True)
        raise OSError("No se pudo leer el archivo de GADM; se descargará de nuevo al reiniciar.") from error


def _sin_islotes(geom, km2=2.0):
    """Quita partes diminutas (islotes) que se ven como manchas sueltas; conserva siempre la mayor."""
    if geom is None or geom.geom_type != "MultiPolygon":
        return geom
    partes = [p for p in geom.geoms if p.area >= km2 * 1e6] or [max(geom.geoms, key=lambda p: p.area)]
    return partes[0] if len(partes) == 1 else MultiPolygon(partes)


def _serranilla_en_san_andres(g: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Islas Serranilla (0,3 km²) no es una unidad del DANE: su polígono se suma a San Andrés."""
    es_serranilla = g.municipio.map(norm) == "ISLASSERRANILLA"
    if not es_serranilla.any():
        return g
    depto = g.loc[es_serranilla, "departamento"].iloc[0]
    destino = g.index[(g.departamento == depto) & (g.municipio.map(norm) == "SANANDRES")]
    if len(destino):
        g.loc[destino[0], "geometry"] = g.loc[destino[0], "geometry"].union(g.loc[es_serranilla, "geometry"].iloc[0])
        g = g[~es_serranilla]
    return g


def _con_municipios_nuevos(g: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Suma los municipios posteriores a GADM 4.1 (Albania, Guachené, Norosí, San José de Uré y Tuchín).

    Vienen de OpenStreetMap: se recortan al departamento y se restan de los vecinos para no solaparse."""
    if not NUEVOS_GEOJSON.exists():
        return g
    nuevos = gpd.read_file(NUEVOS_GEOJSON).to_crs(CRS)
    g = g.copy()
    filas = []
    for n in nuevos.itertuples():
        depto = g[g.departamento == n.departamento]
        zona = depto.geometry.union_all().buffer(80).buffer(-80)
        nueva = n.geometry.simplify(SIMPLIFICAR_M).buffer(0).intersection(zona)
        if nueva.is_empty:
            continue
        toca = g.geometry.intersects(nueva)
        g.loc[toca, "geometry"] = g.loc[toca, "geometry"].map(lambda x: _sin_islotes(x.difference(nueva)))  # noqa: B023
        filas.append({"departamento": n.departamento, "municipio": n.municipio, "geometry": _sin_islotes(nueva)})
    return pd.concat([g, gpd.GeoDataFrame(filas, crs=CRS)], ignore_index=True)


@lru_cache(maxsize=1)
def municipios() -> gpd.GeoDataFrame:
    """Los 1.123 municipios de Colombia con nombre legible de departamento y municipio."""
    g = _leer_gadm()[["NAME_1", "NAME_2", "geometry"]].to_crs(CRS)
    cat = pd.read_csv(CATALOGO_CSV)
    # el catálogo trae "Valle del Cauca" y GADM "ValledelCauca"
    deptos = {norm(d): d for d in cat.Departamento.unique()}
    g["departamento"] = g.NAME_1.map(lambda n: deptos.get(norm(n), n))
    cat["k"] = cat.Departamento.map(norm) + "|" + cat.clave_gadm.map(norm)
    nombres = dict(zip(cat.k, cat.Municipio, strict=False))
    g["municipio"] = (g.departamento.map(norm) + "|" + g.NAME_2.map(norm)).map(nombres).fillna(g.NAME_2)
    g = _serranilla_en_san_andres(g)
    g["geometry"] = g.geometry.simplify(SIMPLIFICAR_M).map(_sin_islotes)
    g = _con_municipios_nuevos(g[["departamento", "municipio", "geometry"]])
    g = g.reset_index(drop=True)
    g["id"] = g.index
    return g


@lru_cache(maxsize=1)
def departamentos() -> gpd.GeoDataFrame:
    """Departamentos armados a partir de los mismos municipios: los bordes coinciden exactamente."""
    d = municipios().dissolve(by="departamento", as_index=False)[["departamento", "geometry"]]
    d["geometry"] = d.geometry.buffer(80).buffer(-80).map(_sin_islotes)  # cierra rendijas
    return d.sort_values("departamento").reset_index(drop=True)


@lru_cache(maxsize=1)
def regiones() -> gpd.GeoDataFrame:
    """Regiones naturales armadas uniendo sus departamentos."""
    d = departamentos().copy()
    d["region"] = d.departamento.map(REGION_DE)
    r = d.dissolve(by="region", as_index=False)[["region", "geometry"]]
    r["geometry"] = r.geometry.buffer(80).buffer(-80)
    orden = list(REGIONES_NATURALES)
    return r.sort_values("region", key=lambda s: s.map(orden.index)).reset_index(drop=True)


# Ciudades con división interna: nombre en la app -> (departamento, municipio)
CIUDADES = {
    "Bogotá": ("Bogotá D.C.", "Bogotá D.C."),
    "Medellín": ("Antioquia", "Medellín"),
    "Barranquilla": ("Atlántico", "Barranquilla"),
    "Bucaramanga": ("Santander", "Bucaramanga"),
    "Cali": ("Valle del Cauca", "Santiago de Cali"),
    "Pasto": ("Nariño", "San Juan de Pasto"),
    "Pereira": ("Risaralda", "Pereira"),
    "Santa Marta": ("Magdalena", "Santa Marta"),
    "Villavicencio": ("Meta", "Villavicencio"),
    "Soacha": ("Cundinamarca", "Soacha"),
    "Neiva": ("Huila", "Neiva"),
    "Armenia": ("Quindío", "Armenia"),
    "Montería": ("Córdoba", "Montería"),
    "Valledupar": ("Cesar", "Valledupar"),
    "Popayán": ("Cauca", "Popayán"),
    "Floridablanca": ("Santander", "Floridablanca"),
    "Riohacha": ("La Guajira", "Riohacha"),
    "Barrancabermeja": ("Santander", "Barrancabermeja"),
    "Yopal": ("Casanare", "Yopal"),
    "Quibdó": ("Chocó", "Quibdó"),
    "Florencia": ("Caquetá", "Florencia"),
    "Buenaventura": ("Valle del Cauca", "Buenaventura"),
}
RURALES = {"Sumapaz"}  # casi todas rurales; los corregimientos se marcan por nombre


def _orden_division(nombre: str):
    m = re.match(r"Comuna (\d+)", nombre)
    return (0, int(m.group(1)), nombre) if m else (1 if nombre.startswith("Corregimiento") else 0, 0, nombre)


@lru_cache(maxsize=1)
def ciudades() -> gpd.GeoDataFrame:
    """Localidades y comunas de las ciudades disponibles (fuente: OpenStreetMap)."""
    if not CIUDADES_GEOJSON.exists():
        return gpd.GeoDataFrame(columns=["ciudad", "departamento", "municipio", "division", "tipo", "rural", "geometry"],
                                geometry="geometry", crs=CRS)
    g = gpd.read_file(CIUDADES_GEOJSON).to_crs(CRS)
    inv = {v: k for k, v in CIUDADES.items()}
    g["ciudad"] = [inv.get((d, m)) for d, m in zip(g.departamento, g.municipio, strict=False)]
    g["rural"] = g.division.isin(RURALES) | g.division.str.startswith("Corregimiento")
    g["k"] = g.division.map(_orden_division)
    return g.sort_values(["ciudad", "k"]).drop(columns="k").reset_index(drop=True)


def lista_ciudades() -> list[str]:
    return [c for c in CIUDADES if c in set(ciudades().ciudad)]


def tipo_division(ciudad: str) -> str:
    t = ciudades()
    t = t[t.ciudad == ciudad]
    return t.tipo.iloc[0] if len(t) else "División"


def lista_regiones(incluir_insular=False) -> list[str]:
    return [r for r in REGIONES_NATURALES if incluir_insular or r != "Insular"]


@lru_cache(maxsize=1)
def vecinos() -> gpd.GeoDataFrame:
    if not VECINOS_GEOJSON.exists():
        return gpd.GeoDataFrame(geometry=[], crs=CRS)
    return gpd.read_file(VECINOS_GEOJSON).to_crs(CRS)


def lista_departamentos(incluir_insular=True) -> list[str]:
    d = departamentos().departamento.tolist()
    return d if incluir_insular else [x for x in d if x != ISLA_INSULAR]


@lru_cache(maxsize=1)
def _nombres_municipios() -> pd.DataFrame:
    return (municipios()[["departamento", "municipio"]].sort_values(["departamento", "municipio"])
            .reset_index(drop=True))


def lista_municipios(deptos: list[str] | None = None) -> pd.DataFrame:
    m = _nombres_municipios()
    if deptos:
        m = m[m.departamento.isin(deptos)].reset_index(drop=True)
    return m.copy()
