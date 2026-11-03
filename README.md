# Mapas de calor de Colombia

Aplicación web en Python y Streamlit para generar mapas de calor (coropletas) de Colombia por departamento,
municipio, región natural y localidad o comuna de 22 ciudades. Recibe datos tabulares (escritos en la app o cargados
desde Excel o CSV), los asocia con la geografía oficial y produce mapas listos para informes y presentaciones.

- **Mapa:** PNG, JPG, TIFF, SVG o PDF, con resolución configurable.
- **Datos:** CSV, Excel, JSON, Parquet o GeoJSON.
- **Idiomas y temas:** español e inglés; modo claro y oscuro.

## Contexto

Los mapas de distribución geográfica (ventas, cobertura, cuentas o visitas) suelen elaborarse de forma manual en
herramientas de ofimática o de inteligencia de negocios. Esto consume tiempo, rara vez permite el nivel municipal y
produce estilos inconsistentes entre mapas. Esta herramienta estandariza el proceso: el usuario define el área, los
datos y el estilo, y obtiene un resultado reproducible. Es independiente de cualquier organización y sirve para
cualquier conjunto de datos del país.

El proyecto se desarrolla como pieza de portafolio en el marco de la formación en Ingeniería Industrial de la
Universidad EAN, con énfasis en análisis de datos, calidad y mejora continua.

## Funcionalidades

### Área geográfica

- Niveles: país completo, regiones naturales, departamentos, municipios (1.123) y ciudades.
- Municipios: todos los de los departamentos elegidos o una selección. Se puede mostrar el departamento completo con la
  selección resaltada, o solo la selección con el encuadre ajustado.
- Ciudades: 22 ciudades con división interna (localidades, comunas o corregimientos). Admiten selección parcial, contexto
  de la ciudad completa y exclusión de la zona rural.
- San Andrés y Providencia se dibuja ampliado en el noroeste cuando el mapa abarca todo el país.

### Datos

- **Edición en la app:** tabla precargada con los lugares del área, con valores aleatorios de prueba opcionales y
  descarga en Excel o CSV.
- **Carga de archivos (XLSX, XLS, CSV):** las columnas se reconocen por su encabezado (`Departamento`, `Municipio`,
  `Región`, `Valor`, `Segmento`) y el área se toma del archivo. Máximo 25 MB y 300.000 filas.
- **Normalización de nombres:** se ignoran tildes, mayúsculas y espacios; se aceptan nombres comunes y alias, y para
  los lugares no reconocidos se propone el nombre más cercano. La carga se habilita cuando todos los lugares quedan
  resueltos.
- **Valores numéricos:** formatos colombiano e internacional (`1.234,5`, `1,234.5`, `45%`, `$ 1.000`). Los valores
  infinitos o fuera de rango se tratan como ausencia de dato.
- **Agregación de duplicados:** suma, promedio, máximo o último valor.

### Estilo

- **Coloración:** escala de color por valor (paleta propia de 1 a 10 colores o 15 paletas predefinidas, número de
  tonos, escala lineal, de raíz, logarítmica o por cuantiles) o categorías con un color por lugar, departamento o
  segmento, sin repetir color entre vecinos.
- **Segmentos:** columna opcional que agrupa lugares (zonas, canales, sedes). Permite colorear por segmento, calcular
  la escala dentro de cada uno o según su total, y dibujar contornos interiores por segmento.
- **Líneas por capa:** entre unidades, límite departamental y contorno del área, con color, tipo y grosor propios.
- **Lupa:** recuadro cuadrado o redondo sobre lugares pequeños, con el resto del mapa atenuado.
- **Elementos cartográficos:** minimapa de ubicación, barra de escala en kilómetros y flecha del norte, ubicados en
  esquinas libres.
- **Textos:** título, subtítulo, nota, leyenda, etiquetas (nombre, valor o ranking) y resumen estadístico, cada uno con
  tipografía, tamaño, formato y color. Tipografías: Arial, Calibri, Times New Roman, Georgia y Great Vibes.
- **Plantillas:** diez configuraciones predefinidas (profesional, publicación científica, presentación, minimalista,
  oscura, térmica, divergente, monocromo, editorial y redes sociales).

### Productividad

- **Mapas guardados:** configuración de varios mapas, galería de miniaturas, selección, eliminación y descarga
  conjunta en ZIP (hasta 20).
- **Resumen estadístico:** total, promedio, extremos y ranking, con opción de incluirlo en la imagen.
- **Interfaz:** barra lateral con bloques Datos, Diseño y Exportación; mapa ajustado a la ventana sin desplazamiento.

## Uso

### En línea

Aplicación en Streamlit Community Cloud: *pendiente de despliegue*. El arranque en frío prepara las geometrías
(del orden de 10 a 40 s); después cada cambio responde en 1 a 2 s. Los archivos cargados se procesan en memoria y
no se almacenan; se recomienda no subir datos sensibles.

### Local

Requiere Python 3.12 o superior (verificado con 3.14).

```bash
git clone https://github.com/fabian-torresg/mapas-de-calor.git
cd mapas-de-calor
pip install -r requirements.txt
streamlit run app.py
```

En Windows también puede ejecutarse `iniciar_app.bat`. En la primera ejecución la aplicación descarga los límites
municipales de GADM (aprox. 1 MB).

