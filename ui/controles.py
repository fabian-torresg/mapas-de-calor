"""Controles reutilizables de la barra lateral."""
from __future__ import annotations

import html

import streamlit as st

from ui.constantes import AYUDA_ESPACIO, ICONO_ESTILO, PALETA_INFO, TIPOGRAFIAS, TIPOS_LINEA
from ui.estado import K, fijar
from ui.textos import t
from mapacalor import geodatos as gd
from mapacalor import paletas as pal


def muestra(colores: list[str], alto=18) -> str:
    """Franja HTML para ver la rampa de color."""
    celdas = "".join(f'<div style="flex:1;background:{c}"></div>' for c in colores)
    return f'<div style="display:flex;height:{alto}px;border-radius:4px;overflow:hidden;margin:4px 0 12px">{celdas}</div>'


def selector_estilo(sec: str, clave: str, por_defecto: list[str], donde=None, desactivado: bool = False) -> list[str]:
    """Botones de formato N, I y U combinables; ninguno = normal."""
    donde = donde or st
    elegidos = donde.pills(t("Formato"), list(ICONO_ESTILO), selection_mode="multi", default=por_defecto,
                           key=K(sec, f"est_{clave}"), label_visibility="collapsed", disabled=desactivado,
                           format_func=lambda x: f"**{t('N')}**" if x == "Negrita" else ICONO_ESTILO[x]) or []
    return [x.lower() for x in elegidos]


def _nombre_pt(texto: str, ayuda: str = "") -> None:
    """Nombre de un control del panel de textos (con ayuda al pasar el cursor, si la tiene)."""
    st.markdown(f'<p class="etq-campo" title="{html.escape(t(ayuda))}">{t(texto)}</p>', unsafe_allow_html=True)


def fila_numeros(clave_est: str):
    """Decimales y sufijo de los valores (etiquetas, resumen y extremos de la leyenda)."""
    with st.container(horizontal=True, gap="xsmall", wrap=True, key=f"pw_n_{clave_est}"):
        with st.container(horizontal=True, vertical_alignment="center", gap="xxsmall", wrap=False, key=f"pt_n_{clave_est}"):
            _nombre_pt("Decimales", "Cifras después de la coma en etiquetas, resumen y leyenda.")
            dec = st.number_input(t("Decimales"), 0, 4, 0, key=K("etq", "decimales"), label_visibility="collapsed")
        with st.container(horizontal=True, vertical_alignment="center", gap="xxsmall", wrap=False, key=f"pt_s_{clave_est}"):
            _nombre_pt("Sufijo", "Texto después de cada valor: %, u, $...")
            suf = st.text_input(t("Sufijo (%, u, $...)"), "", key=K("etq", "sufijo"), label_visibility="collapsed")
    return int(dec), suf


