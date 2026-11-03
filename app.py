"""Generador de mapas de calor de Colombia (Streamlit). Autor: Fabián Torres.

Ejecutar: streamlit run app.py
"""
from __future__ import annotations

import hashlib
import html
import importlib
import io
import json
import os
import re
import struct
import threading
import time
import zipfile
from dataclasses import asdict

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

import mapacalor.render as _motor_dibujo
from mapacalor import geodatos as gd
from mapacalor import paletas as pal
from interfaz.constantes import (
    CALCULO_GEO, CALCULOS, COLA_MAX, DPI_VISTA, FORMATOS, FORMATOS_DATOS, FORMATOS_IMAGEN, RAYAS,
    RES_OPC, TITULO_GRUPO)
from interfaz.controles import (
    boton_aa, cantidad, cuadros_de_color, fila_con_aa, fila_numeros, muestra, opcion_en_linea, panel_aa, panel_texto,
    selector_deptos, selector_paleta, tipo_de_linea)
from interfaz.carga import mapa_carga, mapa_cierre
from interfaz.estado import K, boton_restablecer, iniciar_estado, restablecer_todo, sumar
from interfaz.estilos import CSS, SCRIPT
from interfaz.guia import AYUDA_ES
from interfaz.pestana_datos import area_del_archivo, pestana_datos
from interfaz.plantillas import PLANTILLAS, aplicar_plantilla
from interfaz.textos import rotulos_en_negrita, t

# Streamlit no relee mapacalor/: si cambió render.py, se recarga aquí
_fecha_dibujo = os.path.getmtime(_motor_dibujo.__file__)
if getattr(_motor_dibujo, "_fecha_cargado", _fecha_dibujo) != _fecha_dibujo:
    importlib.reload(_motor_dibujo)
_motor_dibujo._fecha_cargado = _fecha_dibujo

from mapacalor.render import Estilo, categorias, colores_texto, dibujar, exportar, exportar_geojson, lineas_resumen  # noqa: E402

st.set_page_config(page_title="Mapas de calor", page_icon=":material/map:", layout="wide",
                   menu_items={"About": "Mapas de calor de Colombia, por Fabián Torres."})
# Vista compacta: el mapa se ajusta al alto de la ventana, sin desplazar la página
st.markdown(CSS, unsafe_allow_html=True)


@st.cache_resource(show_spinner=False)
def _estado_carga():
    return {"listo": False, "cerrojo": threading.Lock()}


def cargar_geometrias():
    """Prepara los límites del país una sola vez por proceso y muestra el avance por pasos."""
    estado = _estado_carga()
    if estado["listo"]:
        return
    hueco = st.empty()
    with hueco.container(key="pantalla_carga"):
        pantalla = st.empty()
        paso = st.empty()
        inicio = time.monotonic()
        pantalla.markdown(mapa_carga(t("Mapas de calor")), unsafe_allow_html=True)

        def avanzar(texto):
            paso.markdown(f'<p class="carga-paso">{t(texto)}</p>', unsafe_allow_html=True)

        with estado["cerrojo"]:      # con varias sesiones a la vez, solo una prepara los datos
            if not estado["listo"]:
                avanzar("Leyendo los límites municipales (la primera vez se descargan)...")
                gd.municipios()
                avanzar("Preparando los departamentos...")
                gd.departamentos()
                avanzar("Dibujando una prueba...")
                _motor_dibujo.precalentar()
                _motor_dibujo.precalentar_resto()
                avanzar("Listo")
                estado["listo"] = True
        pantalla.markdown(mapa_cierre(t("Mapas de calor"), time.monotonic() - inicio), unsafe_allow_html=True)
        time.sleep(0.7)
    hueco.empty()


try:
    cargar_geometrias()
except OSError:
    st.error(t("No se pudieron descargar los límites de GADM. Revisar la conexión a internet y recargar la página."))
    st.stop()


@st.cache_data(show_spinner=False, max_entries=40)
def render(tabla: pd.DataFrame | None, estilo: dict, formato: str):
    fig, info = dibujar(tabla, Estilo(**estilo))
    try:
        contenido = exportar(fig, formato)
    finally:
        plt.close(fig)
    return contenido, info


@st.cache_data(show_spinner=False, max_entries=30)
def categorias_auto(estilo: dict, tabla: pd.DataFrame | None, paleta: tuple, semilla: int) -> dict:
    """Colores automáticos de los grupos del mapa: dos grupos vecinos nunca repiten color."""
    return categorias(tabla, Estilo(**estilo), list(paleta), semilla)


iniciar_estado()










from interfaz.textos_en import AYUDA_EN  # noqa: E402















































# pestañas del mapa; tema e idioma van en su tarjeta
tab_mapa, tab_datos, tab_ayuda = st.tabs([t(":material/map: Mapa"), t(":material/table_chart: Tabla de datos"), t(":material/help: Guía de uso")])
with tab_mapa:
    tarjeta = st.container(border=True, key="tarjeta_mapa")
with tarjeta:
    cab_tarjeta = st.container(horizontal=True, horizontal_alignment="right", vertical_alignment="center", gap="small",
                               key="cab_tarjeta")
    # lo llena el bloque del mapa
    hueco_iconos = cab_tarjeta.container(key="iconos_mapa", horizontal=True, gap="small")
    fila_selectores = cab_tarjeta.container(horizontal=True, wrap=False, gap="xsmall", key="selectores_cab")
cab_tema, cab_idioma = fila_selectores.container(), fila_selectores.container()
def _no_vaciar(clave):
    """En estos selectores siempre queda una opción marcada (un segundo clic no la desmarca)."""
    if st.session_state.get(clave) is None:
        st.session_state[clave] = st.session_state.get(f"_prev_{clave}")
    st.session_state[f"_prev_{clave}"] = st.session_state[clave]


# Inicio en claro y español; la elección queda en la URL
_qp = st.query_params
st.session_state.setdefault("_prev_idioma", _qp.get("idioma") if _qp.get("idioma") in ("ES", "EN") else "ES")
st.session_state.setdefault("_prev_tema", _qp.get("tema") if _qp.get("tema") in ("claro", "oscuro") else "claro")
idioma_txt = cab_idioma.segmented_control("Idioma", ["ES", "EN"], default=st.session_state["_prev_idioma"], key="idioma",
                                          label_visibility="collapsed", help="Español / English",
                                          on_change=_no_vaciar, args=("idioma",)) or "ES"
L = "en" if idioma_txt == "EN" else "es"
tema = cab_tema.segmented_control(
    "Tema", ["claro", "oscuro"], default=st.session_state["_prev_tema"], key="tema", label_visibility="collapsed",
    format_func=lambda x: ":material/light_mode:" if x == "claro" else ":material/dark_mode:",
    help=t("Modo claro") + " / " + t("Modo oscuro"), on_change=_no_vaciar, args=("tema",)) or "claro"
# textos al pasar el cursor sobre los botones de iconos (los pone el script)
TITULOS_BOTONES = {"light_mode": t("Modo claro"), "dark_mode": t("Modo oscuro"), "format_bold": t("Negrita"),
                   "format_italic": t("Cursiva"), "format_underlined": t("Subrayado"), "ES": "Español", "EN": "English"}
for _clave, _valor, _inicial in (("idioma", idioma_txt, "ES"), ("tema", tema, "claro")):
    if _valor == _inicial:
        _qp.pop(_clave, None)
    elif _qp.get(_clave) != _valor:
        _qp[_clave] = _valor
cab_tema.markdown(f'<div id="ancla-tema" data-tema="{tema}" data-lang="{idioma_txt.lower()}" '
                  f'data-rst="{html.escape(t("Restablecer esta sección"))}" data-alt="{html.escape(t("Mapa de calor de Colombia"))}" '
                  f'data-titulos="{html.escape(json.dumps(TITULOS_BOTONES, ensure_ascii=False), quote=True)}"></div>',
                  unsafe_allow_html=True)

sb = st.sidebar
with sb.container(horizontal=True, vertical_alignment="center", gap="xsmall", wrap=False, key="cab_sb"):
    st.markdown(f'<p class="titulo-app">{t("Mapas de calor")}</p>', unsafe_allow_html=True)
    # la abre el script de la página
    st.button(":material/menu_book:", key="btn_guia", type="tertiary", help=t("Guía de uso"))
    st.button(":material/restart_alt:", key="rst_todo", on_click=restablecer_todo, type="tertiary",
              help=t("Restablecer todo") + ". " + t("Restablece toda la barra lateral y borra los datos de la tabla."))

# Barra lateral: secciones creadas en orden y llenadas más abajo
tab_s_datos, tab_s_diseno, tab_s_export = sb.tabs([t("Datos"), t("Diseño"), t("Exportación")])
with tab_s_datos:
    exp_area = st.expander(t(":material/map: Área geográfica"))
    with st.container(key="fila_tabla"):  # el CSS coloca el signo de pregunta
        # la abre el script de la página
        st.button(t(":material/table_chart: Tabla de datos"), key="btn_tabla", width="stretch")
        st.markdown("&nbsp;", help=t("Edición de datos para la creación del mapa."))
