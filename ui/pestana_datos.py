"""Pestaña Datos: tabla editable, archivo subido y lectura de lugares."""
from __future__ import annotations

import hashlib
import html
from functools import partial

import pandas as pd
import streamlit as st

from ui.constantes import ANCHO_COLUMNA, AYUDA_SEG
from ui.descargas import tabla_en_formato
from ui.estado import K
from ui.textos import t
from mapacalor import datos as dt
from mapacalor import geodatos as gd


def hoja_sugerida(hojas: list[str]) -> int:
    """Primera hoja del Excel que no parezca de instrucciones."""
    return next((i for i, h in enumerate(hojas) if gd.norm(h) not in ("LEEME", "NOTAS", "INSTRUCCIONES")), 0)


def _deptos_del_archivo(df: pd.DataFrame, columna) -> list[str]:
    """Departamentos oficiales que aparecen en la columna (también por alias)."""
    if not columna:
        return []
    oficiales = {gd.norm(d): d for d in gd.lista_departamentos()}
    nombres = (oficiales.get(gd.norm(x)) or gd.ALIAS_DEPTO.get(gd.norm(x)) for x in df[columna].dropna())
    return sorted({n for n in nombres if n})


def _ciudad_del_archivo(df: pd.DataFrame, columna_division: str, cols: dict):
    """Ciudad del archivo: la de su columna Ciudad o, sin ella, la que más localidades reconoce."""
    col = next((c for k, c in cols.items() if k.startswith("ciudad")), None)
    nombres = df[col].dropna().astype(str).str.strip().unique() if col else []
    if len(nombres) == 1 and nombres[0] in gd.lista_ciudades():
        return nombres[0]
    lugares = {gd.norm(x) for x in df[columna_division].dropna().astype(str)}
    aciertos = {c: len(lugares & set(dt.opciones_division(c))) for c in gd.lista_ciudades()}
    mejor = max(aciertos, key=aciertos.get)
    return mejor if aciertos[mejor] else None


def area_del_archivo(clave_archivo: str):
    """Al subir un archivo, el área pasa a ser la de sus encabezados y lugares."""
    f = st.session_state.get(clave_archivo)
    if f is None:
        return
    st.session_state["area_adoptada"] = f.file_id
    try:
        hojas = dt.hojas_excel(f.name, f.getvalue())
        df = dt.leer_archivo(f.name, f.getvalue(), hoja_sugerida(hojas))
    except dt.ArchivoInvalido:
        return
    det = dt.detectar_columnas(df)
    cols = {gd.norm(c).lower(): c for c in df.columns}
    ss = st.session_state
    if det["division"]:
        ss[K("que", "nivel_txt")] = "Ciudades"
        ciudad = _ciudad_del_archivo(df, det["division"], cols)
        if ciudad:
            ss[K("que", "ciudad")] = ciudad
    elif any(k.startswith(("municipio", "mpio")) for k in cols):
        ss[K("que", "nivel_txt")] = "Municipios"
        ss[K("que", "deptos_mun")] = _deptos_del_archivo(df, det["departamento"])
        ss.pop(K("que", "municipios"), None)
    elif det["region"]:
        ss[K("que", "nivel_txt")] = "Regiones"
    elif det["departamento"]:
        deptos = _deptos_del_archivo(df, det["departamento"])
        if len(deptos) >= 30 or not deptos:
            ss[K("que", "nivel_txt")] = "Todo el país"
        else:
            ss[K("que", "nivel_txt")] = "Departamentos"
            ss[K("que", "deptos_dep")] = deptos


def pintar_fila_revisar(fila: pd.Series) -> list[str]:
    """Fila de la tabla subida con un lugar sin reconocer: se pinta toda en rojo claro."""
    return ["background-color: rgba(220, 60, 60, 0.22)" if pd.notna(fila["Estado"]) and fila["Estado"] else ""] * len(fila)


NADA = "(ninguna)"


def _opcional(columna: str):
    return None if columna == NADA else columna


