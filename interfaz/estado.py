"""Estado de la sesión: claves de los controles por sección y botones de restablecer."""
from __future__ import annotations

import streamlit as st

from interfaz.textos import t


# Cada sección versiona las claves de sus controles; al subir la versión se recrean
SECCIONES = ["que", "colores", "bordes", "vista", "amp", "ley", "etq", "res", "mini", "tit", "expo"]


def K(sec: str, nombre: str) -> str:
    return f"{sec}__{nombre}__{st.session_state.gen.get(sec, 0)}"


def subir_version(*secs):
    if "expo" in secs:
        st.session_state.pop("_dpi_guardado", None)
    for sec in secs:
        st.session_state.gen[sec] = st.session_state.gen.get(sec, 0) + 1


def boton_restablecer(*secs: str):
    """Botón (arriba a la derecha) que devuelve la sección a como estaba al abrir la app."""
    st.button(":material/restart_alt:", key=f"rst_{secs[0]}", type="tertiary", help=t("Restablecer esta sección"),
              on_click=subir_version, args=secs)


def restablecer_todo():
    subir_version(*SECCIONES)
    st.session_state.pop("tablas", None)        # datos escritos en la tabla
    st.session_state.gen["datos"] = st.session_state.gen.get("datos", 0) + 1


def sumar(clave: str):
    st.session_state[clave] = st.session_state.get(clave, 0) + 1


def fijar(clave: str, valor):
    st.session_state[clave] = valor


def iniciar_estado():
    """Crea las versiones de cada sección (se llama al inicio de cada ejecución)."""
    if "gen" not in st.session_state:
        st.session_state.gen = {}
