"""Interfaz sin navegador: áreas, colores, etiquetas, resumen y mapas guardados (cola y galería)."""
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from ui.descargas import dibujar_en, tabla_en_formato, zip_de_mapas
from mapacalor import geodatos as gd
import io
import zipfile
import streamlit as st
from mapacalor import render

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TIPOS = ("selectbox", "toggle", "checkbox", "multiselect", "select_slider", "slider", "number_input", "text_input", "radio",
         "segmented_control", "button")


def nueva() -> AppTest:
    return AppTest.from_file(APP, default_timeout=300).run()


def widget(at: AppTest, clave: str):
    for tipo in TIPOS:
        for w in getattr(at, tipo):
            if w.key == clave:
                return w
    raise AssertionError(f"no hay un control con la clave {clave}")


def poner(at: AppTest, clave: str, valor) -> AppTest:
    w = widget(at, clave)
    if hasattr(w, "select") and not hasattr(w, "select_slider") and w.__class__.__name__ == "Selectbox":
        w.select(valor)
    else:
        w.set_value(valor)
    return at.run()


def boton(at: AppTest, texto: str = "", clave: str = ""):
    return next(b for b in at.button if (clave and b.key == clave) or (texto and texto in b.label))


def sin_errores(at: AppTest):
    assert not at.exception, [e.value for e in at.exception]


# ---- área geográfica
def test_ciudades_con_divisiones_y_zona_rural():
    at = poner(nueva(), "que__nivel_txt__0", "Ciudades")
    sin_errores(at)
    div = widget(at, "que__divisiones__0").options
    at = poner(at, "que__divisiones__0", div[:2])
    sin_errores(at)
    at = poner(at, "que__ver_ciudad__0", False)
    sin_errores(at)
    at = poner(at, "que__divisiones__0", [])
    at = poner(at, "que__ciudad__0", "Medellín")
    sin_errores(at)
    assert widget(at, "que__ciudad_rural__0") is not None
    at = poner(at, "que__ciudad_rural__0", False)
    sin_errores(at)


def test_ciudad_sin_elegir_muestra_el_pais(monkeypatch):
    monkeypatch.setattr(gd, "lista_ciudades", lambda: ["Medellín", "Cali"])     # sin Bogotá, no hay ciudad por defecto
    at = poner(nueva(), "que__nivel_txt__0", "Ciudades")
    sin_errores(at)
    assert any("Sin ciudad seleccionada" in i.value for i in at.sidebar.info)


def test_regiones_departamentos_y_municipios():
    at = poner(nueva(), "que__nivel_txt__0", "Regiones")
    at = poner(at, "que__regiones__0", ["Andina"])
    sin_errores(at)
    at = poner(at, "que__nivel_txt__0", "Departamentos")
    at = poner(at, "que__deptos_dep__0", ["Boyacá", "Santander"])
    sin_errores(at)
    at = poner(at, "que__nivel_txt__0", "Municipios")
    assert any("Sin departamentos seleccionados" in w.value for w in at.sidebar.warning)
    at = poner(at, "que__deptos_mun__0", ["Antioquia", "Caldas"])
    at = poner(at, "que__municipios__0", ["Antioquia|Abejorral", "Caldas|Aguadas"])
    sin_errores(at)
    at = poner(at, "que__ver_depto__0", False)
    sin_errores(at)


# ---- colores y bordes
def test_categorias_por_segmento_y_por_departamento():
    at = poner(nueva(), "colores__modo__0", "Categorías")
    sin_errores(at)
    for clave in [w.key for w in at.selectbox if (w.key or "").startswith("colores__")]:
        for opcion in widget(at, clave).options[:4]:
            at = poner(at, clave, opcion)
            sin_errores(at)


def test_mapa_de_calor_con_colores_propios_y_paletas():
    at = nueva()
    for clave in ("colores__invertir__0", "colores__mar_propio__0"):
        at = poner(at, clave, True)
        sin_errores(at)
    for clave in ("colores__n_col__0", "colores__n_tonos__0"):
        at = poner(at, clave, 3)
        sin_errores(at)
    at = boton_paleta(at, 3)
    sin_errores(at)


def boton_paleta(at: AppTest, i: int) -> AppTest:
    return boton(at, clave=f"colores__paleta_sel_op_{i}__0").click().run()


