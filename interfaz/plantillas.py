"""Plantillas de estilo: valores de los controles que se aplican al elegir una plantilla."""
from __future__ import annotations

import streamlit as st

from interfaz.constantes import FUENTE_TEXTOS
from interfaz.estado import SECCIONES, subir_version


# Controles que cambiaron de sección; las plantillas usan el nombre anterior
DESTINO = {("tit", "prop_txt"): "expo", ("tit", "dpi"): "expo"}


def poner_config(secciones: dict, reiniciar: list[str]):
    """Reinicia las secciones indicadas y carga los valores dados (se usan al crear los controles)."""
    subir_version(*reiniciar)
    for sec, valores in secciones.items():
        if sec not in SECCIONES:
            continue
        for nombre, valor in valores.items():
            if nombre == "fuente_txt":  # la tipografía va a todos los textos
                for s, c in FUENTE_TEXTOS:
                    st.session_state[f"{s}__tipo_{c}__{st.session_state.gen.get(s, 0)}"] = valor
                continue
            dest = DESTINO.get((sec, nombre), sec)
            st.session_state[f"{dest}__{nombre}__{st.session_state.gen.get(dest, 0)}"] = valor


def _bordes(color_unidad, grosor_unidad, color_depto, grosor_depto):
    """Valores de las capas de líneas para todos los niveles (sus claves dependen del nivel)."""
    v = {}
    for niv in ("departamento", "municipio", "region", "ciudad"):
        for clave, col, gro in (("mun", color_unidad, grosor_unidad), ("dep", color_depto, grosor_depto),
                                ("reg", color_unidad, grosor_unidad * 2), ("div", color_unidad, grosor_unidad),
                                ("lim", color_depto, grosor_depto)):
            if niv == "departamento" and clave == "dep":
                color, grosor = color_unidad, grosor_unidad * 1.5
            else:
                color, grosor = col, gro
            v[f"col_{clave}_{niv}"] = color
            v[f"gro_{clave}_{niv}"] = round(grosor, 2)
    return v