with tab_s_diseno:
    st.selectbox(t("Plantilla"), list(PLANTILLAS), key="plantilla_sel", on_change=aplicar_plantilla,
                 help=t("Profesional: estilo base. Publicación científica: tipografía serif, colores aptos para "
                         "impresión, escala y norte. Presentación: textos grandes y ranking. Minimalista: solo los "
                         "elementos esenciales. Oscura: fondo azul marino. Térmica: escala de amarillo a rojo. "
                         "Divergente: escala de azul a rojo con centro blanco. Monocromo para imprimir: escala de "
                         "grises. Editorial: fondo crema y colores tierra. Redes sociales: formato cuadrado y texto "
                         "de mayor tamaño."), format_func=t)
    exp_color = st.expander(t(":material/palette: Colores"))
    exp_lineas = st.expander(t(":material/border_style: Líneas y límites"))
    exp_etq = st.expander(t(":material/label: Etiquetas y cifras"))
    exp_vista = st.expander(t(":material/explore: Orientación y vista"))
    with exp_vista:       # una sola sección: primero la orientación y después la vista del mapa
        caja_orient = st.container()
        caja_vista = st.container()
    exp_titulo = st.expander(t(":material/title: Títulos y tipografía"))
with tab_s_export:
    # una sola sección, sin acordeón: proporción primero y la descarga al final
    caja_descarga = st.container(key="caja_descarga")
    with caja_descarga:
        st.markdown(f"**{t('Mapa')}**")

# el área de un archivo recién subido se fija antes de crear los controles
if st.session_state.get("area_pendiente"):
    area_del_archivo(st.session_state.pop("area_pendiente"))
with exp_area:
    nivel_txt = st.selectbox(t("Dividir el mapa por"), ["Todo el país", "Regiones", "Departamentos", "Municipios", "Ciudades"],
                             help=t("Todo el país: por departamentos. Regiones: regiones naturales. "
                                     "Departamentos: los departamentos seleccionados. Municipios: los municipios de "
                                     "los departamentos seleccionados. Ciudades: por división interna."), key=K("que", "nivel_txt"), format_func=t)
    nivel = {"Todo el país": "departamento", "Regiones": "region", "Departamentos": "departamento",
             "Municipios": "municipio", "Ciudades": "ciudad"}[nivel_txt]
    deptos, municipios, regiones, divisiones = [], [], [], []
    ciudad, ciudad_rural, ver_depto = None, True, True

    if nivel == "ciudad":
        ciudades_lista = gd.lista_ciudades()
        ciudad = st.selectbox(t("Ciudad"), ciudades_lista, index=ciudades_lista.index("Bogotá") if "Bogotá" in ciudades_lista else None,
                              placeholder=t("Seleccionar ciudad"), key=K("que", "ciudad"), format_func=t)
        if ciudad:
            c_div = gd.ciudades()
            div_ciudad = c_div[c_div.ciudad == ciudad]
            hay_rural = bool(div_ciudad.rural.any())
            # lo que mostraría "todas"
            rural_pref = st.session_state.get(K("que", "ciudad_rural"), ciudad != "Bogotá")
            n_todas = len(div_ciudad) if rural_pref or not hay_rural else int((~div_ciudad.rural).sum())
            tipo = gd.tipo_division(ciudad).lower()
            divisiones = st.multiselect(t({"localidad": "Localidades", "comuna": "Comunas"}.get(tipo, "Divisiones")),
                                        div_ciudad.division.tolist(), placeholder=t("Todas ({n})").format(n=n_todas),
                                        key=K("que", "divisiones"), format_func=t)
            if divisiones:
                ver_depto = st.toggle(t("Mostrar la ciudad completa"), value=True, key=K("que", "ver_ciudad"),
                                      help=t("Activado: toda la ciudad, con los lugares seleccionados resaltados. "
                                              "Desactivado: solo los lugares seleccionados, con el mapa acercado."))
            elif hay_rural:
                # con todos los lugares se puede quitar la zona rural
                ciudad_rural = st.checkbox(t("Incluir la zona rural"), value=ciudad != "Bogotá",
                                           help=t("Incluye el área rural de la ciudad (en Bogotá, Sumapaz; en "
                                                   "Medellín, 5 corregimientos). Sin zona rural, el mapa se centra "
                                                   "en el área urbana."), key=K("que", "ciudad_rural"))
        else:
            st.info(t("Sin ciudad seleccionada se muestra todo el país."))
    elif nivel == "region":
        regiones = st.multiselect(t("Regiones"), gd.lista_regiones(incluir_insular=True),
                                  placeholder=t("Todas las regiones"), key=K("que", "regiones"), format_func=t)
    elif nivel_txt == "Departamentos":
        deptos = selector_deptos(K("que", "deptos_dep"), [])
    elif nivel == "municipio":
        deptos = selector_deptos(K("que", "deptos_mun"), [])
        if deptos:
            lista = gd.lista_municipios(deptos)
            varios = len(deptos) > 1
            etiquetas_m = {f"{r.departamento}|{r.municipio}": (f"{r.municipio} ({r.departamento})" if varios else r.municipio)
                           for r in lista.itertuples()}
            municipios = st.multiselect(
                t("Municipios"), list(etiquetas_m), format_func=lambda x, _f=(etiquetas_m.get): t(_f(x)),
                placeholder=t("Todos ({n})").format(n=len(etiquetas_m)),
                help=t("Sin selección: todos los municipios de los departamentos elegidos. Con selección: los "
                        "municipios elegidos se resaltan y el resto del departamento se muestra en gris claro."), key=K("que", "municipios"))
            if municipios:
                ver_depto = st.toggle(t("Mostrar el departamento completo"), value=True, key=K("que", "ver_depto"),
                                      help=t("Activado: todo el departamento, con los municipios seleccionados "
                                              "resaltados. Desactivado: solo los municipios seleccionados, con el "
                                              "mapa acercado."))
        else:
            st.warning(t("Sin departamentos seleccionados se muestran los 1.123 municipios del país. El dibujo tarda "
                         "más."))

    if nivel == "ciudad" and not ciudad:  # sin ciudad elegida, el país por departamentos
        nivel, ciudad = "departamento", "Bogotá"
    # el archipiélago solo se dibuja en la vista de todo el país por departamentos
    mostrar_isla = True
    if nivel == "departamento" and not deptos:
        mostrar_isla = st.checkbox(t("Mostrar San Andrés y Providencia"), value=True, key=K("que", "isla"),
                                   help=t("En la vista de todo el país, el archipiélago se dibuja ampliado en la "
                                           "esquina superior izquierda."))
    hay_seleccion = bool(deptos or municipios or nivel == "ciudad"
                         or (regiones and len(regiones) < len(gd.lista_regiones())))
    boton_restablecer("que")

# vista del mapa: qué parte del país se ve
with caja_orient:
    acercar = st.checkbox(t("Acercar el mapa a la selección"), value=True, disabled=not hay_seleccion, key=K("vista", "acercar"))
resto, vecinos = True, True  # el resto del país y los vecinos siempre se dibujan; su color se elige en Colores
isla_en_mapa = mostrar_isla and nivel == "departamento" and not deptos

with tab_datos:
    tabla = pestana_datos(nivel, deptos, municipios, regiones, ciudad, ciudad_rural, divisiones, isla_en_mapa)


zonas = []
if tabla is not None and "grupo" in tabla:
    zonas = [g for g in tabla.grupo.dropna().astype(str).str.strip().unique() if g and g.lower() not in ("nan", "<na>")]



















def estilo_para_grupos(geo: str) -> dict:
    """Lo que define qué lugares se dibujan y cómo se agrupan: de ahí salen los colores automáticos."""
    return asdict(Estilo(nivel=nivel, deptos=deptos, municipios=municipios, regiones=regiones, ciudad=ciudad,
                         ciudad_rural=ciudad_rural, divisiones=divisiones, mostrar_isla=mostrar_isla, grupos_geo=geo))


def bloque_categorias(clave: str, geo: str) -> dict[str, str]:
    """Paleta y un cuadro de color por grupo del mapa; devuelve {grupo: color}."""
    nombre = selector_paleta(f"pcat_{clave}", {"Personalizada": RAYAS, **pal.PALETAS_CATEGORIAS})
    paleta = pal.COLORES_PROPIOS if nombre == "Personalizada" else pal.PALETAS_CATEGORIAS[nombre]
    k_sem, k_ver = K("colores", f"sem_{clave}"), K("colores", f"ver_{clave}")
    st.button(t(":material/shuffle: Barajar los colores"), key=K("colores", f"bar_{clave}"), on_click=sumar,
              args=(k_sem,), help=t("Reasigna los colores entre los grupos."))
    semilla = st.session_state.get(k_sem, 0)
    auto = categorias_auto(estilo_para_grupos(geo), tabla, tuple(paleta), semilla)
    if not auto:
        return {}
    sig = hashlib.md5(f"{tuple(paleta)}|{semilla}|{len(auto)}|{st.session_state.get(k_ver, 0)}".encode(), usedforsecurity=False).hexdigest()[:6]
    final = {}
    # un cuadro por grupo; con muchos, una lista con desplazamiento
    with st.container(height=300) if len(auto) > 8 else st.container():
        for i, (g, c) in enumerate(auto.items()):
            with st.container(horizontal=True, vertical_alignment="center", gap="xsmall", wrap=False, key=f"fila_color_{clave}_{i}"):
                st.markdown(g)
                final[g] = st.color_picker(g, c, key=K("colores", f"cc_{clave}_{sig}_{g}"), label_visibility="collapsed")
    st.button(t(":material/restart_alt: Volver a los colores automáticos"), key=K("colores", f"rv_{clave}"),
              on_click=sumar, args=(k_ver,))
    return final


