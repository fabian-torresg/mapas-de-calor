"""Prueba de la interfaz sin navegador: la app arranca y cada opción principal funciona.
"""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")


@pytest.fixture(scope="module")
def app():
    return AppTest.from_file(APP, default_timeout=300).run()


def errores(at):
    return [e.value for e in at.exception]


def elegir(at, clave, valor):
    next(w for w in at.sidebar.selectbox if w.key == clave).select(valor).run()


def test_arranca_sin_errores(app):
    assert errores(app) == []
    # tres bloques en la barra lateral y las tres pestañas del centro
    etiquetas = [t.label for t in app.tabs]
    assert {"Datos", "Diseño", "Exportación"} <= set(etiquetas)
    assert any("Tabla de datos" in e for e in etiquetas)
    assert [b.label for b in app.sidebar.get("download_button")][0].endswith("Descargar PNG")
    assert any("Por Fabián Torres" in m.value for m in app.sidebar.markdown)


def test_cada_nivel(app):
    for nivel in ("Regiones", "Departamentos", "Municipios", "Ciudades", "Todo el país"):
        elegir(app, "que__nivel_txt__0", nivel)
        assert errores(app) == [], nivel


def test_cada_plantilla(app):
    plantillas = next(w for w in app.sidebar.selectbox if w.key == "plantilla_sel").options
    assert len(plantillas) == 10
    for nombre in plantillas:
        elegir(app, "plantilla_sel", nombre)
        assert errores(app) == [], nombre


def test_en_ingles():
    # instancia propia: en AppTest, volver de EN a ES falla al comparar opciones
    at = AppTest.from_file(APP, default_timeout=300).run()
    at.segmented_control(key="idioma").set_value("EN").run()
    assert errores(at) == []
    assert any(t.label == "Design" for t in at.tabs)


def test_formatos_de_descarga(app):
    for formato in ("svg", "pdf", "jpg", "tiff", "png"):
        next(w for w in app.sidebar.selectbox if w.key.startswith("expo__formato")).select(formato).run()
        assert errores(app) == [], formato


def test_modos_de_color(app):
    def widget(tipo, prefijo):
        return next(w for w in app.sidebar.get(tipo) if w.key.startswith(prefijo))
    widget("selectbox", "colores__modo__").select("Colores distintos").run()
    assert errores(app) == []
    # la paleta se elige en una lista de botones (línea de colores y nombre)
    assert any(b.key.startswith("colores__pcat_d_lugar_op_") for b in app.sidebar.get("button"))
    widget("selectbox", "colores__modo__").select("Mapa de calor").run()
    assert errores(app) == []


def test_tabla_de_datos_es_una_seccion_de_datos(app):
    secciones = [e.label for e in app.sidebar.expander]
    assert any("Área geográfica" in s for s in secciones)
    # la tabla se abre con un botón, no con un acordeón
    assert "btn_tabla" in [b.key for b in app.sidebar.get("button")]
    assert any(c.label == "Países vecinos" for c in app.sidebar.color_picker)


def test_icono_de_la_guia_en_el_encabezado(app):
    claves = [b.key for b in app.sidebar.get("button")]
    assert "btn_guia" in claves and "rst_todo" in claves


def test_opciones_solo_se_ven_con_su_interruptor_activo():
    at = AppTest.from_file(APP, default_timeout=300).run()
    por_clave = lambda tipo, pre: next(w for w in getattr(at.sidebar, tipo) if w.key and w.key.startswith(pre))  # noqa: E731
    hay = lambda tipo, pre: any(w.key and w.key.startswith(pre) for w in getattr(at.sidebar, tipo))  # noqa: E731
    # la lupa y las etiquetas empiezan apagadas y sin controles
    assert not hay("selectbox", "amp__amp_forma") and not hay("selectbox", "etq__etq_txt")
    por_clave("toggle", "amp__amp_on").set_value(True).run()
    por_clave("toggle", "etq__etq_on").set_value(True).run()
    assert hay("selectbox", "amp__amp_forma") and hay("selectbox", "etq__etq_txt") and errores(at) == []
    # la leyenda apagada oculta sus textos
    assert hay("selectbox", "ley__extremos")
    por_clave("toggle", "ley__leyenda").set_value(False).run()
    assert not hay("selectbox", "ley__extremos") and errores(at) == []
    # el minimapa apagado oculta posición y tamaño (aplica con un departamento elegido)
    por_clave("selectbox", "que__nivel_txt").select("Departamentos").run()
    next(w for w in at.sidebar.multiselect if w.key.startswith("que__deptos_dep")).select("Cundinamarca").run()
    assert hay("selectbox", "mini__pos_txt")
    por_clave("toggle", "mini__minimapa").set_value(False).run()
    assert not hay("selectbox", "mini__pos_txt") and not hay("slider", "mini__minimapa_nivel")


def test_ciudad_preseleccionada_y_regiones_sin_errores():
    at = AppTest.from_file(APP, default_timeout=300).run()
    por_clave = lambda pre: next(w for w in at.sidebar.selectbox if w.key and w.key.startswith(pre))  # noqa: E731
    por_clave("que__nivel_txt").select("Ciudades").run()
    assert por_clave("que__ciudad").value == "Bogotá" and errores(at) == []
    por_clave("que__nivel_txt").select("Regiones").run()
    assert errores(at) == []


