"""Estilos (CSS) y script de la página (JavaScript) de la interfaz."""

import json

from ui.carga import MASCARA

CSS = r"""<style>
.block-container{padding-top:0.6rem;padding-bottom:0.6rem;max-width:100%}
[data-testid='stMarkdownContainer'] p.titulo-app{font-size:2.15rem;font-weight:700;margin:0;
  line-height:1.15;letter-spacing:-0.01em}
div[data-testid='stElementContainer']:has(iframe){display:none}
div[data-testid='stElementContainer']:has(#ancla-tema){display:none}
/* barra superior transparente; solo sus botones reciben clics */
[data-testid='stHeader'],[data-testid='stHeader'] *{pointer-events:none}
[data-testid='stHeader']{background:transparent!important}
[data-testid='stHeader'] button,[data-testid='stHeader'] a{pointer-events:auto}
/* cabecera de la tarjeta: iconos de panel y selectores de tema e idioma */
.st-key-cab_tarjeta{padding-right:0;margin-bottom:-0.4rem}
[data-testid='stAppDeployButton']{display:none}      /* Deploy solo sale al ejecutar en local */
/* «Fork» de Community Cloud: tapaba el selector de idioma; el icono de GitHub se conserva */
[data-testid='stToolbarActionButton']:has([data-testid='stToolbarActionButtonLabel']){display:none}
/* pantallas medianas: la barra lateral queda fija, así que no puede quitarle más del 40 % al mapa */
@media (min-width:769px){ [data-testid='stSidebar']{max-width:max(300px,40vw)} }
/* pantallas estrechas: la tarjeta ocupa todo el ancho y el menú de Streamlit queda sobre su esquina; se le deja sitio */
@media (max-width:900px){ .st-key-cab_tarjeta{padding-right:1.8rem} }
/* la barra lateral deja solo el alto del botón de recoger */
[data-testid='stSidebarHeader']{height:0.4rem;min-height:0;padding-top:0;padding-bottom:0}
/* flecha de recoger la barra: junto a los iconos del título, solo al pasar el cursor */
[data-testid='stSidebarCollapseButton']{position:absolute;top:1.75rem;right:0.2rem;z-index:3}
.st-key-iconos_mapa,.st-key-selectores_cab{width:auto!important}
.st-key-cab_tarjeta > [data-testid='stLayoutWrapper']{flex:0 0 auto;width:auto!important}
/* título de la aplicación */
.st-key-btn_guia [role='img'],.st-key-rst_todo [role='img']{font-size:1.25rem!important}      /* guía y restablecer, del mismo tamaño */
.st-key-cab_sb [data-testid='stMarkdownContainer']{margin-bottom:0!important}      /* sin el margen negativo de Streamlit: título centrado con los iconos */
.st-key-cab_sb{container-type:inline-size;padding-right:2.2rem}     /* deja libre el botón de recoger */
.st-key-cab_sb > [data-testid='stElementContainer']:nth-child(1){flex:1 1 0;min-width:0;white-space:nowrap;overflow:hidden}
.st-key-cab_sb > [data-testid='stElementContainer']:nth-child(n+2){flex:0 0 auto;width:auto!important}
/* el título se ajusta al espacio que dejan los iconos (el texto mide unas 6,5 veces su tamaño) y nunca los pisa */
.st-key-cab_sb p.titulo-app{font-size:clamp(0.9rem,calc((100cqw - 5.6rem) / 6.5),2.15rem);
  overflow:hidden;text-overflow:ellipsis}
.st-key-selectores_cab [data-testid='stButtonGroup'] button{min-width:2.1rem;min-height:1.75rem;padding:0.1rem 0.5rem}
.st-key-selectores_cab [data-testid='stButtonGroup'] button *{font-size:0.8rem!important;line-height:1}
.st-key-selectores_cab [data-testid='stButtonGroup'],.st-key-selectores_cab [data-testid='stButtonGroup'] > div{flex-wrap:nowrap!important;white-space:nowrap}
.st-key-selectores_cab > [data-testid='stLayoutWrapper'],.st-key-selectores_cab > div{flex:0 0 auto;width:auto!important;min-width:max-content}
.block-container{position:relative}
/* barra lateral: desplazamiento visible y espacio al final */
[data-testid='stSidebarContent']{overflow-y:auto!important;overflow-x:hidden!important;scrollbar-width:auto;scrollbar-color:#8AA4BF transparent}
[data-testid='stSidebarContent']::-webkit-scrollbar{width:11px}
[data-testid='stSidebarContent']::-webkit-scrollbar-track{background:transparent}
[data-testid='stSidebarContent']::-webkit-scrollbar-thumb{background:#8AA4BF;border-radius:6px;border:2px solid transparent;background-clip:padding-box}
[data-testid='stSidebarUserContent']{padding-bottom:3.4rem;overflow-x:hidden;max-width:100%}
[data-testid='stSidebarUserContent'] [data-testid='stVerticalBlock']:not([data-testid='stExpander'] [data-testid='stVerticalBlock']){gap:0.5rem}
[data-testid='stSidebarUserContent'] *{min-width:0}
/* opción A: tarjeta blanca sobre fondo gris claro */
[data-testid='stMain'] .st-key-tarjeta_mapa{background:var(--tarjeta,#FFFFFF);position:relative;min-height:calc(100vh - 1.2rem)}
.tit-tarjeta{font-size:0.9rem;font-weight:600;margin:0 0 0.2rem}
/* paneles de resumen, avisos y mapas guardados: estrechos y con aire */
[data-testid='stPopoverBody']:has(.cuerpo-panel){width:20rem;max-width:calc(100vw - 2rem);padding:1rem 1.1rem}
[data-testid='stPopoverBody'] .cuerpo-panel{display:none}
/* el panel de mapas guardados se alinea con el borde derecho de la tarjeta (--der-tarjeta lo calcula el script) */
[data-testid='stPopoverBody']:has(.cuerpo-cola){width:21rem;left:auto!important;right:var(--der-tarjeta,0.5rem)!important;transform:none!important;top:4.4rem!important;max-height:calc(100vh - 5.4rem)!important}
/* mapas guardados: lista compacta, dos por fila */
.st-key-lista_cola{gap:0.1rem 0.5rem;overflow:visible!important}
.st-key-lista_cola [class*='st-key-cola_it_'],.st-key-lista_cola > [data-testid='stLayoutWrapper']{overflow:visible!important}
.st-key-lista_cola > [data-testid='stLayoutWrapper']{flex:0 0 calc(50% - 0.25rem);min-width:0}
.st-key-lista_cola [data-testid='stMarkdownContainer'] p{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin:0;font-size:0.9rem}
.st-key-lista_cola [data-testid='stElementContainer']:has([data-testid='stMarkdown']){flex:1 1 0;min-width:0}
.st-key-lista_cola button{min-height:1.7rem;padding:0.1rem 0.3rem}
/* galería: miniaturas sobre la zona del mapa */
.st-key-galeria_cola{gap:0.5rem}
.st-key-cab_galeria{justify-content:space-between}
.st-key-galeria_cerrar button,.st-key-galeria_volver button{min-height:2.2rem;min-width:2.2rem;border:1px solid rgba(128,128,128,0.35)}
.st-key-galeria_cerrar [role='img'],.st-key-galeria_volver [role='img']{font-size:1.5rem!important}
.st-key-mapa_grande [data-testid='stFullScreenFrame'].ampliado img{max-height:calc(100vh - 7.2rem)!important}
.st-key-volver_min,.st-key-cerrar_todo{display:none}
.st-key-fmt_galeria{width:auto;flex:0 0 auto}
.st-key-fmt_galeria [data-testid='stElementContainer']:has([data-testid='stSelectbox']),.st-key-fmt_galeria [data-testid='stSelectbox']{width:5.5rem!important;flex:0 0 5.5rem}
[class*='st-key-miniatura_'] [data-testid='stElementToolbar']{display:none}
[class*='st-key-miniatura_']{position:relative;border:2px solid rgba(128,128,128,0.25);border-radius:0.5rem;padding:0.35rem;cursor:pointer;gap:0.15rem;align-items:center}
.st-key-mapa_grande [data-testid='stImage'] img{max-height:calc(100vh - 12.5rem)!important}     /* el mapa abierto cabe sin desplazar la página */
[class*='st-key-miniatura_']:hover{border-color:var(--primario,#1F4E79)}
[class*='st-key-miniatura_'] [data-testid='stImage']{display:flex;justify-content:center}
[class*='st-key-miniatura_'] [data-testid='stImage'] img{width:auto!important;max-width:100%;max-height:min(8rem,16vh)!important;object-fit:contain;margin:0 auto}
[class*='st-key-miniatura_'] [data-testid='stCaptionContainer']{text-align:center;font-size:0.8rem}
[class*='st-key-miniatura_'] > [data-testid='stElementContainer']:has(> [data-testid='stButton']){position:absolute;inset:0 0 2.5rem 0;width:auto!important;height:auto!important;opacity:0;z-index:2}
[class*='st-key-miniatura_'] > [data-testid='stElementContainer'] [data-testid='stButton'],[class*='st-key-miniatura_'] > [data-testid='stElementContainer'] button{width:100%;height:100%;min-height:0}
/* pie de cada miniatura: casilla con el nombre, descargar y eliminar */
[class*='st-key-pie_']{width:100%;position:relative;z-index:3;min-height:2rem}
[class*='st-key-pie_'] > [data-testid='stElementContainer']:has([data-testid='stCheckbox']){flex:1 1 0;min-width:0}
[class*='st-key-pie_'] [data-testid='stCheckbox'] p{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:0.8rem}
[class*='st-key-pie_'] button{min-height:1.7rem;padding:0.1rem 0.3rem}
.st-key-barra_galeria{flex-wrap:wrap}
.st-key-fila_zip button,.st-key-fila_zip [data-baseweb='select']>div{white-space:nowrap}
.tit-panel{font-size:0.95rem;font-weight:700;margin:0 0 0.15rem}
.tit-panel span{font-weight:400;opacity:0.7}
.st-key-iconos_mapa [data-testid='stPopoverButton'] > div[aria-hidden='true']{display:none}
/* pestañas de la barra lateral: Datos, Diseño y Exportación */
[data-testid='stSidebar'] [role='tablist']{gap:0.1rem}
[data-testid='stSidebar'] [role='tab']{padding:0.35rem 0.55rem;font-size:0.85rem}
/* aire entre el título de la barra lateral y la primera sección */
[data-testid='stSidebar'] [data-testid='stLayoutWrapper']:has(.st-key-rst_todo){margin-bottom:0.9rem}
/* botón pequeño de restablecer: arriba a la derecha de cada sección, en la línea de su título */
[data-testid='stSidebar'] [data-testid='stExpander'] details{position:relative}
[data-testid='stSidebar'] [class*='st-key-rst_']:not(.st-key-rst_todo){position:absolute;top:0.4rem;right:0.5rem;width:auto;z-index:2}
[data-testid='stSidebar'] [class*='st-key-rst_'] button{min-height:1.8rem;padding:0.1rem 0.35rem}
/* pestañas del centro ocultas; las maneja el script */
[data-testid='stMain'] [data-testid='stTabs'] [role='tablist']{display:none}
[data-testid='stMain'] [data-testid='stTabs'] [role='tabpanel']{padding-top:0}
[data-testid='stMain'] [data-testid='stTabs']{margin-top:-1rem}
.st-key-caja_tabla{flex:none!important;height:var(--alto-tabla,calc(100vh - 16rem))!important}   /* --alto-tabla lo calcula el script */
/* la tabla tiene alto fijo: sin la esquina para redimensionarla */
[data-testid='stDataFrameResizable'] div[style*='se-resize']{display:none!important}
.st-key-leyenda_tabla{margin-top:-0.9rem}
/* cuadro de subida compacto, del alto de los demás controles de la fila */
.st-key-subida [data-testid='stFileUploaderDropzone']{padding:0.1rem 0.5rem;min-height:2.2rem;align-items:center}
.st-key-subida [data-testid='stFileUploaderDropzoneInstructions'] small{display:none}
.st-key-subida [data-testid='stFileChips']{padding:0}
.st-key-subida [data-testid='stFileUploaderDropzone']{background:transparent!important;border:none!important;padding:0!important}
.st-key-subida [data-testid='stFileChip']{background:var(--primario,#1F4E79)!important;color:var(--primario-texto,#FFFFFF)!important}
.st-key-subida [data-testid='stFileChip'] *{color:var(--primario-texto,#FFFFFF)!important}
.st-key-subida [data-testid='stFileChip'] > div:first-child{background:#FFFFFF!important}
.st-key-subida [data-testid='stFileChip'] > div:first-child svg{color:#13263A!important;fill:#13263A!important}
.st-key-subida button{min-height:1.9rem;padding-top:0;padding-bottom:0}
.st-key-estado_subida p{margin:0}
.st-key-fila_repetidos p{margin:0;white-space:nowrap}
[data-testid='stVerticalBlock']:has(.st-key-estado_subida) .st-key-caja_tabla{margin-top:1.1rem}   /* las herramientas de la tabla quedan debajo del estado */
.st-key-botones_tabla .st-key-btn_cargar button{width:8.8rem;padding:0 0.5rem}   /* igual de ancho que los selectores de tema e idioma */
.st-key-fila_repetidos{overflow:visible!important}
.st-key-fila_repetidos [data-testid='stMarkdownContainer']{margin-bottom:0!important}
.st-key-fila_repetidos > [data-testid='stElementContainer']{width:auto!important;flex:0 0 auto}
.st-key-fila_repetidos [data-testid='stSelectbox']{width:7.5rem!important}
.st-key-fila_subida > [data-testid='stElementContainer'],.st-key-fila_subida > [data-testid='stLayoutWrapper']{width:auto!important;flex:0 0 auto}
.st-key-fila_subida{overflow:visible!important}
.st-key-estado_subida,.st-key-estado_subida p{text-align:right}
.st-key-subida,.st-key-subida [data-testid='stFileUploaderDropzone']{width:fit-content;max-width:100%}
.st-key-subida [data-testid='stFileChipName']{max-width:none!important}
/* un solo archivo: sin el «+» de agregar más */
[data-testid='stFileUploader'] button[aria-label='Add files']{display:none}
/* botones de la tabla: mismo ancho y algo más bajos */
.st-key-botones_tabla [data-testid='stElementContainer']{width:auto!important;flex:0 0 auto}
.st-key-botones_tabla button{width:10.5rem;min-height:2.2rem;height:2.2rem;padding:0 1rem;white-space:nowrap}
/* iconos de la tabla: siempre visibles y más grandes */
[data-testid='stDataFrame'] > [data-testid='stElementToolbar']{opacity:1!important;visibility:visible!important;
  top:-2.9rem!important;padding:0.25rem 0 0.25rem 0.25rem!important;z-index:5;transition:none!important}
[data-testid='stDataFrame'] > [data-testid='stElementToolbar'] button{width:2rem;height:2rem;min-height:2rem}
/* la descarga va en el botón Descargar; el icono de Streamlit solo baja CSV */
[data-testid='stDataFrame'] > [data-testid='stElementToolbar'] [data-testid='stElementToolbarButton']:has(button[aria-label^='Download']){display:none}
[data-testid='stDataFrame'] > [data-testid='stElementToolbar'] button svg{width:1.15rem;height:1.15rem}
/* sección Descargar sin acordeón: su botón de restablecer se ancla a la caja */
.st-key-caja_descarga{position:relative;gap:1.5rem!important}
.st-key-caja_descarga hr.separador{border:none;border-top:1px dashed rgba(140,155,175,.55);margin:0.5rem 0}
.st-key-caja_descarga > [data-testid='stElementContainer']:first-child{margin-bottom:-0.7rem}
.st-key-caja_descarga > [data-testid='stElementContainer']:has([data-testid='stCaptionContainer']){margin-top:-0.9rem}
.st-key-caja_descarga [class*='st-key-rst_']{top:-0.15rem!important;right:0!important}
.st-key-caja_descarga > [data-testid='stElementContainer']:has(.tit-datos){margin-bottom:-0.7rem}
.st-key-caja_descarga .cap-der{text-align:right}
/* datos: nombre, formato y descarga cuadrada en una fila */
.st-key-fila_datos{flex-wrap:nowrap!important}
.st-key-fila_datos > [data-testid='stElementContainer']{width:auto!important}
.st-key-fila_datos > [data-testid='stElementContainer']:nth-child(1){flex:1 1 0;min-width:0}
.st-key-fila_datos > [data-testid='stElementContainer']:nth-child(2){flex:0 0 6.3rem}
.st-key-fila_datos > [data-testid='stElementContainer']:nth-child(3){flex:0 0 2rem}
.st-key-fila_datos [data-testid='stSelectbox']{width:100%}
.st-key-fila_datos [data-testid='stSelectbox'] input{padding:0 0.2rem;text-align:center}
.st-key-fila_datos [data-testid='stDownloadButton'] button{width:2rem;height:2rem;min-height:2rem;padding:0}
/* botón de la tabla: como una sección de la barra; resaltado mientras la tabla está abierta */
[data-testid='stSidebar'] [class*='st-key-btn_tabla'] button{justify-content:flex-start;min-height:2.6rem;padding-left:1rem;padding-right:2.4rem;
  border:1px solid rgba(128,128,128,.35);border-radius:0.5rem;background:transparent}
[data-testid='stSidebar'] [class*='st-key-btn_tabla'] button > div,
[data-testid='stSidebar'] [class*='st-key-btn_tabla'] button [data-testid='stMarkdownContainer']{width:100%;justify-content:flex-start;text-align:left}
[data-testid='stSidebar'] [class*='st-key-btn_tabla'] button p{text-align:left;display:flex;align-items:center;gap:0.5rem;margin:0}
[class*='st-key-fila_tabla']{position:relative;gap:0!important}
[class*='st-key-fila_tabla'] [data-testid='stElementContainer']:has([data-testid='stTooltipIcon']){
  position:absolute;right:0.7rem;top:0;bottom:0;display:flex;align-items:center;width:auto!important;height:auto!important;z-index:3}
[class*='st-key-fila_tabla'] [data-testid='stElementContainer']:has([data-testid='stTooltipIcon']) *{margin:0!important;padding-top:0!important;padding-bottom:0!important;line-height:1}
[class*='st-key-fila_tabla'] [data-testid='stElementContainer']:has([data-testid='stTooltipIcon']) [data-testid='stMarkdownContainer'] p{display:flex;align-items:center}
body[data-zona='tabla'] [data-testid='stSidebar'] [class*='st-key-btn_tabla'] button{border-color:currentColor;background:rgba(127,167,209,.18)}
/* cuadros de color pequeños y pegados, con su número adentro */
[class*='st-key-cuadros_']{counter-reset:cuadro}
[class*='st-key-cuadros_'] [data-testid='stElementContainer']{width:auto!important;flex:0 0 auto}
[class*='st-key-cuadros_'] [data-testid='stColorPicker']{counter-increment:cuadro;width:auto}
[class*='st-key-cuadros_'] [data-testid='stColorPickerBlock']{width:1.7rem;height:1.7rem;border-radius:0.3rem;position:relative}
[class*='st-key-cuadros_'] [data-testid='stColorPickerBlock']::after{content:counter(cuadro);position:absolute;inset:0;
  display:flex;align-items:center;justify-content:center;font-size:0.72rem;font-weight:700;color:#fff;
  text-shadow:0 0 3px rgba(0,0,0,.95),0 0 2px rgba(0,0,0,.95);pointer-events:none}
/* colores fijos (sin dato, resto del país, vecinos, fondo, mar): mismo cuadro que los de la escala */
[class*='st-key-colores_fijos']{gap:0.6rem!important}
[class*='st-key-fila_color_'] > [data-testid='stElementContainer']:nth-child(1){flex:1 1 0;min-width:0;min-height:1.3rem}
[class*='st-key-fila_color_'] > [data-testid='stElementContainer']:nth-child(2){flex:0 0 auto;width:auto!important}
[class*='st-key-fila_color_'] p{margin:0;line-height:1.2}
[class*='st-key-fila_color_'] [data-testid='stColorPicker']{height:1.65rem;display:flex;align-items:center}
[data-testid='stSidebar'] [class*='st-key-fila_color_'] [data-testid='stColorPickerBlock']{width:4.375rem;height:1.65rem;border-radius:0.3rem}
/* botón de la paleta y campos numéricos más bajos */
[data-testid='stSidebar'] [data-testid='stPopover'] > button,
[data-testid='stSidebar'] [data-testid='stPopover'] button[data-testid='stPopoverButton']{min-height:2rem;height:2rem;padding-top:0;padding-bottom:0}
[data-testid='stSidebar'] [data-testid='stNumberInput'],[data-testid='stSidebar'] [data-testid='stNumberInputContainer'],
[data-testid='stSidebar'] [data-testid='stNumberInput'] [data-baseweb='input'],[data-testid='stSidebar'] [data-testid='stNumberInput'] [data-baseweb='base-input']{min-height:2rem!important;height:2rem!important}
[data-testid='stSidebar'] [data-testid='stNumberInput'] input{padding-top:0;padding-bottom:0}
[data-testid='stSidebar'] [data-testid='stNumberInput'] button{min-height:2rem}
[data-testid='stSidebar'] [data-testid='stElementContainer']:has(.etq-campo){height:auto!important;min-height:1.2rem}
[data-testid='stSidebar'] [data-testid='stNumberInput'] input{text-align:center}
/* lista de paletas: filas pegadas y el signo de pregunta centrado en su columna */
[data-testid='stPopoverBody']:has([class*='_op_']) [data-testid='stVerticalBlock']{gap:0.4rem}
[data-testid='stPopoverBody']:has([class*='st-key-dl_tabla_']){padding:0.5rem;box-sizing:border-box;width:var(--ancho-descarga,auto)!important;min-width:0!important;max-width:none!important}
[data-testid='stPopoverBody']:has([class*='_op_']) [data-testid='stHorizontalBlock']{align-items:center;gap:0.25rem;padding:0.2rem 0}
[data-testid='stPopoverBody']:has([class*='_op_']) [data-testid='stColumn']:nth-child(2){transform:translateY(-0.55rem)}
[data-testid='stPopoverBody']:has([class*='_op_']) [data-testid='stColumn'],
[data-testid='stPopoverBody']:has([class*='_op_']) [data-testid='stColumn'] [data-testid='stVerticalBlock'],
[data-testid='stPopoverBody']:has([class*='_op_']) [data-testid='stElementContainer'],
[data-testid='stPopoverBody']:has([class*='_op_']) [data-testid='stButton']{min-height:0!important;height:auto!important;line-height:0}
[data-testid='stPopoverBody']:has([class*='_op_']) [data-testid='stMarkdown'] p{margin:0;line-height:1}
[data-testid='stPopoverBody']:has([class*='_op_']) [data-testid='stMarkdownContainer']{display:flex;align-items:center;justify-content:center}
[data-testid='stPopoverBody']:has([class*='_op_']) [data-testid='stColumn']:nth-child(2) [data-testid='stElementContainer'],
[data-testid='stPopoverBody']:has([class*='_op_']) [data-testid='stColumn']:nth-child(2) [data-testid='stMarkdown']{
  display:flex;justify-content:center;width:100%}
/* campos de texto con su formato al lado (como en Word) */
.etq-campo{font-size:0.875rem;margin:0;line-height:1.2;white-space:nowrap}
[data-testid='stSidebar'] [data-testid='stColumn']:has([data-testid='stButtonGroup']) [data-testid='stButtonGroup']{justify-content:flex-end}
/* botones de formato (negrita, cursiva, subrayado): círculos pequeños en vez de óvalos */
[data-testid='stSidebar'] [data-testid='stButtonGroup'] button[data-variant='pills']{width:1.4rem;height:1.4rem;min-width:1.4rem;min-height:1.4rem;
  padding:0;border-radius:50%;display:inline-flex;align-items:center;justify-content:center}
[data-testid='stSidebar'] [data-testid='stButtonGroup'] button[data-variant='pills'] *{font-size:0.85rem!important;line-height:1;margin:0}
[data-testid='stSidebarUserContent']{padding-bottom:4rem!important}
/* separadores de la barra lateral: más delgados, con menos aire */
[data-testid='stSidebar'] hr{margin:0.2rem 0!important}
/* círculos de formato a la derecha del campo y del tamaño del «?» */
[data-testid='stSidebar'] [data-testid='stButtonGroup'] button[data-variant='pills']{width:1.1rem!important;height:1.1rem!important;min-width:1.1rem!important;min-height:1.1rem!important}
[data-testid='stSidebar'] [data-testid='stButtonGroup'] button[data-variant='pills'] *{font-size:0.72rem!important}
.etq-centro{text-align:center}
[data-testid='stSidebar'] [data-testid='stColumn']:has([data-testid='stButtonGroup']) > [data-testid='stVerticalBlock']{align-items:flex-end;padding-right:0.35rem}
[data-testid='stSidebar'] [data-testid='stButtonGroup'] > div{justify-content:flex-end}
/* título, subtítulo y nota: una línea que se abre cuando el texto es más largo */
[data-testid='stSidebar'] [data-testid='stTextArea'] textarea{field-sizing:content;min-height:1.85rem!important;height:auto!important;max-height:9rem;padding:0.35rem 0.6rem;line-height:1.25;resize:none}
[data-testid='stSidebar'] [data-testid='stTextArea'] [data-baseweb='textarea'],[data-testid='stSidebar'] [data-testid='stTextArea'] [data-baseweb='base-input']{min-height:2rem!important;height:auto!important}
/* listas desplegables de la barra lateral: misma altura que los campos de texto */
[data-testid='stSidebar'] [data-testid='stSelectbox'] > div,[data-testid='stSidebar'] [data-testid='stSelectbox'] > div > div{min-height:2rem!important;height:2rem!important}
[data-testid='stSidebar'] [data-testid='stSelectbox'] input{height:100%!important;padding-top:0;padding-bottom:0}
[data-testid='stSidebar'] [data-testid='stSelectbox'] button{height:100%!important}
/* campos de tamaño estrechos, sin botones − + */
[class*='st-key-bordes__gro_'] button,[class*='st-key-bordes__contorno_'] button{display:none}
[class*='st-key-pt_'] input,[class*='st-key-bordes__gro_'] input,[class*='st-key-bordes__contorno_'] input{padding:0 0.2rem;text-align:center}
/* panel de texto: pares nombre + control; dos por línea si el ancho alcanza (pw_*); el script muestra el panel del texto activo */
[data-testid='stExpanderDetails']:has(.st-key-panel_texto){padding-left:0.5rem;padding-right:0.5rem}
.st-key-panel_texto{gap:0!important;border:1px solid rgba(140,160,185,.45);border-radius:0.5rem;padding:0.6rem 0.7rem 0.7rem}
.st-key-panel_texto [data-testid='stLayoutWrapper']:has(> [class*='st-key-ctl_']){display:none}
:root:not([data-ctl]) .st-key-panel_texto [data-testid='stLayoutWrapper']:has(> .st-key-ctl_tit),
:root[data-ctl='tit'] .st-key-panel_texto [data-testid='stLayoutWrapper']:has(> .st-key-ctl_tit),
:root[data-ctl='sub'] .st-key-panel_texto [data-testid='stLayoutWrapper']:has(> .st-key-ctl_sub),
:root[data-ctl='nota'] .st-key-panel_texto [data-testid='stLayoutWrapper']:has(> .st-key-ctl_nota),
:root[data-ctl='ley'] .st-key-panel_texto [data-testid='stLayoutWrapper']:has(> .st-key-ctl_ley),
:root[data-ctl='ext'] .st-key-panel_texto [data-testid='stLayoutWrapper']:has(> .st-key-ctl_ext),
:root[data-ctl='extd'] .st-key-panel_texto [data-testid='stLayoutWrapper']:has(> .st-key-ctl_extd){display:block}
[class*='st-key-ctl_']{gap:0.4rem!important}
[class*='st-key-pt_']{gap:0.3rem!important}
[class*='st-key-pt_'] p{margin:0;line-height:1.2;white-space:nowrap}
[class*='st-key-pt_'] .etq-campo{font-size:0.8rem}
.pt-edit{font-size:0.8rem;margin:0 0 0.9rem;opacity:0.85}
[class*='st-key-pw_b_']{margin-top:0.55rem}
.pt-edit b{color:#6FA3D8;font-size:0.9rem}
[class*='st-key-pt_'] > [data-testid='stElementContainer']{width:auto!important;display:flex;align-items:center;justify-content:flex-end}
[class*='st-key-pt_'] > [data-testid='stElementContainer']:nth-child(1){flex:1 1 0;min-width:0;justify-content:flex-start;padding-left:0.4rem}
[class*='st-key-pt_'] > [data-testid='stElementContainer']:nth-child(2){flex:0 0 auto}
[class*='st-key-pt_a_'] > [data-testid='stElementContainer']:nth-child(1){flex:0 0 auto;padding-right:0.3rem}
[class*='st-key-pt_a_'] > [data-testid='stElementContainer']:nth-child(2){flex:1 1 0;min-width:0}
[class*='st-key-pt_'] [data-testid='stNumberInput']{width:4.375rem;margin-left:auto}
[class*='st-key-pt_'] [data-testid='stNumberInput'] button{width:0.95rem;min-width:0.95rem;padding:0}
[class*='st-key-pt_'] [data-testid='stNumberInput'] input{padding:0 0.1rem;font-size:0.85rem}
[class*='st-key-pt_'] [data-testid='stColorPicker']{height:1.7rem;display:flex;align-items:center;justify-content:flex-end}
[class*='st-key-pt_'] [data-testid='stMarkdownContainer']{margin-bottom:0!important}
[class*='st-key-pw_']{display:grid!important;grid-template-columns:repeat(auto-fill,minmax(7.7rem,1fr));gap:0.4rem 0.9rem!important}
[class*='st-key-pw_'] > *{min-width:0}
[class*='st-key-pt_a_'] [data-testid='stSelectbox']{width:100%;max-width:none}
.st-key-panel_texto{container-type:inline-size}
/* con dos pares por línea, la tipografía arranca donde el campo Tamaño (controles de 4,4 rem) */
@container (min-width: 16.4rem){
  [class*='st-key-pt_a_'] > [data-testid='stElementContainer']:nth-child(1){flex:0 0 calc((100% - 0.9rem) / 2 - 4.7rem);padding-right:0}
}
.st-key-panel_texto [data-testid='stButtonGroup'] button[data-variant='pills']{width:1.35rem!important;height:1.35rem!important;min-width:1.35rem!important;min-height:1.35rem!important}
.st-key-panel_texto [data-testid='stButtonGroup'] button[data-variant='pills'] *{font-size:0.85rem!important}
/* controles del panel más bajos que los demás de la barra lateral */
[data-testid='stSidebar'] .st-key-panel_texto [data-testid='stNumberInput'],
[data-testid='stSidebar'] .st-key-panel_texto [data-testid='stNumberInputContainer'],
[data-testid='stSidebar'] .st-key-panel_texto [data-testid='stNumberInput'] [data-baseweb='input'],
[data-testid='stSidebar'] .st-key-panel_texto [data-testid='stNumberInput'] [data-baseweb='base-input'],
[data-testid='stSidebar'] .st-key-panel_texto [data-testid='stNumberInput'] button,
[data-testid='stSidebar'] .st-key-panel_texto [data-testid='stSelectbox'] > div,
[data-testid='stSidebar'] .st-key-panel_texto [data-testid='stSelectbox'] > div > div{min-height:1.65rem!important;height:1.65rem!important}
[data-testid='stSidebar'] .st-key-panel_texto [data-testid='stSelectbox'] button{height:100%!important}
[data-testid='stSidebar'] .st-key-panel_texto [data-testid='stColorPicker']{height:1.65rem}
[data-testid='stSidebar'] .st-key-panel_texto [data-testid='stColorPickerBlock']{width:4.375rem;height:1.65rem}
/* botón Aa: abre debajo el panel de texto de una función */
[class*='st-key-fila_aa_'] > [data-testid='stElementContainer']:nth-child(1){flex:1 1 0;min-width:0}
[class*='st-key-fila_aa_'] > [data-testid='stElementContainer']:nth-child(2){flex:0 0 auto;width:auto!important}
[class*='st-key-fila_aa_'] button,[class*='st-key-fila_lista_aa'] button{min-height:1.7rem;height:1.7rem;padding:0 0.7rem;font-weight:700;font-size:0.85rem}
[class*='st-key-fila_lista_aa'] > [data-testid='stElementContainer']:nth-child(1){flex:0 0 auto}
[class*='st-key-fila_lista_aa'] > [data-testid='stElementContainer']:nth-child(2){flex:1 1 0;min-width:0}
[class*='st-key-fila_lista_aa'] > [data-testid='stElementContainer']:nth-child(3){flex:0 0 auto;width:auto!important}
[class*='st-key-fila_aa_'] button p,[class*='st-key-fila_lista_aa'] button p{font-size:0.85rem;font-weight:700}
[data-testid='stLayoutWrapper']:has(> [class*='st-key-hueco_aa_']):not(:has(.aa-abierto)){display:none}
[class*='st-key-panel_pop_']{gap:0!important;container-type:inline-size;border:1px solid rgba(140,160,185,.45);border-radius:0.5rem;padding:0.6rem 0.7rem 0.7rem}
[data-testid='stSidebar'] [class*='st-key-panel_pop_'] [data-testid='stButtonGroup'] button[data-variant='pills']{width:1.35rem!important;height:1.35rem!important;min-width:1.35rem!important;min-height:1.35rem!important;padding:0!important}
[data-testid='stSidebar'] [class*='st-key-panel_pop_'] [data-testid='stButtonGroup'] button[data-variant='pills'] *{font-size:0.85rem!important}
[data-testid='stSidebar'] [class*='st-key-panel_pop_'] [data-testid='stButtonGroup'] button[data-variant='pills']{border-radius:50%;display:inline-flex;align-items:center;justify-content:center}
[data-testid='stSidebar'] [class*='st-key-panel_pop_'] [data-testid='stButtonGroup'] button[data-variant='pills'] *{line-height:1;margin:0}
[data-testid='stSidebar'] [class*='st-key-panel_pop_'] [data-testid='stButtonGroup'],[class*='st-key-panel_pop_'] [data-testid='stButtonGroup'] > div{justify-content:flex-end;gap:2.6px}
[data-testid='stSidebar'] [class*='st-key-panel_pop_'] [data-testid='stNumberInput'],
[data-testid='stSidebar'] [class*='st-key-panel_pop_'] [data-testid='stNumberInputContainer'],
[data-testid='stSidebar'] [class*='st-key-panel_pop_'] [data-testid='stNumberInput'] [data-baseweb='input'],
[data-testid='stSidebar'] [class*='st-key-panel_pop_'] [data-testid='stNumberInput'] [data-baseweb='base-input'],
[data-testid='stSidebar'] [class*='st-key-panel_pop_'] [data-testid='stNumberInput'] button,
[data-testid='stSidebar'] [class*='st-key-panel_pop_'] [data-testid='stSelectbox'] > div,
[data-testid='stSidebar'] [class*='st-key-panel_pop_'] [data-testid='stSelectbox'] > div > div{min-height:1.65rem!important;height:1.65rem!important}
[data-testid='stSidebar'] [class*='st-key-panel_pop_'] [data-testid='stSelectbox'] button{height:100%!important}
[data-testid='stSidebar'] [class*='st-key-panel_pop_'] [data-testid='stColorPicker']{height:1.65rem}
[data-testid='stSidebar'] [class*='st-key-panel_pop_'] [data-testid='stColorPickerBlock']{width:4.375rem;height:1.65rem}
[class*='st-key-pt_s_'] [data-testid='stTextInput']{width:4.375rem;margin-left:auto}
[data-testid='stSidebar'] [class*='st-key-panel_pop_'] [data-testid='stTextInputRootElement'],
[data-testid='stSidebar'] [class*='st-key-panel_pop_'] [data-testid='stTextInput'] [data-baseweb='input'],
[data-testid='stSidebar'] [class*='st-key-panel_pop_'] [data-testid='stTextInput'] [data-baseweb='base-input']{min-height:1.65rem!important;height:1.65rem!important}
.etq-caja{margin-top:0.2rem}
[data-testid='stElementContainer']:has(.etq-caja){margin-bottom:-0.5rem}
/* la caja del texto activo lleva el borde de color del panel */
:root:not([data-ctl]) [class*='st-key-tit__titulo__'] [data-testid='stTextAreaRootElement'],
:root[data-ctl='tit'] [class*='st-key-tit__titulo__'] [data-testid='stTextAreaRootElement'],
:root[data-ctl='sub'] [class*='st-key-tit__subtitulo__'] [data-testid='stTextAreaRootElement'],
:root[data-ctl='nota'] [class*='st-key-tit__fuente_nota__'] [data-testid='stTextAreaRootElement'],
:root[data-ctl='ley'] [class*='st-key-ley__ley_tit_'] [data-testid='stTextAreaRootElement'],
:root[data-ctl='ext'] [class*='st-key-ley__texto_menor__'] [data-testid='stTextInputRootElement'],
:root[data-ctl='extd'] [class*='st-key-ley__texto_mayor__'] [data-testid='stTextInputRootElement']{border-color:#6FA3D8!important}
/* Líneas y límites: tres celdas de medida fija (color, nombre y grosor), centradas en vertical */
[class*='st-key-linea_'] p{margin:0;line-height:1.2;font-size:0.84rem}
/* filas con nombre a la izquierda y lista al frente; nombre y «?» en una línea */
[class*='st-key-fila_op_'] > [data-testid='stElementContainer']:nth-child(1){flex:1 1 0;min-width:0}
[class*='st-key-fila_op_'] > [data-testid='stElementContainer']:nth-child(2){flex:0 0 9.2rem;width:9.2rem!important}
[class*='st-key-fila_op_'] p{margin:0;white-space:nowrap}
/* celulares: la barra mide menos de 330 px; la lista pasa debajo de su nombre y los nombres largos pueden partirse */
@media (max-width:480px){
  [class*='st-key-fila_op_']{flex-wrap:wrap!important}
  [class*='st-key-fila_op_'] > [data-testid='stElementContainer']:nth-child(n){flex:1 1 100%;width:100%!important}
  [class*='st-key-fila_color_'] p,.etq-campo{white-space:normal}
}
[data-testid='stSidebar'] p:has([data-testid='stTooltipIcon']){white-space:nowrap}
/* listas desplegables: opciones más juntas, igual en toda la aplicación */
[role='listbox'] [role='option']{height:2.1rem!important;min-height:0!important}
/* cantidad de colores y de tonos: un campo pequeño, sin botones − y + */
[data-testid='stSidebar'] [class*='st-key-colores__n_'] button{display:none}
[data-testid='stSidebar'] [class*='st-key-colores__n_'] [data-testid='stNumberInput']{width:3.2rem;margin-left:auto}
[data-testid='stSidebar'] [class*='st-key-colores__n_'] input{text-align:center;padding:0 0.2rem}
[class*='st-key-linea_'] [data-testid='stMarkdownContainer']{margin-bottom:0!important}
[class*='st-key-linea_'] [data-testid='stColorPicker']{height:1.7rem;display:flex;align-items:center}
[class*='st-key-linea_'] > [data-testid='stElementContainer']{width:auto!important;display:flex;align-items:center}
[class*='st-key-linea_'] > [data-testid='stElementContainer']:nth-child(1){flex:0 0 2.3rem;justify-content:center}
[class*='st-key-linea_'] > [data-testid='stElementContainer']:nth-child(2){flex:1 1 0;min-width:0}
[class*='st-key-linea_'] > [data-testid='stElementContainer']:nth-child(3){flex:0 0 5.7rem;justify-content:center}
[class*='st-key-linea_'] > [data-testid='stElementContainer']:nth-child(4){flex:0 0 2.8rem;justify-content:center}
/* con barra estrecha, el nombre de la línea pasa arriba */
[data-testid='stExpanderDetails']:has([class*='st-key-linea_']){container-type:inline-size}
@container (max-width: 17.5rem){
  [class*='st-key-linea_']{flex-wrap:wrap!important;row-gap:0.3rem!important}
  [class*='st-key-linea_'] > [data-testid='stElementContainer']:nth-child(2){flex:1 0 100%;order:-1}
  [class*='st-key-linea_'] > [data-testid='stElementContainer']:nth-child(1){justify-content:flex-start}
}
[data-testid='stSidebar'] [class*='st-key-linea_'] [data-testid='stSelectbox'] > div,[data-testid='stSidebar'] [class*='st-key-linea_'] [data-testid='stSelectbox'] > div > div{min-height:1.85rem!important;height:1.85rem!important}
/* tipo de línea: muestra con flecha; el botón de abrir cubre la celda */
[class*='st-key-linea_'] [data-testid='stSelectbox'] [role='group']{position:relative;padding:0}
[class*='st-key-linea_'] [data-testid='stSelectbox'] [role='group'] button{position:absolute;inset:0;width:100%;height:100%;background:transparent;justify-content:flex-end;padding:0 0.3rem 0 0}
[class*='st-key-linea_'] [data-testid='stSelectbox'] [role='group'] button svg{width:1.15rem;height:1.15rem}
[class*='st-key-linea_'] [data-testid='stSelectbox'] input{flex:1 1 auto;width:100%!important;padding:0 1.9rem 0 0.3rem!important;text-align:center;font-size:0.9rem;letter-spacing:0;pointer-events:none;text-overflow:clip;caret-color:transparent}
[data-baseweb='popover'] [role='option']:has(> div){white-space:nowrap}
[class*='st-key-linea_'] [data-testid='stNumberInput']{width:2.8rem}
/* cuadros de color de las líneas: del mismo tamaño que los de Colores */
[class*='st-key-bordes__col_'] [data-testid='stColorPicker']{width:auto}
[class*='st-key-bordes__col_'] [data-testid='stColorPickerBlock']{width:1.7rem;height:1.7rem;border-radius:0.3rem}
/* cuadros de color de la barra: todos del mismo tamaño */
[data-testid='stSidebar'] [data-testid='stColorPicker']{width:auto}
[data-testid='stSidebar'] [data-testid='stColorPickerBlock']{width:1.7rem;height:1.7rem;border-radius:0.3rem}
/* campos de texto de la barra lateral: misma altura que los campos numéricos y las listas */
[data-testid='stSidebar'] [data-testid='stTextInputRootElement']{min-height:2rem!important;height:2rem!important}
[data-testid='stSidebar'] [data-testid='stTextInput'] input{padding-top:0;padding-bottom:0}
[data-testid='stSidebar'] [data-testid='stButtonGroup'] > div{flex-wrap:nowrap;gap:0.15rem}
/* el mapa se ajusta al alto de la ventana: se ve completo sin desplazarse */
.st-key-tarjeta_mapa [data-testid='stFullScreenFrame']>div{width:100%!important;justify-content:center}
/* el script amplía o reduce el mapa con un clic; se oculta el botón de Streamlit */
.st-key-tarjeta_mapa [data-testid='stImage'] img{cursor:pointer}
.st-key-tarjeta_mapa [data-testid='stBaseButton-elementToolbar']{display:none}
[data-testid='stImage'] img{max-height:calc(100vh - 7.2rem);width:auto!important;max-width:100%;
  object-fit:contain;display:block;margin:0 auto}
/* pantalla de carga: silueta de Colombia que se llena de calor, con el título y la etapa */
/* crédito fijo al pie de la barra lateral; el script le da el fondo y el ancho de la barra */
.credito{position:fixed;bottom:0;left:0;width:var(--lateral-ancho,21rem);box-sizing:border-box;padding:0.45rem 1.6rem 0.6rem;background:var(--lateral-fondo,#13263A);color:#8FA9C4;font-size:0.8rem;letter-spacing:0.02em;z-index:5;border-top:1px solid rgba(143,169,196,0.18)}
.st-key-pantalla_carga{height:calc(100vh - 6rem);align-items:center;justify-content:center;padding-top:4rem;gap:0.3rem}
.st-key-pantalla_carga [data-testid='stElementContainer']{width:100%!important}
.st-key-pantalla_carga p.carga-paso{text-align:center}
.carga{display:flex;flex-direction:column;align-items:center;gap:1rem;text-align:center;width:100%}
.carga-mapa{position:relative;height:calc(100vh - 21rem);max-height:46rem;aspect-ratio:100/137}
.carga-mapa > div{position:absolute;inset:0}
@property --n{syntax:'<number>';inherits:true;initial-value:0}
@keyframes carga-sube{0%{--n:0;animation-timing-function:cubic-bezier(0.215,0.61,0.355,1)}20%{--n:90;animation-timing-function:linear}100%{--n:99}}
@keyframes carga-cierra{from{--n:var(--de)}to{--n:var(--a)}}
.carga-mapa{--n:0;animation:carga-sube 60s forwards}
.carga-mapa.carga-fin{animation:carga-cierra 0.6s linear forwards}
.carga-calor{clip-path:inset(calc(100% - var(--n) * 1%) 0 0 0)}
.carga-pct{display:flex;align-items:center;justify-content:center;font-size:3.4rem;font-weight:700;color:#fff;text-shadow:0 0 0.4rem #13263A,0 0 0.9rem #13263A,0 0 1.4rem #13263A;font-variant-numeric:tabular-nums;counter-reset:n calc(var(--n))}
.carga-pct::after{content:counter(n) ' %'}
.carga-base{background:rgba(19,38,58,0.12);-webkit-mask:__MASCARA__;mask:__MASCARA__}
.carga-calor{background:#13263A;-webkit-mask:__MASCARA__;mask:__MASCARA__}
.carga h1{font-size:3.2rem;line-height:1.1;font-weight:700;color:var(--primario,#1F4E79);margin:0;padding:0}
.st-key-pantalla_carga [data-testid='stMarkdownContainer'] p.carga-paso,.carga p{margin:0;color:#5D6B80;font-size:1.25rem;min-height:1.8rem}
</style>""".replace("__MASCARA__", MASCARA)

