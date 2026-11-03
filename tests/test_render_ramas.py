"""Ramas del dibujo que las pruebas generales no recorren: subrayados, límites, caídas de respaldo y combinaciones raras."""
import logging

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Point, Polygon

import mapacalor as mc
from mapacalor import datos as dt
from mapacalor import geodatos as gd
from interfaz.constantes import TIPOGRAFIAS
from mapacalor import render

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402  (mapacalor fija el backend antes)
import threading
from shapely.geometry import box  # noqa: E402

PALETA = ["#C0392B", "#2E86C1", "#28B463", "#D4AC0D"]


def con_segmentos(nivel="departamento", **kw):
    pl = dt.plantilla(nivel, aleatorio=True, semilla=3, **kw)
    pl["Segmento"] = ["A" if i % 3 == 0 else ("B" if i % 3 == 1 else "C") for i in range(len(pl))]
    if nivel == "municipio":
        return dt.emparejar(pl, "Departamento", "Valor", col_muni="Municipio", nivel="municipio", col_grupo="Segmento").tabla
    return dt.emparejar(pl, "Departamento", "Valor", col_grupo="Segmento").tabla


def dibuja(tabla, **kw):
    fig, info = mc.dibujar(tabla, mc.Estilo(dpi=40, **kw))
    plt.close(fig)
    return info


ZONAS = {"A": PALETA[0], "B": PALETA[1], "C": PALETA[2]}


def test_resumen_vacio_y_escalas_sin_datos():
    assert render.calcular_resumen(render.preparar(None, mc.Estilo()), mc.Estilo(resumen=True)) is None
    assert render._indices_tono(pd.Series([], dtype=float), 8, "raiz").empty
    assert dibuja(con_segmentos(), escala="lineal")["con_dato"] > 0


def test_textos_vacios_y_contornos_vacios():
    fig, ax = plt.subplots()
    render._subrayar(fig, [fig.text(0.1, 0.1, ""), fig.text(0.2, 0.2, "texto")])
    render._contorno_interior(ax, None, "#000000", 1)
    render._contorno_interior(ax, Polygon(), "#000000", 1)
    plt.close(fig)


def test_cache_de_uniones_descarta_la_mas_antigua(monkeypatch):
    monkeypatch.setattr(render, "_UNIONES", {(str(i), 0.0): None for i in range(61)})
    deptos = gd.departamentos().head(2)
    render._unir(deptos)
    assert ("0", 0.0) not in render._UNIONES and len(render._UNIONES) <= 63


def test_precalentar_resto_registra_el_fallo(monkeypatch, caplog):
    monkeypatch.setattr(gd, "regiones", lambda: (_ for _ in ()).throw(RuntimeError("fallo de prueba")))
    with caplog.at_level(logging.ERROR):
        render.precalentar_resto()
        for hilo in threading.enumerate():
            if hilo.name == "precalentar":
                hilo.join(timeout=30)
    assert "No se pudo precalentar" in caplog.text


def test_centro_de_una_geometria_sin_polo():
    assert render._centro(Point(1, 1)).equals(Point(1, 1))


def test_agrupar_por_lugar_en_municipios_y_zona_valor_global():
    assert dibuja(con_segmentos("municipio", deptos=["Quindío"]), nivel="municipio", deptos=["Quindío"], relleno="zona",
                  grupos_geo="lugar", colores_zona={"Armenia (Quindío)": PALETA[0]})["unidades"] > 0
    assert dibuja(con_segmentos(), relleno="zona_valor", colores_zona=ZONAS)["unidades"] > 0


def test_encuadre_del_pais_con_la_isla_elegida():
    tabla = dt.emparejar(dt.plantilla("departamento", aleatorio=True, semilla=3), "Departamento", "Valor").tabla
    assert dibuja(tabla, deptos=[gd.ISLA_INSULAR, "Boyacá"], encuadre="pais")["unidades"] > 0


def test_lista_de_zonas_arriba_y_contornos_de_grupo():
    tabla = con_segmentos()
    for pos in ("arriba", "abajo"):
        dibuja(tabla, relleno="zona_total", etiquetas="ranking", ranking_pos=pos, top_n=3)
    dibuja(tabla, relleno="zona", colores_zona=ZONAS, colores_grupo={"A": "#000000"}, contorno_grupo_grosor=2)


def test_ranking_omite_el_archipielago_en_el_mapa():
    tabla = dt.emparejar(dt.plantilla("departamento", aleatorio=True, semilla=3, isla=True), "Departamento", "Valor").tabla
    tabla.loc[tabla.departamento == gd.ISLA_INSULAR, "valor"] = tabla.valor.max() * 10
    assert dibuja(tabla, etiquetas="ranking", ranking_modo="mapa", top_n=3)["con_dato"] > 0