PLANTILLAS = {
    "Profesional": {},
    "Publicación científica": {
        "colores": {"paleta_sel": "Personalizada",
                    "n_col": 4, "cp4_0": "#FDE725", "cp4_1": "#7AD151", "cp4_2": "#2A788E", "cp4_3": "#3B0F70",
                    "n_tonos": 7, "color_contexto": "#EDEDED", "color_fondo": "#FFFFFF"},
        "bordes": _bordes("#6B6B6B", 0.3, "#1F1F1F", 0.8),
        "mini": {"minimapa": True, "escala_km": True, "norte": True},
        "ley": {"leyenda": True, "extremos": "Valor mínimo y máximo", "est_ley": ["Negrita"]},
        "tit": {"fuente_txt": "Times New Roman", "tam_tit": 15, "tam_sub": 11, "tam_nota": 8,
                "est_tit": ["Negrita"], "est_sub": ["Cursiva"], "est_nota": ["Cursiva"], "dpi": 300},
    },
    "Presentación": {
        "colores": {"paleta_sel": "Personalizada", "n_col": 1, "cp1_0": "#1F4E79", "rol_unico": "Más fuerte", "n_tonos": 6, "color_contexto": "#E5E3DE"},
        "bordes": _bordes("#FFFFFF", 1.0, "#FFFFFF", 2.0),
        "ley": {"leyenda": True, "extremos": "Texto", "est_ley": ["Negrita"]},
        "etq": {"etq_on": True, "etq_txt": "Ranking", "top_n": 5, "modo_txt": "Números y lista",
                "etiqueta_tam": 9},
        "tit": {"fuente_txt": "Arial", "tam_tit": 24, "tam_sub": 14, "est_tit": ["Negrita"]},
    },
    "Minimalista": {
        "colores": {"paleta_sel": "Personalizada", "n_col": 1, "cp1_0": "#2F6DB5", "rol_unico": "Más fuerte", "n_tonos": 5, "color_contexto": "#F2F2F2"},
        "bordes": _bordes("#FFFFFF", 0.4, "#FFFFFF", 0.8),
        "mini": {"minimapa": False, "escala_km": False, "norte": False},
        "ley": {"leyenda": True, "extremos": "Texto", "est_ley": []},
        "etq": {"etq_on": False},
        "tit": {"fuente_txt": "Arial", "tam_tit": 15, "est_tit": []},
    },
    "Oscura": {
        "colores": {"paleta_sel": "Personalizada",
                    "n_col": 4, "cp4_0": "#2B5C8A", "cp4_1": "#3E9BC9", "cp4_2": "#7FD8E8", "cp4_3": "#F6E27A",
                    "n_tonos": 8, "color_sin_dato": "#223246", "color_contexto": "#1A2736", "color_fondo": "#0B1622", "mar_propio": False},
        "bordes": _bordes("#0B1622", 0.4, "#8FA6BD", 1.0),
        "ley": {"leyenda": True, "extremos": "Texto", "est_ley": ["Negrita"]},
        "tit": {"fuente_txt": "Calibri", "tam_tit": 20, "est_tit": ["Negrita"]},
    },
    "Térmica": {
        "colores": {"paleta_sel": "Personalizada",
                    "n_col": 5, "cp5_0": "#FFF3B0", "cp5_1": "#FDBE5A", "cp5_2": "#F57C3B", "cp5_3": "#D7301F",
                    "cp5_4": "#7F0000", "n_tonos": 9, "color_contexto": "#E6E6E6", "color_fondo": "#F5F5F2"},
        "bordes": _bordes("#FFFFFF", 0.5, "#FFFFFF", 1.5),
        "ley": {"leyenda": True, "extremos": "Valor mínimo y máximo", "est_ley": ["Negrita"]},
        "tit": {"fuente_txt": "Arial", "tam_tit": 18, "est_tit": ["Negrita"]},
    },
    "Divergente": {
        "colores": {"paleta_sel": "Personalizada",
                    "n_col": 5, "cp5_0": "#2166AC", "cp5_1": "#92C5DE", "cp5_2": "#F7F7F7", "cp5_3": "#F4A582",
                    "cp5_4": "#B2182B", "n_tonos": 7, "color_sin_dato": "#D9D9D9",
                    "color_contexto": "#ECEAE6", "color_fondo": "#FFFFFF"},
        "bordes": _bordes("#FFFFFF", 0.5, "#666666", 1.0),
        "ley": {"leyenda": True, "extremos": "Valor mínimo y máximo", "est_ley": ["Negrita"]},
        "tit": {"fuente_txt": "Calibri", "tam_tit": 18, "est_tit": ["Negrita"]},
    },
    "Monocromo para imprimir": {
        "colores": {"paleta_sel": "Personalizada", "n_col": 1, "cp1_0": "#1A1A1A", "rol_unico": "Más fuerte", "n_tonos": 6, "color_contexto": "#F0F0F0",
                    "color_fondo": "#FFFFFF"},
        "bordes": _bordes("#8A8A8A", 0.3, "#000000", 0.9),
        "mini": {"minimapa": True, "escala_km": True, "norte": True},
        "ley": {"leyenda": True, "extremos": "Valor mínimo y máximo", "est_ley": ["Negrita"]},
        "tit": {"fuente_txt": "Times New Roman", "tam_tit": 15, "tam_sub": 11, "tam_nota": 8,
                "est_tit": ["Negrita"], "est_sub": ["Cursiva"], "est_nota": ["Cursiva"], "dpi": 300},
    },
    "Editorial": {
        "colores": {"paleta_sel": "Personalizada",
                    "n_col": 3, "cp3_0": "#EBD6AA", "cp3_1": "#C77D3B", "cp3_2": "#5E2B14", "n_tonos": 7,
                    "color_sin_dato": "#F0E9DA", "color_contexto": "#E6DECB", "color_fondo": "#FAF6EE"},
        "bordes": _bordes("#FAF6EE", 0.5, "#FAF6EE", 1.5),
        "ley": {"leyenda": True, "extremos": "Texto", "est_ley": []},
        "tit": {"fuente_txt": "Georgia", "tam_tit": 22, "tam_sub": 12, "tam_nota": 8,
                "est_tit": ["Negrita"], "est_sub": ["Cursiva"], "est_nota": ["Cursiva"]},
    },
    "Redes sociales": {
        "colores": {"paleta_sel": "Personalizada",
                    "n_col": 3, "cp3_0": "#FFD166", "cp3_1": "#EF476F", "cp3_2": "#4B1D8F", "n_tonos": 8,
                    "color_contexto": "#EEEEEE", "color_fondo": "#FFFFFF"},
        "bordes": _bordes("#FFFFFF", 0.6, "#FFFFFF", 2.0),
        "ley": {"leyenda": True, "extremos": "Texto", "est_ley": ["Negrita"]},
        "tit": {"fuente_txt": "Calibri", "tam_tit": 26, "tam_sub": 15, "est_tit": ["Negrita"],
                "prop_txt": "Cuadrada (1:1)"},
    },
}


SECCIONES_ESTILO = ["colores", "bordes", "mini", "ley", "etq", "tit", "expo"]


def aplicar_plantilla():
    """Se ejecuta al elegir una plantilla: aplica sus valores a las secciones de estilo."""
    poner_config(PLANTILLAS[st.session_state["plantilla_sel"]], SECCIONES_ESTILO)
