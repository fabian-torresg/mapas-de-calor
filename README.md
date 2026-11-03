# Mapas de calor

Aplicación web para crear mapas de calor (coropletas) de Colombia **por departamento, municipio, región o
localidades y comunas de ciudades**, lista para presentaciones e informes. Eliges el área, cargas o escribes los
datos y ajustas todo el estilo sin escribir código. El mapa se descarga en PNG, JPG, TIFF, SVG o PDF, y los datos
en CSV, Excel, JSON, Parquet o GeoJSON.

## El problema

En equipos comerciales y de análisis es común necesitar mapas de Colombia para mostrar dónde se concentra
algo (ventas, cobertura, cuentas, visitas). Hacerlos a mano en PowerPoint o en herramientas de BI toma
tiempo, los municipios casi nunca están disponibles y cada mapa termina con un estilo distinto.

Este proyecto nace del interés por la visualización de datos geográficos y se desarrolla en el marco de mi
formación en Ingeniería Industrial en la Universidad EAN, como una herramienta de análisis aplicada. Es
**genérico y abierto**: sirve para cualquier dato y cualquier parte del país.

## Qué se puede hacer

**Área y nivel**
- Dividir el mapa por **todo el país**, **regiones naturales** (Caribe, Andina, Pacífica, Orinoquía,
  Amazonía, Insular), **departamentos**, **municipios** (los 1.123 del país) o **ciudades**. Sin elegir
  departamentos se ve Colombia completa; en ciudades, Bogotá viene preseleccionada.
- Por municipios: todos los de los departamentos elegidos o solo algunos. Con un interruptor se ve el
  departamento completo con los elegidos resaltados, o solo los elegidos con el mapa acercado a ellos.
- **Ciudades por dentro**: 22 ciudades divididas en localidades, comunas o corregimientos: Bogotá, Medellín,
  Cali, Barranquilla, Bucaramanga, Pasto, Pereira, Santa Marta, Villavicencio, Soacha, Neiva, Armenia, Montería,
  Valledupar, Popayán, Floridablanca, Riohacha, Barrancabermeja, Yopal, Quibdó, Florencia y Buenaventura.
  Se puede elegir solo algunos lugares (con la ciudad completa de fondo o solos) o dejar fuera la zona rural.
- **Colores muy personalizables**, en una sola sección con dos formas de colorear:
  - *Mapa de calor*: una escala de color según el valor. Paleta propia de 1 a 10 colores (cuadritos numerados) o
    15 paletas listas, entre ellas "Mapa de calor" (amarillo a rojo); número de tonos e invertir. La escala se
    calcula por lugar, por departamento (con más de uno en el área) o, con una columna Segmento
    (zonas, vendedores, canales, sedes...), dentro de cada segmento o según el total de cada uno.
  - *Categorías*: un color diferente para cada lugar, departamento o segmento. Los colores se asignan solos
    y **dos vecinos nunca repiten color**; hay un cuadro de color por cada grupo para cambiarlo a mano, y se puede
    barajar o elegir otra paleta.
- Estilo de los textos (negrita, cursiva, subrayado) y tamaño para título, subtítulo, nota, leyenda y etiquetas.
- **Lupa**: cuadrada o redonda, puesta sobre los lugares pequeños (por ejemplo la Sabana de Bogotá) y más grande;
  el resto del mapa se atenúa. Tamaño de 1 a 5.
- Acercar el mapa a la selección o mostrarla dentro de todo el país.
- **San Andrés y Providencia**: cuando el mapa muestra todo el país se dibujan agrandadas, una al lado de la
  otra, en el noroeste (se pueden ocultar). Entran en la tabla de datos como un departamento más.

**Datos**
- **Editar tabla**: se escribe en una tabla dentro de la app, precargada con los lugares del área (en regiones,
  con sus departamentos). Se puede llenar con valores aleatorios de prueba y descargar en Excel o CSV.
- **Subir archivo** (Excel o CSV): las columnas se detectan solas (`Departamento`, `Municipio`, `Región`, `Valor`,
  `Segmento`) y el área se toma del archivo. La tabla descargada se completa y se vuelve a subir; se puede editar en
  la app, que marca los nombres que no coinciden con una sugerencia y no carga los datos hasta corregirlos.
- Para regiones se puede subir una columna `Región` o directamente los departamentos: se suman por región.
- Los nombres no tienen que estar perfectos: no importan tildes, mayúsculas ni espacios, se reconocen nombres
  comunes (Cali, Cartagena, Cúcuta, Bogotá) y para lo que no coincide se sugiere el nombre más parecido.
