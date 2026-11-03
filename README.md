# Mapas de calor

[![Streamlit](https://img.shields.io/badge/Streamlit-App%20en%20l%C3%ADnea-FF4B4B?logo=streamlit&logoColor=white)](https://mapas-de-calor.streamlit.app/)
[![Pruebas](https://github.com/fabian-torresg/mapas-de-calor/actions/workflows/pruebas.yml/badge.svg)](https://github.com/fabian-torresg/mapas-de-calor/actions/workflows/pruebas.yml)
[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Tecnologías](https://img.shields.io/badge/Tecnolog%C3%ADas-Pandas%20%7C%20GeoPandas%20%7C%20Matplotlib-orange)](#estructura)

Aplicación en Python y Streamlit que genera mapas de calor (coropletas) de Colombia por departamento, municipio,
región natural y localidad o comuna de 22 ciudades. Recibe datos escritos en la aplicación o cargados desde Excel o CSV,
los asocia con la geografía y exporta el mapa listo para informes y presentaciones.

**Aplicación en línea:** <https://mapas-de-calor.streamlit.app/>

**Presentación:** <https://fabian-torresg.github.io/mapas-de-calor/>

## Funcionalidades

- **Área:** país, regiones, departamentos, municipios (1.123) y ciudades con división interna. Admite selección parcial
  y encuadre ajustado.
- **Datos:** tabla editable o carga de XLSX, XLS y CSV. Los nombres se normalizan (tildes, mayúsculas, alias) y los no
  reconocidos reciben una sugerencia. Admite formatos numéricos colombianos e internacionales y agrega duplicados.
- **Coloración:** escala continua (lineal, raíz, logarítmica o cuantiles) o categorías, con 15 paletas o colores
  propios. Una columna opcional de segmentos permite agrupar, colorear y delimitar lugares.
- **Diseño:** líneas por capa, lupa sobre lugares pequeños, minimapa, barra de escala, flecha del norte, etiquetas,
  leyenda, resumen estadístico y diez plantillas.
- **Exportación:** mapa en PNG, JPG, TIFF, SVG o PDF; datos en CSV, Excel, JSON, Parquet o GeoJSON. Los mapas
  guardados se descargan en un ZIP.
- **Idioma y tema:** español e inglés; modo claro y oscuro.

## Instalación

Requiere Python 3.12 o superior.

```bash
git clone https://github.com/fabian-torresg/mapas-de-calor.git
cd mapas-de-calor
pip install -r requirements.txt
streamlit run app.py
```

En la primera ejecución se descargan los límites municipales de GADM (aprox. 1 MB).

## Formato de los datos

Las columnas se reconocen por su encabezado. `Municipio` solo se requiere en mapas por municipio y `Segmento` es
opcional.

| Departamento | Municipio | Valor | Segmento |
| --- | --- | --- | --- |
| Antioquia | Rionegro | 1.250 | Oriente |
| Santander | Barichara | 38,5 | Turismo |
| Nariño | Pasto | 45 % | Sur |
| Meta | Villavicencio | $ 2.400.000 | Llanos |

El archivo [`examples/datos_ejemplo.xlsx`](examples/datos_ejemplo.xlsx) contiene datos ficticios de prueba.

## Uso como biblioteca

```python
import pandas as pd
import mapacalor as mc

df = pd.read_excel("examples/datos_ejemplo.xlsx", sheet_name="Municipios")
em = mc.emparejar(df, "Departamento", "Valor", col_muni="Municipio", nivel="municipio")
fig, info = mc.dibujar(em.tabla, mc.Estilo(nivel="municipio", deptos=["Cundinamarca", "Boyacá"], titulo="Mi mapa"))
fig.savefig("mi_mapa.png")
```

## Estructura

```text
app.py          Flujo de la página y barra lateral
ui/             Controles, estilos, textos y pestañas de la interfaz
mapacalor/      Motor: geometrías, lectura y emparejamiento de datos, dibujo y paletas
data/           Catálogo de municipios, geometrías propias y tipografía de la firma
docs/           Página de presentación (GitHub Pages)
examples/       Datos de ejemplo
tests/          Pruebas con pytest
```

Stack: Python, pandas, GeoPandas, Shapely, matplotlib y Streamlit.

## Pruebas y despliegue

```bash
pip install pytest
python -m pytest tests
```

GitHub Actions ejecuta pyflakes, las pruebas en Python 3.12, 3.13 y 3.14, y un análisis de seguridad. La aplicación se
despliega en Streamlit Community Cloud apuntando a `app.py`; `requirements.txt` define las dependencias y
`packages.txt` las tipografías de sustitución en Linux.

## Fuentes y licencias

- **Municipios y departamentos:** [GADM 4.1](https://gadm.org), uso académico y no comercial. No se redistribuye: la
  aplicación lo descarga del sitio oficial.
- **Países vecinos:** [Natural Earth](https://www.naturalearthdata.com), dominio público.
- **Localidades, comunas y cinco municipios posteriores a GADM:** © colaboradores de
  [OpenStreetMap](https://www.openstreetmap.org/copyright), licencia ODbL.
- **Tipografía Great Vibes:** SIL Open Font License 1.1 (`data/fonts/OFL.txt`).
- **Código:** licencia MIT.

Se usó Claude Code (Anthropic) como asistente de programación; el diseño, la revisión y la validación son del autor.

## Autor

**Fabián Torres** · [LinkedIn](https://www.linkedin.com/in/fabian-torresg) · [GitHub](https://github.com/fabian-torresg)
