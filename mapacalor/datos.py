"""Lectura de la tabla del usuario y emparejamiento de nombres con las geometrías.

La tabla necesita una columna de lugar y una de valor; Zona (opcional) agrupa lugares. Los nombres no tienen
que coincidir exactamente: se ignoran tildes, espacios y mayúsculas, y se sugiere el más parecido.
"""
from __future__ import annotations

import difflib
import io
import re
import zipfile
from dataclasses import dataclass, field
from functools import cache

import numpy as np
import pandas as pd

from . import geodatos as gd

SINONIMOS = {
    "departamento": ["departamento", "depto", "dpto", "departamentos", "estado"],
    "municipio": ["municipio", "municipios", "ciudad", "mpio", "localidad"],
    "valor": ["valor", "valores", "cantidad", "total", "peso", "ventas", "unidades", "monto", "dato"],
    "region": ["region", "regiones"],
    "division": ["localidad", "comuna", "division", "sector", "corregimiento"],
    "grupo": ["zona", "grupo", "territorio", "categoria", "segmento", "vendedor", "asesor", "representante",
              "responsable", "ejecutivo", "rep", "sede", "canal"],
}


def detectar_columnas(df: pd.DataFrame) -> dict[str, str | None]:
    """Adivina qué columna es cada cosa a partir del encabezado."""
    cols = {gd.norm(c).lower(): c for c in df.columns}
    out = {}
    for clave, opciones in SINONIMOS.items():
        out[clave] = next((cols[k] for o in opciones for k in cols if k.startswith(o)), None)
    if out["valor"] is None:  # primera columna numérica que no sea otra cosa
        num = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c not in out.values()]
        out["valor"] = num[0] if num else None
    return out


class ArchivoInvalido(ValueError):
    """El archivo no se puede leer como una tabla (vacío, dañado o de otro formato)."""


def _decodificar(contenido: bytes) -> str:
    try:
        return contenido.decode("utf-8-sig")
    except UnicodeDecodeError:
        return contenido.decode("cp1252", errors="replace")  # CSV de Excel en Windows


def _separador(texto: str) -> str:
    """Separador de columnas según el encabezado (la primera línea con contenido)."""
    primera = next((linea for linea in texto.splitlines() if linea.strip()), "")
    cuentas = {sep: primera.count(sep) for sep in (",", ";", "	", "|")}
    return max(cuentas, key=lambda sep: (cuentas[sep], sep == ","))


MAX_FILAS = 300_000  # filas que se aceptan por archivo
MAX_DESCOMPRIMIDO = 300_000_000  # bytes máximos de un .xlsx descomprimido (evita archivos «bomba»)


def _revisar_xlsx(contenido: bytes) -> None:
    """Rechaza un libro de Excel cuyo contenido descomprimido es desproporcionado, antes de leerlo."""
    try:
        with zipfile.ZipFile(io.BytesIO(contenido)) as z:
            if sum(i.file_size for i in z.infolist()) > MAX_DESCOMPRIMIDO:
                raise ArchivoInvalido("El archivo de Excel es demasiado grande para leerlo.")
    except zipfile.BadZipFile:
        pass            # un .xls antiguo no es un zip: lo valida la lectura


def hojas_excel(nombre: str, contenido: bytes) -> list[str]:
    if nombre.lower().endswith((".csv", ".txt")):
        return []
    _revisar_xlsx(contenido)
    try:
        return pd.ExcelFile(io.BytesIO(contenido)).sheet_names
    except Exception as error:
        raise ArchivoInvalido(str(error)) from error


def leer_archivo(nombre: str, contenido: bytes, hoja=0) -> pd.DataFrame:
    try:
        if nombre.lower().endswith((".csv", ".txt")):
            texto = _decodificar(contenido)
            df = pd.read_csv(io.StringIO(texto), sep=_separador(texto), nrows=MAX_FILAS + 1)
        else:
            _revisar_xlsx(contenido)
            df = pd.read_excel(io.BytesIO(contenido), sheet_name=hoja, nrows=MAX_FILAS + 1)
    except ArchivoInvalido:
        raise
    except Exception as error:
        raise ArchivoInvalido(str(error)) from error
    if len(df.columns) == 0:
        raise ArchivoInvalido("La tabla no tiene columnas.")
    if len(df) > MAX_FILAS:
        raise ArchivoInvalido(f"La tabla tiene más de {MAX_FILAS:,} filas.".replace(",", "."))
    return df


