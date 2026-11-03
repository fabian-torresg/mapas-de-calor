"""Ramas poco frecuentes del motor y de la interfaz: errores, casos límite y combinaciones del dibujo."""
import io

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

import mapacalor as mc
from mapacalor import datos as dt
from mapacalor import geodatos as gd
from mapacalor import paletas as pal

import matplotlib.pyplot as plt  # noqa: E402  (mapacalor fija el backend antes)
from mapacalor.render import categorias, exportar_geojson  # noqa: E402


# ---- datos
def test_valor_se_detecta_por_ser_la_primera_columna_numerica():
    det = dt.detectar_columnas(pd.DataFrame({"Departamento": ["Cauca"], "Cosa": [3]}))
    assert det["departamento"] == "Departamento" and det["valor"] == "Cosa"
    assert dt.detectar_columnas(pd.DataFrame({"Departamento": ["Cauca"]}))["valor"] is None


def test_excel_sin_columnas_y_hoja_inexistente_avisan():
    import openpyxl
    buf = io.BytesIO()
    openpyxl.Workbook().save(buf)
    with pytest.raises(dt.ArchivoInvalido):
        dt.leer_archivo("a.xlsx", buf.getvalue())
    with pytest.raises(dt.ArchivoInvalido):
        dt.leer_archivo("a.xlsx", buf.getvalue(), hoja="no existe")
    with pytest.raises(dt.ArchivoInvalido):
        dt.hojas_excel("a.xlsx", b"no es un excel")


@pytest.mark.parametrize("texto,esperado", [("1.234,56", 1234.56), ("1,234.56", 1234.56), ("1,5", 1.5), ("12%", 12.0),
                                            ("$ 1.000", 1000.0), ("abc", None), (None, None), (True, None)])
def test_conversion_de_celdas(texto, esperado):
    v = dt._a_float(texto)
    assert (np.isnan(v) if esperado is None else v == esperado)


def test_coincidencia_parcial_y_sugerencias():
    opciones = {gd.norm("El Carmen de Viboral"): "El Carmen de Viboral", gd.norm("Rionegro"): "Rionegro"}
    assert dt._buscar("Carmen de Viboral", opciones) == ("El Carmen de Viboral", None)
    assert dt._buscar("Rionegr", opciones) == ("Rionegro", None)
    assert dt._buscar("Rionero", opciones) == (None, "Rionegro")
    assert dt._buscar("zzz", opciones) == (None, None)


def test_revisar_lugar_en_cada_nivel():
    ciudad = gd.lista_ciudades()[0]
    assert dt.revisar_lugar("nombre_ciudad", ciudad)[0]
    assert dt.revisar_lugar("region", "Andina")[0]
    assert dt.revisar_lugar("departamento", "Antioqia")[1] == "Antioquia"
    assert dt.revisar_lugar("municipio", "Medellín", depto="Antioquia")[0]
    assert dt.revisar_lugar("municipio", "Medellín", depto="Atlantis") == (True, None)
    division = gd.ciudades().query("ciudad == @ciudad").division.iloc[0]
    assert dt.revisar_lugar("ciudad", division, ciudad=ciudad)[0]


def test_agregaciones_y_emparejamientos_con_problemas():
    assert dt._func("promedio") == "mean" and dt._func("suma")(pd.Series([1, 2])) == 3
    df = pd.DataFrame({"Depto": ["Cauca", "Atlantis", "Cauca"], "Muni": ["Popayán", "X", None], "Valor": [1, 2, 3]})
    em = dt.emparejar(df, "Depto", "Valor", col_muni="Muni", nivel="municipio")
    problemas = {m["Problema"] for m in em.sin_match}
    assert problemas == {"Departamento no encontrado", "Falta el municipio"}
    otro = pd.DataFrame({"Depto": ["Cauca"], "Muni": ["Zzz"], "Valor": [1]})
    assert dt.emparejar(otro, "Depto", "Valor", col_muni="Muni", nivel="municipio").sin_match[0]["Problema"] == "Municipio no encontrado"
    region = pd.DataFrame({"R": ["Andina", "Nada"], "V": [1, 2]})
    assert dt.emparejar(region, None, "V", nivel="region", col_region="R").sin_match[0]["Problema"] == "Región no encontrado"
    ciudad = gd.lista_ciudades()[0]
    div = gd.ciudades().query("ciudad == @ciudad").division.iloc[0]
    tabla = pd.DataFrame({"D": [div, "Nada", None, div], "V": [1, 2, 3, "x"]})
    em = dt.emparejar_ciudad(tabla, ciudad, "D", "V")
    assert len(em.tabla) == 1 and len(em.sin_match) == 1 and em.sin_match[0]["Problema"].endswith("no encontrada")