def test_ampliacion_en_cada_nivel():
    for nivel, clave in (("Regiones", "amp__amp_region__0"), ("Departamentos", "amp__amp_departamento__0"),
                         ("Municipios", "amp__amp_municipio__0"), ("Ciudades", "amp__amp_ciudad__0")):
        at = poner(nueva(), "que__nivel_txt__0", nivel)
        if nivel == "Municipios":
            at = poner(at, "que__deptos_mun__0", ["Cundinamarca"])
        at = poner(at, "amp__amp_on__0", True)
        sin_errores(at)
        opciones = widget(at, clave).options
        at = poner(at, clave, opciones[:2])
        sin_errores(at)


def test_minimapa_y_escala():
    at = poner(nueva(), "que__nivel_txt__0", "Departamentos")
    at = poner(at, "que__deptos_dep__0", ["Boyacá"])
    at = poner(at, "mini__minimapa__0", True)
    for pos in widget(at, "mini__pos_txt__0").options:
        at = poner(at, "mini__pos_txt__0", pos)
        sin_errores(at)


# ---- etiquetas y resumen
def test_etiquetas_en_cada_modo_y_su_panel_aa():
    at = poner(nueva(), "etq__etq_on__0", True)
    for modo in widget(at, "etq__etq_txt__0").options:
        at = poner(at, "etq__etq_txt__0", modo)
        sin_errores(at)
    at = boton(at, clave="aa_etq_btn").click().run()
    sin_errores(at)
    at = poner(at, "etq__etq_txt__0", "Nombre y valor")
    at = poner(at, "etq__valor_junto__0", "Al lado del nombre")
    sin_errores(at)
    at = poner(at, "etq__etq_txt__0", "Ranking")
    at = boton(at, clave="aa_lista_btn").click().run()
    sin_errores(at)


def test_resumen_con_mayores_y_menores():
    at = poner(nueva(), "res__resumen__0", True)
    sin_errores(at)
    at = poner(at, "res__resumen_items__0", ["total", "mayores", "menores"])
    at = poner(at, "res__resumen_n__0", 3)
    at = poner(at, "res__resumen_en_imagen__0", False)
    at = boton(at, clave="aa_res_btn").click().run()
    sin_errores(at)


# ---- mapas guardados
def guardar(at: AppTest, nombre: str) -> AppTest:
    widget(at, f"nom_cola_{len(at.session_state['cola']) if 'cola' in at.session_state else 0}").set_value(nombre)
    return boton(at, "Guardar este mapa").click().run()


def test_cola_galeria_seleccion_y_eliminacion():
    at = nueva()
    for nombre in ("uno", "uno", "tres", "cuatro"):
        at = guardar(at, nombre)
        sin_errores(at)
    cola = at.session_state["cola"]
    assert [m["nombre"] for m in cola] == ["uno", "uno", "tres", "cuatro"]
    at = boton(at, clave="btn_galeria").click().run()
    sin_errores(at)
    at = boton(at, clave="elegir_1").click().run()
    assert at.session_state["cola_sel"] == 1
    at = boton(at, clave="volver_min").click().run()
    assert at.session_state["cola_sel"] is None
    at = boton(at, clave="elegir_0").click().run()
    at = boton(at, clave="galeria_volver").click().run()
    at = poner(at, "sel_todos", True)
    assert all(at.session_state[f"sel_{m['id']}"] for m in cola)
    at = poner(at, f"sel_{cola[0]['id']}", False)
    at = poner(at, f"sel_{cola[1]['id']}", False)
    at = boton(at, "Eliminar seleccionados").click().run()
    assert len(at.session_state["cola"]) == 2
    sin_errores(at)
    at = boton(at, clave=f"del_{at.session_state['cola'][0]['id']}").click().run()
    sin_errores(at)
    at = boton(at, "Eliminar todos").click().run()
    assert at.session_state["cola"] == [] and not at.session_state["cola_galeria"]


def test_cola_quitar_vaciar_y_cerrar_la_galeria():
    at = nueva()
    at = guardar(at, "a")
    at = guardar(at, "b")
    at = boton(at, clave="cola_x_0").click().run()
    assert [m["nombre"] for m in at.session_state["cola"]] == ["b"]
    at = boton(at, clave="btn_galeria").click().run()
    at = boton(at, clave="galeria_cerrar").click().run()
    assert not at.session_state["cola_galeria"]
    at = boton(at, clave="btn_galeria").click().run()
    at = boton(at, clave="cerrar_todo").click().run()
    assert not at.session_state["cola_galeria"]
    at = boton(at, "Vaciar").click().run()
    assert at.session_state["cola"] == []