### Como biblioteca
```python
import pandas as pd
import mapacalor as mc

df = pd.read_excel("ejemplos/datos_ejemplo.xlsx", sheet_name="Municipios")
em = mc.emparejar(df, "Departamento", "Valor", col_muni="Municipio", nivel="municipio")
fig, info = mc.dibujar(em.tabla, mc.Estilo(nivel="municipio", deptos=["Cundinamarca", "Boyacá"],
                                           colores=mc.paletas.colores_base("Esmeralda"),
                                           etiquetas="ranking", titulo="Mi mapa"))
fig.savefig("mi_mapa.png")
```

## Formato de los datos

| Departamento | Municipio | Valor | Segmento |
| --- | --- | --- | --- |
| Cundinamarca | Chía | 120 | Sabana Centro |
| Cundinamarca | Zipaquirá | 85 | Sabana Centro |
| Cundinamarca | Girardot | 40 | Alto Magdalena |

`Municipio` solo es necesario en mapas por municipio. `Segmento` es opcional. El archivo
[`ejemplos/datos_ejemplo.xlsx`](ejemplos/datos_ejemplo.xlsx) incluye datos de prueba; la tabla de la app puede
descargarse para el área elegida y volver a cargarse una vez completada.

## Despliegue

Ver [`PUBLICAR.md`](PUBLICAR.md) para la publicación en Streamlit Community Cloud. `requirements.txt` define las
dependencias y `packages.txt` las tipografías de sustitución para Linux. El límite de carga es de 25 MB
(`.streamlit/config.toml`).

## Arquitectura

```text
app.py                  Flujo de la página y secciones de la barra lateral (Streamlit)
interfaz/               estilos.py (CSS y script de la página), controles.py, estado.py, plantillas.py,
                        pestana_datos.py, descargas.py, carga.py, constantes.py, textos.py y textos_en.py
mapacalor/
  geodatos.py           Descarga y preparación de geometrías (EPSG:3116); departamentos construidos a partir
                        de los municipios para que los bordes coincidan
  datos.py              Lectura de Excel y CSV, detección de columnas, conversión numérica y emparejamiento
                        difuso de nombres
  render.py             Dibujo con matplotlib: escala de color, contornos, minimapa, leyenda y etiquetas
  paletas.py            Paletas e interpolación de colores
datos/catalogo/         Nombres de los municipios de GADM
datos/geometrias/       Localidades y comunas, municipios posteriores a GADM (OSM) y países vecinos
datos/fuentes/          Great Vibes (SIL OFL 1.1), tipografía de la firma «Por Ft.»
tests/                  Pruebas con pytest
```

**Stack:** Python, pandas, GeoPandas, Shapely, matplotlib y Streamlit.

Decisiones de diseño:

- **Fuente única de fronteras.** Los departamentos se obtienen uniendo sus municipios; los límites son coherentes al
  combinar niveles.
- **Contorno interior.** La línea de cada grupo se traza al doble de ancho y se recorta con la propia figura, por lo
  que no invade al grupo vecino.
- **Escala no lineal.** La escala de raíz cuadrada evita que la concentración de valores en pocos lugares deje el
  resto del mapa en un solo color.
- **Arranque diferido.** Se prepara primero la vista por departamento; lo necesario para municipios y regiones se
  calcula en segundo plano.

## Calidad

- **Pruebas:** 146 pruebas (motor, dibujo e interfaz sin navegador) con 100 % de cobertura de líneas.
  Ejecución: `pip install pytest` y `python -m pytest tests`.
- **Integración continua:** GitHub Actions ejecuta pyflakes y las pruebas en Python 3.12, 3.13 y 3.14, con
  cobertura mínima, y un análisis de seguridad con Bandit y pip-audit.
- **Auditoría:** el código se sometió a una auditoría funcional, de datos, rendimiento, seguridad, arquitectura,
  usabilidad, confiabilidad y despliegue, con corrección y verificación de los hallazgos.

## Fuentes y licencias

- **Municipios y departamentos:** [GADM 4.1](https://gadm.org). Uso académico y no comercial; no se permite su
  redistribución, por lo que no se incluye en el repositorio y la aplicación lo descarga del sitio oficial.
- **Países vecinos:** [Natural Earth](https://www.naturalearthdata.com), dominio público.
- **Localidades, comunas y cinco municipios posteriores a GADM** (Albania, Guachené, Norosí, San José de Uré y
  Tuchín): © colaboradores de [OpenStreetMap](https://www.openstreetmap.org/copyright), licencia ODbL.
- **Tipografía Great Vibes:** SIL Open Font License 1.1 (`datos/fuentes/OFL.txt`).
- **Código:** licencia MIT.

## Uso de inteligencia artificial

Cada cambio fue revisado y probado por el autor. Se usó Claude Code (Anthropic) como asistente de programación para
implementar parte del código. El diseño, las decisiones técnicas y la validación de resultados son responsabilidad
del autor.

## Autor

**Fabián Torres** · Ingeniería Industrial, Universidad EAN ·
[LinkedIn](https://www.linkedin.com/in/fabian-torresg) · [GitHub](https://github.com/fabian-torresg)