# ---- geodatos
def test_capas_opcionales_sin_archivo(monkeypatch, tmp_path):
    monkeypatch.setattr(gd, "NUEVOS_GEOJSON", tmp_path / "no.geojson")
    base = gd.municipios().head(3)
    assert gd._con_municipios_nuevos(base) is base
    monkeypatch.setattr(gd, "CIUDADES_GEOJSON", tmp_path / "no.geojson")
    monkeypatch.setattr(gd, "VECINOS_GEOJSON", tmp_path / "no.geojson")
    assert gd.ciudades.__wrapped__().empty
    assert gd.vecinos.__wrapped__().empty


def test_serranilla_se_suma_a_san_andres_y_sin_islotes():
    sin_serranilla = gd.municipios().head(3)
    assert gd._serranilla_en_san_andres(sin_serranilla) is sin_serranilla
    pequena = gd.municipios().geometry.iloc[0]
    assert gd._sin_islotes(None) is None and gd._sin_islotes(pequena) is not None


# ---- paletas
def test_paletas_auxiliares():
    assert pal.tonos(["#000000", "#FFFFFF"], 1) == ["#ffffff"]
    assert pal.oscurecer("#FF0000", 0.5) == "#800000"
    assert pal.rampa_un_color("#336699", fuerte=False)[0] == "#336699"
    vecinos = [{1, 2}, {0, 2}, {0, 1}]
    colores = pal.colorear_grafo(vecinos, ["#111111", "#222222"], semilla=1)
    assert len(colores) == 3 and len(set(colores[:2])) >= 1


# ---- estado de la sesión
def _guion_estado():
    import streamlit as st
    from interfaz.estado import fijar, iniciar_estado, restablecer_todo, sumar, subir_version
    iniciar_estado()
    sumar("n"); sumar("n")
    fijar("x", 5)
    st.session_state.tablas = {"a": 1}
    subir_version("expo")
    restablecer_todo()
    st.session_state["gen_datos"] = st.session_state.gen["datos"]


def test_funciones_de_estado():
    at = AppTest.from_function(_guion_estado).run()
    assert not at.exception
    assert at.session_state["n"] == 2 and at.session_state["x"] == 5
    assert "tablas" not in at.session_state and at.session_state["gen_datos"] == 1


# ---- textos y animación de carga
def test_rotulos_en_negrita_y_curva_de_carga():
    from interfaz.carga import _avance, mapa_cierre
    from interfaz.textos import rotulos_en_negrita
    assert rotulos_en_negrita("Total: 5 · Promedio: 2") == "**Total:** 5 · **Promedio:** 2"
    assert _avance(0) == 0 and _avance(5) < _avance(12) == 90 < _avance(30) <= 99 == _avance(100)
    assert "carga-fin" in mapa_cierre("Mapas de calor", 7)


# ---- dibujo: combinaciones poco comunes (solo comprueba que dibujan)
def _plantilla(nivel="departamento", **kw):
    pl = dt.plantilla(nivel, aleatorio=True, semilla=3, **kw)
    pl["Segmento"] = ["A" if i % 3 == 0 else ("B" if i % 3 == 1 else "C") for i in range(len(pl))]
    if nivel == "municipio":
        return dt.emparejar(pl, "Departamento", "Valor", col_muni="Municipio", nivel="municipio", col_grupo="Segmento").tabla
    return dt.emparejar(pl, "Departamento", "Valor", col_grupo="Segmento").tabla