def test_mapa_guardado_sin_imagen_se_dibuja_al_abrirlo():
    at = nueva()
    at = guardar(at, "a")
    at.session_state["cola"][0].pop("png")
    at.session_state["cola"][0].pop("id")
    at = boton(at, clave="btn_galeria").click().run()
    sin_errores(at)
    assert at.session_state["cola"][0]["id"]


# ---- contenido de las descargas
def _render_falso(tabla, estilo, formato):
    return (f"{estilo['x']}.{formato}".encode(), {})


def test_descargas():
    items = [{"nombre": "Mapa 1", "tabla": None, "estilo": {"x": 1}}, {"nombre": "Mapa 1", "tabla": None, "estilo": {"x": 2}},
             {"nombre": "***", "tabla": None, "estilo": {"x": 3}}]
    with zipfile.ZipFile(io.BytesIO(zip_de_mapas(items, "png", _render_falso))) as z:
        assert z.namelist() == ["Mapa_1.png", "Mapa_1_2.png", "mapa.png"]
        assert z.read("mapa.png") == b"3.png"
    assert dibujar_en(_render_falso, None, {"x": 9}, "svg") == b"9.svg"
    tabla = pd.DataFrame({"Departamento": ["Cauca"], "Valor": [1.5]})
    assert tabla_en_formato(tabla, "csv").decode("utf-8-sig").startswith("Departamento,Valor")
    assert b"Cauca" in tabla_en_formato(tabla, "json")
    assert tabla_en_formato(tabla, "xlsx", "Datos")[:2] == b"PK"
    assert tabla_en_formato(tabla, "parquet")[:4] == b"PAR1"
    with pytest.raises(ValueError):
        tabla_en_formato(tabla, "xml")


# ---- casos sueltos de la interfaz
def test_selector_de_idioma_no_queda_vacio():
    at = nueva()
    at.segmented_control(key="idioma").set_value(None).run()
    sin_errores(at)
    assert at.segmented_control(key="idioma").value == "ES"


def test_ampliacion_con_municipios_elegidos():
    at = poner(nueva(), "que__nivel_txt__0", "Municipios")
    at = poner(at, "que__deptos_mun__0", ["Cundinamarca"])
    at = poner(at, "que__municipios__0", ["Cundinamarca|Chía", "Cundinamarca|Cajicá"])
    at = poner(at, "amp__amp_on__0", True)
    sin_errores(at)
    assert set(widget(at, "amp__amp_municipio__0").options) == {"Chía", "Cajicá"}


def test_categorias_sin_grupos_y_paleta_desconocida(monkeypatch):
    st.cache_data.clear()
    monkeypatch.setattr(render, "categorias", lambda *a, **k: {})
    at = poner(nueva(), "colores__modo__0", "Categorías")
    sin_errores(at)
    st.cache_data.clear()
    inicial = nueva()
    inicial.session_state["colores__paleta_sel__0"] = "Paleta que no existe"
    inicial.run()
    sin_errores(inicial)


def test_seleccion_de_galeria_desactualizada():
    at = boton(guardar(nueva(), "a"), clave="btn_galeria").click().run()
    at.session_state["cola_sel"] = 7
    at.run()
    sin_errores(at)
    assert at.session_state["cola_sel"] is None


def _guion_configuracion():
    import streamlit as st  # noqa: PLC0415
    from ui.estado import iniciar_estado  # noqa: PLC0415
    from ui.plantillas import poner_config  # noqa: PLC0415
    iniciar_estado()
    poner_config({"seccion_inexistente": {"x": 1}, "que": {"nivel_txt": "Regiones"}}, [])
    st.session_state["listo"] = st.session_state["que__nivel_txt__0"]


def test_plantilla_ignora_secciones_desconocidas():
    at = AppTest.from_function(_guion_configuracion).run()
    assert not at.exception and at.session_state["listo"] == "Regiones"


def test_agrupar_por_departamento_deja_de_aplicar_con_un_solo_departamento():
    at = poner(nueva(), "que__nivel_txt__0", "Municipios")
    at = poner(at, "que__deptos_mun__0", ["Antioquia", "Caldas"])
    at = poner(at, "colores__modo__0", "Categorías")
    at = poner(at, "colores__agrupar__0", "Departamento")
    at = poner(at, "que__deptos_mun__0", ["Antioquia"])
    sin_errores(at)