def panel_texto(sec: str, nombre: str, clave: str, tam: tuple, clave_est: str, est_defecto: list[str], color_auto: str,
                esp_clave: str = "", marcador: str | None = None, ayuda_tam: str = "Tamaño de letra, en puntos.",
                con_numeros: bool = False):
    """Controles de un texto: tipografía, tamaño, espacio, formato (N, I, U) y color.

    tam = (mínimo, máximo, valor, clave). Sin `esp_clave` no hay espacio; con `marcador` va un selector de
    color del marcador; `con_numeros` añade decimales y sufijo. El color es None si coincide con el automático.
    Devuelve (tamaño, estilo, color, espacio, tipografía)."""
    esp = 0.0
    with st.container(key=f"ctl_{clave_est}"):
        st.markdown(f'<p class="pt-edit">{t("Editando")}: <b>{nombre}</b></p>', unsafe_allow_html=True)
        with st.container(horizontal=True, vertical_alignment="center", gap="xxsmall", wrap=False, key=f"pt_a_{clave_est}"):
            _nombre_pt("Tipografía")
            tipo = st.selectbox(t("Tipografía"), list(TIPOGRAFIAS), key=K(sec, f"tipo_{clave_est}"), label_visibility="collapsed")
        # dos pares por fila; si no caben, el segundo baja
        with st.container(horizontal=True, gap="xsmall", wrap=True, key=f"pw_a_{clave_est}"):
            with st.container(horizontal=True, vertical_alignment="center", gap="xxsmall", wrap=False, key=f"pt_b_{clave_est}"):
                _nombre_pt("Tamaño", ayuda_tam)
                tamano = st.number_input(t("Tamaño"), tam[0], tam[1], tam[2], key=K(sec, tam[3]), label_visibility="collapsed")
            if esp_clave:
                with st.container(horizontal=True, vertical_alignment="center", gap="xxsmall", wrap=False, key=f"pt_e_{clave_est}"):
                    _nombre_pt("Espacio", AYUDA_ESPACIO)
                    esp = st.number_input(t("Espacio"), -10, 60, 0, 1, key=K(sec, esp_clave), label_visibility="collapsed")
            elif marcador:
                with st.container(horizontal=True, vertical_alignment="center", gap="xxsmall", wrap=False, key=f"pt_g_{clave_est}"):
                    _nombre_pt("Marcador", "Color de los círculos numerados.")
                    st.color_picker(t("Color del marcador"), marcador, key=K(sec, "color_marcador"), label_visibility="collapsed")
        with st.container(horizontal=True, gap="xsmall", wrap=True, key=f"pw_b_{clave_est}"):
            with st.container(horizontal=True, vertical_alignment="center", gap="xxsmall", wrap=False, key=f"pt_c_{clave_est}"):
                _nombre_pt("Formato", "Negrita, cursiva y subrayado; se pueden combinar.")
                estilo = selector_estilo(sec, clave_est, est_defecto)
            with st.container(horizontal=True, vertical_alignment="center", gap="xxsmall", wrap=False, key=f"pt_f_{clave_est}"):
                _nombre_pt("Color", "Color del texto.")
                # al pasar a un fondo oscuro vuelve el color automático
                modo = "o" if pal.es_oscuro(st.session_state.get(K("colores", "color_fondo"), "#FFFFFF")) else "c"
                elegido = st.color_picker(t("Color del texto"), color_auto, key=K(sec, f"col_{clave}_{modo}"), label_visibility="collapsed")
        if con_numeros:
            fila_numeros(clave_est)
    return (tamano, estilo, (None if elegido.lower() == color_auto.lower() else elegido), float(esp), TIPOGRAFIAS[tipo])


def selector_deptos(clave: str, por_defecto: list[str], placeholder="Seleccionar departamentos") -> list[str]:
    """Multiselección de departamentos."""
    if clave not in st.session_state:
        st.session_state[clave] = por_defecto
    return st.multiselect(t("Departamentos"), gd.lista_departamentos(), key=clave,
                          placeholder=t(placeholder), format_func=t)


def _tira_css(clave_boton: str, cols: list[str], elegida: bool) -> str:
    """Regla CSS que pinta el botón de una paleta con su línea de colores."""
    n = len(cols)
    tramos = ", ".join(f"{c} {i * 100 / n:.2f}% {(i + 1) * 100 / n:.2f}%" for i, c in enumerate(cols))
    marca = "box-shadow:0 0 0 2px #7FA7D1;color:#fff;text-shadow:0 0 3px #000;" if elegida else "color:transparent;"
    return (f"[class~='st-key-{clave_boton}'] button{{background:linear-gradient(90deg,{tramos})!important;"
            f"border:1px solid rgba(128,128,128,0.45);min-height:0.75rem;height:0.75rem;padding:0;border-radius:0;{marca}}}")


