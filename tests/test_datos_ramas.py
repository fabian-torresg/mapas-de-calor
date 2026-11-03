"""Pestaña Datos: áreas que adopta el archivo, datos solo con segmentos, correcciones y datos cargados."""
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

from interfaz.constantes import FORMATOS_DATOS
from interfaz.pestana_datos import _actualizar_estados, _aplicar_correcciones
from mapacalor import geodatos as gd

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TIPOS = ("selectbox", "toggle", "checkbox", "multiselect", "number_input", "text_input", "radio", "button")


def abrir_subida() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=300).run()
    next(r for r in at.radio if "Subir archivo" in r.options).set_value("Subir archivo").run()
    return at


def subir(texto: str, nombre: str = "a.csv") -> AppTest:
    at = abrir_subida()
    return at.file_uploader[0].upload(nombre, texto.encode()).run()


def textos(at: AppTest) -> str:
    return " ".join(m.value for m in at.markdown)


def boton(at: AppTest, texto: str = "", clave: str = ""):
    return next(b for b in at.button if (clave and b.key == clave) or (texto and texto in b.label))


def widget(at: AppTest, clave: str):
    for tipo in TIPOS:
        for w in getattr(at, tipo):
            if w.key == clave:
                return w
    raise AssertionError(clave)


def cargar(at: AppTest) -> AppTest:
    return boton(at, clave="btn_cargar").click().run()


# ---- el archivo decide el área
def test_el_archivo_con_ciudad_y_localidades_adopta_la_ciudad():
    ciudad = gd.lista_ciudades()[0]
    divisiones = list(gd.ciudades().query("ciudad == @ciudad").division)[:3]
    filas = "".join(f"{ciudad},{d},{i + 1}\n" for i, d in enumerate(divisiones))
    at = subir("Ciudad,Localidad,Valor\n" + filas)
    assert not at.exception
    assert at.session_state["que__nivel_txt__0"] == "Ciudades" and at.session_state["que__ciudad__0"] == ciudad
    cargar(at)
    sin_ciudad = subir("Localidad,Valor\n" + "".join(f"{d},{i + 1}\n" for i, d in enumerate(divisiones)))
    assert sin_ciudad.session_state["que__ciudad__0"] == ciudad
    assert not cargar(sin_ciudad).exception


def test_el_archivo_con_municipios_regiones_o_sin_lugares_conocidos():
    municipios = subir("Departamento,Municipio,Valor\nAntioquia,Medellín,1\nCauca,Popayán,2\n")
    assert municipios.session_state["que__nivel_txt__0"] == "Municipios"
    sin_departamento = subir("Municipio,Valor\nMedellín,1\n")
    assert sin_departamento.session_state["que__deptos_mun__0"] == []
    regiones = subir("Región,Valor\nAndina,1\nCaribe,2\n")
    assert regiones.session_state["que__nivel_txt__0"] == "Regiones"
    todo = subir("Departamento,Valor\nZzz,1\n")
    assert todo.session_state["que__nivel_txt__0"] == "Todo el país"


def test_archivo_solo_con_segmentos_repetidos_y_filas_sin_lugar():
    solo_segmentos = subir("Departamento,Segmento\nAntioquia,A\nCauca,B\n")
    assert not solo_segmentos.exception
    assert any("no tiene valores" in i.value for i in solo_segmentos.info)
    repetidos = subir("Departamento,Valor\nAntioquia,1\nAntioquia,2\n,3\n")
    assert "filas repetidas combinadas" in textos(repetidos)


def test_cambio_de_hoja_y_area_pendiente():
    at = subir("Departamento,Valor\nAntioquia,1\nCauca,2\n")
    at.session_state["area_adoptada"] = "otro"
    at.run()
    assert not at.exception and at.session_state["area_adoptada"] == at.file_uploader[0].value.file_id


