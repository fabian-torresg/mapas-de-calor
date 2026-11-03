"""Pruebas del motor (sin interfaz): python -m pytest tests"""
import io
import json
import time
import zipfile

import numpy as np
import pandas as pd
import pytest

import mapacalor as mc
from mapacalor import datos as dt
from mapacalor import geodatos as gd
from mapacalor import render
from mapacalor.render import exportar, exportar_geojson

import matplotlib.colors as mcolors  # noqa: E402  (mapacalor fija el backend antes)
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402
from shapely import STRtree  # noqa: E402


def ancho_encuadre(fig) -> float:
    """Ancho, en metros, de la zona que muestra el mapa."""
    x0, x1 = fig.axes[0].get_xlim()
    return x1 - x0


def test_geometrias():
    assert len(gd.municipios()) == 1123
    assert len(gd.departamentos()) == 33


def test_emparejar_nombres_imperfectos():
    df = pd.DataFrame({"Depto": ["CUNDINAMARCA", "valle", "Bogota"], "Ciudad": ["CHIA", "Cali", "BOGOTA"],
                       "Ventas": ["1.234", "2,5", "10"]})
    em = mc.emparejar(df, "Depto", "Ventas", col_muni="Ciudad", nivel="municipio")
    assert set(em.tabla.municipio) == {"Chía", "Santiago de Cali", "Bogotá D.C."}
    assert em.tabla.valor.tolist() == [1234.0, 2.5, 10.0]


def test_sugerencia():
    em = mc.emparejar(pd.DataFrame({"Departamento": ["Antioqia"], "Valor": [1]}), "Departamento", "Valor")
    assert em.sin_match[0]["Sugerencia"] == "Antioquia"


def test_dibujar():
    t = mc.plantilla("municipio", ["Quindío"], aleatorio=True)
    em = mc.emparejar(t, "Departamento", "Valor", col_muni="Municipio", nivel="municipio")
    fig, info = mc.dibujar(em.tabla, mc.Estilo(nivel="municipio", deptos=["Quindío"], etiquetas="ranking"))
    assert info["con_dato"] == info["unidades"] == 12
    assert mc.exportar(fig, "png")[:4] == b"\x89PNG"


def test_regiones_y_municipios_sueltos():
    d = mc.plantilla("departamento", aleatorio=True)
    em = mc.emparejar(d, "Departamento", "Valor", nivel="region")   # suma departamentos por región
    assert set(em.tabla.region) == set(gd.lista_regiones())
    fig, info = mc.dibujar(em.tabla, mc.Estilo(nivel="region", encuadre="pais"))
    assert info["unidades"] == 5
    sel = ["Cundinamarca|Chía", "Cundinamarca|Cajicá"]
    t = mc.plantilla("municipio", ["Cundinamarca"], aleatorio=True, municipios=sel)
    em = mc.emparejar(t, "Departamento", "Valor", col_muni="Municipio", nivel="municipio")
    fig, info = mc.dibujar(em.tabla, mc.Estilo(nivel="municipio", deptos=["Cundinamarca"], municipios=sel))
    assert info["unidades"] == 2 and info["minimapa"]


def test_municipios_con_y_sin_departamento_completo():
    estilo = dict(nivel="municipio", deptos=["Boyacá"], municipios=["Boyacá|Tunja", "Boyacá|Duitama"])
    completo, _ = mc.dibujar(None, mc.Estilo(**estilo, mostrar_depto_completo=True))
    solo, info = mc.dibujar(None, mc.Estilo(**estilo, mostrar_depto_completo=False))
    assert info["unidades"] == 2
    assert ancho_encuadre(solo) < ancho_encuadre(completo) / 3      # solo los elegidos: el mapa se acerca


def test_ciudades_y_ampliacion():
    assert len(gd.lista_ciudades()) == 22
    df = pd.DataFrame({"Comuna": ["14", "Comuna 11", "Belen"], "Valor": [5, 3, 2]})
    em = dt.emparejar_ciudad(df, "Medellín", "Comuna", "Valor")
    assert set(em.tabla.division) == {"Comuna 14 - El Poblado", "Comuna 11 - Laureles-Estadio", "Comuna 16 - Belén"}
    fig, info = mc.dibujar(em.tabla, mc.Estilo(nivel="ciudad", ciudad="Medellín", ciudad_rural=False))
    assert info["unidades"] == 16
    t = mc.plantilla("municipio", ["Cundinamarca"], aleatorio=True)
    em = mc.emparejar(t, "Departamento", "Valor", col_muni="Municipio", nivel="municipio")
    fig, info = mc.dibujar(em.tabla, mc.Estilo(nivel="municipio", deptos=["Cundinamarca"], ampliar=["Chía", "Cota"]))
    assert info["ampliacion"] == "lupa"                     # la lupa va sobre los lugares elegidos, no en una esquina
    fig, info = mc.dibujar(em.tabla, mc.Estilo(nivel="municipio", deptos=["Cundinamarca"], ampliar=["Chía", "Cota"],
                                               ampliar_forma="redonda", etiquetas="nombre_valor", valor_junto="parentesis"))
    assert info["ampliacion"] == "lupa"