def bloque_paleta_valor():
    """Paleta de la escala, tonos e invertir. Devuelve (colores, tonos, invertir)."""
    nombre = selector_paleta("paleta_sel", {"Personalizada": RAYAS,
                                            **{n: pal.tonos(pal.colores_base(n), 8) for n in pal.PALETAS}})
    if nombre == "Personalizada":
        n_col = cantidad("Colores", 1, 10, 1, "n_col",
                         "Con 1 color, los demás tonos se generan a partir de él. Con más colores, cada uno "
                         "corresponde a un nivel, de menor a mayor.")
        if n_col == 1:
            cols_escala = cuadros_de_color("escala", 1, ["#1F4E79"], "cp1")
            rol = opcion_en_linea("Este color es el", ["Más fuerte", "Más suave"], "rol_unico",
                                  "Más fuerte: color de los valores más altos; los valores bajos se aclaran. Más "
                                  "suave: color de los valores más bajos; los valores altos se oscurecen.")
            cols_escala = pal.rampa_un_color(cols_escala[0], fuerte=rol == "Más fuerte")
        else:
            st.caption(t("De menor a mayor valor."))
            cols_escala = cuadros_de_color("escala", n_col, pal.tonos(["#DCE8F3", "#3F7AB5", "#0F2D4D"], n_col), f"cp{n_col}")
    else:
        cols_escala = pal.colores_base(nombre)
    tonos_n = cantidad("Tonos", 3, 12, 8, "n_tonos", "Niveles de color entre el valor menor y "
                                                                          "el mayor.")
    inv = st.checkbox(t("Invertir el orden de los colores"), value=False, key=K("colores", "invertir"))
    st.markdown(muestra(pal.tonos(cols_escala, tonos_n, inv)), unsafe_allow_html=True)
    return cols_escala, tonos_n, inv


with exp_color:
    modo = opcion_en_linea("Colorear con", ["Mapa de calor", "Colores distintos"], "modo",
                           "Mapa de calor: escala de color según el valor. Categorías: un color por grupo (lugar, "
                           "departamento, región o segmento).",
                           lambda x: t({"Mapa de calor": "Mapa de calor", "Colores distintos": "Categorías"}[x]))
    relleno, grupos_geo = "valor", ""
    zona_agregar, zona_rol, zona_escala = "suma", "fuerte", "global"
    colores, n_tonos, invertir, escala = pal.colores_base("Azul marino"), 8, False, "raiz"
    colores_zona = {}
    # agrupar por departamento solo tiene sentido si el área elegida abarca más de uno
    n_deptos = len(deptos or gd.lista_departamentos(incluir_insular=nivel == "departamento"))
    if modo == "Mapa de calor":
        calculo = "Por lugar"
        geo_posibles = [k for k in CALCULO_GEO[nivel] if n_deptos > 1]
        calculos = ["Por lugar"] + geo_posibles + (["Dentro de cada segmento", "Según el total de cada segmento"] if zonas else [])
        if st.session_state.get(K("colores", "calculo"), "Por lugar") not in calculos:
            st.session_state.pop(K("colores", "calculo"))       # la opción elegida ya no aplica al área actual
        if len(calculos) > 1:
            calculo = opcion_en_linea("Calcular la escala", calculos, "calculo",
                                      "Por lugar: tono según el valor de cada lugar. Dentro de cada segmento: un color por "
                                      "segmento, con tono según el valor. Según el total: se suma (o promedia) cada segmento "
                                      "y todos sus lugares llevan el mismo tono. Por departamento: igual que por segmento, "
                                      "tomando el departamento como segmento.",
                                      lambda x: t({"Por lugar": "Por lugar", "Dentro de cada departamento": "Por departamento",
                                                   "Dentro de cada segmento": "Por segmento",
                                                   "Según el total de cada segmento": "Total por segmento"}[x]))
        grupos_geo = CALCULO_GEO[nivel].get(calculo, "")
        relleno = CALCULOS.get(calculo, "zona_valor")
        if relleno == "zona_total":
            zona_agregar = opcion_en_linea("Resumir cada segmento con", ["suma", "promedio"], "zona_agregar",
                                           "Cómo se resumen los valores de cada segmento.",
                                           lambda x: t({"suma": "La suma de sus lugares", "promedio": "El promedio de sus lugares"}[x]))
        if relleno == "zona_valor":
            # grupo: el segmento de los datos o, por departamento, ese departamento
            grupo = "departamento" if grupos_geo == "departamento" else "segmento"
            rol = opcion_en_linea("Color de cada grupo", ["Más fuerte", "Más suave"], "rol_segmento",
                                  "Más fuerte: color de los valores más altos; los valores bajos se aclaran. Más suave: color "
                                  "de los valores más bajos; los valores altos se oscurecen.")
            zona_rol = "fuerte" if rol == "Más fuerte" else "suave"
            esc = opcion_en_linea("Comparar los valores", ["Entre todos los segmentos", "Dentro de cada segmento"], "esc",
                                  "Entre todos: un mismo valor tiene la misma intensidad en cualquier grupo. Dentro de cada "
                                  "grupo: cada grupo usa su propia escala, de su valor mínimo al máximo.",
                                  lambda x: t("Entre todos" if x.startswith("Entre") else "Por separado"))
            zona_escala = "global" if esc.startswith("Entre") else "por_zona"
            st.markdown(f"**{t({'segmento': 'Colores de los segmentos', 'departamento': 'Colores de los departamentos'}[grupo])}**")
            colores_zona = bloque_categorias(f"seg_{grupos_geo}" if grupos_geo else "seg", grupos_geo)
            n_tonos = cantidad("Tonos", 3, 12, 8, "n_tonos", "Niveles de color entre el valor "
                                                                                  "menor y el mayor.")
        else:
            colores, n_tonos, invertir = bloque_paleta_valor()
        if zonas and relleno != "zona_valor":
            # colores de la línea de contorno de cada segmento
            if st.session_state.get(K("bordes", "dibujar_contorno"), True):
                with st.expander(t("Colores del contorno de cada segmento")):
                    colores_zona = bloque_categorias("seg", "")
            else:
                colores_zona = categorias_auto(estilo_para_grupos(""), tabla, tuple(pal.PALETAS_CATEGORIAS["Vivos"]), 0)
    else:
        opciones_grupo = {"departamento": {"Cada departamento": "lugar"},
                          "municipio": {"Cada municipio": "lugar", "Departamento": "departamento"},
                          "region": {"Cada región": "lugar"},
                          "ciudad": {"Cada lugar": "lugar"}}[nivel]
        opciones_grupo = {k: v for k, v in opciones_grupo.items() if not (v == "departamento" and n_deptos < 2)}
        if st.session_state.get(K("colores", "agrupar"), next(iter(opciones_grupo))) not in {**opciones_grupo, "Segmento": ""}:
            st.session_state.pop(K("colores", "agrupar"))        # la opción elegida ya no aplica al área actual
        if zonas:
            opciones_grupo = {**opciones_grupo, "Segmento": ""}
        if len(opciones_grupo) > 1:
            c_etq, c_sel = st.columns([2, 3], vertical_alignment="center", gap="small")
            c_etq.markdown(t("Agrupar por"), help=t("Los lugares de un mismo grupo comparten color. «Segmento» usa "
                                                    "la columna Segmento de los datos."))
            grupo_txt = c_sel.selectbox(t("Agrupar por"), list(opciones_grupo), key=K("colores", "agrupar"), format_func=t,
                                        label_visibility="collapsed")
        else:
            grupo_txt = next(iter(opciones_grupo))
        grupos_geo = opciones_grupo[grupo_txt]
        relleno = "zona"
        colores_zona = bloque_categorias(f"d_{grupos_geo or 'seg'}", grupos_geo)
    st.divider()
    with st.container(key="colores_fijos"):
        st.markdown(f"**{t('Otros colores')}**")

        def fila_color(etiqueta, valor, clave, ayuda, **extra):
            """Nombre (con ayuda) a la izquierda y el cuadro de color a la derecha, centrados en vertical."""
            with st.container(horizontal=True, vertical_alignment="center", gap="xsmall", wrap=False, key=f"fila_color_{clave}"):
                st.markdown(t(etiqueta), help=t(ayuda))
                return st.color_picker(t(etiqueta), valor, key=K("colores", clave), label_visibility="collapsed", **extra)

        color_sin_dato = fila_color("Sin datos", "#D4D7DC", "color_sin_dato", "Lugares del área sin valor.")
        color_contexto = fila_color("Resto del país", "#E5E3DE", "color_contexto", "Zona del país fuera del área "
                                                                                   "elegida.")
        color_vecinos = fila_color("Países vecinos", "#EFEDE8", "color_vecinos",
                                   "Color de los países vecinos.")
        color_fondo = fila_color("Fondo", "#FFFFFF", "color_fondo",
                                 "Color detrás del título, la leyenda y los márgenes. Sin color de mar, también se "
                                 "aplica al mar.")
        with st.container(horizontal=True, vertical_alignment="center", gap="xsmall", wrap=False, key="fila_color_mar"):
            mar_activo = st.toggle(t("Mar"), value=True, key=K("colores", "mar_propio"),
                                   help=t("Aplica un color al mar alrededor del país. Si está apagado, el mar usa el "
                                          "color del fondo."))
            color_mar = st.color_picker(t("Mar"), "#DDE3EA", key=K("colores", "color_oceano"),
                                        label_visibility="collapsed", disabled=not mar_activo)
        color_oceano = color_mar if mar_activo else None
    boton_restablecer("colores")