- Números en formato colombiano o internacional (`1.234,5`, `1,234.5`, `45%`, `$ 1.000`).

**Estilo**
- **Líneas por capa** (entre unidades, límite departamental, contorno del área), cada una con su color, tipo (continua, guiones, espaciada, círculos, puntos, guion y punto) y grosor; grosor 0 la apaga.
- **Contornos por segmento** dibujados hacia adentro del límite, para que no invadan al segmento vecino.
- Minimapa de ubicación, barra de escala y flecha del norte: cada uno busca solo una esquina donde no tape el área.
- Vista ajustada a la ventana: el mapa se ve completo sin desplazarse, en cualquier tamaño de pantalla.
- Diseño tipo panel: barra lateral azul marino con tres bloques (**Datos**, **Diseño** y **Exportación**), el
  mapa en una tarjeta que ocupa toda la ventana (con un clic se amplía a pantalla completa) y, arriba a la
  derecha de la tarjeta, los selectores de tema e idioma y los iconos de aviso, resumen y cola de mapas. La tabla de datos es una sección del bloque Datos que se
  abre en la zona del mapa, y la descarga está en el bloque Exportación.
- Colores del contexto: el resto de Colombia, los países vecinos y el mar tienen cada uno su color.
- Las paletas se eligen en una lista donde cada fila muestra su línea de colores y, al final, un signo de pregunta con su nombre.
- Modo claro y modo oscuro con un selector de iconos junto al de idioma, dentro de la tarjeta del mapa.
- Botones para restablecer cada sección, toda la configuración o los datos escritos.
- Leyenda de color con texto o con valores mínimo y máximo (con su tamaño y formato).
- Etiquetas de nombre o valor (el valor debajo, al lado o entre paréntesis) y ranking (hasta 50) con números sobre el
  mapa, una lista (a la derecha, izquierda, arriba o abajo) o ambos. Cada texto tiene su botón **Aa** con tipografía,
  tamaño, formato y color; la lista del ranking y el resumen también.
- Título, subtítulo y nota de fuente (con formato y tamaño), tipografía (Arial, Calibri, Times New Roman o Georgia),
  proporción de la imagen y resolución de exportación (se elige al descargar).

**Productividad**
- **Plantillas de estilo** que se aplican al elegirlas: Profesional, Publicación científica (letra serif,
  colores legibles impresos y con daltonismo, escala, norte y 300 dpi), Presentación, Minimalista, Oscura,
  Térmica, Divergente, Monocromo para imprimir, Editorial y Redes sociales.
- **Cola de mapas**: se configura un mapa, se agrega a la cola, se configura otro y al final se descargan todos en un
  ZIP (hasta 20).
- **Resumen de los datos**: total, promedio, mayor y menor, los primeros y los últimos lugares y su
  porcentaje del total. Se ve en un panel junto al mapa; se elige qué mostrar y si va o no en la imagen descargada.
- **Tablas ordenables**: al pulsar el encabezado de una columna, la tabla se ordena por ella.
- **Versión en inglés**: un botón ES / EN arriba a la derecha traduce la app y los textos del mapa.

## Cómo usarla

### Opción 1: en línea
Abre el enlace de la app publicada (Streamlit Community Cloud): *pendiente de agregar*.

- La primera visita después de un periodo sin uso tarda cerca de 30 segundos: la app se reactiva y prepara las
  geometrías. Después cada cambio responde en 1 o 2 segundos.
- Los archivos que se suben se procesan en el servidor y no se guardan, pero conviene no subir datos sensibles.

### Opción 2: en tu computador
Necesitas Python 3.10 o superior (probado con 3.14).

```bash
git clone https://github.com/fabian-torresg/mapas-de-calor.git
cd mapas-de-calor
pip install -r requirements.txt
streamlit run app.py
```

En Windows también puedes hacer doble clic en **`iniciar_app.bat`**.

Para correr las pruebas: `pip install pytest` y luego `python -m pytest tests` (tardan poco más de un minuto).

La primera vez la app descarga los límites municipales desde el sitio oficial de GADM (unos 1 MB).

### Opción 3: desde Python
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

## Publicarla en línea