def test_ciudad_con_lugares_elegidos():
    lugares = ["Comuna 10 - La Candelaria", "Comuna 14 - El Poblado"]
    assert len(mc.plantilla("ciudad", ciudad="Medellín", divisiones=lugares)) == 2
    estilo = dict(nivel="ciudad", ciudad="Medellín", divisiones=lugares)
    completa, info = mc.dibujar(None, mc.Estilo(**estilo, mostrar_depto_completo=True))
    solo, _ = mc.dibujar(None, mc.Estilo(**estilo, mostrar_depto_completo=False))
    assert info["unidades"] == 2
    assert ancho_encuadre(solo) < ancho_encuadre(completa)
    # un corregimiento se puede elegir con la zona rural apagada en "todas"
    rural = [d for d in gd.ciudades().query("ciudad == 'Medellín'").division if d.startswith("Corregimiento")][:1]
    _, info = mc.dibujar(None, mc.Estilo(nivel="ciudad", ciudad="Medellín", divisiones=rural, ciudad_rural=True))
    assert info["unidades"] == 1


def test_san_andres_en_todo_el_pais():
    t = mc.plantilla("departamento", aleatorio=True, isla=True)
    assert len(t) == 33 and gd.ISLA_INSULAR in set(t.Departamento)
    em = mc.emparejar(t, "Departamento", "Valor", nivel="departamento")
    fig, info = mc.dibujar(em.tabla, mc.Estilo(nivel="departamento"))
    assert info["unidades"] == 33 and info["fuera_del_area"] == 0
    assert len(mc.plantilla("departamento")) == 32
    fig, info = mc.dibujar(em.tabla, mc.Estilo(nivel="departamento", mostrar_isla=False))
    assert info["unidades"] == 32 and info["fuera_del_area"] == 1       # la fila de la isla queda fuera
    # con departamentos elegidos no se dibuja el archipiélago
    fig, info = mc.dibujar(None, mc.Estilo(nivel="departamento", deptos=["Boyacá"]))
    assert info["unidades"] == 1


def test_relleno_por_zona():
    t = mc.plantilla("municipio", ["Quindío"])
    t["Zona"] = ["Ana"] * 6 + ["Luis"] * 6            # sin valores: solo zonas
    em = mc.emparejar(t, "Departamento", "Valor", col_muni="Municipio", col_grupo="Zona", nivel="municipio")
    assert len(em.tabla) == 12 and em.tabla.valor.isna().all()
    fig, info = mc.dibujar(em.tabla, mc.Estilo(nivel="municipio", deptos=["Quindío"], relleno="zona",
                                               colores_zona={"Ana": "#F28C28", "Luis": "#2D9CDB"}))
    assert info["con_dato"] == 12


def test_calor_por_zona_y_estilos():
    t = mc.plantilla("municipio", ["Quindío"], aleatorio=True)
    t["Zona"] = ["Ana"] * 6 + ["Luis"] * 6
    em = mc.emparejar(t, "Departamento", "Valor", col_muni="Municipio", col_grupo="Zona", nivel="municipio")
    fig, info = mc.dibujar(em.tabla, mc.Estilo(nivel="municipio", deptos=["Quindío"], relleno="zona_total",
                                               etiquetas="ranking", titulo="T", estilo_titulo=["negrita", "subrayado"],
                                               estilo_etiquetas=["cursiva"]))
    assert info["con_dato"] == 12
    assert mc.exportar(fig, "svg")[:5] in (b"<?xml", b"<svg ")


@pytest.mark.parametrize("fuente", ["arial", "calibri", "times", "georgia"])
def test_tipografias(fuente):
    fig, info = mc.dibujar(None, mc.Estilo(nivel="departamento", deptos=["Boyacá"], fuente=fuente, titulo="Título"))
    assert info["unidades"] == 1


def test_fondo_oscuro_cambia_los_textos():
    assert render._txt(mc.Estilo(color_fondo="#0B1622"))["titulo"] != render._txt(mc.Estilo())["titulo"]
    fig, info = mc.dibujar(None, mc.Estilo(nivel="departamento", color_fondo="#0B1622", titulo="Oscuro"))
    assert info["unidades"] == 33