def fila_linea(clave: str, *, fila_key: str | None = None):
    """Fila de Líneas y límites: tres celdas (color, nombre y grosor) con medidas fijas por CSS."""
    return st.container(horizontal=True, vertical_alignment="center", gap="xxsmall", wrap=False,
                        key=f"linea_{fila_key or clave}_{nivel}")






def capa_linea(titulo: str, clave: str, activa: bool, color: str, grosor: float, ayuda: str):
    """Capa de líneas en una fila: color, nombre, tipo y grosor (0 = apagada). Devuelve (color, grosor, tipo)."""
    clave_gro = K("bordes", f"gro_{clave}_{nivel}")
    apagada = st.session_state.get(clave_gro, grosor if activa else 0.0) == 0
    with fila_linea(clave):
        col = st.color_picker(t(titulo), color, key=K("bordes", f"col_{clave}_{nivel}"), label_visibility="collapsed",
                              disabled=apagada)
        st.markdown(t(titulo), help=t(ayuda))
        tipo = tipo_de_linea(titulo, f"{clave}_{nivel}", apagada)
        gro = st.number_input(t(titulo), 0.0, 5.0, grosor if activa else 0.0, 0.1, format="%.1f", key=clave_gro,
                              label_visibility="collapsed")
    return col, gro, tipo


with exp_lineas:
    with fila_linea("encabezado"):
        st.markdown(f'<p class="etq-campo etq-centro">{t("Color")}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="etq-campo">{t("Línea")}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="etq-campo etq-centro">{t("Tipo")}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="etq-campo etq-centro">{t("Grosor")}</p>', unsafe_allow_html=True)
    borde_depto_color, borde_depto_grosor, borde_depto_tipo, borde_tipo = "#FFFFFF", 0.0, "continua", "continua"
    if nivel == "municipio":
        borde_color, borde_grosor, borde_tipo = capa_linea("Entre municipios", "mun", True, "#FFFFFF", 0.5,
                                               "Separan cada municipio de sus vecinos.")
        borde_depto_color, borde_depto_grosor, borde_depto_tipo = capa_linea("Límite departamental", "dep", True, "#FFFFFF", 2.0,
                                                           ("Línea más gruesa en el límite de cada departamento, "
                                                            "sobre los municipios."))
    elif nivel == "departamento":
        borde_color, borde_grosor, borde_tipo = capa_linea("Entre departamentos", "dep", True, "#FFFFFF", 1.0,
                                               "Separan cada departamento de sus vecinos.")
    elif nivel == "ciudad":
        borde_color, borde_grosor, borde_tipo = capa_linea(t("Entre {d}").format(d=t({"localidad": "localidades", "comuna": "comunas"}.get(
            gd.tipo_division(ciudad).lower(), "divisiones"))), "div", True,
                                               "#FFFFFF", 1.0, "Separan cada localidad o comuna de sus vecinas.")
        borde_depto_color, borde_depto_grosor, borde_depto_tipo = capa_linea("Límite del municipio", "lim", True, "#FFFFFF", 1.5,
                                                           "Línea alrededor de todo el municipio.")
    else:
        borde_color, borde_grosor, borde_tipo = capa_linea("Entre regiones", "reg", True, "#FFFFFF", 2.0,
                                               "Separan cada región de sus vecinas.")
        borde_depto_color, borde_depto_grosor, borde_depto_tipo = capa_linea("Límite departamental", "dep", True, "#FFFFFF", 0.5,
                                                           "Líneas de los departamentos dentro de cada región.")
    contorno_area_color, contorno_area_grosor, contorno_area_tipo = capa_linea("Contorno del área", "area", False, "#26302E", 2.0,
                                                           "Línea alrededor de toda el área elegida.")
    if not contorno_area_grosor:
        contorno_area_color = None
    colores_grupo, contorno_grupo_grosor, contorno_grupo_tipo = {}, 0.0, "continua"
    if zonas and not grupos_geo:
        # sin cuadro de color: la línea toma el color de cada segmento
        with fila_linea("segmento"):
            st.markdown("&nbsp;")
            st.markdown(t("Línea de segmento"), help=t("Útil con mapa de calor: el relleno muestra el valor y la línea "
                                                         "indica el segmento de cada lugar."))
            contorno_grupo_tipo = tipo_de_linea("Línea de segmento", "segmento")
            contorno_grupo_grosor = st.number_input(
                t("Línea de segmento"), 0.0, 5.0, 2.25 if relleno in ("valor", "zona_total") else 0.0, 0.25, format="%.1f",
                key=K("bordes", "contorno_grupo_grosor"), label_visibility="collapsed")
        if contorno_grupo_grosor:
            colores_grupo = dict(colores_zona)
    boton_restablecer("bordes")

with caja_vista:
    st.divider()
    amp_on = st.toggle(t("Ampliar una parte del mapa"), value=False, key=K("amp", "amp_on"),
                       help=t("Lupa sobre lugares pequeños: se dibujan ampliados en un recuadro."))
    ampliar, ampliar_forma, ampliar_tam, ampliar_nombres = [], "cuadrada", 0.37, True
    tam_amp, estilo_amp, color_amp, tipo_amp = 8.0, [], None, ""
    if not amp_on:
        nombres_amp = []
    elif nivel == "municipio":
        ops = gd.lista_municipios(deptos or None)
        if municipios:
            ops = ops[(ops.departamento + "|" + ops.municipio).isin(set(municipios))]
        nombres_amp = sorted(ops.municipio.unique())
    elif nivel == "departamento":
        nombres_amp = deptos or gd.lista_departamentos(incluir_insular=False)
    elif nivel == "ciudad":
        c_ = gd.ciudades()
        nombres_amp = divisiones or c_[(c_.ciudad == ciudad) & (ciudad_rural | ~c_.rural)].division.tolist()
    else:
        nombres_amp = regiones or gd.lista_regiones()
    if amp_on:
        ampliar = st.multiselect(t("Lugares a ampliar"), nombres_amp, key=K("amp", f"amp_{nivel}"),
                                 placeholder=t("Seleccionar lugares cercanos"), format_func=t)
        c_af, c_af_sel = st.columns([1, 3.4], vertical_alignment="center", gap="small")
        c_af.markdown(f'<p class="etq-campo">{t("Forma")}</p>', unsafe_allow_html=True)
        forma_txt = c_af_sel.selectbox(t("Forma"), ["Cuadrada", "Redonda"], key=K("amp", "amp_forma"), format_func=t,
                                       label_visibility="collapsed")
        ampliar_forma = "redonda" if forma_txt == "Redonda" else "cuadrada"
        c_at, c_at_sl = st.columns([1, 3.4], vertical_alignment="center", gap="small")
        c_at.markdown(f'<p class="etq-campo">{t("Tamaño")}</p>', unsafe_allow_html=True)
        nivel_amp = c_at_sl.slider(t("Tamaño de la lupa"), 1, 5, 3, key=K("amp", "amp_nivel_lupa"), label_visibility="collapsed")
        ampliar_tam = {1: 0.18, 2: 0.27, 3: 0.37, 4: 0.48, 5: 0.62}[nivel_amp]
        with st.container(horizontal=True, vertical_alignment="center", gap="xsmall", key="fila_aa_amp"):
            ampliar_nombres = st.checkbox(t("Nombrar lugares ampliados"), value=True, key=K("amp", "ampliar_nombres"))
            if ampliar_nombres:
                boton_aa("amp")
        hueco_amp = st.container(key="hueco_aa_amp")
        if ampliar_nombres:
            with hueco_amp, panel_aa("amp"):
                tam_amp, estilo_amp, color_amp, _, tipo_amp = panel_texto(
                    "amp", t("Nombres de los lugares ampliados"), "amp", (4, 14, 8, "tam_amp"), "amp", [], "#1F2A28")

