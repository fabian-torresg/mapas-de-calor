"""Contenido de las descargas: se arma solo cuando se pulsa el botón, por eso son funciones sueltas."""
from __future__ import annotations

import io
import re
import zipfile

import pandas as pd


def dibujar_en(render, tabla, estilo: dict, formato: str) -> bytes:
    """Bytes del mapa en el formato pedido; `render` devuelve (contenido, info)."""
    return render(tabla, estilo, formato)[0]


def zip_de_mapas(items: list[dict], formato: str, render) -> bytes:
    """ZIP con un archivo por mapa guardado; los nombres repetidos se numeran."""
    buf, usados = io.BytesIO(), {}
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for item in items:
            base = re.sub(r"[^\w\-]+", "_", item["nombre"]).strip("_") or "mapa"
            usados[base] = usados.get(base, 0) + 1
            nombre = base if usados[base] == 1 else f"{base}_{usados[base]}"
            zf.writestr(f"{nombre}.{formato}", render(item["tabla"], item["estilo"], formato)[0])
    return buf.getvalue()


def tabla_en_formato(tabla: pd.DataFrame, formato: str, hoja: str = "Datos") -> bytes:
    """La tabla de datos como CSV, Excel, JSON o Parquet."""
    if formato == "csv":
        return tabla.to_csv(index=False).encode("utf-8-sig")
    if formato == "json":
        return tabla.to_json(orient="records", force_ascii=False, indent=2).encode("utf-8")
    buf = io.BytesIO()
    if formato == "xlsx":
        tabla.to_excel(buf, index=False, sheet_name=hoja)
    elif formato == "parquet":
        tabla.to_parquet(buf, index=False)
    else:
        raise ValueError(f"Formato de datos no admitido: {formato}")
    return buf.getvalue()
