"""Arranque de la app: recarga del motor y aviso cuando no se pueden bajar los límites (corre al final: toca módulos y cachés)."""
from pathlib import Path

import streamlit as st
from streamlit.testing.v1 import AppTest

from mapacalor import geodatos as gd
from mapacalor import render

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def test_la_app_recarga_el_motor_si_cambio_su_archivo(monkeypatch):
    AppTest.from_file(APP, default_timeout=300).run()
    monkeypatch.setattr(render, "_fecha_cargado", 0.0, raising=False)
    at = AppTest.from_file(APP, default_timeout=300).run()
    assert not at.exception
    assert render._fecha_cargado > 0


def test_aviso_si_no_se_pueden_descargar_los_limites(monkeypatch):
    def sin_red():
        raise OSError("sin conexión")
    st.cache_resource.clear()
    monkeypatch.setattr(gd, "municipios", sin_red)
    try:
        at = AppTest.from_file(APP, default_timeout=300).run()
        assert any("No se pudieron descargar los límites" in e.value for e in at.error)
    finally:
        st.cache_resource.clear()