with caja_orient:
    minimapa = st.toggle(t("Mostrar minimapa"), value=True, disabled=not (hay_seleccion and acercar),
                         help=t("Mapa reducido de Colombia que indica la ubicación del área. Solo aplica con el "
                                 "mapa acercado."), key=K("mini", "minimapa"))
    minimapa_pos, minimapa_tam = "auto", 0.22
    if minimapa and hay_seleccion and acercar:      # posición y tamaño solo se ven con el minimapa activo
        c_pos, c_pos_sel = st.columns([1, 3.4], vertical_alignment="center", gap="small")
        c_pos.markdown(f'<p class="etq-campo">{t("Posición")}</p>', unsafe_allow_html=True)
        pos_txt = c_pos_sel.selectbox(t("Posición"), ["Automática", "Arriba a la izquierda",
                                                      "Arriba a la derecha", "Abajo a la izquierda", "Abajo a la derecha"],
                                      key=K("mini", "pos_txt"), format_func=t, label_visibility="collapsed")
        minimapa_pos = {"Auto": "auto", "Arri": "sup-", "Abaj": "inf-"}[pos_txt[:4]]
        if minimapa_pos != "auto":
            minimapa_pos += "izq" if "izquierda" in pos_txt else "der"
        c_tm, c_tm_sl = st.columns([1, 3.4], vertical_alignment="center", gap="small")
        c_tm.markdown(f'<p class="etq-campo">{t("Tamaño")}</p>', unsafe_allow_html=True)
        nivel_mini = c_tm_sl.slider(t("Tamaño del minimapa"), 1, 5, 3, key=K("mini", "minimapa_nivel"), label_visibility="collapsed")
        minimapa_tam = {1: 0.12, 2: 0.17, 3: 0.22, 4: 0.28, 5: 0.35}[nivel_mini]
    with st.container(horizontal=True, horizontal_alignment="center", gap="medium", wrap=False):
        escala_km = st.toggle(t("Escala (km)"), value=False, key=K("mini", "escala_km"))
        norte = st.toggle(t("Norte"), value=False, key=K("mini", "norte"))

with caja_vista:
    boton_restablecer("mini", "vista", "amp")







with exp_etq:
    etq_on, hueco_etq = fila_con_aa("etq", "Etiquetas en el mapa", "Ranking, valores o nombres de los lugares.",
                                  ("etq", "etq_on"))
    etiquetas, top_n, ranking_modo, ranking_pos = "ninguna", 5, "ambos", "derecha"
    if etq_on:
        c_tx, c_tx_sel = st.columns([1, 1.8], vertical_alignment="center", gap="small")
        c_tx.markdown(f'<p class="etq-campo">{t("Texto")}</p>', unsafe_allow_html=True)
        etq_txt = c_tx_sel.selectbox(t("Texto sobre el mapa"), ["Ranking", "Valor", "Nombre", "Nombre y valor"],
                                     key=K("etq", "etq_txt"), format_func=t, label_visibility="collapsed")
        etiquetas = {"Ranking": "ranking", "Valor": "valor", "Nombre": "nombre", "Nombre y valor": "nombre_valor"}[etq_txt]
    if etiquetas == "ranking":
        c_tn, c_tn_num = st.columns([2.4, 1], vertical_alignment="center", gap="small")
        c_tn.markdown(t("Cantidad"), help=t("Lugares del ranking, de 1 a 50."))
        top_n = int(c_tn_num.number_input(t("Cantidad en el ranking"), 1, 50, 10, key=K("etq", "top_n"), label_visibility="collapsed"))
        c_mr, c_mr_sel = st.columns([1, 1.8], vertical_alignment="center", gap="small")
        c_mr.markdown(t("Mostrar"), help=t("Con muchos lugares pequeños (municipios de todo el país), los números sobre el "
                                            "mapa se vuelven ilegibles; la lista lateral siempre se lee bien."))
        modo_txt = c_mr_sel.selectbox(t("Mostrar el ranking"), ["Números y lista", "Solo lista", "Solo números"],
                                      key=K("etq", "modo_txt"), format_func=t, label_visibility="collapsed")
        ranking_modo = {"Números y lista": "ambos", "Solo lista": "lista", "Solo números": "mapa"}[modo_txt]
        if ranking_modo != "mapa":
            with st.container(horizontal=True, vertical_alignment="center", gap="xsmall", key="fila_lista_aa"):
                st.markdown(t("Lista"), help=t("Lado de la imagen donde va la lista del ranking."))
                pos_lista = st.selectbox(t("Posición de la lista"), ["Derecha", "Izquierda", "Arriba", "Abajo"],
                                         key=K("etq", "pos_lista"), format_func=t, label_visibility="collapsed")
                boton_aa("lista")
            ranking_pos = pos_lista.lower()
            hueco_lista = st.container(key="hueco_aa_lista")
    valor_junto = "debajo"
    if etiquetas == "nombre_valor":
        c_vj, c_vj_sel = st.columns([1, 1.8], vertical_alignment="center", gap="small")
        c_vj.markdown(f'<p class="etq-campo">{t("Valor")}</p>', unsafe_allow_html=True)
        vj_txt = c_vj_sel.selectbox(t("Valor"), ["Debajo del nombre", "Al lado del nombre", "Entre paréntesis"],
                                    key=K("etq", "valor_junto"), format_func=t, label_visibility="collapsed")
        valor_junto = {"Debajo del nombre": "debajo", "Al lado del nombre": "lado", "Entre paréntesis": "parentesis"}[vj_txt]
    etiqueta_tam, estilo_etiquetas, color_marcador, color_etiquetas, tipo_etiquetas = 8.0, [], None, None, ""
    tam_lista, estilo_lista, color_lista, tipo_lista = 10, [], None, ""
    if etq_on:
        with hueco_etq, panel_aa("etq"):
            ranking = etiquetas == "ranking"
            etiqueta_tam, estilo_etiquetas, color_etiquetas, _, tipo_etiquetas = panel_texto(
                "etq", t("Etiquetas"), "etq", (4, 14, 6 if nivel == "municipio" else 8, "etiqueta_tam"), "etq", [], "#1F2A28",
                marcador=pal.tonos(colores, n_tonos, invertir)[-1] if ranking else None,
                ayuda_tam="Tamaño de los marcadores, en puntos." if ranking else "Tamaño de letra, en puntos.", con_numeros=True)
            color_marcador = st.session_state.get(K("etq", "color_marcador")) if ranking else None
        if etiquetas == "ranking" and ranking_modo != "mapa":       # la lista del ranking tiene su propio texto
            with hueco_lista, panel_aa("lista"):
                tam_lista, estilo_lista, color_lista, _, tipo_lista = panel_texto(
                    "etq", t("Lista del ranking"), "lista", (5, 14, 10, "tam_lista"), "lista", [], colores_texto(color_fondo)["titulo"])

with exp_etq:
    st.divider()
    resumen, hueco_res = fila_con_aa("res", "Resumen de los datos", "Total, promedio, valor mayor y menor, y primeros y últimos lugares.",
                                   ("res", "resumen"))
    resumen_items, resumen_n, resumen_en_imagen = ["total", "promedio", "max_min", "mayores"], 5, False
    tam_resumen, estilo_resumen, color_resumen, tipo_resumen = 9.0, [], None, ""
    if resumen:
        resumen_items = st.multiselect(t("Contenido del resumen"), list(RES_OPC), default=resumen_items,
                                       format_func=lambda x, _f=(RES_OPC.get): t(_f(x)), key=K("res", "resumen_items"))
        if "mayores" in resumen_items or "menores" in resumen_items:
            c_rn, c_rn_num = st.columns([2.4, 1], vertical_alignment="center", gap="small")
            c_rn.markdown(t("Cantidad"), help=t("Lugares en Los mayores y Los menores, de 1 a 100."))
            resumen_n = int(c_rn_num.number_input(t("Cantidad de mayores y menores"), 1, 100, 5, key=K("res", "resumen_n"),
                                                  label_visibility="collapsed"))
        resumen_en_imagen = st.checkbox(t("Incluir en la imagen descargada"), value=True, key=K("res", "resumen_en_imagen"),
                                        help=t("Si no se marca, el resumen solo aparece en la app."))
        with hueco_res, panel_aa("res"):
            tam_resumen, estilo_resumen, color_resumen, _, tipo_resumen = panel_texto(
                "res", t("Resumen"), "res", (6, 14, 9, "tam_resumen"), "res", [], colores_texto(color_fondo)["resumen"],
                con_numeros=not etq_on)
    # decimales y sufijo valen para etiquetas, resumen y extremos de la leyenda
    ley_valores = (st.session_state.get(K("ley", "leyenda"), True)
                   and st.session_state.get(K("ley", "extremos"), "Texto") == "Valor mínimo y máximo")
    decimales, sufijo = 0, ""
    if etq_on or resumen:  # los campos están en el panel Aa de las etiquetas o, sin ellas, del resumen
        decimales = st.session_state.get(K("etq", "decimales"), 0)
        sufijo = st.session_state.get(K("etq", "sufijo"), "")
    elif ley_valores:
        st.divider()
        decimales, sufijo = fila_numeros("ley")
    boton_restablecer("etq", "res")