@pytest.mark.parametrize("kw", [
    dict(etiquetas="valor", estilo_etiquetas=["subrayado"]),
    dict(subtitulo="Subtítulo", estilo_subtitulo=["subrayado"]),
    dict(estilo_leyenda=["subrayado"]),
    dict(estilo_extremos=["subrayado"], estilo_extremos_der=["subrayado"]),
    dict(relleno="zona", colores_zona=ZONAS, estilo_leyenda=["subrayado"]),
    dict(ampliar=["Quindío", "Risaralda"], estilo_amp=["subrayado"]),
])
def test_textos_subrayados(kw):
    assert dibuja(con_segmentos(), **kw)["unidades"] > 0


def test_barra_de_escala_centrada_y_lupa_sin_lugares():
    x0, y0, largo, alto, km = render._medidas_barra((0, 200_000), (0, 150_000), "inf-cen")
    assert x0 == 100_000 - largo / 2 and km > 0
    assert dibuja(con_segmentos(), ampliar=["Lugar que no existe"])["ampliacion"] is None


def test_nombres_largos_se_recortan_en_la_lista():
    tabla = con_segmentos("municipio", deptos=["Antioquia", "Cundinamarca"])
    info = dibuja(tabla, nivel="municipio", deptos=["Antioquia", "Cundinamarca"], etiquetas="ranking",
                  ranking_modo="lista", ranking_pos="derecha", tam_lista=14, top_n=15)
    assert info["con_dato"] > 0


def test_minimapa_sin_esquina_libre_usa_la_primera_disponible():
    pais = gd.departamentos()
    xlim, ylim = (0.0, 1_000_000.0), (0.0, 800_000.0)
    cubre_todo = gpd.GeoDataFrame({"fill": ["#C0392B"]}, geometry=[box(-10, -10, 1_000_010, 800_010)], crs=gd.CRS)
    fig, ax = plt.subplots()
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    esquina = render._minimapa(ax, pais, cubre_todo, xlim, ylim, 6.0, 4.5, mc.Estilo(minimapa_pos="auto"), evitar="sup-der")
    plt.close(fig)
    assert esquina is not None


def test_municipio_nuevo_fuera_de_su_departamento_se_ignora(monkeypatch, tmp_path):
    lejos = gpd.GeoDataFrame({"departamento": ["Cauca"], "municipio": ["Lejos"]},
                             geometry=[Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])], crs=gd.CRS)
    archivo = tmp_path / "nuevos.geojson"
    lejos.to_file(archivo, driver="GeoJSON")
    monkeypatch.setattr(gd, "NUEVOS_GEOJSON", archivo)
    base = gd.municipios().copy()
    assert len(gd._con_municipios_nuevos(base)) == len(base)


def test_tipografia_propia_y_muchos_grupos():
    assert dibuja(con_segmentos(), titulo="Título", tipo_titulo="georgia", fuente="times")["unidades"] > 0
    tabla = con_segmentos()
    tabla["grupo"] = [f"G{i}" for i in range(len(tabla))]
    colores = {g: PALETA[i % 4] for i, g in enumerate(tabla["grupo"])}
    assert dibuja(tabla, relleno="zona", colores_zona=colores)["unidades"] > 0


def test_firma_en_la_esquina_inferior_derecha_segun_el_idioma():
    for idioma, texto in (("es", "Por Ft."), ("en", "By Ft.")):
        fig, _ = mc.dibujar(None, mc.Estilo(dpi=60, idioma=idioma, fuente_nota="Fuente: prueba", resumen=False))
        fig.canvas.draw()
        render_ = fig.canvas.get_renderer()
        firma = [t for t in fig.texts if t.get_text() == texto]
        assert len(firma) == 1
        caja = firma[0].get_window_extent(render_)
        ancho, alto = fig.canvas.get_width_height()
        assert caja.x1 <= ancho and caja.y0 >= 0 and caja.x0 > ancho / 2 and caja.y1 < alto * 0.1
        otros = [t for t in fig.texts if t is not firma[0] and t.get_text().strip()]
        assert not any(t.get_window_extent(render_).overlaps(caja) for t in otros)
        plt.close(fig)


def test_firma_tenue_sobre_fondo_claro_y_oscuro():
    for fondo in ("#FFFFFF", "#10161F"):
        fig, _ = mc.dibujar(None, mc.Estilo(dpi=40, color_fondo=fondo))
        firma = next(t for t in fig.texts if t.get_text() == "Por Ft.")
        r, g, b = (int(firma.get_color()[i:i + 2], 16) for i in (1, 3, 5))
        f = tuple(int(fondo[i:i + 2], 16) for i in (1, 3, 5))
        assert max(abs(r - f[0]), abs(g - f[1]), abs(b - f[2])) < 80      # casi del color del fondo
        plt.close(fig)


def test_tipografia_manuscrita_disponible_para_los_textos():
    assert TIPOGRAFIAS["Great Vibes"] == "firma" and "firma" in render.FUENTES
    assert any(f.name == "Great Vibes" for f in font_manager.fontManager.ttflist)
    assert dibuja(None, titulo="Título", tipo_titulo="firma", subtitulo="Sub", tipo_subtitulo="firma")["unidades"] > 0