# ---- datos cargados
def test_datos_cargados_con_segmentos_se_quitan_o_se_descartan_al_cambiar_el_area():
    at = subir("Departamento,Valor,Segmento\nAntioquia,10,A\nCauca,7,B\nHuila,4,A\nNariño,9,B\n")
    at = cargar(at)
    assert not at.exception and "datos_subidos" in at.session_state
    for opcion in widget(at, "colores__calculo__0").options:
        widget(at, "colores__calculo__0").select(opcion)
        at.run()
        assert not at.exception, opcion
        for clave in ("colores__zona_agregar__0", "colores__rol_segmento__0", "colores__esc__0"):
            if any(w.key == clave for w in at.selectbox):
                for o in widget(at, clave).options:
                    widget(at, clave).select(o)
                    at.run()
                    assert not at.exception, (opcion, clave, o)
    widget(at, "colores__calculo__0").select(widget(at, "colores__calculo__0").options[1])
    at.run()
    boton(at, "Quitar").click().run()
    assert "datos_subidos" not in at.session_state and not at.exception
    at = cargar(subir("Departamento,Valor,Segmento\nAntioquia,10,A\nCauca,7,B\n"))
    next(w for w in at.sidebar.selectbox if w.key == "que__nivel_txt__0").select("Regiones").run()
    assert not at.exception


def test_colores_con_segmentos_en_cada_modo():
    at = cargar(subir("Departamento,Valor,Segmento\nAntioquia,10,A\nCauca,7,B\nHuila,4,A\n"))
    widget(at, "bordes__contorno_grupo_grosor__0").set_value(2.0).run()
    assert not at.exception
    at.session_state["bordes__dibujar_contorno__0"] = False
    at.run()
    assert not at.exception
    widget(at, "colores__modo__0").select("Colores distintos").run()
    assert not at.exception
    for o in widget(at, "colores__agrupar__0").options:
        widget(at, "colores__agrupar__0").select(o)
        at.run()
        assert not at.exception, o


def test_datos_en_formatos_y_botones_de_la_tabla():
    at = AppTest.from_file(APP, default_timeout=300).run()
    boton(at, "Borrar datos").click().run()
    boton(at, "Valores aleatorios").click().run()
    assert not at.exception
    for formato in FORMATOS_DATOS:
        widget(at, "expo__formato_datos__0").select(formato).run()
        assert not at.exception, formato


# ---- correcciones sin editar celdas a mano
def _guion_correcciones():
    import pandas as pd  # noqa: PLC0415
    import streamlit as st  # noqa: PLC0415
    from interfaz.pestana_datos import _actualizar_estados, _aplicar_correcciones  # noqa: PLC0415
    editado = pd.DataFrame({"Departamento": ["Antioqia", "Cauca"], "Valor": [1, 2], "Estado": ["", ""], "Corregir": [True, False]})
    trabajo = {"df": editado.copy(), "v": 0}
    if not st.session_state.get("hecho"):
        st.session_state["hecho"] = True
        _aplicar_correcciones(editado, [("Departamento", "Antioquia"), None], trabajo, "k")
    st.session_state["resultado"] = st.session_state["trabajo_k"]["df"]["Departamento"].tolist()
    sin_sugerencias = editado.assign(Estado=["x", ""])
    if not st.session_state.get("segundo"):
        st.session_state["segundo"] = True
        _actualizar_estados(sin_sugerencias, ["Sin dato", ""], False, {"df": sin_sugerencias, "v": 1}, "otro")
    st.session_state["otro_resultado"] = list(st.session_state["trabajo_otro"]["df"].columns)


def test_correcciones_y_estados():
    at = AppTest.from_function(_guion_correcciones).run()
    assert not at.exception
    assert at.session_state["resultado"] == ["Antioquia", "Cauca"]
    assert "Corregir" not in at.session_state["otro_resultado"]


def test_funciones_sin_cambios_no_reescriben_la_tabla():
    editado = pd.DataFrame({"Departamento": ["Cauca"], "Estado": [""]})
    assert _aplicar_correcciones(editado, [None], {"df": editado, "v": 0}, "k") is None
    assert _actualizar_estados(editado, [""], False, {"df": editado, "v": 0}, "k") is None


def test_quitar_el_archivo_no_rompe_nada():
    at = subir("Departamento,Valor\nAntioquia,1\n")
    at.file_uploader[0].set_value(None).run()
    assert not at.exception