def test_colores_distintos_sin_repetir_entre_vecinos():
    paleta = mc.paletas.PALETAS_CATEGORIAS["Vivos"]
    e = mc.Estilo(nivel="departamento", grupos_geo="lugar", mostrar_isla=False)
    colores = mc.categorias(None, e, paleta)
    # con más grupos que colores, el motor completa la paleta empezando por los suyos
    assert len(colores) == 32 and set(paleta) <= set(colores.values())
    d = gd.departamentos().query("departamento != @gd.ISLA_INSULAR").reset_index(drop=True)
    geoms = list(d.geometry.buffer(150))
    a, b = STRtree(geoms).query(geoms, predicate="intersects")
    assert all(colores[d.departamento[i]] != colores[d.departamento[j]] for i, j in zip(a, b, strict=False) if i < j)
    assert colores != mc.categorias(None, e, paleta, semilla=3)          # barajar cambia el reparto


def test_colorear_por_departamento_y_por_region():
    paleta = mc.paletas.PALETAS_CATEGORIAS["Suaves"]
    sel = dict(nivel="municipio", deptos=["Boyacá", "Santander"])
    colores = mc.categorias(None, mc.Estilo(**sel, grupos_geo="departamento"), paleta)
    assert set(colores) == {"Boyacá", "Santander"} and colores["Boyacá"] != colores["Santander"]
    fig, info = mc.dibujar(None, mc.Estilo(**sel, grupos_geo="departamento", relleno="zona", colores_zona=colores))
    assert info["con_dato"] == info["unidades"]                         # cada municipio quedó en su grupo
    regiones = mc.categorias(None, mc.Estilo(nivel="departamento", grupos_geo="region"), paleta)
    assert set(regiones) == set(gd.lista_regiones(incluir_insular=True))


def test_paletas_de_valor_y_de_categorias():
    assert list(mc.paletas.PALETAS)[:2] == ["Mapa de calor", "Azul marino"]    # las dos primeras de la lista
    for nombre in mc.paletas.PALETAS:
        assert len(mc.paletas.tonos(mc.paletas.colores_base(nombre), 8)) == 8
    assert all(len(p) >= 8 for p in mc.paletas.PALETAS_CATEGORIAS.values())


def test_color_de_otros_paises_y_del_mar():
    e = dict(nivel="departamento", deptos=["Boyacá"], mostrar_vecinos=True, color_vecinos="#33AA33")
    fig, _ = mc.dibujar(None, mc.Estilo(**e, color_oceano="#3366CC"))
    mar = [p for p in fig.axes[0].patches if isinstance(p, Rectangle) and p.get_zorder() == -5]
    assert len(mar) == 1 and mar[0].get_facecolor()[:3] == pytest_approx_color("#3366CC")
    fig, _ = mc.dibujar(None, mc.Estilo(**e))                                  # sin color propio: el mar usa el fondo
    assert not [p for p in fig.axes[0].patches if isinstance(p, Rectangle) and p.get_zorder() == -5]


def pytest_approx_color(hex_color):
    return mcolors.to_rgb(hex_color)


def test_exportar_jpg_tiff_y_geojson():
    fig, _ = mc.dibujar(None, mc.Estilo(nivel="departamento", dpi=60))
    assert exportar(fig, "jpg")[:2] == bytes([0xFF, 0xD8])
    assert exportar(fig, "tiff")[:2] in (b"II", b"MM")
    datos = json.loads(exportar_geojson(None, mc.Estilo(nivel="departamento", deptos=["Quindío"])))
    assert len(datos["features"]) == 1 and "color" in datos["features"][0]["properties"] and datos["attribution"]


def test_lectura_de_archivos_con_formatos_distintos():
    tabulado = b"Departamento\tValor\nAntioquia\t10\n"
    assert list(dt.leer_archivo("a.csv", tabulado).columns) == ["Departamento", "Valor"]
    df = dt.leer_archivo("a.csv", "Departamento,Valor\nBogotá D.C.,10\n".encode("latin-1"))
    assert df.iloc[0, 0] == "Bogotá D.C."                         # CSV guardado en Windows (cp1252)
    assert dt.leer_archivo("a.csv", b"Departamento;Valor\nCaldas;1,5\n").iloc[0, 1] == "1,5"


def test_archivo_danado_o_vacio_avisa_sin_romper():
    for nombre, contenido in (("a.csv", b""), ("a.xlsx", b"no es un excel")):
        with pytest.raises(dt.ArchivoInvalido):
            dt.leer_archivo(nombre, contenido)