def selector_paleta(clave: str, opciones: dict[str, list[str]]) -> str:
    """Lista de paletas: cada fila es su línea de colores, con un icono de ayuda con el nombre. Devuelve la elegida."""
    k = K("colores", clave)
    actual = st.session_state.get(k, "Personalizada")
    if actual not in opciones:
        actual = "Personalizada"
    c_etq, c_sel = st.columns([2, 5], vertical_alignment="center", gap="xsmall")
    c_etq.markdown(f'<p class="etq-campo">{t("Paleta")}</p>', unsafe_allow_html=True)
    with c_sel.popover(t(actual), width="stretch", help=t("Paleta predefinida, o «Personalizada» para elegir cada "
                                                          "color.")):
        reglas = []
        for i, (nombre, cols) in enumerate(opciones.items()):
            c1, c2 = st.columns([8, 1], vertical_alignment="center", gap="xsmall")
            clave_boton = K("colores", f"{clave}_op_{i}")
            c1.button(":material/check:" if nombre == actual else " ", key=clave_boton, width="stretch",
                      on_click=fijar, args=(k, nombre))
            c2.markdown("&nbsp;", help=f"**{t(nombre)}**\n\n{t(PALETA_INFO[nombre])}")
            reglas.append(_tira_css(clave_boton, cols, nombre == actual))
        st.markdown(f"<style>{''.join(reglas)}</style>", unsafe_allow_html=True)
    return actual


def cantidad(etiqueta: str, minimo: int, maximo: int, defecto: int, clave: str, ayuda: str) -> int:
    """Número entero con su nombre a la izquierda y el campo a la derecha, en una sola línea."""
    c_etq, c_num = st.columns([3, 2], vertical_alignment="center", gap="small")
    c_etq.markdown(t(etiqueta), help=t(ayuda))
    return int(c_num.number_input(t(etiqueta), minimo, maximo, defecto, key=K("colores", clave), label_visibility="collapsed"))


def opcion_en_linea(etiqueta: str, opciones: list[str], clave: str, ayuda: str, formato=None) -> str:
    """Nombre a la izquierda y la lista desplegable de opciones al frente."""
    with st.container(horizontal=True, vertical_alignment="center", gap="xsmall", wrap=False, key=f"fila_op_{clave}"):
        st.markdown(t(etiqueta), help=t(ayuda))
        return st.selectbox(t(etiqueta), opciones, key=K("colores", clave), format_func=formato or t,
                            label_visibility="collapsed")


def cuadros_de_color(clave: str, n: int, base: list[str], prefijo: str) -> list[str]:
    """n cuadros de color pequeños y pegados, con su número adentro (el número lo pone el CSS)."""
    with st.container(horizontal=True, gap="xxsmall", key=f"cuadros_{clave}"):
        return [st.color_picker(str(i + 1), base[i % len(base)], key=K("colores", f"{prefijo}_{i}"),
                                label_visibility="collapsed") for i in range(n)]


def tipo_de_linea(titulo: str, clave: str, desactivado: bool = False) -> str:
    """Lista desplegable con la muestra de cada tipo de línea."""
    return st.selectbox(t(titulo), list(TIPOS_LINEA), key=K("bordes", f"tipo_{clave}"), format_func=TIPOS_LINEA.get,
                        label_visibility="collapsed", disabled=desactivado, help=None)


def boton_aa(clave: str):
    """Botón Aa que abre o recoge el panel de texto `clave` (se ve activo mientras el panel está abierto)."""
    abierto = f"aa_{clave}_abierto"

    def alternar():
        st.session_state[abierto] = not st.session_state.get(abierto, False)

    st.button("Aa", key=f"aa_{clave}_btn", type="primary" if st.session_state.get(abierto) else "secondary",
              help=t("Tipografía, tamaño, formato y color del texto."), on_click=alternar)


def fila_con_aa(clave: str, interruptor: str, ayuda: str, tecla: tuple):
    """Interruptor con botón Aa a su derecha que abre el panel de texto de la función. Devuelve (activo, hueco)."""
    with st.container(horizontal=True, vertical_alignment="center", gap="xsmall", key=f"fila_aa_{clave}"):
        activo = st.toggle(t(interruptor), value=False, key=K(*tecla), help=t(ayuda))
        if activo:
            boton_aa(clave)
    return activo, st.container(key=f"hueco_aa_{clave}")


def panel_aa(clave: str):
    """Contenedor del panel de texto; el CSS lo oculta mientras el botón Aa no lo abre (marca `aa-abierto`)."""
    caja = st.container(key=f"panel_pop_{clave}")
    if st.session_state.get(f"aa_{clave}_abierto"):
        caja.markdown('<span class="aa-abierto"></span>', unsafe_allow_html=True)
    return caja