with exp_titulo:
    # un panel con los cinco textos; el script muestra el activo
    panel = st.container(key="panel_texto")
    ct = colores_texto(color_fondo)  # colores automáticos; cada uno se puede cambiar
    with panel:
        titulo_tam, estilo_titulo, color_titulo, esp_titulo, tipo_titulo = panel_texto(
            "tit", t("Título"), "titulo", (8, 40, 17, "tam_tit"), "tit", ["Negrita"], ct["titulo"], "esp_tit")
        subtitulo_tam, estilo_subtitulo, color_subtitulo, esp_subtitulo, tipo_subtitulo = panel_texto(
            "tit", t("Subtítulo"), "subtitulo", (6, 30, 12, "tam_sub"), "sub", [], ct["sub"], "esp_sub")
        nota_tam, estilo_nota, color_nota, esp_nota, tipo_nota = panel_texto(
            "tit", t("Nota"), "nota", (5, 20, 8, "tam_nota"), "nota", [], ct["suave"], "esp_nota")
    st.divider()
    st.markdown(f'<p class="etq-campo etq-caja">{t("Título")}</p>', unsafe_allow_html=True)
    titulo = st.text_area(t("Título"), "", key=K("tit", "titulo"), label_visibility="collapsed", height="content",
                          placeholder=t("Escribir el título"))
    st.markdown(f'<p class="etq-campo etq-caja">{t("Subtítulo")}</p>', unsafe_allow_html=True)
    subtitulo = st.text_area(t("Subtítulo"), "", key=K("tit", "subtitulo"), label_visibility="collapsed", height="content",
                             placeholder=t("Escribir el subtítulo"))
    st.markdown(f'<p class="etq-campo etq-caja">{t("Nota")}</p>', unsafe_allow_html=True)
    fuente_nota = st.text_area(t("Nota o fuente"), "", key=K("tit", "fuente_nota"), label_visibility="collapsed",
                               height="content", placeholder=t("Escribir la nota o fuente"))
    # leyenda de color: sus textos se configuran aquí, con el mismo panel que el resto
    st.divider()
    leyenda = st.toggle(t("Mostrar leyenda de color"), value=True, key=K("ley", "leyenda"))
    leyenda_titulo, estilo_leyenda, leyenda_tam, color_leyenda, esp_leyenda, tipo_leyenda = "ESCALA", ["negrita"], 13, None, 0.0, ""
    extremos, texto_menor, texto_mayor, extremos_tam, estilo_extremos, color_extremos, tipo_extremos = (
        "Texto", "MENOR", "MAYOR", 11, [], None, "")
    extremos_tam_der, estilo_extremos_der, color_extremos_der, tipo_extremos_der = 11, [], None, ""
    esp_leyenda_extremos = esp_leyenda_extremos_der = 0.0
    if leyenda:
        with panel:
            leyenda_tam, estilo_leyenda, color_leyenda, esp_leyenda, tipo_leyenda = panel_texto(
                "ley", t("Leyenda"), "ley", (8, 24, 13, "tam_ley"), "ley", ["Negrita"], ct["leyenda"], "esp_ley")
            extremos_tam, estilo_extremos, color_extremos, esp_leyenda_extremos, tipo_extremos = panel_texto(
                "ley", t("Texto izquierdo"), "ext", (6, 20, 11, "tam_extremos"), "ext", [], ct["suave"], "esp_ley_ext")
            extremos_tam_der, estilo_extremos_der, color_extremos_der, esp_leyenda_extremos_der, tipo_extremos_der = panel_texto(
                "ley", t("Texto derecho"), "extd", (6, 20, 11, "tam_extremos_der"), "extd", [], ct["suave"], "esp_ley_ext_der")
        st.markdown(f'<p class="etq-campo etq-caja">{t("Título de la leyenda")}</p>', unsafe_allow_html=True)
        leyenda_titulo = st.text_area(
            t("Título de la leyenda"), t(TITULO_GRUPO[grupos_geo]) if relleno in ("zona", "zona_valor") else t("ESCALA"),
            key=K("ley", f"ley_tit_{relleno in ('zona', 'zona_valor')}_{grupos_geo}"), label_visibility="collapsed",
            height="content")
        c_ext, c_ext_sel = st.columns([1.15, 1], vertical_alignment="center", gap="small")
        c_ext.markdown(f'<p class="etq-campo">{t("Extremos de la leyenda")}</p>', unsafe_allow_html=True)
        extremos = c_ext_sel.selectbox(t("Extremos de la leyenda"), ["Texto", "Valor mínimo y máximo"], key=K("ley", "extremos"),
                                       format_func=lambda v: t("Valor mín. y máx.") if v.startswith("Valor") else t(v),
                                       label_visibility="collapsed")
        if extremos == "Texto":
            c_t1, c_t2 = st.columns(2, gap="xsmall")
            texto_menor = c_t1.text_input(t("Texto izquierdo"), t("MENOR"), key=K("ley", "texto_menor"))
            texto_mayor = c_t2.text_input(t("Texto derecho"), t("MAYOR"), key=K("ley", "texto_mayor"))
    boton_restablecer("tit", "ley")

with caja_descarga:
    c_prop, c_prop_op = st.columns([2, 3], vertical_alignment="center", gap="small")
    c_prop.markdown(t("Proporción"), help=t("Forma de la imagen. Automática se adapta al área elegida."))
    prop_txt = c_prop_op.selectbox(t("Proporción"), ["Automática", "Cuadrada (1:1)", "Vertical (4:5)", "Horizontal (16:9)"], key=K("expo", "prop_txt"),
                                   format_func=t, label_visibility="collapsed")
    proporcion = {"Auto": "auto", "Cuad": "cuadrado", "Vert": "vertical", "Hori": "horizontal"}[prop_txt[:4]]
    boton_restablecer("expo")
# el control está en Descargar; la vista previa siempre usa DPI_VISTA
dpi = st.session_state.get(K("expo", "dpi"), st.session_state.get("_dpi_guardado", 200))


estilo = Estilo(
    nivel=nivel, deptos=deptos, municipios=municipios, regiones=regiones, ciudad=ciudad, ciudad_rural=ciudad_rural,
    # etiquetas y demás textos del mapa: la tipografía del título
    divisiones=divisiones, mostrar_depto_completo=ver_depto, mostrar_isla=mostrar_isla, idioma=L, fuente=tipo_titulo,
    tipo_titulo=tipo_titulo, tipo_subtitulo=tipo_subtitulo, tipo_nota=tipo_nota, tipo_leyenda=tipo_leyenda,
    tipo_extremos=tipo_extremos, tipo_extremos_der=tipo_extremos_der, extremos_tam_der=float(extremos_tam_der),
    estilo_extremos_der=estilo_extremos_der, color_extremos_der=color_extremos_der,
    esp_leyenda_extremos_der=esp_leyenda_extremos_der, escala_km=escala_km, norte=norte,
    resumen=resumen, resumen_items=resumen_items, resumen_n=resumen_n, resumen_en_imagen=resumen_en_imagen,
    tam_lista=float(tam_lista), estilo_lista=estilo_lista, color_lista=color_lista, tipo_lista=tipo_lista,
    tam_resumen=float(tam_resumen), estilo_resumen=estilo_resumen, color_resumen=color_resumen, tipo_resumen=tipo_resumen,
    tipo_etiquetas=tipo_etiquetas, color_etiquetas=color_etiquetas,
    ampliar=ampliar, ampliar_tam=ampliar_tam, ampliar_forma=ampliar_forma, ampliar_nombres=ampliar_nombres,
    tam_amp=float(tam_amp), estilo_amp=estilo_amp, color_amp=color_amp, tipo_amp=tipo_amp,
    encuadre="seleccion" if (hay_seleccion and acercar) else "pais",
    mostrar_resto_pais=resto, mostrar_vecinos=vecinos,
    colores=colores, n_tonos=n_tonos, invertir=invertir, escala=escala, grupos_geo=grupos_geo,
    # si los datos solo traen zonas (sin valores), se pinta por zona automáticamente
    relleno=(relleno if relleno not in ("valor", "zona_total") or tabla is None or tabla.valor.notna().any()
             else "zona")
    if colores_zona else "valor", colores_zona=colores_zona, zona_agregar=zona_agregar,
    zona_rol=zona_rol, zona_escala=zona_escala,
    estilo_titulo=estilo_titulo, estilo_subtitulo=estilo_subtitulo, estilo_nota=estilo_nota,
    estilo_leyenda=estilo_leyenda, estilo_etiquetas=estilo_etiquetas, estilo_extremos=estilo_extremos,
    color_titulo=color_titulo, color_subtitulo=color_subtitulo, color_nota=color_nota, color_leyenda=color_leyenda,
    color_extremos=color_extremos, esp_titulo=esp_titulo, esp_subtitulo=esp_subtitulo, esp_nota=esp_nota,
    esp_leyenda=esp_leyenda, esp_leyenda_extremos=esp_leyenda_extremos,
    estilo_borde=borde_tipo, estilo_borde_depto=borde_depto_tipo, estilo_contorno_area=contorno_area_tipo,
    estilo_contorno_grupo=contorno_grupo_tipo,
    color_sin_dato=color_sin_dato, color_contexto=color_contexto, color_fondo=color_fondo,
    color_vecinos=color_vecinos, color_oceano=color_oceano,
    borde_color=borde_color, borde_grosor=borde_grosor,
    borde_depto_color=borde_depto_color, borde_depto_grosor=borde_depto_grosor,
    contorno_area_color=contorno_area_color, contorno_area_grosor=contorno_area_grosor,
    colores_grupo=colores_grupo, contorno_grupo_grosor=contorno_grupo_grosor,
    minimapa=minimapa, minimapa_pos=minimapa_pos, minimapa_tam=minimapa_tam,
    leyenda=leyenda, leyenda_titulo=leyenda_titulo,
    leyenda_extremos="texto" if extremos == "Texto" else "valores",
    texto_menor=texto_menor, texto_mayor=texto_mayor, leyenda_tam=leyenda_tam, extremos_tam=extremos_tam,
    etiquetas=etiquetas, top_n=top_n, ranking_modo=ranking_modo, ranking_pos=ranking_pos, etiqueta_tam=float(etiqueta_tam), valor_junto=valor_junto, color_marcador=color_marcador,
    decimales=int(decimales), sufijo=sufijo, titulo=titulo, subtitulo=subtitulo, fuente_nota=fuente_nota,
    titulo_tam=float(titulo_tam), subtitulo_tam=float(subtitulo_tam), nota_tam=float(nota_tam),
    proporcion=proporcion, dpi=DPI_VISTA,
)