# Script de la página: acordeón, pestañas, tema, tabla y paneles
_CODIGO = r"""
const W = window, doc = document;
// Tema: aplica el selector de la tarjeta con el menú de Streamlit
function esOscuro() {
  const app = doc.querySelector(".stApp");
  if (!app) return false;
  const m = getComputedStyle(app).backgroundColor.match(/\d+/g) || [255, 255, 255];
  return (0.2126 * m[0] + 0.7152 * m[1] + 0.0722 * m[2]) / 255 < 0.5;
}
let cambiando = false;
async function cambiarTema(destino) {
  const menu = doc.querySelector("[data-testid='stMainMenu']");
  if (!menu || cambiando) return;
  cambiando = true;
  // oculta el menú mientras se usa, para que no parpadee
  let oc = doc.getElementById("ocultar-menu");
  if (!oc) {
    oc = doc.createElement("style");
    oc.id = "ocultar-menu";
    doc.head.appendChild(oc);
  }
  oc.textContent = "[data-testid='stMainMenuPopover'],div[data-baseweb='popover']:has([data-testid='stMainMenuPopover'])," +
                   "[data-baseweb='layer']:has([data-testid='stMainMenuPopover']){opacity:0!important;" +
                   "pointer-events:none!important;transition:none!important}";
  (menu.querySelector("button") || menu).click();
  for (let i = 0; i < 40; i++) {
    const op = doc.querySelector(`[data-testid='stMainMenuItem-theme-${destino}']`);
    if (op) { op.click(); break; }
    await new Promise(r => setTimeout(r, 50));
  }
  setTimeout(() => {   // cierra el menú si quedó abierto
    if (doc.querySelector("[data-testid='stMainMenuPopover']"))
      doc.body.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
    setTimeout(() => {
      if (!doc.querySelector("[data-testid='stMainMenuPopover']")) oc.textContent = "";
      cambiando = false;
    }, 250);
  }, 150);
}
function aplicarTema() {
  const viejo = doc.getElementById("btn-tema");   // botón de versiones anteriores
  if (viejo) viejo.remove();
  const ancla = doc.getElementById("ancla-tema");
  if (!ancla || !ancla.dataset.tema) return;
  const quiereOscuro = ancla.dataset.tema === "oscuro";
  if (quiereOscuro !== esOscuro()) cambiarTema(quiereOscuro ? "Dark" : "Light");
}
function ponerTitulos() {
  // título al pasar el cursor sobre los botones de iconos
  const ancla = doc.getElementById("ancla-tema");
  if (!ancla || !ancla.dataset.titulos) return;
  const titulos = JSON.parse(ancla.dataset.titulos);
  doc.querySelectorAll("[data-testid='stButtonGroup'] button").forEach(b => {
    const contenido = (b.textContent || "").trim();     // los iconos traen su nombre dos veces: "light_mode iconlight_mode"
    const clave = Object.keys(titulos).find(k => contenido === k || contenido === `${k} icon${k}`);
    if (clave && b.title !== titulos[clave]) b.title = titulos[clave];
  });
}
function accesibilidad() {
  // idioma del documento, texto alternativo de los mapas y nombre de los botones de restablecer
  const ancla = doc.getElementById("ancla-tema");
  if (!ancla) return;
  if (ancla.dataset.lang && doc.documentElement.lang !== ancla.dataset.lang) doc.documentElement.lang = ancla.dataset.lang;
  doc.querySelectorAll("[data-testid='stImage'] img").forEach(i => { if (ancla.dataset.alt && i.alt !== ancla.dataset.alt) i.alt = ancla.dataset.alt; });
  doc.querySelectorAll("[class*='st-key-rst_'] button").forEach(b => { if (ancla.dataset.rst && b.getAttribute("aria-label") !== ancla.dataset.rst) b.setAttribute("aria-label", ancla.dataset.rst); });
}
function sinDesplazamientoLateral() {
  const c = doc.querySelector("[data-testid='stSidebarContent']");
  if (c && c.scrollLeft) c.scrollLeft = 0;
}
if (!doc.__tema) {
  doc.__tema = true;
  setInterval(() => {
    aplicarTema(); sinDesplazamientoLateral(); ponerTitulos(); accesibilidad();
    // color de las tarjetas según el tema (blanco en claro, gris azulado en oscuro)
    const tj = doc.querySelector(".st-key-tarjeta_mapa");
    if (tj) {   // borde derecho de la tarjeta: el panel de mapas guardados se alinea con él
      const der = Math.round(doc.documentElement.clientWidth - tj.getBoundingClientRect().right + 8) + "px";
      if (doc.documentElement.style.getPropertyValue("--der-tarjeta") !== der) doc.documentElement.style.setProperty("--der-tarjeta", der);
    }
    const lat = doc.querySelector("[data-testid='stSidebar']");
    if (lat) {   // fondo y ancho de la barra lateral para el crédito
      const fondo = getComputedStyle(lat).backgroundColor, ancho = Math.round(lat.getBoundingClientRect().width) + "px";
      if (doc.documentElement.style.getPropertyValue("--lateral-fondo") !== fondo) doc.documentElement.style.setProperty("--lateral-fondo", fondo);
      if (doc.documentElement.style.getPropertyValue("--lateral-ancho") !== ancho) doc.documentElement.style.setProperty("--lateral-ancho", ancho);
    }
    const c = esOscuro() ? "#1A2430" : "#FFFFFF";
    if (doc.documentElement.style.getPropertyValue("--tarjeta") !== c) doc.documentElement.style.setProperty("--tarjeta", c);
    // azul principal del tema
    const azul = esOscuro() ? "#7FA7D1" : "#1F4E79", texto = esOscuro() ? "#0B1622" : "#FFFFFF";
    if (doc.documentElement.style.getPropertyValue("--primario") !== azul) {
      doc.documentElement.style.setProperty("--primario", azul);
      doc.documentElement.style.setProperty("--primario-texto", texto);
    }
  }, 300);
}
if (!doc.__mapaClic) {
  doc.__mapaClic = true;
  // un clic en el mapa lo amplía; otro clic (en el mapa o en el fondo) lo reduce
  doc.addEventListener("click", (ev) => {
    const marco = ev.target.closest("[data-testid='stFullScreenFrame']");
    if (!marco || !marco.closest(".st-key-tarjeta_mapa") || ev.target.closest("button")) return;
    const ampliado = getComputedStyle(marco).position === "fixed";
    if (!ev.target.closest("img") && !ampliado) return;
    const boton = marco.querySelector("button[data-testid='stBaseButton-elementToolbar']");
    if (boton) boton.click();
    setTimeout(() => marco.classList.toggle("ampliado", getComputedStyle(marco).position === "fixed"), 200);
  }, true);
}
if (!doc.__colaAbierta) {
  doc.__colaAbierta = { abierta: false };
  // el panel de mapas guardados se queda abierto al guardar o eliminar (Streamlit lo cierra al redibujar)
  const trigger = () => [...doc.querySelectorAll(".st-key-iconos_mapa [data-testid='stPopoverButton']")].find(b => b.textContent.includes("layers"));
  const estado = doc.__colaAbierta;
  doc.addEventListener("click", (ev) => {
    const dentro = ev.target.closest("[data-testid='stPopoverBody']:has(.cuerpo-cola)"), b = trigger();
    if (ev.target.closest(".st-key-btn_galeria")) estado.abierta = false;
    else if (dentro) estado.abierta = estado.abierta || !!ev.target.closest("button");
    else if (b && b.contains(ev.target)) { estado.abierta = b.getAttribute("aria-expanded") !== "true"; estado.visto = false; }
    else estado.abierta = false;
  }, true);
  doc.addEventListener("keydown", (ev) => { if (ev.key === "Escape") estado.abierta = false; }, true);
  setInterval(() => {
    const b = trigger();
    if (!b) return;
    if (b.getAttribute("aria-expanded") === "true") { estado.visto = true; return; }
    if (estado.abierta && estado.visto) { estado.visto = false; b.click(); }   // se cerró solo al redibujar: se reabre
  }, 400);
}
if (!doc.__galeria) {
  doc.__galeria = true;
  doc.addEventListener("click", (ev) => {
    // «Ver galería» cierra el panel de mapas guardados
    if (ev.target.closest(".st-key-btn_galeria"))
      [250, 700].forEach(ms => setTimeout(() => {
        const b = [...doc.querySelectorAll(".st-key-iconos_mapa [data-testid='stPopoverButton']")].find(x => x.textContent.includes("layers"));
        if (b && b.getAttribute("aria-expanded") === "true") b.click();
      }, ms));
    // un clic en la barra lateral cierra la galería
    if (ev.target.closest("[data-testid='stSidebar']")) {
      const x = doc.querySelector(".st-key-cerrar_todo button");
      if (x) setTimeout(() => x.click(), 0);
    }
    // un clic fuera del mapa abierto vuelve a las miniaturas
    const g = doc.querySelector(".st-key-galeria_cola");
    if (!g || !ev.target.closest("[data-testid='stMain']")) return;
    if (ev.target.closest("[class*='st-key-miniatura_'],.st-key-mapa_grande img,.st-key-mapa_grande button,.st-key-cab_galeria,.st-key-barra_galeria,.st-key-iconos_mapa,[data-testid='stPopoverBody'],[data-baseweb='popover'],.ampliado")) return;
    const b = g.querySelector(".st-key-volver_min button");
    if (b) setTimeout(() => b.click(), 0);
  }, true);
}
if (!doc.__cierraLista) {
  doc.__cierraLista = true;
  // las listas de paletas se cierran al elegir una opción, como un menú desplegable
  doc.addEventListener("click", (ev) => {
    if (!ev.target.closest("[data-testid='stPopoverBody'] [class*='_op_']")) return;
    setTimeout(() => doc.body.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true })), 300);
  }, true);
}
// zona del mapa: tres pestañas ocultas (map = mapa, table_chart = tabla de datos, help = guía de uso)
const pestana = (icono) => [...doc.querySelectorAll("[data-testid='stMain'] [role='tab']")].find(x => x.textContent.includes(icono));
const visible = (icono) => { const x = pestana(icono); return !!x && x.getAttribute("aria-selected") === "true"; };
const irA = (icono) => { const x = pestana(icono); if (x && x.getAttribute("aria-selected") !== "true") x.click(); };
if (!doc.__guia) {
  doc.__guia = true;
  // el icono de la guía alterna entre la guía y el mapa
  doc.addEventListener("click", (ev) => {
    if (!ev.target.closest("[class*='st-key-btn_guia']")) return;
    irA(visible("help") ? "map" : "help");
  }, true);
}
if (!doc.__tooltips) {
  doc.__tooltips = true;
  // las ayudas "?" salen a la derecha de la barra, centradas en el icono
  let icono = null;
  doc.addEventListener("mouseover", (ev) => {
    const i = ev.target.closest && ev.target.closest("[data-testid='stSidebar'] [data-testid='stTooltipIcon']");
    if (i) icono = i;
  }, true);
  const colocar = (contenido) => {
    const marco = contenido.parentElement, barra = doc.querySelector("[data-testid='stSidebar']");
    if (!icono || !marco || !barra || !icono.isConnected) return;
    const r = icono.getBoundingClientRect(), b = barra.getBoundingClientRect();
    const alto = contenido.offsetHeight, ancho = contenido.offsetWidth;
    const x = Math.min(b.right + 10, W.innerWidth - ancho - 8);
    const y = Math.max(8, Math.min(r.top + r.height / 2 - alto / 2, W.innerHeight - alto - 8));
    marco.style.setProperty("transform", "translate(" + x + "px," + y + "px)", "important");
  };
  new MutationObserver((cambios) => {
    for (const c of cambios) for (const n of c.addedNodes) {
      if (n.nodeType !== 1) continue;
      const contenido = n.matches("[data-testid='stTooltipContent']") ? n : n.querySelector("[data-testid='stTooltipContent']");
      if (contenido) { colocar(contenido); setTimeout(() => colocar(contenido), 60); }
    }
  }).observe(doc.body, { childList: true, subtree: true });
}
if (!doc.__altoTabla) {
  doc.__altoTabla = true;
  // la tabla llena la ventana hasta 28 px del borde inferior
  const ajustarTabla = () => {
    const c = doc.querySelector(".st-key-caja_tabla");
    if (!c || !c.offsetParent) return;
    const principal = doc.querySelector("[data-testid='stMain']");
    const arriba = c.getBoundingClientRect().top + (principal ? principal.scrollTop : 0);
    const alto = Math.max(260, Math.round(W.innerHeight - arriba - 28));
    if (doc.documentElement.style.getPropertyValue("--alto-tabla") !== alto + "px")
      doc.documentElement.style.setProperty("--alto-tabla", alto + "px");
  };
  W.addEventListener("resize", ajustarTabla);
  let pendiente = false;
  new MutationObserver(() => {
    if (pendiente) return;
    pendiente = true;
    requestAnimationFrame(() => { pendiente = false; ajustarTabla(); });
  }).observe(doc.body, { childList: true, subtree: true });
  setInterval(ajustarTabla, 800);
}
if (!doc.__pestanas_barra) {
  doc.__pestanas_barra = true;
  // al pasar a Diseño o Exportación, la zona principal vuelve al mapa
  doc.addEventListener("click", (ev) => {
    const pest = ev.target.closest("[data-testid='stSidebar'] [role='tab']");
    if (!pest) return;
    const todas = [...pest.parentElement.querySelectorAll("[role='tab']")];
    if (todas.indexOf(pest) > 0 && !visible("map")) irA("map");
    // al cambiar de bloque, las secciones que quedaron abiertas se contraen
    const indice = todas.indexOf(pest);
    if (indice !== (doc.__pestanaActiva ?? 0)) {
      doc.__pestanaActiva = indice;
      doc.querySelectorAll("[data-testid='stSidebar'] [data-testid='stExpander'] details[open]").forEach(d => {
        if (!d.parentElement.closest("details")) d.querySelector("summary").click();
      });
    }
  }, true);
}
if (!doc.__tabla) {
  doc.__tabla = true;
  // el botón de la tabla alterna entre tabla y mapa y cierra las secciones abiertas
  doc.addEventListener("click", (ev) => {
    if (!ev.target.closest("[class*='st-key-btn_tabla']")) return;
    doc.querySelectorAll("[data-testid='stSidebar'] [data-testid='stExpander'] details[open]").forEach(d => {
      if (!d.parentElement.closest("details")) d.querySelector("summary").click();
    });
    irA(visible("table_chart") ? "map" : "table_chart");
  }, true);
  // marca el botón cuando la tabla es lo que se ve
  const marcar = () => { doc.body.dataset.zona = visible("table_chart") ? "tabla" : "otra"; };
  new MutationObserver(marcar).observe(doc.body, { subtree: true, attributes: true, attributeFilter: ["aria-selected"] });
  marcar();
}
if (!doc.__panelTexto) {
  doc.__panelTexto = true;
  // al entrar en la caja de un texto, el panel pasa a sus controles
  const CAJAS = [["st-key-tit__titulo__", "tit"], ["st-key-tit__subtitulo__", "sub"], ["st-key-tit__fuente_nota__", "nota"],
                 ["st-key-ley__ley_tit_", "ley"], ["st-key-ley__texto_menor__", "ext"], ["st-key-ley__texto_mayor__", "extd"],
                 ["st-key-ley__extremos__", "ext"]];
  doc.addEventListener("focusin", (ev) => {
    const caja = ev.target.closest && ev.target.closest("[class*='st-key-']");
    if (!caja) return;
    const par = CAJAS.find(c => [...caja.classList].some(k => k.startsWith(c[0])));
    if (par) doc.documentElement.dataset.ctl = par[1];
  });
}
// la lista de tipografía arranca donde el campo Tamaño; se reinstala en cada ejecución
const alinear = () => {
  const v = [...doc.querySelectorAll("[class*='st-key-ctl_']")].find(c => c.offsetParent);
  if (!v) return;
  const fila = v.querySelector("[class*='st-key-pt_a_']"), tam = v.querySelector("[class*='st-key-pt_b_'] [data-testid='stNumberInput']"),
        esp = v.querySelector("[class*='st-key-pt_e_']");
  if (!fila || !tam || !esp || !fila.firstElementChild) return;
  const juntos = Math.abs(esp.getBoundingClientRect().top - tam.getBoundingClientRect().top) < 8;
  const hueco = parseFloat(getComputedStyle(fila).columnGap) || 0;
  const x = tam.getBoundingClientRect().left - fila.getBoundingClientRect().left - hueco;
  const etq = fila.firstElementChild;
  etq.style.flex = juntos && x > 0 ? "0 0 " + x.toFixed(1) + "px" : "";
  etq.style.paddingRight = juntos && x > 0 ? "0" : "";
};
// el cuadro de Descargar mide lo mismo que el botón (--ancho-descarga)
const anchoDescarga = () => {
  const boton = doc.querySelector("[data-testid='stPopover'] button[aria-expanded='true']");
  if (boton) doc.documentElement.style.setProperty("--ancho-descarga", boton.getBoundingClientRect().width + "px");
};
// el panel Aa se recoge al pulsar fuera (listas y selector de color cuentan como dentro)
if (!doc.__aaFuera) {
  doc.__aaFuera = true;
  doc.addEventListener("click", (ev) => {
    const hueco = doc.querySelector("[class*='st-key-hueco_aa_']:has(.aa-abierto)");
    if (!hueco || !hueco.isConnected) return;
    if (ev.target.closest("[class*='st-key-hueco_aa_'], [class*='st-key-fila_aa_'], [data-baseweb='popover'], [data-baseweb='menu'], [role='listbox']")) return;
    const clave = ([...hueco.classList].find(k => k.startsWith("st-key-hueco_aa_")) || "").replace("st-key-hueco_aa_", "");
    const boton = doc.querySelector(`.st-key-aa_${clave}_btn button`);
    if (boton) boton.click();
  });
}
// el tipo de línea solo se elige en la lista: no se escribe en el campo
if (!doc.__sinEscribir) {
  doc.__sinEscribir = true;
  doc.addEventListener("keydown", (ev) => {
    if (ev.key.length === 1 && ev.target.closest && ev.target.closest("[class*='st-key-linea_'] [data-testid='stSelectbox']")) ev.preventDefault();
  }, true);
}
if (doc.__relojPanel) clearInterval(doc.__relojPanel);
doc.__relojPanel = setInterval(() => {
  // si el texto activo ya no existe (leyenda apagada), el panel vuelve al título
  const c = doc.documentElement.dataset.ctl;
  if (c && !doc.querySelector(".st-key-ctl_" + c)) delete doc.documentElement.dataset.ctl;
  alinear();
  anchoDescarga();
}, 250);
if (!doc.__acordeon) {
  doc.__acordeon = true;
  doc.addEventListener("click", (ev) => {
    const sum = ev.target.closest("[data-testid='stSidebar'] [data-testid='stExpander'] summary");
    if (!sum) return;
    const actual = sum.closest("details");
    if (actual.parentElement.closest("details")) return;    // expansor dentro de una sección: no es del acordeón
    if (actual.open) return;               // se está cerrando
    if (visible("table_chart")) irA("map");
    doc.querySelectorAll("[data-testid='stSidebar'] [data-testid='stExpander'] details[open]").forEach(d => {
      if (d !== actual && !d.parentElement.closest("details")) d.querySelector("summary").click();
    });
    if (!visible("map")) irA("map");
    // lleva la sección abierta al inicio de la barra lateral para ver todas sus opciones
    setTimeout(() => {
      const caja = doc.querySelector("[data-testid='stSidebarContent']");
      if (!caja) return;
      const y = actual.getBoundingClientRect().top - caja.getBoundingClientRect().top + caja.scrollTop - 12;
      caja.scrollTo({ top: y, behavior: "smooth" });
    }, 350);
  }, true);
}
"""

# El código se instala en la propia página y no en el iframe: Streamlit recrea el iframe en algunas recargas y, al
# desmontarlo, el navegador deja de ejecutar sus eventos, temporizadores y promesas. Se instala una sola vez.
SCRIPT = ("<script>(function(){const doc=window.parent.document;if(doc.getElementById('script-pagina'))return;"
          "const s=doc.createElement('script');s.id='script-pagina';s.textContent=" +
          json.dumps("(function(){" + _CODIGO + "})();").replace("</", "<\\/") + ";doc.head.appendChild(s);})();</script>")
