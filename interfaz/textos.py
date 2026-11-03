"""Traducción de los textos de la interfaz (español / inglés)."""
from __future__ import annotations

import re

import streamlit as st

from interfaz.textos_en import EN


_ITEM_DE_AYUDA = re.compile(r"(?<=[.;]) (?=[A-ZÁÉÍÓÚ«0-9][^.:]{0,45}: )")


def _items_en_lineas(texto: str) -> str:
    """Cada opción de una ayuda con varias («Nombre: explicación.») va en su línea."""
    n = len(_ITEM_DE_AYUDA.findall(texto))
    empieza_con_opcion = re.match(r"[^.:]{1,45}: ", texto)
    separador = "  " + chr(10)  # dos espacios y salto: nueva línea sin párrafo en blanco
    return _ITEM_DE_AYUDA.sub(separador, texto) if (empieza_con_opcion and n >= 1) or n >= 2 else texto


def t(texto: str) -> str:
    """Devuelve el texto en el idioma elegido arriba a la derecha (ES / EN)."""
    if not isinstance(texto, str):
        return str(texto)
    return _items_en_lineas(EN.get(texto, texto) if st.session_state.get("idioma") == "EN" else texto)


def rotulos_en_negrita(linea: str) -> str:
    """Pone en negrita los rótulos del resumen («Total:», «Promedio:»...), al inicio o tras « · »."""
    return re.sub(r"(^|·\s*)([^:·]+:)", lambda m: f"{m[1]}**{m[2]}**", linea)