def _columnas_detectadas(df_archivo: pd.DataFrame, nivel: str) -> dict:
    """Columnas reconocidas por los encabezados (Departamento, Municipio, Valor...)."""
    det = dt.detectar_columnas(df_archivo)
    col = {k: det[k] or NADA for k in ("region", "departamento", "division", "valor", "grupo")}
    col["municipio"] = (det["municipio"] or NADA) if nivel == "municipio" else NADA
    return col


def _tabla_base(base: pd.DataFrame, nivel: str, ciudad: str, lugares: list[str]) -> tuple[pd.DataFrame, list[str]]:
    """Agrega la columna informativa del nivel (departamentos de la región o ciudad elegida)."""
    lugares_fijos = list(lugares)
    if nivel == "region":
        deptos_de = {r: ", ".join(sorted(d for d, g in gd.REGION_DE.items() if g == r)) for r in base["Región"]}
        base = base.copy()
        base.insert(base.columns.get_loc("Región") + 1, "Departamentos", base["Región"].map(deptos_de))
        lugares_fijos.append("Departamentos")
    elif nivel == "ciudad":
        base = base.copy()
        base.insert(0, "Ciudad", ciudad)
        lugares_fijos.insert(0, "Ciudad")
    return base, lugares_fijos


def _editor_de_tabla(base: pd.DataFrame, ed_key: str, lugares_fijos: list[str]) -> pd.DataFrame:
    with st.container(key="caja_tabla"):  # el CSS ajusta el alto hasta el borde de la ventana
        return st.data_editor(
            base, key=ed_key, hide_index=True, width="stretch", disabled=lugares_fijos, height="stretch",
            column_config={"Valor": st.column_config.NumberColumn(t("Valor"), format="%.2f"),
                           "Segmento": st.column_config.TextColumn(t("Segmento"), help=t(AYUDA_SEG)),
                           "Departamento": st.column_config.TextColumn(t("Departamento")),
                           "Municipio": st.column_config.TextColumn(t("Municipio")),
                           "Ciudad": st.column_config.TextColumn(t("Ciudad")),
                           "Región": st.column_config.TextColumn(t("Región")),
                           "Departamentos": st.column_config.TextColumn(t("Departamentos")),
                           "Localidad o comuna": st.column_config.TextColumn(t("Localidad o comuna"))})


def _descargar_tabla(contenedor, editada: pd.DataFrame, nivel: str):
    with contenedor.popover(t(":material/download: Descargar"), width="content", help=t("Descargar la tabla tal como está.")):
        st.download_button(t(":material/download: Excel"), partial(tabla_en_formato, editada, "xlsx", t("Datos")), file_name=f"datos_{nivel}.xlsx", width="stretch",
                           key="dl_tabla_xlsx")
        st.download_button(t(":material/download: CSV"), editada.to_csv(index=False).encode("utf-8-sig"),
                           file_name=f"datos_{nivel}.csv", width="stretch", key="dl_tabla_csv")


def _editar_tabla(nivel, deptos, municipios, regiones, ciudad, ciudad_rural, divisiones, isla_en_mapa, clave, botones):
    """Origen «Editar tabla»: tabla de lugares del área con valores y segmentos escritos a mano."""
    col_lugar = {"departamento": ["Departamento"], "municipio": ["Departamento", "Municipio"],
                 "ciudad": ["Localidad o comuna"], "region": ["Región"]}[nivel]
    if "tablas" not in st.session_state:
        st.session_state.tablas = {}
    args = dict(deptos=deptos or None, municipios=municipios or None, regiones=regiones or None,
                ciudad=ciudad, rural=ciudad_rural, divisiones=divisiones or None, isla=isla_en_mapa)

    def crear_tabla(**extra):
        return dt.plantilla(nivel, **args, **extra)
    if clave not in st.session_state.tablas:
        st.session_state.tablas[clave] = crear_tabla(aleatorio=True)
    ed_key = f"ed_{clave}_{st.session_state.gen.get('datos', 0)}"
    if botones.button(t(":material/shuffle: Valores aleatorios"), width="content", help=t("Llena la tabla con valores ficticios aleatorios.")):
        st.session_state.tablas[clave] = crear_tabla(aleatorio=True, semilla=pd.Timestamp.now().microsecond)
        st.session_state.pop(ed_key, None)
    if botones.button(t(":material/restart_alt: Borrar datos"), width="content", help=t("Borra valores y segmentos. Los lugares se mantienen.")):
        st.session_state.tablas[clave] = crear_tabla()
        st.session_state.pop(ed_key, None)
    with st.container(key="leyenda_tabla"):
        st.caption(t("Valor: número de cada lugar (sin valor, se muestra en gris). Segmento: opcional, agrupa por zona, canal u otra categoría."))
    base, lugares_fijos = _tabla_base(st.session_state.tablas[clave], nivel, ciudad, col_lugar)
    editada = _editor_de_tabla(base, ed_key, lugares_fijos)
    st.session_state[f"_editada_{clave}"] = editada
    _descargar_tabla(botones, editada, nivel)
    if nivel == "ciudad":
        em = dt.emparejar_ciudad(editada, ciudad, "Localidad o comuna", "Valor", col_grupo="Segmento")
    elif nivel == "region":
        em = dt.emparejar(editada, None, "Valor", col_grupo="Segmento", nivel="region", col_region="Región")
    else:
        em = dt.emparejar(editada, "Departamento", "Valor",
                          col_muni="Municipio" if nivel == "municipio" else None, col_grupo="Segmento", nivel=nivel)
    return em.tabla