# Crédito fijo en la parte inferior de la barra lateral
sb.markdown(f'<div class="credito">{t("Por Fabián Torres")}</div>', unsafe_allow_html=True)

# Acordeón: al abrir una sección se cierran las demás (lo simula el script)
st.iframe(SCRIPT, height=1)

with tab_mapa:
    with st.spinner(t("Dibujando el mapa...")):
        png, info = render(tabla, asdict(estilo), "png")
    cola = st.session_state.setdefault("cola", [])

    for _item in cola:   # cada mapa guardado lleva un id propio (las casillas de selección dependen de él)
        if "id" not in _item:
            st.session_state["_cola_id"] = st.session_state.get("_cola_id", 0) + 1
            _item["id"] = st.session_state["_cola_id"]

    def alternar_galeria():
        st.session_state["cola_galeria"] = not st.session_state.get("cola_galeria")
        st.session_state["cola_sel"] = None

    def elegir_mapa_cola(i):
        st.session_state["cola_sel"] = None if st.session_state.get("cola_sel") == i else i

    def vista_guardada(item):
        """Vista del mapa guardado: se reutiliza la imagen del momento de guardarlo (sin volver a dibujar)."""
        return item.get("png") or render(item["tabla"], {**item["estilo"], "dpi": DPI_VISTA}, "png")[0]

    def volver_a_miniaturas():
        st.session_state["cola_sel"] = None

    def eliminar_de_cola(ids):
        cola[:] = [x for x in cola if x["id"] not in ids]
        for i in ids:
            st.session_state.pop(f"sel_{i}", None)
        st.session_state["cola_sel"] = None
        if not cola:
            st.session_state["cola_galeria"] = False

    def marcar_todos():
        for x in cola:
            st.session_state[f"sel_{x['id']}"] = st.session_state["sel_todos"]

    def zip_de_cola(items, fmt):
        buf, usados = io.BytesIO(), {}
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for item in items:
                base = re.sub(r"[^\w\-]+", "_", item["nombre"]).strip("_") or "mapa"
                usados[base] = usados.get(base, 0) + 1
                nom = base if usados[base] == 1 else f"{base}_{usados[base]}"
                zf.writestr(f"{nom}.{fmt}", render(item["tabla"], item["estilo"], fmt)[0])
        return buf.getvalue()

    def formato_cola(en_linea=False):
        fmt = st.selectbox(t("Formato"), FORMATOS, index=FORMATOS.index(st.session_state.get("_fmt_cola", FORMATOS[0])),
                           key="fmt_zip", format_func=str.upper, label_visibility="collapsed" if en_linea else "visible")
        st.session_state["_fmt_cola"] = fmt
        return fmt

    galeria_abierta = bool(st.session_state.get("cola_galeria")) and bool(cola)

    with tarjeta:
        # iconos arriba a la derecha del mapa; cada uno abre su panel
        with hueco_iconos:
            if info["fuera_del_area"]:
                with st.popover(":material/warning:", help=t("Hay datos fuera del área elegida")):
                    st.markdown('<span class="cuerpo-panel"></span>', unsafe_allow_html=True)
                    st.warning(t("{n} lugares de los datos están fuera del área elegida y no se dibujan.").format(n=info['fuera_del_area']))
            if info.get("resumen"):
                with st.popover(":material/summarize:", help=t("Resumen de los datos")):
                    st.markdown('<span class="cuerpo-panel"></span><p class="tit-panel">' + t("Resumen")
                                + ("" if estilo.resumen_en_imagen else f' <span>· {t("solo en la app")}</span>') + "</p>",
                                unsafe_allow_html=True)
                    for linea in lineas_resumen(info["resumen"], estilo):
                        st.markdown(rotulos_en_negrita(linea))
            # cola de mapas: guardar varios y descargarlos juntos
            with st.popover(":material/layers:" + (f" {len(cola)}" if cola else "")):
                st.markdown(f'<span class="cuerpo-panel cuerpo-cola"></span><p class="tit-panel">{t("Mapas guardados")} '
                            f'<span>{len(cola)} / {COLA_MAX}</span></p>', unsafe_allow_html=True)
                st.caption(t("Guardar el mapa con su configuración actual. Pueden guardarse varios y descargarse "
                              "juntos en un ZIP (máximo {m}).").format(m=COLA_MAX))
                nombre_cola = st.text_input(t("Nombre de este mapa"), value=f"mapa_{len(cola) + 1}", key=f"nom_cola_{len(cola)}")
                if st.button(t(":material/add: Guardar este mapa"), disabled=len(cola) >= COLA_MAX, width="stretch"):
                    st.session_state["_cola_id"] = st.session_state.get("_cola_id", 0) + 1
                    cola.append({"id": st.session_state["_cola_id"], "nombre": (nombre_cola or f"mapa_{len(cola) + 1}").strip(),
                                 "estilo": {**asdict(estilo), "dpi": dpi}, "tabla": None if tabla is None else tabla.copy(), "png": png})
                    st.toast(t("«{x}» guardado ({n}/{m}).").format(x=cola[-1]['nombre'], n=len(cola), m=COLA_MAX))
                    st.rerun()
                # lista compacta: dos por fila, cada uno con su X
                with st.container(horizontal=True, wrap=True, gap="xsmall", key="lista_cola"):
                    for i, item in enumerate(cola):
                        with st.container(horizontal=True, vertical_alignment="center", gap="xxsmall", wrap=False, key=f"cola_it_{i}"):
                            st.markdown(f"{i + 1}. {item['nombre']}")
                            if st.button(":material/close:", key=f"cola_x_{i}", type="tertiary", help=t("Quitar de los guardados")):
                                eliminar_de_cola({item["id"]})
                                st.rerun()
                if cola:
                    st.button(t(":material/visibility: Ver galería"), key="btn_galeria", on_click=alternar_galeria, width="stretch",
                              help=t("Ver las miniaturas de los mapas guardados sobre la zona del mapa"))
                    if not galeria_abierta:   # con la galería abierta estos controles están en su barra
                        with st.container(key="fila_zip"):
                            c_fmt_zip, c_zip, c_vaciar = st.columns(3, vertical_alignment="bottom", gap="xsmall")
                            with c_fmt_zip:
                                fmt_zip = formato_cola()
                            c_zip.download_button(t(":material/download: ZIP"), lambda: zip_de_cola(cola, fmt_zip),
                                                  file_name="mapas_de_calor.zip", on_click="ignore", width="stretch",
                                                  help=t("Descargar todos los mapas guardados en un ZIP"))
                            c_vaciar.button(t(":material/delete: Vaciar"), width="stretch",
                                            help=t("Eliminar todos los mapas guardados"),
                                            on_click=eliminar_de_cola, args=({x["id"] for x in cola},))
        if galeria_abierta:
            # galería: miniaturas; pulsar una la abre grande y pulsarla otra vez la cierra
            sel = st.session_state.get("cola_sel")
            if sel is not None and sel >= len(cola):
                sel = st.session_state["cola_sel"] = None

            def miniaturas(por_fila):
                for ini in range(0, len(cola), por_fila):
                    for i, col in zip(range(ini, min(ini + por_fila, len(cola))), st.columns(por_fila, gap="small"), strict=False):
                        item = cola[i]
                        with col.container(key=f"miniatura_{i}"):
                            if i == sel:
                                st.markdown('<span class="mini-sel"></span>', unsafe_allow_html=True)
                            st.image(vista_guardada(item))
                            st.button(item["nombre"], key=f"elegir_{i}", on_click=elegir_mapa_cola, args=(i,))
                            with st.container(horizontal=True, vertical_alignment="center", gap="xxsmall", wrap=False, key=f"pie_{i}"):
                                st.checkbox(f"{i + 1}. {item['nombre']}", key=f"sel_{item['id']}")
                                st.download_button(":material/download:", lambda x=item: render(x["tabla"], x["estilo"], fmt_zip)[0],
                                                   file_name=f"{item['nombre']}.{fmt_zip}", on_click="ignore", type="tertiary",
                                                   key=f"dl_{item['id']}", help=t("Descargar este mapa"))
                                st.button(":material/delete:", key=f"del_{item['id']}", type="tertiary", on_click=eliminar_de_cola,
                                          args=({item["id"]},), help=t("Eliminar este mapa"))

            marcados = [x for x in cola if st.session_state.get(f"sel_{x['id']}")]
            with st.container(key="galeria_cola"):
                with st.container(horizontal=True, vertical_alignment="center", key="cab_galeria"):
                    st.markdown(f'<p class="tit-panel">{t("Mapas guardados")} <span>{len(cola)} / {COLA_MAX}</span></p>' if sel is None
                                else f'<p class="tit-panel">{html.escape(cola[sel]["nombre"])}</p>', unsafe_allow_html=True)
                    if sel is None:
                        st.button(":material/close:", key="galeria_cerrar", type="tertiary", on_click=alternar_galeria, help=t("Cerrar galería"))
                    else:   # con un mapa abierto, la X vuelve a las miniaturas
                        st.button(":material/close:", key="galeria_volver", type="tertiary", on_click=volver_a_miniaturas, help=t("Volver a la galería"))
                    # lo pulsa el script al tocar la barra lateral
                    st.button("cerrar", key="cerrar_todo", on_click=alternar_galeria)
                if sel is None:
                    with st.container(horizontal=True, vertical_alignment="center", gap="small", key="barra_galeria"):
                        st.session_state["sel_todos"] = len(marcados) == len(cola)
                        st.checkbox(t("Seleccionar todos"), key="sel_todos", on_change=marcar_todos)
                        with st.container(horizontal=True, vertical_alignment="center", gap="xsmall", key="fmt_galeria"):
                            st.markdown(t("Formato"))
                            fmt_zip = formato_cola(en_linea=True)
                        st.download_button(t(":material/download: Descargar {n} seleccionados").format(n=len(marcados)) if marcados
                                           else t(":material/download: Descargar todos"),
                                           lambda: zip_de_cola(marcados or cola, fmt_zip), file_name="mapas_de_calor.zip",
                                           on_click="ignore", help=t("Descargar en un ZIP los mapas seleccionados, o todos si no hay selección"))
                        st.button(t(":material/delete: Eliminar seleccionados"), disabled=not marcados, on_click=eliminar_de_cola,
                                  args=({x["id"] for x in marcados},), help=t("Eliminar los mapas seleccionados"))
                        st.button(t(":material/delete_sweep: Eliminar todos"), on_click=eliminar_de_cola,
                                  args=({x["id"] for x in cola},), help=t("Eliminar todos los mapas guardados"))
                if sel is None:
                    miniaturas(5)
                else:
                    with st.container(key="mapa_grande"):
                        # lo pulsa el script al hacer clic fuera
                        st.button("volver", key="volver_min", on_click=elegir_mapa_cola, args=(sel,))
                        st.image(vista_guardada(cola[sel]), width="stretch")
        else:
            st.image(png, width="stretch")