def _a_float(x) -> float:
    """Celda como número: acepta 1.234,5, 1,234.5, 45% y $ 1.000; texto no numérico e infinitos dan NaN."""
    if x is None or (not isinstance(x, str) and pd.isna(x)):
        return np.nan
    if isinstance(x, (int, float, np.number)) and not isinstance(x, bool):
        v = float(x)
    else:
        t = str(x).strip().replace("$", "").replace("%", "").replace(" ", "")
        if "," in t and "." in t:
            t = t.replace(".", "").replace(",", ".") if t.rfind(",") > t.rfind(".") else t.replace(",", "")
        elif "," in t:
            t = t.replace(",", ".") if len(t.split(",")[-1]) != 3 else t.replace(",", "")
        elif t.count(".") > 1 or (t.count(".") == 1 and len(t.split(".")[-1]) == 3 and len(t) > 4):
            t = t.replace(".", "")
        try:
            v = float(t)
        except ValueError:
            return np.nan
    return v if np.isfinite(v) else np.nan       # inf, -inf y desbordes no son datos


def a_numero(s: pd.Series) -> pd.Series:
    """Acepta 1.234,5 / 1,234.5 / 45% / $ 1.000. Lo que no es un número finito queda vacío (NaN)."""
    if pd.api.types.is_numeric_dtype(s):
        v = s.astype(float)
        return v.where(np.isfinite(v))
    return s.map(_a_float).astype(float)


@dataclass
class Emparejado:
    tabla: pd.DataFrame                       # departamento, municipio?, valor, grupo? (nombres oficiales)
    sin_match: list[dict] = field(default_factory=list)   # filas que no se encontraron, con sugerencia
    duplicados: int = 0                        # filas que se sumaron por repetirse


def _buscar(nombre, opciones: dict[str, str], alias: dict[str, str] | None = None):
    k = gd.norm(nombre)
    if alias and k in alias:
        return alias[k], None
    if k in opciones:
        return opciones[k], None
    # coincidencia parcial: "CARMENDEVIBORAL" está dentro de "ELCARMENDEVIBORAL"
    contiene = [v for kk, v in opciones.items() if len(k) >= 5 and (k in kk or kk in k)]
    if len(contiene) == 1:
        return contiene[0], None
    sug = difflib.get_close_matches(k, list(opciones), n=1, cutoff=0.75)
    return None, (opciones[sug[0]] if sug else None)


def _buscador(opciones: dict[str, str], alias: dict[str, str] | None = None):
    """`_buscar` con memoria: cada nombre distinto se resuelve una sola vez."""
    memo = {}

    def buscar(nombre):
        k = gd.norm(nombre)
        if k not in memo:
            memo[k] = _buscar(nombre, opciones, alias)
        return memo[k]
    return buscar


@cache
def _opciones_lugar(nivel: str, ciudad: str | None, depto: str | None):
    """Nombres aceptados (y alias) del nivel pedido, en la forma normalizada que usa _buscar."""
    if nivel == "nombre_ciudad":
        return {gd.norm(c): c for c in gd.lista_ciudades()}, None
    if nivel == "ciudad":
        return opciones_division(ciudad), None
    if nivel == "region":
        return {gd.norm(r): r for r in gd.REGIONES_NATURALES}, None
    if nivel == "municipio":
        munis = gd.lista_municipios([depto]).municipio
        return ({gd.norm(m): m for m in munis}, {k: v for (dd, k), v in gd.ALIAS_MUNI.items() if dd == depto})
    return {gd.norm(x): x for x in gd.lista_departamentos()}, gd.ALIAS_DEPTO


def revisar_lugar(nivel: str, texto, ciudad: str | None = None, depto=None) -> tuple[bool, str | None]:
    """Dice si un nombre ya es el oficial (o un alias) y, si no, el más cercano.

    nivel: 'departamento', 'municipio', 'region', 'ciudad' (localidad o comuna) o 'nombre_ciudad'.
    Devuelve (exacto, sugerencia); la sugerencia es None si nada se parece."""
    if nivel == "municipio":
        depto, _ = _buscar(depto, *_opciones_lugar("departamento", None, None))
        if depto is None:
            return True, None            # el departamento se revisa aparte
    opciones, alias = _opciones_lugar(nivel, ciudad, depto)
    k = gd.norm(texto)
    if k in opciones or (alias and k in alias):
        return True, None
    oficial, sug = _buscar(texto, opciones, alias)
    return False, oficial or sug


def _func(agregar):
    """Función de agregación; la suma deja vacío (no 0) cuando ningún valor viene lleno."""
    if agregar == "suma":
        return lambda x: x.sum(min_count=1)
    return {"promedio": "mean", "máximo": "max", "último": "last"}[agregar]


def _con_zona(base: pd.DataFrame) -> pd.Series:
    if "grupo" not in base:
        return pd.Series(False, index=base.index)
    g = base.grupo.astype("string").str.strip()
    return g.notna() & (g != "") & (g.str.lower() != "nan")