def _cuadro_de_subida(c_arch, clave_archivo: str):
    """Cuadro para subir el archivo. Devuelve el archivo, o None si no hay o no se puede leer."""
    # se reemplazan los textos del cuadro de subida por los del idioma elegido
    st.markdown("<style>"
                ".st-key-subida [data-testid='stBaseButton-secondary'] [data-testid='stMarkdownContainer']{display:none}"
                f".st-key-subida [data-testid='stBaseButton-secondary']::after{{content:'{t('Subir archivo')}';"
                "margin-left:0.4rem;font-size:0.875rem}"
                ".st-key-subida [data-testid='stFileUploaderDropzoneInstructions']{display:none}</style>",
                unsafe_allow_html=True)
    with c_arch.container(horizontal=True, vertical_alignment="center", gap="xsmall", wrap=False, key="fila_subida"):
        with st.container(key="subida"):
            archivo = st.file_uploader(t("Archivo"), type=["xlsx", "xls", "csv"], key=clave_archivo,
                                       label_visibility="collapsed", on_change=area_del_archivo, args=(clave_archivo,))
        if not archivo:
            # el signo de pregunta indica límite y formatos
            st.markdown("&nbsp;", help=t("Hasta 25 MB. XLSX, XLS o CSV"))
    if archivo:
        try:
            dt.leer_archivo(archivo.name, archivo.getvalue(), hoja_sugerida(dt.hojas_excel(archivo.name, archivo.getvalue())))
        except dt.ArchivoInvalido:
            st.error(t("No se pudo leer el archivo. Debe ser un Excel (XLSX o XLS) o un CSV con encabezados."))
            return None
    return archivo


def _lugares_por_revisar(df: pd.DataFrame, nivel: str, ciudad: str, col: dict):
    """Revisa cada fila: None si sus lugares son oficiales o (columna, sugerencia) del primero que no."""
    col_ciudad = next((c for c in df.columns if gd.norm(c).lower().startswith("ciudad")), None)
    por_region = (col["region"] if col["region"] != NADA else col["departamento"],
                  "region" if col["region"] != NADA else "departamento")
    columnas_lugar = {"region": [por_region],
                      "ciudad": ([(col_ciudad, "nombre_ciudad")] if col_ciudad else []) + [(col["division"], "ciudad")],
                      "municipio": [(col["departamento"], "departamento"), (col["municipio"], "municipio")]
                      }.get(nivel, [(col["departamento"], "departamento")])

    def revisar(fila):
        for c, tipo in columnas_lugar:
            texto = str(fila[c]).strip()
            if texto in ("", "nan"):
                continue
            exacto, sug = dt.revisar_lugar(tipo, texto, ciudad=ciudad,
                                           depto=str(fila[col["departamento"]]) if nivel == "municipio" else None)
            if not exacto:
                return c, sug or "-"
        return None
    return [revisar(f) for _, f in df.iterrows()], columnas_lugar