# descarga: va en Exportación, necesita el mapa ya dibujado
with caja_descarga:
    c_fmt, c_fmt_op = st.columns([2, 3], vertical_alignment="center", gap="small")
    c_fmt.markdown(t("Formato"), help=t("PNG: imagen para presentaciones y documentos. JPG: imagen liviana para "
                                         "correo y web. TIFF: imagen para impresión profesional y publicaciones. "
                                         "SVG: vectorial, editable en Illustrator o Figma. PDF: vectorial, para "
                                         "impresión."))
    formato = c_fmt_op.selectbox(t("Formato"), FORMATOS, key=K("expo", "formato"), format_func=str.upper,
                                 label_visibility="collapsed")
    if formato in FORMATOS_IMAGEN:  # la resolución solo aplica a imágenes; con SVG o PDF no se muestra
        c_dpi, c_dpi_op = st.columns([2, 3], vertical_alignment="center", gap="small")
        c_dpi.markdown(t("Resolución"), help=t("Píxeles por pulgada (dpi) de la imagen. 100: pantalla o correo. "
                                                "150: presentaciones. 200: uso general. 300: impresión. 400 a 600: "
                                                "impresión en gran formato; el archivo es más pesado."))
        dpi = c_dpi_op.select_slider(t("Resolución"), [100, 150, 200, 300, 400, 600], key=K("expo", "dpi"),
                                     value=st.session_state.get("_dpi_guardado", 200), format_func=t, label_visibility="collapsed")
        st.session_state["_dpi_guardado"] = dpi   # se recuerda mientras el control está oculto
        # tamaño y peso estimados desde la vista previa
        px_w, px_h = struct.unpack(">II", png[16:24])
        k = dpi / DPI_VISTA
        miles = (lambda n: f"{n:,}") if L == "en" else (lambda n: f"{n:,}".replace(",", "."))
        medidas = f"≈ {miles(round(px_w * k))} × {miles(round(px_h * k))} px"
        if formato == "png":
            peso = len(png) * k * k
            peso_txt = f"{peso / 1e6:.1f} MB" if peso >= 1e6 else f"{peso / 1e3:.0f} KB"
            st.caption(f'<div class="cap-der">{t("{m} · peso aprox. {p}").format(m=medidas, p=peso_txt)}</div>',
                       unsafe_allow_html=True)
        else:
            st.caption(f'<div class="cap-der">{medidas}</div>', unsafe_allow_html=True)
    if formato == "png" and dpi == DPI_VISTA:
        archivo_final = png
    else:   # el archivo se dibuja solo al pulsar la descarga
        def archivo_final():
            return render(tabla, {**asdict(estilo), "dpi": dpi}, formato)[0]
    partes = {"region": regiones, "ciudad": [ciudad]}.get(nivel, deptos)
    nombre_archivo = "mapa_calor_" + ("_".join(gd.norm(d).lower() for d in partes[:3]) or "colombia")
    st.download_button(t(":material/download: Descargar {f}").format(f=formato.upper()), archivo_final,
                       file_name=f"{nombre_archivo}.{formato}", type="primary", width="stretch")
    # datos: segunda descarga con su formato y botón
    if tabla is not None and len(tabla):
        st.markdown('<hr class="separador">', unsafe_allow_html=True)
        st.markdown(f'<p class="tit-datos"><strong>{t("Datos")}</strong></p>', unsafe_allow_html=True)
        fila_datos = st.container(horizontal=True, vertical_alignment="center", gap="xsmall", key="fila_datos")
        fila_datos.markdown(t("Formato"), help=t("CSV y Excel: tabla con los valores del mapa. JSON y Parquet: la misma "
                                             "tabla, para análisis en Python, R o Power BI. GeoJSON: lugares con "
                                             "valor, segmento y color, para QGIS, Power BI o Tableau."))
        formato_datos = fila_datos.selectbox(t("Formato"), list(FORMATOS_DATOS), key=K("expo", "formato_datos"),
                                           format_func=FORMATOS_DATOS.get, label_visibility="collapsed")
        # encabezados como en la tabla de la app (la tabla interna usa nombres en minúscula)
        nombres = {"ciudad": "Ciudad", "departamento": "Departamento", "municipio": "Municipio", "region": "Región",
                   "division": "Localidad o comuna", "valor": "Valor", "grupo": "Segmento"}
        tabla_legible = tabla.rename(columns={c: t(n) for c, n in nombres.items()})
        if formato_datos == "csv":
            archivo_datos = tabla_legible.to_csv(index=False).encode("utf-8-sig")
        elif formato_datos == "xlsx":
            def archivo_datos():
                buf = io.BytesIO()
                tabla_legible.to_excel(buf, index=False, sheet_name=t("Datos"))
                return buf.getvalue()
        elif formato_datos == "json":
            archivo_datos = tabla_legible.to_json(orient="records", force_ascii=False, indent=2).encode("utf-8")
        elif formato_datos == "parquet":
            def archivo_datos():
                buf = io.BytesIO()
                tabla_legible.to_parquet(buf, index=False)
                return buf.getvalue()
        else:   # los polígonos se arman solo al pulsar la descarga
            archivo_datos = lambda: exportar_geojson(tabla, estilo)  # noqa: E731
        with fila_datos:
            st.download_button(":material/download:", archivo_datos, file_name=f"{nombre_archivo}.{formato_datos}")

with tab_ayuda:
    st.markdown(AYUDA_EN if st.session_state.get("idioma") == "EN" else AYUDA_ES)