def opciones_division(ciudad: str) -> dict[str, str]:
    """Formas de escribir cada localidad o comuna: 'Comuna 14 - El Poblado', 'Comuna 14', 'El Poblado' o '14'."""
    ops = {}
    for d in gd.ciudades().query("ciudad == @ciudad").division:
        ops[gd.norm(d)] = d
        m = re.match(r"Comuna (\d+)\s*-\s*(.+)", d)
        if m:
            ops[gd.norm(f"Comuna {m.group(1)}")] = d
            ops[m.group(1)] = d
            ops.setdefault(gd.norm(m.group(2)), d)
        m = re.fullmatch(r"Comuna (\d+)", d)
        if m:
            ops[m.group(1)] = d
        if d.startswith("Corregimiento "):
            ops.setdefault(gd.norm(d.replace("Corregimiento ", "")), d)
    return ops


def emparejar_ciudad(df: pd.DataFrame, ciudad: str, col_division, col_valor, col_grupo=None,
                     agregar="suma") -> Emparejado:
    func = _func(agregar)
    buscar = _buscador(opciones_division(ciudad))
    etiqueta = gd.tipo_division(ciudad)
    filas, malas = [], []
    grupos = df[col_grupo].tolist() if col_grupo else [None] * len(df)
    for div, val, grp in zip(df[col_division].tolist(), df[col_valor].tolist(), grupos, strict=True):
        v = _a_float(val)
        z = col_grupo and pd.notna(grp) and str(grp).strip() not in ("", "nan")
        if pd.isna(div) or (pd.isna(v) and not z):
            continue
        x = str(div).strip()
        x = x[:-2] if x.endswith(".0") else x
        d, sug = buscar(x)
        if d is None:
            malas.append({etiqueta: div, "Problema": f"{etiqueta} no encontrada", "Sugerencia": sug or "-"})
            continue
        filas.append({"division": d, "valor": v, **({"grupo": str(grp).strip() if pd.notna(grp) else ""} if col_grupo else {})})
    t = pd.DataFrame(filas, columns=["division", "valor"] + (["grupo"] if col_grupo else []))
    dup = int(t.duplicated("division").sum())
    agg = {"valor": func, **({"grupo": "first"} if col_grupo else {})}
    return Emparejado(_sin_infinitos(t.groupby("division", as_index=False, sort=False).agg(agg)), malas, dup)


def _sin_infinitos(t: pd.DataFrame) -> pd.DataFrame:
    """Una suma que desborda deja el lugar sin dato (NaN) en vez de infinito."""
    if "valor" in t and len(t):
        t["valor"] = t["valor"].where(np.isfinite(t["valor"].astype(float)))
    return t


def _emparejar_region(df, col_depto, col_valor, col_grupo, agregar, col_region) -> Emparejado:
    func = _func(agregar)
    malas = []
    base = pd.DataFrame({"valor": a_numero(df[col_valor])})
    if col_grupo:
        base["grupo"] = df[col_grupo].astype("string").str.strip()
    if col_region:
        base["in"] = df[col_region]
        buscar = _buscador({gd.norm(r): r for r in gd.REGIONES_NATURALES})
        etiqueta = "Región"
    else:
        base["in"] = df[col_depto]
        buscar_d = _buscador({gd.norm(d): d for d in gd.lista_departamentos()}, gd.ALIAS_DEPTO)
        etiqueta = "Departamento"

        def buscar(x):
            d, sug = buscar_d(x)
            return (gd.REGION_DE.get(d), None) if d else (None, sug)
    base = base[base["in"].notna() & (base.valor.notna() | _con_zona(base))]
    filas = []
    grupos = base["grupo"].tolist() if col_grupo else [None] * len(base)
    for lugar, valor, grp in zip(base["in"].tolist(), base["valor"].tolist(), grupos, strict=True):
        reg, sug = buscar(lugar)
        if reg is None:
            malas.append({etiqueta: lugar, "Problema": f"{etiqueta} no encontrado", "Sugerencia": sug or "-"})
            continue
        filas.append({"region": reg, "valor": valor, **({"grupo": grp} if col_grupo else {})})
    t = pd.DataFrame(filas, columns=["region", "valor"] + (["grupo"] if col_grupo else []))
    dup = int(t.duplicated("region").sum())
    agg = {"valor": func if col_region else _func("suma"), **({"grupo": "first"} if col_grupo else {})}
    return Emparejado(_sin_infinitos(t.groupby("region", as_index=False, sort=False).agg(agg)), malas, dup)