# ---- auditoría: no finitos, límites de lectura, descarga de GADM y rendimiento
def test_infinitos_y_desbordes_no_son_datos():
    serie = dt.a_numero(pd.Series(["inf", "-inf", "infinity", "nan", "5", "1e999"]))
    assert serie.isna().tolist() == [True, True, True, True, False, True]
    assert dt.a_numero(pd.Series([np.inf, 2.0])).isna().tolist() == [True, False]
    # una suma que desborda deja el lugar sin dato en vez de infinito
    grande = pd.DataFrame({"Departamento": ["Cauca", "Cauca"], "Valor": [1.7e308, 1.7e308]})
    assert dt.emparejar(grande, "Departamento", "Valor").tabla.valor.isna().all()


def test_mapa_con_infinitos_se_dibuja():
    df = pd.DataFrame({"Departamento": ["Cauca", "Huila", "Nariño"], "Valor": ["inf", 5, -3]})
    tabla = dt.emparejar(df, "Departamento", "Valor").tabla
    fig, _ = mc.dibujar(tabla, mc.Estilo(nivel="departamento", dpi=40))
    plt.close(fig)


def test_limites_de_lectura(monkeypatch):
    monkeypatch.setattr(dt, "MAX_FILAS", 3)
    with pytest.raises(dt.ArchivoInvalido, match="filas"):
        dt.leer_archivo("a.csv", b"Departamento,Valor\n" + b"Cauca,1\n" * 4)
    assert len(dt.leer_archivo("a.csv", b"Departamento,Valor\n" + b"Cauca,1\n" * 3)) == 3
    monkeypatch.setattr(dt, "MAX_DESCOMPRIMIDO", 1000)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("xl/grande.xml", b"0" * 5000)                  # muy comprimible: ocupa poco y se expande mucho
    with pytest.raises(dt.ArchivoInvalido, match="demasiado grande"):
        dt.leer_archivo("a.xlsx", buf.getvalue())


def test_emparejar_con_muchas_filas_es_rapido():
    n = 50_000
    df = pd.DataFrame({"Departamento": np.random.choice(["Antioquia", "Cauca", "Boyacá", "Atlantis"], n), "Valor": 1.0})
    t0 = time.time()
    em = dt.emparejar(df, "Departamento", "Valor")
    assert time.time() - t0 < 5                                   # antes tardaba más de 10 s
    assert em.tabla.valor.sum() == (df.Departamento != "Atlantis").sum() and len(em.sin_match) == (df.Departamento == "Atlantis").sum()


def _zip_en_bytes() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("datos.json", "{}")
    return buf.getvalue()


class _Respuesta:
    def __init__(self, contenido: bytes, largo: int | None = None):
        self._buf, self.headers = io.BytesIO(contenido), {"Content-Length": str(len(contenido) if largo is None else largo)}

    def read(self, n=-1):
        return self._buf.read(n)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_gadm_danado_se_descarga_de_nuevo(tmp_path, monkeypatch):
    destino = tmp_path / "gadm.zip"
    destino.write_bytes(b"esto no es un zip")                      # copia truncada o dañada
    monkeypatch.setattr(gd.urllib.request, "urlopen", lambda *a, **k: _Respuesta(_zip_en_bytes()))
    assert gd.asegurar_gadm(destino) == destino and gd._zip_valido(destino)


def test_gadm_descarga_incompleta_o_invalida_falla_con_oserror(tmp_path, monkeypatch):
    monkeypatch.setattr(gd.time, "sleep", lambda s: None)
    monkeypatch.setattr(gd.urllib.request, "urlopen", lambda *a, **k: _Respuesta(_zip_en_bytes(), largo=10_000))
    with pytest.raises(OSError, match="incompleta"):
        gd.asegurar_gadm(tmp_path / "a.zip", intentos=2)
    monkeypatch.setattr(gd.urllib.request, "urlopen", lambda *a, **k: _Respuesta(b"basura sin formato"))
    with pytest.raises(OSError, match="no es válido"):
        gd.asegurar_gadm(tmp_path / "b.zip", intentos=1)
    assert not (tmp_path / "a.zip").exists() and not (tmp_path / "b.zip").exists()


def test_gadm_ilegible_se_descarta_y_avisa_con_oserror(tmp_path, monkeypatch):
    malo = tmp_path / "gadm.zip"
    malo.write_bytes(_zip_en_bytes())                              # zip válido, pero sin una capa geográfica
    monkeypatch.setattr(gd, "asegurar_gadm", lambda *a, **k: malo)
    with pytest.raises(OSError, match="GADM"):
        gd._leer_gadm()
    assert not malo.exists()


def test_dibujar_ignora_infinitos_aunque_la_tabla_no_pase_por_emparejar():
    tabla = pd.DataFrame({"departamento": ["Cauca", "Huila", "Nariño"], "valor": [np.inf, -np.inf, 4.0]})
    fig, _ = mc.dibujar(tabla, mc.Estilo(nivel="departamento", dpi=40))
    plt.close(fig)
