"""Guía de uso en español (la versión en inglés está en textos_en.py de esta carpeta)."""

AYUDA_ES = """
**Pasos**
1. En **Área geográfica** (bloque Datos): elegir si el mapa es de todo el país, regiones, departamentos, municipios o una
   ciudad, y qué parte mostrar.
2. En **Tabla de datos** (bloque Datos): editar la tabla o subir un archivo (Excel o CSV). Los datos de la
   tabla se pueden descargar, editar y volver a subir. Los nombres no necesitan ser exactos (tildes, mayúsculas y
   espacios no importan) y los que no se reconocen traen una sugerencia.
3. En el bloque **Diseño**: elegir una plantilla y ajustar colores, líneas y límites, etiquetas y cifras, vista del mapa
   (acercar y ampliar con una lupa redonda o cuadrada), orientación (minimapa, escala y flecha del norte) y títulos,
   tipografía y leyenda de color.
4. En el bloque **Exportación**: elegir la proporción y descargar el mapa en PNG (presentaciones), JPG (correo o web), TIFF
   (impresión profesional), SVG (edición en Illustrator o Figma) o PDF (impresión), o sumarlo a la cola para descargar
   varios juntos. Los datos se descargan en CSV, Excel, JSON, Parquet o GeoJSON.

**Formato del archivo**

| Departamento | Municipio | Valor | Segmento |
|---|---|---|---|
| Cundinamarca | Chía | 120 | Sabana Centro |
| Cundinamarca | Zipaquirá | 85 | Sabana Centro |
| Cundinamarca | Girardot | 40 | Alto Magdalena |

*Municipio* solo se necesita en mapas por municipio. Para regiones, una columna *Región* (o *Departamento*, que se suma
por región).

**Segmento** es opcional: agrupa lugares bajo un mismo nombre (zonas, vendedores, canales, sedes, tipos de cliente...).
Cada segmento puede tener su color o su contorno. En el ejemplo, Chía y Zipaquirá quedan en el segmento "Sabana Centro".

**Regiones**: Caribe, Andina, Pacífica, Orinoquía, Amazonía e Insular (regiones naturales de Colombia).

**Ciudades** (22): Bogotá, Medellín, Cali, Barranquilla, Bucaramanga, Pasto, Pereira, Santa Marta, Villavicencio, Soacha,
Neiva, Armenia, Montería, Valledupar, Popayán, Floridablanca, Riohacha, Barrancabermeja, Yopal, Quibdó, Florencia y
Buenaventura, con sus localidades, comunas o corregimientos. En la tabla sirve el nombre, el número o ambos
(*Comuna 14*, *El Poblado* o *14*). En varias ciudades la fuente solo trae la zona urbana: el resto del municipio se ve
como "sin división".

**Fuentes**: límites municipales de [GADM 4.1](https://gadm.org) (uso no comercial); países vecinos de
[Natural Earth](https://www.naturalearthdata.com) (dominio público); localidades y comunas, y los límites de cinco
municipios creados después de GADM, de [OpenStreetMap](https://www.openstreetmap.org/copyright) (© colaboradores de
OpenStreetMap, licencia ODbL).
"""