def _emparejar_lugares(df, col_depto, col_valor, col_muni, col_grupo, nivel, agregar) -> Emparejado:
    func = _func(agregar)
    malas = []
    base = pd.DataFrame({"departamento_in": df[col_depto], "valor": a_numero(df[col_valor])})
    if col_muni:
        base["municipio_in"] = df[col_muni]
    if col_grupo:
        base["grupo"] = df[col_grupo].astype("string").str.strip()
    base = base[base.departamento_in.notna() & (base.valor.notna() | _con_zona(base))]

    buscar_d = _buscador({gd.norm(d): d for d in gd.lista_departamentos()}, gd.ALIAS_DEPTO)
    buscadores_muni = {}  # buscador de municipios por departamento
    filas = []
    n = len(base)
    munis = base["municipio_in"].tolist() if col_muni else [""] * n
    grupos = base["grupo"].tolist() if col_grupo else [None] * n
    for dep_in, muni_in, valor, grp in zip(base.departamento_in.tolist(), munis, base.valor.tolist(), grupos, strict=True):
        d, sug = buscar_d(dep_in)
        if d is None:
            malas.append({"Departamento": dep_in, "Municipio": muni_in, "Problema": "Departamento no encontrado",
                          "Sugerencia": sug or "-"})
            continue
        fila = {"departamento": d, "valor": valor}
        if col_grupo:
            fila["grupo"] = grp
        if nivel == "municipio":
            if not col_muni or pd.isna(muni_in):
                malas.append({"Departamento": d, "Municipio": "", "Problema": "Falta el municipio", "Sugerencia": "-"})
                continue
            if d not in buscadores_muni:
                buscadores_muni[d] = _buscador({gd.norm(m): m for m in gd.lista_municipios([d]).municipio},
                                               {k: v for (dd, k), v in gd.ALIAS_MUNI.items() if dd == d})
            m, sug = buscadores_muni[d](muni_in)
            if m is None:
                malas.append({"Departamento": d, "Municipio": muni_in, "Problema": "Municipio no encontrado",
                              "Sugerencia": sug or "-"})
                continue
            fila["municipio"] = m
        filas.append(fila)

    return _agrupar_lugares(filas, malas, nivel, col_grupo, func)


def _agrupar_lugares(filas: list, malas: list, nivel: str, col_grupo, func) -> Emparejado:
    """Suma (o resume) las filas que caen en el mismo lugar."""
    llave = ["departamento"] + (["municipio"] if nivel == "municipio" else [])
    cols = llave + ["valor"] + (["grupo"] if col_grupo else [])
    t = pd.DataFrame(filas, columns=cols)
    if t.empty:
        return Emparejado(t, malas, 0)
    dup = int(t.duplicated(llave).sum())
    agg = {"valor": func, **({"grupo": "first"} if col_grupo else {})}
    return Emparejado(_sin_infinitos(t.groupby(llave, as_index=False, sort=False).agg(agg)), malas, dup)


def emparejar(df: pd.DataFrame, col_depto, col_valor, col_muni=None, col_grupo=None,
              nivel="departamento", agregar="suma", col_region=None) -> Emparejado:
    """Convierte la tabla a nombres oficiales (nivel: departamento, municipio o region)."""
    if nivel == "region":
        return _emparejar_region(df, col_depto, col_valor, col_grupo, agregar, col_region)
    return _emparejar_lugares(df, col_depto, col_valor, col_muni, col_grupo, nivel, agregar)


def plantilla(nivel="departamento", deptos: list[str] | None = None, aleatorio=False, semilla=7,
              municipios: list[str] | None = None, regiones: list[str] | None = None,
              ciudad: str | None = None, rural=True, divisiones: list[str] | None = None,
              isla=False) -> pd.DataFrame:
    """Tabla lista para llenar: una fila por lugar del área. `municipios`: claves "Departamento|Municipio"."""
    rng = np.random.default_rng(semilla)
    if nivel == "municipio":
        t = gd.lista_municipios(deptos or None).rename(columns={"departamento": "Departamento", "municipio": "Municipio"})
        if municipios:
            t = t[(t.Departamento + "|" + t.Municipio).isin(set(municipios))].reset_index(drop=True)
    elif nivel == "region":
        t = pd.DataFrame({"Región": regiones or gd.lista_regiones()})
    elif nivel == "ciudad":
        c = gd.ciudades()
        c = c[(c.ciudad == ciudad) & (rural | ~c.rural)]
        if divisiones:
            c = c[c.division.isin(divisiones)]
        t = pd.DataFrame({"Localidad o comuna": c.division.tolist()})
    else:
        t = pd.DataFrame({"Departamento": deptos or gd.lista_departamentos(incluir_insular=isla)})
    if aleatorio:
        # valores con cola larga, como en datos reales
        t["Valor"] = np.round(rng.lognormal(mean=4.0, sigma=1.0, size=len(t)), 1)
    else:
        t["Valor"] = np.nan
    t["Segmento"] = ""
    return t