ESTILOS = [
    dict(nivel="departamento", estilo_borde="espaciada", estilo_borde_depto="circulos", borde_grosor=2),
    dict(nivel="departamento", estilo_borde="puntos", contorno_area_color="#222222", estilo_contorno_area="guion_punto"),
    dict(nivel="departamento", resumen=True, resumen_items=["total", "promedio", "max_min", "mayores", "menores", "porcentaje"],
         resumen_n=3, decimales=2, sufijo=" %", estilo_resumen=["negrita", "subrayado"], tam_resumen=11),
    dict(nivel="departamento", etiquetas="ranking", ranking_pos="abajo", ranking_modo="lista", top_n=8, estilo_lista=["cursiva"]),
    dict(nivel="departamento", etiquetas="ranking", ranking_pos="arriba", top_n=12, tam_lista=8),
    dict(nivel="departamento", etiquetas="nombre_valor", valor_junto="parentesis", decimales=1),
    dict(nivel="departamento", etiquetas="valor", leyenda_extremos="valores", estilo_extremos_der=["cursiva"]),
    dict(nivel="departamento", escala="cuantiles", n_tonos=3, invertir=True, color_sin_dato="#EEEEEE"),
    dict(nivel="departamento", escala="log", relleno="zona_total", zona_agregar="promedio", etiquetas="ranking"),
    dict(nivel="departamento", relleno="zona_valor", zona_escala="por_zona", zona_rol="suave"),
    dict(nivel="departamento", idioma="en", titulo="T", subtitulo="S", fuente_nota="N", estilo_titulo=["subrayado"],
         estilo_subtitulo=["cursiva"], estilo_nota=["subrayado"], esp_titulo=4, esp_subtitulo=3, esp_nota=2, esp_leyenda=3),
    dict(nivel="departamento", deptos=["Boyacá"], minimapa=True, minimapa_pos="sup-izq", escala_km=True, norte=True),
    dict(nivel="departamento", deptos=["Boyacá", "Santander"], encuadre="pais", mostrar_vecinos=True, color_oceano="#CFE3F2"),
    dict(nivel="departamento", ampliar=["Quindío", "Risaralda"], ampliar_forma="redonda", ampliar_nombres=False, escala_km=True),
    dict(nivel="departamento", proporcion="vertical", ancho_pulgadas=5, mostrar_isla=False),
    dict(nivel="region", etiquetas="ranking", ranking_pos="izquierda", borde_depto_grosor=1),
    dict(nivel="municipio", deptos=["Cundinamarca"], municipios=["Cundinamarca|Chía", "Cundinamarca|Cajicá"],
         mostrar_depto_completo=True, etiquetas="nombre", color_vecinos="#DDDDDD", contorno_area_color="#000000"),
    dict(nivel="municipio", deptos=["Quindío"], relleno="zona", grupos_geo="departamento",
         colores_zona={"Quindío (Quindío)": "#C0392B"}),
]


@pytest.mark.parametrize("kw", ESTILOS, ids=[f"{i}-{k['nivel']}" for i, k in enumerate(ESTILOS)])
def test_dibuja_combinaciones_poco_comunes(kw):
    nivel = kw["nivel"]
    tabla = _plantilla("municipio", deptos=kw.get("deptos")) if nivel == "municipio" else (
        dt.emparejar(dt.plantilla("departamento", aleatorio=True, semilla=3), "Departamento", "Valor", nivel="region").tabla
        if nivel == "region" else _plantilla())
    if kw.get("relleno") in ("zona", "zona_valor", "zona_total") and nivel == "departamento":
        segmentos = list(dict.fromkeys(tabla["grupo"].dropna().astype(str)))
        kw = {**kw, "colores_zona": {s: ["#C0392B", "#2E86C1", "#28B463", "#D4AC0D", "#7D3C98"][i % 5] for i, s in enumerate(segmentos)}}
    fig, info = mc.dibujar(tabla, mc.Estilo(dpi=40, **kw))
    plt.close(fig)
    assert info["unidades"] > 0


def test_categorias_y_geojson_con_segmentos():
    tabla = _plantilla()
    paleta = ["#C0392B", "#2E86C1", "#28B463"]
    colores = categorias(tabla, mc.Estilo(nivel="departamento"), paleta, semilla=2)
    assert colores and set(colores.values()) <= set(pal.ampliar(paleta, len(colores)))
    assert categorias(None, mc.Estilo(nivel="departamento"), paleta) == {}
    datos = exportar_geojson(tabla, mc.Estilo(nivel="departamento"))
    assert b"features" in datos if isinstance(datos, bytes) else "features" in datos