def _editor_de_archivo(trabajo: dict, clave_ed: str) -> pd.DataFrame:
    """Tabla del archivo; la columna Estado marca los lugares sin reconocer, con sugerencia."""
    with st.container(key="caja_tabla"):  # el CSS ajusta el alto hasta el borde de la ventana
        return st.data_editor(
            trabajo["df"].style.apply(pintar_fila_revisar, axis=1), key=f"ed_archivo_{clave_ed}_{trabajo['v']}",
            hide_index=True, width="stretch", height="stretch", disabled=["Estado"],
            column_config={
                **{c: st.column_config.Column(width=w) for c, w in ANCHO_COLUMNA.items() if c in trabajo["df"]},
                "Estado": st.column_config.TextColumn(t("Estado"), width=ANCHO_COLUMNA["Estado"]),
                "Corregir": st.column_config.CheckboxColumn(
                    t("Corregir"), width=ANCHO_COLUMNA["Corregir"],
                    help=t("Marcar para reemplazar el lugar por la sugerencia."))})


def _aplicar_correcciones(editado: pd.DataFrame, revisadas: list, trabajo: dict, clave_ed: str):
    """Casilla Corregir marcada: el lugar pasa a ser la sugerencia y la tabla se vuelve a dibujar."""
    if "Corregir" in editado and editado["Corregir"].any():
        nuevo = editado.copy()
        for i, r in enumerate(revisadas):
            if r and r[1] != "-" and editado["Corregir"].iloc[i]:
                nuevo.iloc[i, nuevo.columns.get_loc(r[0])] = r[1]
        nuevo["Corregir"] = False
        st.session_state[f"trabajo_{clave_ed}"] = {"df": nuevo, "v": trabajo["v"] + 1}
        st.rerun()


def _actualizar_estados(editado: pd.DataFrame, estados: list, hay_sugerencias: bool, trabajo: dict, clave_ed: str):
    """La tabla se vuelve a dibujar con las marcas de Estado al día."""
    if estados != trabajo["df"]["Estado"].tolist() or hay_sugerencias != ("Corregir" in trabajo["df"]):
        nuevo = editado.assign(Estado=estados)
        if hay_sugerencias and "Corregir" not in nuevo:
            nuevo["Corregir"] = False
        elif not hay_sugerencias and "Corregir" in nuevo:
            nuevo = nuevo.drop(columns="Corregir")
        st.session_state[f"trabajo_{clave_ed}"] = {"df": nuevo, "v": trabajo["v"] + 1}
        st.rerun()


def _leer_hoja(archivo, estado):
    """Hoja del Excel a leer (con selector si hay varias) y su tabla, con las celdas vacías en blanco."""
    with estado:
        hojas = dt.hojas_excel(archivo.name, archivo.getvalue())
        hoja = 0
        if len(hojas) > 1:
            hoja = st.selectbox(t("Hoja del Excel"), hojas, index=hoja_sugerida(hojas), format_func=t, label_visibility="collapsed",
                                width=170)
    df_archivo = dt.leer_archivo(archivo.name, archivo.getvalue(), hoja)
    df_archivo = df_archivo.apply(     # celdas vacías en blanco, no «None»
        lambda c: c.astype(object).fillna("") if c.isna().all() or not pd.api.types.is_numeric_dtype(c) else c)
    return hoja, df_archivo


def _tabla_de_lugares(df: pd.DataFrame, nivel: str, ciudad: str, col: dict, c_val: str, agregar: str) -> dt.Emparejado:
    if nivel == "ciudad":
        return dt.emparejar_ciudad(df, ciudad, col["division"], c_val, col_grupo=_opcional(col["grupo"]), agregar=agregar)
    return dt.emparejar(df, _opcional(col["departamento"]), c_val,
                        col_muni=_opcional(col["municipio"]) if nivel == "municipio" else None,
                        col_grupo=_opcional(col["grupo"]), nivel=nivel, agregar=agregar, col_region=_opcional(col["region"]))


def _columnas_que_faltan(nivel: str, col: dict) -> list[str]:
    por_nivel = {"region": col["region"] == NADA and col["departamento"] == NADA, "ciudad": col["division"] == NADA}
    return [n for n, falta_col in (
        ({"region": "Región", "ciudad": "Localidad o comuna"}.get(nivel, "Departamento"),
         por_nivel.get(nivel, col["departamento"] == NADA)),
        ("Valor", col["valor"] == NADA and col["grupo"] == NADA)) if falta_col]


