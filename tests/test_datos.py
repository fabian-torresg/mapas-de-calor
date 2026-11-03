"""Pestaña Datos sin navegador: tabla editable y archivo subido (python -m pytest tests/test_datos.py)."""
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from ui.pestana_datos import (
    NADA, _ciudad_del_archivo, _columnas_detectadas, _columnas_que_faltan, _lugares_por_revisar, _tabla_base,
)
from mapacalor import datos as dt
from mapacalor import geodatos as gd

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def abrir_subida() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=300).run()
    next(r for r in at.radio if "Subir archivo" in r.options).set_value("Subir archivo").run()
    return at


def subir(at: AppTest, nombre: str, contenido: bytes) -> AppTest:
    return at.file_uploader[0].upload(nombre, contenido).run()


def textos(at: AppTest) -> str:
    return " ".join(m.value for m in at.markdown)


def test_archivo_con_lugares_por_corregir():
    at = subir(abrir_subida(), "a.csv", b"Departamento,Valor\nAntioquia,10\nAntioqia,5\nCauca,7\nAtlantis,3\n")
    assert not at.exception
    assert "2 por corregir" in textos(at)
    assert next(b for b in at.button if b.key == "btn_cargar").disabled


def test_archivo_correcto_se_puede_cargar():
    at = subir(abrir_subida(), "a.csv", b"Departamento,Valor\nAntioquia,10\nCauca,7\nHuila,4\n")
    assert "3 lugares reconocidos" in textos(at)
    boton = next(b for b in at.button if b.key == "btn_cargar")
    assert not boton.disabled
    boton.click().run()
    assert at.session_state["datos_subidos"]["nombre"] == "a.csv"
    assert len(at.session_state["datos_subidos"]["tabla"]) == 3


def test_archivo_ilegible_avisa():
    at = subir(abrir_subida(), "a.csv", b"")
    assert not at.exception
    assert any("No se pudo leer el archivo" in e.value for e in at.error)


def test_archivo_sin_columna_de_lugar_avisa():
    at = subir(abrir_subida(), "a.csv", b"Cosa,Valor\nx,1\n")
    assert not at.exception
    assert "No se encuentra la columna" in textos(at)


def test_excel_de_ejemplo_adopta_el_area():
    contenido = (Path(__file__).resolve().parent.parent / "examples" / "datos_ejemplo.xlsx").read_bytes()
    at = subir(abrir_subida(), "datos_ejemplo.xlsx", contenido)
    assert not at.exception
    assert "lugares reconocidos" in textos(at)


def test_columnas_detectadas_y_faltantes():
    df = pd.DataFrame({"Departamento": ["Cauca"], "Municipio": ["Popayán"], "Valor": [1]})
    col = _columnas_detectadas(df, "municipio")
    assert (col["departamento"], col["municipio"], col["valor"]) == ("Departamento", "Municipio", "Valor")
    assert _columnas_que_faltan("municipio", col) == []
    assert _columnas_que_faltan("departamento", {**col, "departamento": NADA}) == ["Departamento"]
    assert _columnas_que_faltan("ciudad", {**col, "division": NADA}) == ["Localidad o comuna"]


def test_lugares_por_revisar_sugiere_el_oficial():
    df = pd.DataFrame({"Departamento": ["Antioquia", "Antioqia", "Atlantis"], "Valor": [1, 2, 3]})
    col = _columnas_detectadas(df, "departamento")
    revisadas, columnas = _lugares_por_revisar(df, "departamento", "Bogotá", col)
    assert revisadas[0] is None
    assert revisadas[1] == ("Departamento", "Antioquia")
    assert revisadas[2][0] == "Departamento"
    assert columnas == [("Departamento", "departamento")]


def test_tabla_base_agrega_la_columna_informativa():
    region = dt.plantilla("region")
    base, fijos = _tabla_base(region, "region", "Bogotá", ["Región"])
    assert list(base.columns)[:2] == ["Región", "Departamentos"] and fijos == ["Región", "Departamentos"]
    ciudad = dt.plantilla("ciudad", ciudad=gd.lista_ciudades()[0])
    base, fijos = _tabla_base(ciudad, "ciudad", "X", ["Localidad o comuna"])
    assert base.columns[0] == "Ciudad" and fijos[0] == "Ciudad"


def test_ciudad_del_archivo_por_sus_localidades():
    ciudad = gd.lista_ciudades()[0]
    divisiones = list(gd.ciudades().query("ciudad == @ciudad").division)[:3]
    df = pd.DataFrame({"Localidad": divisiones, "Valor": [1, 2, 3]})
    cols = {gd.norm(c).lower(): c for c in df.columns}
    assert _ciudad_del_archivo(df, "Localidad", cols) == ciudad
    sin_coincidencias = pd.DataFrame({"Localidad": ["zzz"], "Valor": [1]})
    assert _ciudad_del_archivo(sin_coincidencias, "Localidad", {"localidad": "Localidad", "valor": "Valor"}) is None


@pytest.mark.parametrize("nivel", ["departamento", "municipio", "region", "ciudad"])
def test_editar_tabla_en_cada_nivel(nivel):
    at = AppTest.from_file(APP, default_timeout=300).run()
    nombres = {"departamento": "Departamentos", "municipio": "Municipios", "region": "Regiones", "ciudad": "Ciudades"}
    next(w for w in at.sidebar.selectbox if w.key == "que__nivel_txt__0").select(nombres[nivel]).run()
    assert not at.exception