La app está lista para [Streamlit Community Cloud](https://share.streamlit.io) (gratis):

1. Subir el repositorio a GitHub (público en el plan gratuito).
2. En share.streamlit.io elegir **Create app**, el repositorio, la rama `main` y el archivo `app.py`.
3. En **Advanced settings** escoger Python 3.12 o 3.13.
4. Pulsar **Deploy** y copiar el enlace en la Opción 1 de este archivo.

`requirements.txt` instala las librerías y `packages.txt` las tipografías de sustitución de Linux. El límite de
subida de archivos es de 25 MB (`.streamlit/config.toml`). Las pruebas corren solas en cada envío al repositorio
(`.github/workflows/pruebas.yml`).

## Formato de los datos

| Departamento | Municipio | Valor | Segmento |
|---|---|---|---|
| Cundinamarca | Chía | 120 | Sabana Centro |
| Cundinamarca | Zipaquirá | 85 | Sabana Centro |
| Cundinamarca | Girardot | 40 | Alto Magdalena |

`Municipio` solo se necesita en mapas por municipio. `Segmento` es opcional: agrupa lugares bajo un mismo
nombre (zonas, vendedores, canales, sedes...) para pintarlos de un color o rodearlos con una línea. En
[`ejemplos/datos_ejemplo.xlsx`](ejemplos/datos_ejemplo.xlsx) hay un archivo de prueba, y la tabla de la app se
puede descargar para el área que elijas.

## Cómo está hecho

```
app.py                  Interfaz en Streamlit: flujo de la página y secciones de la barra lateral
interfaz/               Piezas de la interfaz: estilos.py (CSS y script de la página), controles.py (paneles de
                        texto, listas, paletas), estado.py (claves y restablecer), plantillas.py, constantes.py,
                        textos.py y textos_en.py (traducción), pestana_datos.py (tabla y archivo subido) y guia.py
mapacalor/
  geodatos.py           Descarga y prepara geometrías (proyección MAGNA-SIRGAS EPSG:3116),
                        arma los departamentos a partir de los municipios para que los bordes coincidan
  datos.py              Lectura de Excel/CSV, detección de columnas, limpieza de números
                        y emparejamiento difuso de nombres
  render.py             Dibujo con matplotlib: escala de color, contornos interiores,
                        minimapa, leyenda y etiquetas
  paletas.py            Interpolación de colores y paletas de referencia
datos/catalogo/         Nombres legibles de los municipios de GADM
datos/geometrias/       Localidades y comunas (OSM), municipios creados después de GADM (OSM) y países vecinos
datos/fuentes/          Great Vibes, tipografía manuscrita de la firma «Por Ft.» (licencia SIL OFL 1.1, incluida)
tests/                  Pruebas con pytest (146): el motor, el dibujo y la interfaz sin navegador, con cobertura del 100 % de líneas
packages.txt            Tipografías de sustitución para la nube (Linux): Liberation y Carlito
```

**Stack:** Python · pandas · GeoPandas · Shapely · matplotlib · Streamlit

Algunas decisiones técnicas:
- **Un solo origen para todas las fronteras.** Los departamentos se construyen uniendo sus municipios, así
  los límites nunca se desfasan cuando se mezclan los dos niveles.
- **Contorno hacia adentro.** La línea de cada grupo se traza al doble de ancho y se recorta con la propia
  figura, de modo que solo queda la mitad interior y no se superpone con el grupo vecino.
- **Escala no lineal.** Con datos de negocio, pocos lugares suelen concentrar la mayor parte del
  total; la escala de raíz cuadrada evita que todo el resto quede del mismo color.

## Fuentes y licencias

- Límites de municipios y departamentos: [GADM 4.1](https://gadm.org). Uso libre académico y no comercial;
  no se permite redistribuirlos, por eso no están en el repositorio y la app los descarga del sitio oficial.
- Países vecinos: [Natural Earth](https://www.naturalearthdata.com), dominio público.
- Localidades y comunas, y los límites de cinco municipios creados después de GADM (Albania en La Guajira,
  Guachené, Norosí, San José de Uré y Tuchín): © colaboradores de [OpenStreetMap](https://www.openstreetmap.org/copyright), licencia ODbL.
  En varias ciudades solo está la zona urbana.
- Código: licencia MIT.

Los datos geográficos nuevos (`datos/geometrias/municipios_nuevos_osm.geojson`) se recortan de los municipios vecinos
al cargar, para que no se solapen.

## Autor

**Fabián Torres** · Ingeniería Industrial, Universidad EAN ·
[LinkedIn](https://www.linkedin.com/in/fabian-torresg) · [GitHub](https://github.com/fabian-torresg)