def _estado_de_lectura(estado, em: dt.Emparejado, por_corregir: int, filas_con_lugar: int):
    with estado:
        if por_corregir:
            st.markdown(":orange[:material/warning: " + t("{n} lugares reconocidos, {m} por corregir.").format(
                n=filas_con_lugar - por_corregir, m=por_corregir) + "]")
        else:
            st.markdown(":green[:material/check_circle: " + t("{n} lugares reconocidos.").format(n=len(em.tabla)) + "]")
        if em.duplicados:
            st.markdown(":gray[" + t("{n} filas repetidas combinadas").format(n=em.duplicados) + "]")


def _revisar_archivo(archivo, nivel, ciudad, clave_area, clave_archivo, gen_datos, guardado, agregar, estado, aviso, b1):
    """Tabla del archivo subido: revisión de lugares, estado de la lectura y botón «Cargar datos»."""
    hoja, df_archivo = _leer_hoja(archivo, estado)
    # si la devolución de llamada no llegó, se aplica al inicio
    if st.session_state.get("area_adoptada") != archivo.file_id:
        st.session_state["area_pendiente"] = clave_archivo
        st.rerun()
    col = _columnas_detectadas(df_archivo, nivel)
    clave_ed = f"{archivo.file_id}_{hoja}_{gen_datos}"
    trabajo = st.session_state.get(f"trabajo_{clave_ed}") or {"df": df_archivo.assign(Estado=""), "v": 0}
    editado = _editor_de_archivo(trabajo, clave_ed)
    df = editado.drop(columns=[c for c in ("Estado", "Corregir") if c in editado]).reset_index(drop=True)
    falta = _columnas_que_faltan(nivel, col)
    if falta:
        estado.markdown(":red[:material/error: " + t(
            "No se encuentra la columna {c}. El archivo debe corresponder al área elegida.").format(
                c=" y ".join(t(n) for n in falta)) + "]")
        return
    df_datos, c_val = df, col["valor"]
    if c_val == NADA:
        df_datos = df.assign(_sin_valor=float("nan"))  # solo segmentos: se pinta por segmento
        c_val = "_sin_valor"
        aviso.info(t("El archivo no tiene valores: el mapa se colorea con un color por segmento."))
    em = _tabla_de_lugares(df_datos, nivel, ciudad, col, c_val, agregar)
    # lugares cuyo nombre no es el oficial
    revisadas, columnas_lugar = _lugares_por_revisar(df, nivel, ciudad, col)
    por_corregir = sum(r is not None for r in revisadas)
    filas_con_lugar = int((~df[columnas_lugar[-1][0]].astype(str).str.strip().isin(["", "nan"])).sum())
    estados = ["" if r is None else (f"{t('Sugerencia')}: {r[1]}" if r[1] != "-" else t("No reconocido")) for r in revisadas]
    hay_sugerencias = any(r and r[1] != "-" for r in revisadas)
    _aplicar_correcciones(editado, revisadas, trabajo, clave_ed)
    _actualizar_estados(editado, estados, hay_sugerencias, trabajo, clave_ed)
    firma = (archivo.file_id, hoja, agregar, col["region"], col["departamento"], col["municipio"], col["division"], c_val,
             col["grupo"])
    pendiente = not guardado or guardado["firma"] != firma or not guardado["df"].equals(df)
    _estado_de_lectura(estado, em, por_corregir, filas_con_lugar)
    # «Cargar datos» guarda la tabla para el mapa
    if b1.button(t(":material/upload: Cargar datos") if pendiente else t(":material/check: Datos cargados"),
                 type="primary" if pendiente else "secondary", disabled=not pendiente or bool(por_corregir),
                 width="content", key="btn_cargar",
                 help=t("Corregir los lugares marcados en la tabla para poder cargar los datos.") if por_corregir
                 else t("Aplica la tabla al mapa. Los datos quedan guardados aunque se cambie de origen.")):
        st.session_state["datos_subidos"] = {"tabla": em.tabla, "df": df.copy(), "firma": firma, "area": clave_area,
                                             "gen": gen_datos, "nombre": archivo.name}
        st.session_state["subida_n"] = st.session_state.get("subida_n", 0) + 1
        st.rerun()


