"""Paletas de color para el mapa de calor y para los contornos de grupo."""
from __future__ import annotations

import colorsys
import random

import matplotlib
from matplotlib.colors import LinearSegmentedColormap

# Rampas de claro a oscuro; las de matplotlib son uniformes y aptas para daltonismo
PALETAS = {
    "Violeta": ["#E6E1FA", "#A08CE0", "#6A4FBF", "#36215E"],
    "Turquesa": ["#D9F4F9", "#6FD3E8", "#2196AE", "#0A4A57"],
    "Ámbar": ["#FFF3BF", "#FFCB1F", "#E39A00", "#8F5100"],
    "Esmeralda": ["#D7F5E5", "#5CCB8E", "#1C8C5E", "#0B3B2C"],
    "Océano": ["#DCEAF7", "#7FB2E5", "#2F6DB5", "#0F2F5C"],
    "Coral": ["#FDE3D9", "#F79A7E", "#D6493B", "#7A1420"],
    "Fucsia": ["#FBE0F3", "#E879C9", "#B3268F", "#5C0A47"],
    "Grafito": ["#EDEDED", "#B5B5B5", "#6E6E6E", "#262626"],
    "Viridis": "viridis",
    "Magma": "magma",
    "Cividis": "cividis",
    "Rojo → Azul (divergente)": ["#B2182B", "#F4A582", "#F7F7F7", "#92C5DE", "#2166AC"],
    "Café → Verde (divergente)": ["#8C510A", "#DFC27D", "#F5F5F5", "#80CDC1", "#01665E"],
}

# Colores distintos para categorías
PALETAS_CATEGORIAS = {
    "Vivos": ["#E4572E", "#17BEBB", "#FFC914", "#2E86AB", "#76B041", "#9B5DE5", "#F15BB5", "#FF8C42"],
    "Suaves": ["#A8DADC", "#F4A261", "#B8D8BA", "#E9C46A", "#CDB4DB", "#FFAFCC", "#BDE0FE", "#D4A373"],
    "Alto contraste": ["#1B4079", "#D1495B", "#EDAE49", "#00798C", "#66A182", "#8E5572", "#30638E", "#F2542D"],
    "Tierra": ["#C9A66B", "#8C6A4F", "#A3B18A", "#588157", "#BC6C25", "#DDA15E", "#6B705C", "#B5838D"],
    "Apta para daltónicos": ["#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7", "#999999"],
}

# Colores base de la paleta propia
COLORES_PROPIOS = PALETAS_CATEGORIAS["Vivos"] + ["#8D6E63", "#34495E"]


def colores_base(nombre: str) -> list[str]:
    p = PALETAS[nombre]
    if isinstance(p, str):
        cmap = matplotlib.colormaps[p]
        # en viridis, magma y cividis el extremo claro es el 1: se invierte
        return [matplotlib.colors.to_hex(cmap(x)) for x in (0.95, 0.75, 0.5, 0.25, 0.05)]
    return list(p)


def tonos(colores: list[str], n: int, invertir=False) -> list[str]:
    """n tonos discretos interpolados entre los colores dados."""
    cols = list(reversed(colores)) if invertir else list(colores)
    cmap = LinearSegmentedColormap.from_list("rampa", cols)
    if n == 1:
        return [matplotlib.colors.to_hex(cmap(1.0))]
    return [matplotlib.colors.to_hex(cmap(i / (n - 1))) for i in range(n)]


def aclarar(color: str, f=0.6) -> str:
    r, g, b = matplotlib.colors.to_rgb(color)
    return matplotlib.colors.to_hex([c + (1 - c) * f for c in (r, g, b)])


def es_oscuro(color: str) -> bool:
    r, g, b = matplotlib.colors.to_rgb(color)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b < 0.5


def oscurecer(color: str, f=0.6) -> str:
    r, g, b = matplotlib.colors.to_rgb(color)
    return matplotlib.colors.to_hex([c * (1 - f) for c in (r, g, b)])


def rampa_un_color(color: str, fuerte=True) -> list[str]:
    """Escala de un color: `fuerte=True` aclara los valores bajos; `fuerte=False` oscurece los altos."""
    if fuerte:
        return [aclarar(color, 0.88), aclarar(color, 0.45), color]
    return [color, oscurecer(color, 0.3), oscurecer(color, 0.58)]


# primero la paleta de siempre y la de mapa de calor
PALETAS = {"Mapa de calor": ["#FFF3B0", "#FDBE5A", "#F57C3B", "#D7301F", "#7F0000"],
           "Azul marino": rampa_un_color("#1F4E79"), **PALETAS}


def ampliar(paleta: list[str], n: int) -> list[str]:
    """Paleta de al menos n colores distintos: los propios y, si faltan, nuevos del círculo cromático."""
    paleta = list(paleta)
    i = 0
    while len(paleta) < n:
        r, g, b = colorsys.hls_to_rgb((i * 0.381966 + 0.07) % 1.0, (0.50, 0.62, 0.38)[i % 3], 0.68)
        c = f"#{round(r * 255):02X}{round(g * 255):02X}{round(b * 255):02X}"
        if all(_distancia(c, otro) > 40 for otro in paleta) or i > 400:
            paleta.append(c)
        i += 1
    return paleta


def _distancia(a: str, b: str) -> float:
    """Distancia entre dos colores hexadecimales (RGB)."""
    return sum((int(a[k:k + 2], 16) - int(b[k:k + 2], 16)) ** 2 for k in (1, 3, 5)) ** 0.5


def colorear_grafo(vecinos: list[set[int]], paleta: list[str], semilla: int = 0) -> list[str]:
    """Color por elemento sin repetirlo entre vecinos (mientras alcance la paleta); `semilla` cambia el reparto.

    `vecinos[i]` son los índices vecinos de i."""
    # reparto de colores reproducible con semilla; no es un uso criptográfico
    azar = random.Random(semilla)  # noqa: S311  # nosec B311
    paleta = list(paleta)
    if semilla:
        azar.shuffle(paleta)
    orden = sorted(range(len(vecinos)), key=lambda i: (-len(vecinos[i]), azar.random() if semilla else i))
    asignado: dict[int, int] = {}
    uso = [0] * len(paleta)
    for i in orden:
        usados = {asignado[j] for j in vecinos[i] if j in asignado}
        libres = [k for k in range(len(paleta)) if k not in usados]
        if libres:
            k = min(libres, key=lambda k: (uso[k], k))             # el color libre menos usado
        else:  # con paleta corta, el que menos vecinos repite
            k = min(range(len(paleta)), key=lambda k: (sum(asignado.get(j) == k for j in vecinos[i]), uso[k]))
        asignado[i] = k
        uso[k] += 1
    return [paleta[asignado[i]] for i in range(len(vecinos))]