def _subir_tabla(nivel, ciudad, clave_area, botones):
    """Origen «Subir archivo»: lee el archivo, revisa los lugares y guarda lo cargado con «Cargar datos»."""
    gen_datos = st.session_state.gen.get("datos", 0)
    guardado = st.session_state.get("datos_subidos")
    if guardado and (guardado["area"] != clave_area or guardado["gen"] != gen_datos):
        guardado = None  # eran de otra área o se restablecieron
    st.markdown(t("Subir el archivo ya configurado para el área elegida. La tabla de **Editar tabla** puede "
                  "descargarse, completarse y volver a subirse."))
    # una fila: archivo, lugares repetidos y estado de la lectura
    clave_archivo = f"archivo_{gen_datos}_{st.session_state.get('subida_n', 0)}"
    cargado = st.session_state.get(clave_archivo) is not None
    c_arch, c_rep, c_est = st.columns([1.6, 1.8, 3.8] if cargado else [1.6, 0.1, 5], vertical_alignment="center", gap="small")
    archivo = _cuadro_de_subida(c_arch, clave_archivo)
    agregar = "suma"
    if archivo:
        with c_rep.container(key="fila_repetidos", horizontal=True, vertical_alignment="center", gap="xsmall", wrap=False):
            st.markdown('<p class="etq-campo" title="' + html.escape(t(
                "Si un lugar aparece varias veces, sus valores se combinan con la suma, el promedio, el máximo "
                "o el último.")) + '">' + t("Lugares repetidos") + '</p>', unsafe_allow_html=True)
            agregar = st.selectbox(t("Lugares repetidos"), ["suma", "promedio", "máximo", "último"],
                                   format_func=lambda x: t(x).capitalize(), label_visibility="collapsed", width=130)
    estado = c_est.container(key="estado_subida")
    aviso = st.container()
    tabla = guardado["tabla"] if guardado else None  # el mapa usa lo cargado con «Cargar datos»
    if archivo:
        _revisar_archivo(archivo, nivel, ciudad, clave_area, clave_archivo, gen_datos, guardado, agregar, estado, aviso, botones)
    elif guardado:
        with c_est.container(horizontal=True, horizontal_alignment="right", vertical_alignment="center", gap="small"):
            st.markdown(":green[:material/check_circle: " + t("Datos cargados: {n} lugares de {f}.").format(
                n=len(guardado["tabla"]), f=guardado["nombre"]) + "]")
            if st.button(t(":material/delete: Quitar"), width="content", help=t("Quita los datos cargados del mapa.")):
                st.session_state.pop("datos_subidos", None)
                st.rerun()
    return tabla


def pestana_datos(nivel, deptos, municipios, regiones, ciudad, ciudad_rural, divisiones, isla_en_mapa):
    """Dibuja la pestaña Datos y devuelve la tabla cargada para el mapa (None si no hay datos)."""
    c_fuente, c_botones = st.columns([1, 1.7], vertical_alignment="center")
    # tres botones del mismo ancho; el CSS fija su medida
    botones = c_botones.container(horizontal=True, horizontal_alignment="right", vertical_alignment="center",
                                  gap="small", key="botones_tabla")
    fuente = c_fuente.radio(t("Origen de los datos"), ["Editar tabla", "Subir archivo"], horizontal=True, format_func=t,
                            label_visibility="collapsed")
    clave_area = hashlib.md5(f"{nivel}|{sorted(deptos)}|{sorted(municipios)}|{sorted(regiones)}|{ciudad}|{ciudad_rural}|{sorted(divisiones)}|{isla_en_mapa}"
                             .encode(), usedforsecurity=False).hexdigest()[:10]
    if fuente == "Editar tabla":
        return _editar_tabla(nivel, deptos, municipios, regiones, ciudad, ciudad_rural, divisiones, isla_en_mapa, clave_area, botones)
    return _subir_tabla(nivel, ciudad, clave_area, botones)
