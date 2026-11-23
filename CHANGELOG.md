---
tipo: changelog
estado: activo
---
# CHANGELOG — gui-comun

Formato: [Keep a Changelog 1.1.0](https://keepachangelog.com/es-ES/1.1.0/); versiones: [SemVer 2.0.0](https://semver.org/lang/es/).
La versión vive en `gui_comun/__init__.py` y en `pyproject.toml`. Las secciones llevan los nombres del formato
(Added · Changed · Deprecated · Removed · Fixed · Security) para que el validador las reconozca.

## [Unreleased]

## [4.4.1] - 2026-11-22

### Changed
- El submenú «Esquema de color de la ventana» llama a la variante de Kvantum por el nombre de su tema, sin más:
  «Lliphi Dark» (antes «Como Dolphin (Kvantum: LliphiDark)»), como Kate nombra los esquemas; `esquemas.nombre_tema`.

## [4.4.0] - 2026-11-22

### Added
- **El esquema de color de la ventana, como en Kate, y la variante «como Dolphin»** (4.4, pedido del autor,
  2026-11-22: las ventanas de la familia se veían más claras que Dolphin). La causa: con Kvantum, Dolphin toma la paleta
  del tema de Kvantum (`LliphiDark.kvconfig`: ventana `#1b1c1e`, vista `#101012`) y las ventanas QML la del esquema de
  KDE (`LliphiOscuro.colors`: `#363636`, `#242424`). `gui_comun.esquemas` ofrece, para toda la familia:
  «Predeterminado» (el esquema del sistema, como hasta ahora y por omisión), «Como Dolphin (Kvantum: <tema>)» (un
  `.colors` generado del esquema del sistema con los colores del tema de Kvantum activo, el claro o el oscuro) y todos los
  esquemas instalados. Se aplica como `KColorSchemeManager`: la propiedad `KDE_COLOR_SCHEME_PATH` de la aplicación (que
  `KColorScheme`, y con él Kirigami, lee en lugar de `kdeglobals`) y una paleta nueva, al arrancar y al momento.
  Ajuste `ventana/esquema` en `<organización>/gui-comun.conf`; `aplicacionStudio.esquemas`.
- Acciones `ventana.esquema.<id>` (las registra `Acciones.estandar` dentro de una `Aplicacion`) y, en
  `Acciones.definir_menus`, el submenú «Esquema de color de la ventana» y «Ventana translúcida» tras «Configurar…»
  (`app.ajustes`), como en el menú Preferencias de Kate; un studio que ya los puso no los ve repetidos.
- **Lo elegido como bloque lleno en la variante «como Dolphin»**: `EstiloSeleccion` (singleton) da el fondo de la fila
  elegida, la selección de Kvantum al 65 % sobre la fila (`#991e21` sobre `#101012`; Dolphin, medido: `#992024`), sin la
  marca lateral y con el texto en `highlightedTextColor`. Lo usan `FondoSeleccion`, `PanelNavegacion`, `TablaDatos`,
  `ArbolDatos`, `ListaDiagnosticos`, `ListaErrores` y `PaletaOrdenes`. Con el predeterminado, el tinte de la 4.2.
- **Los menús en el menú global de Plasma** (la barra de arriba, como Dolphin y Kate): con
  `Kirigami.Settings.hasPlatformMenuBar`, `VentanaBase` pone los menús del registro en un `Qt.labs.platform` `MenuBar`
  (`MenuGlobalAcciones`, nuevo) y oculta la barra de la ventana; Plasma los pinta con el estilo del escritorio (con
  Kvantum, translúcidos y desenfocados, como los de Kate). Los atajos los registra ese menú. Sin menú global, la barra de
  siempre. Ojo: en Qt 6.10 añadir a la barra un menú que ya tiene elementos tumba la aplicación; el menú se une vacío y
  se llena después.
- `EstiloSeleccion` no importa Kirigami: Qt resuelve los singletons del `qmldir` al cargar cualquier archivo de
  la carpeta, y quien carga un componente suelto sin Kirigami (el visor PDF en las pruebas de LaTeX Studio) fallaba.

### Changed
- `tests/test_qml.py` reconoce los tipos `singleton` del `qmldir`.

## [4.3.0] - 2026-11-22

### Added
- **Ventanas translúcidas y desenfocadas como Dolphin con Kvantum** (4.3, pedido del autor, 2026-11-22). Kvantum es un
  `QStyle` de Qt Widgets: vuelve translúcidas a Dolphin y Kate pero no toca una `QQuickWindow`, cuyo fondo pintaba QML
  opaco. Ahora `gui_comun.translucidez` lee la misma configuración que Kvantum (`widgetStyle` de `kdeglobals`, el tema
  de `kvantum.kvconfig` con la variante oscura de `kvantum-dark`, `translucent_windows`, `blurring`,
  `reduce_window_opacity` y `opaque=`) y, si la pide para la aplicación, `Aplicacion` pide un búfer con canal alfa antes
  de crear la ventana y, con la ventana cargada, el desenfoque a KWin con `KWindowEffects::enableBlurBehind` por ctypes
  (`libKF6WindowSystem.so.6`; no hay bindings de KF6 para Python), solo si `isEffectAvailable(BlurBehind)`; si el
  efecto no está o la llamada falla, la ventana queda opaca (nunca texto sobre el escritorio sin desenfocar).
  `VentanaBase` pinta su fondo con el color de ventana a la opacidad del tema (`1 - reduce_window_opacity/100`: 0,75
  con LliphiDark) y la barra de menú, las barras de herramientas de `header`/`footer`, `PanelNavegacion` y
  `PanelDetalles` dejan ver esa única capa (`FondoVentana`, nuevo); las zonas de lectura (`colorSet: View`: tablas,
  árbol, editor, visor PDF, consola) siguen opacas. Sin Kvantum, sin pantalla, con la aplicación en `opaque=` o con
  `GUI_COMUN_TRANSLUCIDA=0`, todo como antes. `aplicacionStudio.translucidez` (`activa`, `opacidad`, `posible`,
  `motivo`, `preferida`, `preferir(bool)`).
- Acción estándar `ventana.translucida` (Ver ▸ «Ventana translúcida», Ctrl+K): apaga o enciende la translucidez al
  momento; el ajuste es de toda la familia (`ventana/translucida` en `~/.config/<organización>/gui-comun.conf`).
  `Acciones.estandar` registra una acción más (once en lugar de diez): quien cuente las estándar, que sume una.

## [4.2.0] - 2026-11-21

### Changed
- **Lo que pidieron los studios al aplicar el acabado** (2026-11-21):
  - `VentanaBase`: cabe en un celular o media pantalla (`minimumWidth` de 640 a 20 unidades) y, por debajo de 34
    unidades (`menuPlegado`), la barra de menú se pliega en un solo «☰ Menú» con todos los menús dentro.
  - `TablaDatos`: columnas con `etiqueta` (el texto como píldora `EtiquetaNivel` de su nivel) y `elidir: "medio"`
    (rutas).
  - `VistaPdf`: cada hoja, papel con sombra sobre la mesa (sin la raya gris); `iconoVacio`.
  - Los vacíos de `ListaErrores`, `ListaDiagnosticos`, `VistaPdf`, `TerminalSalida`, `VistaTexto` y
    `VistaComparacion`, con un icono mediano en un panel bajo (el grande tapaba el texto).
  - `PestanasArchivos.nombreDe(modelo)`: el nombre que muestra cada pestaña, a gusto del studio.
  - `PaletaCategorica.porNombre(nombre)`: un color estable por nombre, el mismo en claro y en oscuro.
  - `BotonAccion` con `plano: false`: aire a los lados (el texto tocaba el borde).
  - `PaginaFormulario`: el `SpinBox` con un ancho mínimo.
- **El acabado de la familia** (pedido del autor, 2026-11-19: «que sea así de elegante» como la barra de la selección de
  Ñawinchay, en los trece programas; auditoría de cada uno en claro y oscuro). Sin quitar ni renombrar nada:
  - **Lo elegido, teñido y no en bloque lleno**: `PanelNavegacion`, `TablaDatos`, `ArbolDatos`, `PaletaOrdenes`,
    `ListaDiagnosticos` y `ListaErrores` marcan la fila elegida con un tinte del acento (`tintWithAlpha`), una marca de
    acento a la izquierda y el texto en su color (en negrita en la navegación); los colores semánticos se conservan
    sobre la selección. Con el acento rojo de Lliphi Oscuro, el bloque lleno hacía que todo lo elegido pareciera un
    error. La navegación tiene más aire, esquinas redondeadas y velo al pasar; `ArbolDatos` también responde al ratón.
  - **Pestañas como selector segmentado**: `PanelDetalles` y `PanelInferior` usan `SelectorSegmentado` en lugar del
    `TabBar` (misma API: `pestanaActual`, `mostrarSalida()`…).
  - **Una sola X, neutra**: `PanelInferior`, `BarraBuscarReemplazar`, `VistaPdf` y `PestanasArchivos` cierran con
    `BotonCierre` (los `window-close`, `dialog-close` y `tab-close` de Colloid y Papirus son círculos rojos);
    `DialogoError`, `DialogoConfirmacion` y `DialogoCambiosSinGuardar` sin la × de la cabecera (tienen sus botones).
  - `BotonAccion` marcable: tinte del acento y borde, con su propio icono (con Kvantum el marcado era un bloque azul
    saturado aun en un esquema de otro acento); `plano: false` le pone borde fuera de una barra.
  - `PaletaOrdenes`: superficie flotante (opaca, radio, borde y sombra), fondo atenuado y alto ceñido a los resultados.
  - `BarraEstado` en letra pequeña, cortada por la derecha; el contexto tenue y la pista en el color del texto.
  - `PanelInferior`: la salida resaltada con el tema claro u oscuro de KSyntaxHighlighting (en oscuro apenas se leía).
  - `GraficoXY`: el equilibrio, un punto neutro con anillo (con el acento parecía una serie); el resultado inválido,
    una `EtiquetaNivel` en la esquina con su motivo en la ayuda, no un sello gigante girado sobre los datos; la base,
    punteada también en la leyenda; repinta al hacerse visible; la ayuda del punto con sombra.
  - `PasosEscritura`: cada paso, una píldora con su insignia redonda (✓ hecho, el número del siguiente y los
    pendientes, ✕ si un conflicto lo frena), la elegida teñida con borde y que no se encoge, y la línea entre pasos del
    acento hasta el alcanzado (antes, botones de barra con flechas y rayas).
  - `ListaDiagnosticos`: nivel `correcto` (icono `checkmark`, color positivo); `data-success` parecía una casilla.
  - `VistaTexto` en Markdown se lee como documento con el aspecto del tema (títulos con aire y raya, tablas tenues
    con la cabecera tenue, código sobre fondo alterno, columna de lectura centrada): `gui_comun.markdown_html` (de
    Filesystem Studio) por `aplicacionStudio.markdownHtml`; fuera de una `Aplicacion`, el Markdown de Qt, que ahora
    escapa los «<nombre>» que no son etiquetas HTML (se tragaban el resto del documento).
  - `SelectorSegmentado` no se asigna `actual` al hacer clic ni con ← →: solo emite `elegida(clave)`, y quien lo usa
    fija su estado (asignarlo rompía el enlace de `actual` con ese estado; lo encontró Filesystem Studio).
  - `EtiquetaNivel` en oscuro, con el texto aclarado hacia el del tema (rojo sobre granate apenas se leía); el vacío
    «Sin diferencias» de `VistaComparacion`, sin el documento grande a todo color.
  - `VistaComparacion` parte por palabras; `EtiquetaNivel` con el icono del color del nivel; el vacío de
    `TerminalSalida`, un terminal (no un paisaje).
  - `entorno_con_esquema` copia `fontconfig` y fija `QT_QPA_PLATFORMTHEME=kde`: las capturas salen con la fuente del
    escritorio.

- `Mensajes`: ningún aviso en una franja de la ventana (pedido del autor, 2026-11-19, para toda la familia de los
  studios). Un aviso con botones también va a las notificaciones de KDE (`notificarConAcciones`); sin escritorio que lo
  muestre (pruebas, capturas sin pantalla, sin `notify-send`), un aviso sin botones va a la barra de estado como pista.
  Solo una decisión sin escritorio queda en línea, para no perderla.

### Added
- **Piezas del acabado** (nacidas de la barra de la selección de Ñawinchay): `BarraFlotante` (contenedor que flota
  sobre el contenido, con radio, borde y sombra del tema), `GrupoOpciones` (el «pozo» tenue que agrupa opciones),
  `OpcionColor` (opción en píldora con su punto de color, que es un dato: estado al pasar, rellena si es la elegida,
  borde doble con el foco, atajo en la ayuda), `SelectorSegmentado` (una entre pocas vistas, áreas o filtros, con
  ← →; reemplaza un `TabBar` de cabecera o una fila de botones sueltos), `BotonCierre` (la X neutra) y
  `BotonPrincipal` (la acción principal con el relleno del acento: con Kvantum, `highlighted` no pinta nada) y
  `FondoSeleccion` (el fondo de una fila de lista propia: tinte del acento y marca si es la elegida, velo al pasar; los
  programas tenían cuatro copias). En la galería: «Opciones y barra flotante».
- `gui_comun.markdown_html.html_de_markdown(texto, tema)` y `aplicacionStudio.markdownHtml(texto, tema)`.
- `PestanasArchivos`: las pestañas de los archivos abiertos de un `ControladorEditor`, con la × de cerrar (al pasar el
  ratón y siempre en la activa) y el clic central; emiten `cerrarPedido(ruta)` y el studio decide. Lo pidió LaTeX Studio
  («no hay para cerrar una ventana»); Quarto Studio tiene la misma copia sin ×.
- `DialogoCambiosSinGuardar`: «Guardar · Descartar · Cancelar» antes de cerrar algo modificado, con
  `pedir(nombres, alGuardar, alDescartar)`.

### Fixed
- `ControladorEditor.cerrar` avisa `actualCambiado` también cuando el archivo activo no cambia: al cerrar una pestaña
  anterior su índice baja, y sin el aviso la pila de editores seguía mostrando el índice viejo (fuera de rango).
- `EditorTexto.comentar()` descomentaba con `trimStart`/`trimEnd`, que el JavaScript de QML no tiene: quitar el
  comentario de una línea comentada (Ctrl+/ en LaTeX Studio y Quarto Studio) fallaba con un TypeError.

## [4.1.0] - 2026-11-18

Junta lo que esperaba sin versión desde el 2026-11-08 (avisos a las notificaciones de Plasma, la tabla y el árbol para
LaTeX Studio, la consola que no congela) y lo que propusieron los diez studios rediseñados el 2026-11-18
(`docs/modernizacion-visual-kde.md`, D2 y D3): ocho de sus nueve propuestas, en piezas que un studio elige. Nada se
quita ni se renombra; ningún studio está obligado a cambiar. Fuera queda la paleta por grupos recorrida con flechas
(Raphi): es la forma propia de su taller y nadie más la usa; la navegación con flechas se hace en Raphi.

| propuesta (studio) | en la base |
|---|---|
| un tipo «pista» de `Mensajes` hacia la barra de estado (Simuladores, Quarto; lo repetían Datafw, Simuladores y Huella) | `Mensajes.mostrar(texto, "pista")`, `pista`, `duracionPista`, `mostrarPista()`; `BarraEstado.mensajes`, `pista`, `textoDerecha` |
| un ayudante para la prueba en vivo aislada que detenga los portales huérfanos (Simuladores, Lliphi, Huella, Raphi, Muyu) | `gui_comun.galeria.vivo` |
| el nivel en el borde de la fila de `TablaDatos` (Huella) | `TablaDatos.nivelesBorde`, `anchoBorde` |
| acciones en las notificaciones (Git) | `Mensajes.notificarConAcciones()`, `Notificador.notificarConAcciones()`, señales `accionElegida` y `notificacionCerrada`; `notificaciones.orden(acciones=)` |
| «+n −m» en color en `VistaComparacion` (Git) | `VistaComparacion.cifrasEnColor` (verdadero por omisión) |
| un componente común de salida de terminal (Dotfiles) | `TerminalSalida` |
| `pasos.informe` con los nombres de los pasos (Filesystem) | `pasos.informe(pasos=)`, `pasos.TITULOS_INFORME` |
| `entorno_con_esquema` fija `widgetStyle` de Kvantum (Lliphi) | `esquema.kvantum_a_juego()`, `esquema.es_oscuro()` |

### Fixed
- `Aplicacion` fija un `organizationDomain` si nadie lo fijó (`<organización>.local`): el `Settings` de QtCore se negaba
  a abrir sin él («Failed to initialize QSettings instance») y `TablaDatos` no recordaba los anchos de columna. En Linux
  la ruta de los ajustes no cambia (sale del nombre de la organización y de la aplicación). Lo destapó Datafw Studio.

### Changed
- `VistaComparacion`: «+n» y «−m» de la cabecera en los colores de estado del tema (lo añadido y lo quitado, como
  Dolphin y Kompare); los trozos siguen tenues. `cifrasEnColor: false` los devuelve al gris de antes.
- `galeria.esquema.entorno_con_esquema`: si el usuario usa Kvantum, el kdeglobals temporal lleva `widgetStyle` =
  `kvantum-dark` con un esquema oscuro y `kvantum` con uno claro. Desde Lliphi 4.19 el tema de Kvantum trae sus dos
  variantes (`Lliphi`, `LliphiDark`) y ya no hay uno por esquema (`LliphiOscuro`): las capturas oscuras salían con
  campos y pestañas claros. Si existe un tema con el nombre del esquema, se sigue eligiendo (3.1).
- `ModeloConsola` (`consola.salida`, `consola.registro`): `textoCambiado` ya no sale en cada escritura. Sale al
  instante la primera vez y, mientras siga llegando texto, como mucho una vez cada 100 ms (o cuatro veces lo que tardó
  en pintarse el aviso anterior, hasta 2 s), con un último aviso al acabar. `texto` y `textoConHora` se calculan una
  vez por cambio. El `TextArea` del `PanelInferior` rehacía y resaltaba el texto entero en cada línea: 2 000 líneas
  seguidas tardaban 112 s con el panel cargado y ahora 0,1 s; 10 000 líneas llegadas de una en una (la salida de un
  proceso) pasan de minutos a 1,5 s. `escrita`, `lineas`, `ultimas` y el modelo de lista siguen al día en cada
  escritura; ningún studio cambia su código. Lo destapó Detectar hardlinks de Filesystem Studio sobre una carpeta
  con `node_modules` de pnpm (12 413 conjuntos, una línea por conjunto).
- `Mensajes`: un aviso sin acciones va a las notificaciones del escritorio (las de KDE Plasma, con el nombre y el
  icono del studio) en lugar de apilarse en la ventana; información y éxito son transitorios y cada uno reemplaza al
  anterior, un error queda en el historial de Plasma. Solo los avisos con acciones (una decisión) siguen en línea, y
  todos cuando no hay escritorio (offscreen, `GUI_COMUN_SIN_NOTIFICACIONES=1`). Ningún studio cambia su código.
- `EditorTexto`: la revisión ortográfica de KDE (Sonnet), que el estilo de KDE enciende sola en todo `TextArea`
  editable, queda apagada por omisión (`revisarOrtografia: false`): en código LaTeX subrayaba en rojo las órdenes y
  todo lo que no fuera del idioma predeterminado de Sonnet. El studio la enciende si el usuario lo pide.
- `VistaPdf`: las páginas de QtPdf se dibujan al doble de la resolución de pantalla y se reducen (`sobremuestreo: 2`,
  con tope de 4096 px): Pdfium a la resolución exacta empastaba el texto; así sale nítido, como Poppler.

### Fixed
- `TablaDatos`: un clic no elegía la fila: la `TableView` de Qt 6 solo movía la celda actual (y la pintaba con un
  marco en esa celda sola). Ahora el clic elige la fila entera con el color de selección del tema, como una lista de
  KDE; Ctrl+clic añade o quita, Mayús+clic y Mayús+↑/↓ eligen el tramo desde la última elegida, las flechas mueven la
  elegida; la fila bajo el ratón lleva el tinte de «pasar por encima»; el marco de la fila actual sin selección rodea
  la fila entera; el icono de una columna `semantica` toma el color del texto elegido. `pointerNavigationEnabled` pasa
  a `false` (el clic lo atiende `clicEnFila(fila, modificadores)`).
- `TablaDatos`: las columnas no se podían ensanchar ni estrechar desde la cabecera (el `HorizontalHeaderView`
  sincronizado no redimensiona; solo el cuerpo, donde nadie lo busca). Cada cabecera tiene ahora un asa en su borde
  derecho (cursor de separación, realce al pasar): arrastrar cambia el ancho sin ordenar y se recuerda con
  `claveAjustes`; doble clic lo devuelve al de la definición.
- `PanelNavegacion`: la barra de desplazamiento vertical tapaba los contadores; el contenido toma el ancho disponible
  del `ScrollView`, que ya descuenta la barra cuando se ve.
- `ControladorEditor`: un cambio hecho fuera se avisa (`cambioExterno`) cuando el archivo lleva 400 ms quieto y no
  vacío de pronto (hasta ~4 s de espera). Quien escribe truncando y luego escribiendo dejaba un instante el archivo en
  0 bytes; el editor lo leía entonces y la ventana recargaba la pestaña vacía (un Ctrl+S lo habría borrado).

### Added
- `Mensajes`: el tipo `"pista"` (`mostrar(texto, "pista")` o `mostrarPista(texto)`): lo efímero («elige primero un
  modelo») no va a las notificaciones ni en línea, sino a `pista`, que `BarraEstado` muestra en lugar de su contexto
  durante `duracionPista` (6 s) y luego borra. `BarraEstado` lee la `pista` de los `mensajes` de su ventana
  (`ApplicationWindow.window.mensajes`) o de los que se le den (`mensajes:`); `textoDerecha` es lo que se ve.
- `Mensajes.notificarConAcciones(texto, tipo, acciones)`: un aviso con botones en las notificaciones de Plasma
  («Informe guardado» → «Abrir»); el botón pulsado allí corre su `ejecutar`. Sin escritorio, en línea como `mostrar`.
  Debajo, `Notificador.notificarConAcciones(texto, tipo, [{clave, texto}])` → id, con `notify-send --action`, y las
  señales `accionElegida(id, clave)` y `notificacionCerrada(id)`; no es transitoria y dura 15 s (el error, hasta que
  se cierre).
- `TablaDatos.nivelesBorde`: los `nivel` que se pintan además en el borde izquierdo de la fila, con su color de estado
  y también con la fila elegida (Huella: `["negativo", "neutro"]`, alta y media); vacío por omisión, sin borde.
- `TerminalSalida`: la salida de una orden como una terminal (la orden arriba, el número de líneas, un botón con su
  `Accion`; cada línea en el color de su nivel, por `reglas` `{contiene, nivel}` o el `nivel` de la línea). Viene de la
  `TerminalSimulacion` de Dotfiles; el nombre no choca con ningún componente de un studio.
- `gui_comun.galeria.vivo`: la prueba del cambio de esquema en vivo, aislada. `correr_en_bus_propio(orden, env,
  carpeta)` (bajo `dbus-run-session`, con el entorno marcado) detiene al acabar los servicios que el bus activó y
  sobreviven (`xdg-desktop-portal-kde`, `ksecretd`…), por PID y solo los de esa marca (`huerfanos`,
  `detener_huerfanos(simular=)`); `aplicar_esquema_en_vivo(colors)` reescribe el kdeglobals temporal y emite
  `notifyChange` solo en el bus propio (se niega en el de la sesión o sobre la configuración real, que `config_real()`
  toma de la cuenta del usuario y no de `$HOME`: con una casa falsa, como la copia de Lliphi, su `.config` es la
  temporal y la guarda la confundía con la real).
- `pasos.informe(..., pasos=[...])`: los nombres de los pasos del studio (los de `PasosEscritura.pasos`) titulan las
  secciones del informe; sin ellos, los de siempre (`TITULOS_INFORME`).
- `galeria.esquema.kvantum_a_juego(colors, config)` y `es_oscuro(colors)`.
- `PanelNavegacion` en árbol: una fila puede llevar `nivel` (sangría), `ancestros` (los `nombre` de las de arriba) y
  `plegable` (su flecha); las hijas se ven con su rama desplegada, elegir una rama la despliega y una fila escondida
  que pasa a `actual` despliega sus ancestros (`abiertos`, `alternar(nombre)`, `fijarAbierta(nombre, abrir)`). Las
  secciones sin esos campos se ven como antes.
- `TablaDatos`: una columna con `lineas: n` parte el texto largo en hasta n líneas (y elide la última) y su fila crece
  lo justo; `cortarTras: "/"` prefiere partir tras esos caracteres (una ruta, por carpetas). Clic derecho en la
  cabecera: restablecer los anchos y mostrar u ocultar columnas (`restablecerAnchos()`, `fijarAncho(c, ancho)`).
- `gui_comun.notificaciones` (`Notificador`, expuesto a todo el QML como `notificador`): `notificar(texto, tipo)` por
  `notify-send` en un `QProcess` (PySide6 no pasa a D-Bus los tipos que pide `Notify`).
- `ControladorEditor.rutasAbiertas`: las rutas abiertas, para quien vigila cambios hechos fuera de la ventana.

## [4.0.0] - 2026-11-03

Retira la capa 1.x de Qt Widgets, congelada desde 2.0.0. Sube la mayor porque desaparecen módulos públicos; lo de
2.x–3.x no cambia y los diez studios arrancan igual.

**Quién la usaba** (`rg` del 2026-11-03 en todo `~/Documents` y `~/.dotfiles`, con `scripts-linux`, `datafw`,
`divulgacion`, `qillqa` y los módulos de la plataforma, sin las carpetas sensibles, que solo se miran por estructura):
ningún código. Las únicas apariciones son pruebas de los diez studios que **prohíben** importarla
(`"gui_comun.widgets" not in texto`), y los worktrees viejos `lliphi/.claude/worktrees/*` (ramas de otras sesiones de
antes de Lliphi Studio 2.0, que aún traen `lliphi_studio/`): no se tocan, y si alguno se volviera a usar con su
ventana de Widgets, fija `v3.2.0`. Las instalaciones con pip fijan `v3.0.0` (Dotfiles, Lliphi, Raphi): no cambian.

### Removed
- `gui_comun.widgets` (`marco`: `Marco`, `montar_studio`, `Comando`; `paleta`; `avisos`; `tarjetas`; `grafico_barras`;
  `console_dock`: `ConsoleDock`), `gui_comun.diseno` (`Disenador`, los tokens y la hoja QSS, `preparar_plataforma`),
  `gui_comun.theming` (`aplicar_tema`), `gui_comun.ui_loader` e `gui_comun.icons`.

### Changed
- Se quedan los auxiliares que los studios QML usan: `workers` (los envuelve `tareas`), `lanzador` + `acentos`,
  `rutas`, `ajustes`, `format`, `history_service`, y `Consola.log` (el nombre de 1.x, que sigue funcionando).

**Migración**: nada que hacer en un studio QML. Un programa de Qt Widgets que use `aplicar_tema`, `montar_studio`,
`Marco` o los widgets: fijar `gui-comun @ …@v3.2.0`, o pasar a `Aplicacion` + `VentanaBase` (la migración de 2.0.0).

## [3.2.0] - 2026-11-03

El visor completo: lo que LaTeX Studio ganó hoy en su visor (`latex-studio` 07d19b6, decisiones §1.11) pasa a
`VistaPdf`, para que Raphi y Quarto lo tengan sin copiarlo. Aditiva.

### Added
- **Con QtQuick.Pdf**, en `VistaPdf`: seleccionar texto arrastrando (Ctrl+C lo copia, Ctrl+A toma la página, Esc la
  suelta; clic derecho: copiar, seleccionar la página, buscar y la acción del punto del studio), **enlaces del PDF**
  (internos: a su página y punto; externos: `VisorPdf.abrirEnlace`, solo `http`, `https` y `mailto`; `file:`, órdenes
  o `javascript:` no se siguen) y **búsqueda en el PDF** (`buscarEnPdf()`, que el studio ata a su atajo: Ctrl+Alt+F en
  LaTeX; Intro y Mayús+Intro saltan; cada resultado resaltado en su página). Vive en `CapaQtPdf` y `BusquedaQtPdf`,
  cargados aparte como `DocumentoQtPdf`: sin el módulo, la vista sigue igual (con `pdftoppm`) y no ofrece nada de eso.
- `VistaPdf`: `textoSeleccionado`, `buscando`, `buscarEnPdf()`, `cerrarBusqueda()`, `resultado(paso)`,
  `copiarSeleccion()`, `aVentana(pagina, x, y)` (un punto de la página en la ventana), `textoPunto` y `puntoHabilitado`
  (la entrada del menú del clic derecho que emite `dobleClic`: «Ir al código de este punto» en LaTeX).
- La galería: el PDF de muestra lleva texto que buscar y un enlace interno y uno externo.

### Fixed
- `EditorTexto.aceptarSugerencia` dejaba el cursor detrás del `cierre` (aceptar «\frac» tras «\fra» daba
  `\frac{}{}|`); el cierre va tras el cursor, como dice su documentación: `\frac{|}{}` (lo vio el carril B al
  adoptar el editor en LaTeX). Prueba nueva con el cierre ausente y ya presente.
- La primera búsqueda saltaba al segundo resultado: `PdfSearchModel` empieza en 0 y no admite −1; el primer Intro va
  ahora al primero (también en LaTeX, que lo tiene igual: anotado para el carril B).

## [3.1.0] - 2026-11-03

Aditiva: lo que los studios repetían tras la reingeniería del 2026-11-02 sube a la base, cada pieza con su página en
la galería, sus pruebas y su entrada en `docs/componentes.md`. Nada cambia de nombre ni se retira; los diez studios
arrancan igual. Las copias de cada studio pueden quedarse hasta que su repo las cambie por la de la base.

**Nombres propios, a propósito.** Un tipo de `GuiComun` con el mismo nombre que un componente local de un studio *lo
tapa* en los archivos de su carpeta `componentes/` (la importación del módulo manda sobre la de la carpeta implícita):
con el nombre de la copia, la `EtiquetaEstado` de la base rompía Dotfiles y Lliphi (su API usa `texto`), y el editor
de LaTeX habría cambiado al abrir un archivo. Por eso las piezas promovidas llevan nombre nuevo; un studio las adopta
cambiando el nombre y borrando su copia:

| copia en el studio | en la base (3.1) |
|---|---|
| `EditorArchivo` (LaTeX, Quarto) · `controladores/editor.py` | `EditorTexto` · `gui_comun.editor.ControladorEditor` |
| `BarraBusqueda` (LaTeX, Quarto) | `BarraBuscarReemplazar` |
| `VisorPdf` (LaTeX) · `visor.py` · `controladores/visor.py` | `VistaPdf` · `gui_comun.visor_pdf.VisorPdf` (SyncTeX queda en el studio) |
| `ListaProblemas` (LaTeX) | `ListaErrores` (roles `ubicacion` en vez de `relativa`) |
| `VistaDiferencia` (Git, Dotfiles, Lliphi) · `diferencias.py` | `VistaComparacion` · `gui_comun.diferencias` |
| `PasosOperacion` (Filesystem, Lliphi) · `PasosPuerta` (Biblioteca) · `pasos.py` | `PasosEscritura` · `LineaPasos` · `gui_comun.pasos` |
| `GraficoCientifico` (Simuladores) · `servicios/paleta.py` · `ColoresCategoria` (Filesystem) | `GraficoXY` · `gui_comun.paleta` · `PaletaCategorica` |
| `EtiquetaEstado` (Dotfiles, Lliphi; `texto`) | `EtiquetaNivel` (`text`) |
| `controladores/portadas.py` (Biblioteca) | `gui_comun.miniaturas.ProveedorMiniaturas` |

### Added
- `VistaComparacion` + `gui_comun.diferencias` (de Git, que Dotfiles y Lliphi copiaron): la diferencia lado a lado con
  qué es cada lado y sus notas, botones por trozo pedidos por el studio (`accionesTrozo` → `trozoPedido`), **selección
  de líneas sueltas** (`seleccionable`, `filasElegidas`) y `parche_de_lineas` para prepararlas o quitarlas del índice;
  `comparar(antes, despues)` sin git.
- `EditorTexto` + `BarraBuscarReemplazar` + `gui_comun.editor.ControladorEditor` (de LaTeX, que Quarto copió): las
  definiciones de resaltado y el comentario de línea por lenguaje como parámetros; autocompletado y Ctrl+clic como
  ganchos (`completar`, `disparaCompletado`, `ctrlClic`).
- `VistaPdf` + `gui_comun.visor_pdf.VisorPdf` (de LaTeX): QtQuick.Pdf si está instalado, `pdftoppm` de respaldo
  (`GUI_COMUN_VISOR=pdftoppm`); `dobleClic(pagina, x, y)` y `marcarRecuadro` para lo propio de cada disciplina (SyncTeX).
- `ListaErrores` (de LaTeX): errores y avisos presentables en lista, con causa, acción y detalle desplegable.
- `PasosEscritura`, `LineaPasos` + `gui_comun.pasos` (de Filesystem, Lliphi y Biblioteca): los seis pasos de una
  escritura, el plan con sus conflictos que bloquean, la verificación y el informe en Markdown; la línea de pasos con
  estado.
- `GraficoXY` + `PaletaCategorica` + `gui_comun.paleta` (de Simuladores y Filesystem): el gráfico con el x de
  cada línea, la base punteada y la marca de lo no verificado; colores con significado llevados al tema.
- `EtiquetaNivel` (de Dotfiles y Lliphi); `gui_comun.miniaturas.ProveedorMiniaturas` (de las portadas de Biblioteca).
- `ArbolDatos.ordenable` y `ModeloArbol.ordenar(columna, descendente)`: el orden por cabecera que pidieron Filesystem,
  Dotfiles y Huella (grupos primero, valores crudos por columna, los hijos perezosos se ordenan al cargarse).
- `ModeloLista.todas()` es un `Slot` (Git tuvo que exponer otra propiedad para leer la lista desde QML).
- `gui_comun.qt` exporta `QImage`, `QImageReader`, `QQuickImageProvider` y `QQmlImageProviderBase`.
- La galería: seis páginas nuevas (VistaComparacion, EditorTexto, VistaPdf, ListaErrores, pasos, GraficoXY)
  y el árbol ordenable, sobre muestras en una carpeta temporal que se borra al salir.

### Changed
- `VistaTexto` resalta con el tema de KSyntaxHighlighting claro u oscuro según el fondo (`ResaltadoEditor`).
- `Aplicacion` fija `AA_ShareOpenGLContexts` antes de crear la aplicación (lo exige QtWebEngine de QML: la vista
  previa de Quarto).
- `galeria.esquema.entorno_con_esquema` pone también el tema de Kvantum del mismo nombre (con `QApplication` los
  controles los pinta Kvantum; una captura oscura salía con campos claros). Cinco `capturar.py` lo hacían a mano.

### Fixed
- **Un diálogo de archivo o carpeta con el título vacío salía con el de Qt, en inglés («Select Folder»)**, visto en la
  sesión real con Quarto y Biblioteca, cuyo `CampoRuta` recibe la etiqueta de una entrada que aún no se conoce:
  `ElegirCarpeta`, `ElegirArchivos` y `GuardarComo` ponen el suyo por omisión, y `CampoRuta` tiene `tituloVisible`.
- El editor de LaTeX Studio se marcaba como modificado nada más abrir un archivo: en la base, «modificado» compara con
  el texto leído. La lista de problemas se leía mal en la fila elegida (rojo sobre el color de selección).

## [3.0.0] - 2026-11-02

La base de la reingeniería de los diez studios (encargo del autor del 2026-11-02): cada studio deja de ser una
variación de Dolphin y tiene la arquitectura de su disciplina; la identidad común es Lliphi y el comportamiento, no la
distribución. Sube la mayor porque cambian la clase de la aplicación, el árbol de `VentanaStudio` y el nivel con que
termina una tarea cancelada; la API de 2.x se conserva y la capa 1.x (`widgets/`, `diseno`, `theming`, `marco`,
`ui_loader`, `icons`) sigue congelada, sin retirar (lo hará 4.0).

**Migración desde 2.x**

1. Nada obligatorio para seguir funcionando: los diez studios arrancan con 3.0 sin cambiar una línea (`--smoke`
   de cada uno, 2026-11-02). Si un studio comprobaba `isinstance(app, QGuiApplication)` sigue valiendo (`QApplication`
   la hereda); si una prueba suya prohibía importar `QtWidgets`, `gui_comun.qt` ya lo importa para la aplicación.
2. Para dejar la distribución de Dolphin: `VentanaBase { acciones: studio.acciones; …contenido propio… }` en vez de
   `VentanaStudio`, y `acciones.estandar("Mi Studio", paneles=False)`.
3. Diálogos: `FileDialog`/`FolderDialog` sueltos → `ElegirArchivos`/`ElegirCarpeta`/`GuardarComo` (rutas locales, sin
   `replace("file://", "")`). «Abrir carpeta» y «Mostrar en el explorador» → `escritorio.abrirCarpeta` /
   `escritorio.mostrarEnDolphin`; abrir un archivo → `escritorio.abrirConAplicacion` (no `Qt.openUrlExternally` con
   rutas sin codificar).
4. Operaciones de riesgo: declarar `operacion="publicacion"` (o instalación, eliminación) con `consecuencias=` y
   quitar la confirmación hecha a mano en QML; `verificar=` en las tareas que escriben.
5. Errores: `tareas` ya los presenta al fallar; donde un lote resume sus fallos, `error=False`. En `except`,
   `aplicacion.errores.desde_excepcion(exc, "No se pudo …", recurso=ruta)`.
6. Atajos: los de la disciplina con `registrar(..., atajo)` y `fijar_atajo`; una prueba del studio con
   `assert acciones.conflictos() == {}`.
7. Si un studio escuchaba `terminada("error", …)` para saber que el usuario canceló un proceso, ahora llega
   `terminada("warn", nombre, "cancelada")`.

### Added

- `VentanaBase` (QML): la ventana sin plantilla. Aporta solo lo común —barra de menú desde `Acciones`, paleta de
  órdenes (Ctrl+K), mensajes, el diálogo de errores presentables, la confirmación de las operaciones de riesgo,
  «Acerca de», el diálogo de ajustes, pantalla completa y la geometría recordada— y deja el contenido libre (lo que se
  declara dentro, con `anchors.fill: parent`); `header` y `footer` quedan libres. API: `confirmar(peticion, alAceptar)`,
  `error(descripcion, causa, recurso, accion, detalle)`, `notificar(texto, tipo)`, `paleta`, `mensajes`,
  `confirmacion`, `dialogoError`, `conMenu`, `notificarTareas`.
- `gui_comun.escritorio.Escritorio` (expuesto como `escritorio` y `aplicacionStudio.escritorio`): tres operaciones que no
  se confunden — `abrirConAplicacion(ruta)` (`QDesktopServices.openUrl`: la aplicación asociada; también direcciones
  web), `mostrarEnDolphin(ruta)` (`dolphin --select`; sin Dolphin, la carpeta con `xdg-open`) y `abrirCarpeta(ruta)`
  (`xdg-open`) — más `rutaDeUrl`, `urlDeRuta`, `existe` y `hayDolphin`. Si la ruta no existe o nada arranca, devuelve
  `false` y presenta el error. El lanzador, la apertura de URL y la búsqueda de programas se inyectan (pruebas).
- `ElegirArchivos`, `ElegirCarpeta`, `GuardarComo` (QML, sobre `QtQuick.Dialogs`): el diálogo de archivos del escritorio
  (el de KDE) con filtros (`["PDF (*.pdf)"]` o `[{nombre, patrones}]`), carpeta inicial, selección múltiple, nombre
  sugerido y sufijo; hablan en rutas locales (`elegidos(rutas)`, `elegido(ruta)`, `elegida(ruta)`, `cancelado()`).
- Errores presentables: `gui_comun.errores` (`Errores` con su cola, `presentar`, `presentarTexto`, `presentarMapa`,
  `desde_excepcion`, `desde_proceso`; `explicar(excepcion)` y `explicar_codigo(codigo, salida)` dan la causa probable y
  la acción para los errores frecuentes: archivo inexistente, permisos, disco lleno, sin red, clave SSH rechazada, base
  de datos bloqueada, orden no encontrada…), `Aplicacion.error(...)`, y en QML `TarjetaError` (descripción, causa,
  recurso con «Mostrar en Dolphin» y copiar, acción, detalle técnico desplegable, «Copiar todo») y `DialogoError` (la
  cola, uno detrás de otro; «Siguiente», «Descartar todos»).
- Estados de operación en `Acciones`: `registrar(..., operacion=, consecuencias=, confirmar=)` con
  `OPERACIONES` = lectura · simulación · preparación · escritura · instalación · publicación · eliminación. Instalación,
  publicación y eliminación **siempre** piden confirmación y `registrar` exige sus consecuencias redactadas (texto o
  función que las calcula al pedirlas); otra la pide con `confirmar=True`. Disparar una acción así emite
  `confirmacionPedida(peticion)` y no la ejecuta; `DialogoConfirmacion` (que `VentanaBase` ya trae) nombra la operación
  y sus consecuencias, con el foco en Cancelar y el botón que dice qué hace, y llama a `Acciones.confirmar(nombre)`.
  `Accion.operacion`, `operacionTexto`, `requiereConfirmacion`, `consecuencias`, `confirmar()`; `Acciones.peticion(n)`.
- Atajos por disciplina: `Acciones.estandar(nombre, paneles=False, atajos={...})` (sin los conmutadores de paneles de
  `VentanaStudio`; atajos de las estándar cambiados), `fijar_atajo(nombre, atajo)` (y `Accion.fijar_atajo`; `atajo` y
  `atajoTexto` avisan al cambiar) y `conflictos()` (los atajos repetidos, que no disparan ninguna acción). La base no
  impone ningún atajo de disciplina (ni F5).
- `Tareas`: `operacion=` (y las propiedades `operacion`, `operacionTexto`; la barra de estado la nombra),
  `verificar=` (una comprobación tras el éxito, notificada aparte con `verificada(nombre, ok, detalle)`), `error=`
  (`False` no presenta; un dict redacta el error) y la señal `resultado(mapa)`. Cuando una tarea falla presenta un
  error (descripción, causa por su excepción o por su código y su salida, recurso, acción, las últimas 60 líneas como
  detalle) en el `errores` de la aplicación; la consola conserva la salida entera. `Tareas(consola, errores=)`.
- `FunctionWorker.excepcion`: la excepción que dio `failed` (para explicarla).
- `rutas.js` (en el módulo): `deUrl`, `aUrl`, `carpetaDe`, `nombreDe`, `filtros`, `lista`.
- Galería: páginas «VentanaBase», «Escritorio y diálogos», «Errores presentables» y «Operaciones», el menú
  Operaciones con una acción de cada estado de riesgo (trabajo de muestra que no toca nada) y `--ventana-libre`.
- `docs/integracion-kde.md`: por qué `QApplication`, las tres operaciones, los diálogos y lo comprobado en Wayland.

### Changed

- **`Aplicacion` crea una `QApplication`** (antes `QGuiApplication`): el tema de plataforma de KDE solo da su diálogo de
  archivos (el de Dolphin) y el estilo `org.kde.desktop` solo pinta con el `QStyle` del sistema cuando la aplicación es
  una `QApplication`; con `QGuiApplication`, `FileDialog` caía a su versión en QML, el «selector extraño». Comprobado en
  Plasma 6.6 Wayland. De `QtWidgets` solo se usa la clase de la aplicación; la interfaz sigue siendo QML. Requiere
  `python3-pyside6.qtwidgets` (o `python3-pyqt6`). Crea además `errores` y `escritorio` y los expone.
- **`VentanaStudio` se construye sobre `VentanaBase`** con la misma API (ranuras, `resumen`, `contexto`, paneles,
  `herramientasExtra`, `mensajes`, `paleta`); la barra de menú, la paleta, «Acerca de», los ajustes y la geometría los
  pone la base. `mensajes` pasa de `alias` a propiedad (sigue siendo el `Mensajes` sobre el centro).
- **Cancelar un proceso termina en `("warn", "cancelada")`** (antes `("error", "código de salida -15")`), igual que
  cancelar una función; una cancelación no presenta error.
- `CampoRuta` abre `ElegirCarpeta`, `ElegirArchivos` o (con `guardar: true`) `GuardarComo`; añade `carpetaInicial`,
  `guardar` y `poner(ruta)`.
- La paleta de órdenes recibe `operacion` en cada entrada (el estado en palabras).
- `BarraEstado` antepone el estado de la tarea («Escritura: …») cuando la tarea lo declara.

### Fixed

- `CampoRuta` devolvía las rutas con espacios codificadas («00%20metodo») y no aceptaba rutas con «#»: ahora las rutas
  van y vuelven de URL con `rutas.js`.

## [2.7.0] - 2026-11-02

Lo que la fase 5 (Raphi Studio, el octavo tras el piloto) pidió al marco; se añade sin quitar.

### Added

- `PaginaFormulario` (QML): un formulario generado desde una lista de campos (la ficha de una herramienta) sobre
  `Kirigami.FormLayout`, con un control por tipo (texto, multilínea, entero, decimal, opción, casilla, clave, color,
  ruta, carpeta), la ayuda debajo y el asterisco de lo obligatorio; `valores` (lo escrito, sin los vacíos),
  `valor(clave)`, `fijar`, `poner`, `restablecer` y la señal `cambiado(clave, valor)`. Lo que Raphi Studio hacía a mano
  con QtWidgets. Página en la galería (`--pagina formulario_ficha`) y pruebas.

## [2.6.0] - 2026-11-02

Lo que la fase 5 (Simuladores Studio, el séptimo tras el piloto) pidió al marco; se añade sin quitar.

### Added

- `Grafico` (QML): un gráfico de líneas o de barras sobre `org.kde.quickcharts` con las series sobre una rejilla común
  de x, las etiquetas de los ejes, la rejilla, la leyenda, los puntos marcados, el equilibrio, las marcas verticales u
  horizontales y una anotación; los colores de las series salen de la paleta de QuickCharts sobre el acento de
  `Kirigami.Theme`, nunca de una lista propia. Si el módulo falta, muestra la imagen alternativa (`imagen`, un PNG) o
  el mensaje de vacío. El interior que importa QuickCharts (`GraficoQuickCharts.qml`) se carga con un `Loader`, así
  `Grafico` existe aunque el módulo no esté. Página en la galería (`--pagina grafico`) y prueba.

## [2.5.0] - 2026-11-02

Lo que la fase 5 (Quarto Studio, el sexto tras el piloto) pidió al marco; se añade sin quitar.

### Added

- `Tareas.proceso(…, entrada=, entorno=)` y `ProcessWorker(entrada=, entorno=)`: `entrada` es el texto que se
  escribe en la entrada estándar del proceso y se cierra (las respuestas a las confirmaciones de un guion que la
  ventana ya confirmó con el usuario: el respaldo y «eliminar rotos» de Quarto Studio); sin ella la entrada está
  cerrada (`DEVNULL`), así un guion que pregunta no se cuelga. `entorno` añade variables al entorno del proceso.
- `Tareas` limpia las secuencias ANSI (colores y controles de terminal) de la salida de un proceso antes de pasarla a la
  consola y a `linea`: los guiones de Bash que colorean su salida (el gestor de blogs de Quarto Studio) se leen limpios.

## [2.4.0] - 2026-11-02

Lo que la fase 5 (Biblioteca Studio, el quinto tras el piloto) pidió al marco; se añade sin quitar.

### Fixed

- `PanelDetalles`: los botones de las pestañas ya no se recrean cuando cambia un contador o la visibilidad de una pestaña
  (el modelo del `Repeater` es el número de pestañas y cada botón lee la suya): el `TabBar` de `org.kde.desktop` leía la
  altura del botón actual mientras se destruía y fallaba con «Cannot read property 'height' of null». Si la pestaña actual
  pasa a oculta, el panel salta a la primera visible. Biblioteca Studio cambia la lista de pestañas por vista (el libro:
  Resumen y Fichas; una etapa: Elemento, Operación, Plan y Registro).

## [2.3.0] - 2026-11-02

Lo que la fase 5 (LaTeX Studio, el cuarto tras el piloto) pidió al marco; se añade sin quitar.

### Added

- `ListaDiagnosticos` (QML): la lista de errores y avisos de una herramienta con nivel (icono y color semántico:
  error, aviso, información, tipografía), mensaje en varias líneas, archivo y línea; `activada(fila)` con Intro o
  doble clic («ir a»), `filaActualCambiada`, `menuContextual`, `mensajeVacio`, `seleccionarFila`. Para la pestaña
  Problemas de un panel de detalles, donde una tabla no deja leer el mensaje entero. La galería la muestra en su página.
- `Tareas.proceso(…, progreso_de=)`: una función que recibe cada línea de la salida del proceso y devuelve
  `(porcentaje, elemento)` o `None`; la barra de estado muestra así el progreso de un proceso que anuncia sus pasos
  («Pasada 2/3 con lualatex…») sin que el proceso sepa nada de la ventana.
- `gui_comun.qt` exporta también `QFileSystemWatcher` («Recompilar al guardar» de LaTeX Studio).

## [2.2.0] - 2026-11-02

Lo que la fase 5 (Huella Studio, el tercero tras el piloto) pidió al marco; se añade sin quitar.

### Added

- `VistaTexto` (QML): la vista de texto de solo lectura con mensaje de vacío, en Markdown (los enlaces abren fuera) o
  monoespaciada con resaltado de KSyntaxHighlighting (`definicion`); `ajustarLineas`, `nombreAccesible`, `area`. La
  repetían Filesystem (el árbol de `tree`), Git (la diferencia) y Dotfiles (el diff y la Guía); Huella la usa para la
  lectura de cada auditoría y el manual. La galería la muestra en su página.

### Fixed

- `workers.ProcessWorker` arranca el proceso en su propia sesión y `cancel()` termina el grupo entero (`SIGTERM` al
  grupo): cancelar un `main.sh` que lanza un guion que lanza una herramienta ya no deja vivos a los nietos.
  `Tareas.proceso` no cambia de API.

## [2.1.0] - 2026-11-02

Lo que la fase 5 (Filesystem Studio, el primero tras el piloto) pidió al marco; se añade sin quitar.

### Added

- `ArbolDatos` (QML): la vista en árbol hermana de `TablaDatos` sobre `TreeView` de Qt Quick, con la misma
  descripción de columnas y los mismos roles (`display`, `nivel`, `icono`, `habilitado`), flecha de expandir, ← → por
  teclado, selección por filas, menú contextual, `activada(indice)`, `raiz` para acotar la vista a un índice y
  `expandirAlCargar`.
- `CampoRuta` (QML): campo de ruta con botón de elegir (`FolderDialog` o `FileDialog`) y la señal `aceptada`.
- `modelos.ModeloTabla` (tabla desde filas de diccionario con columnas (título, clave), roles semánticos y valor
  crudo para ordenar) y `modelos.ModeloArbol` (árbol desde nodos de diccionario; `hijos` como lista o como función
  que se consulta al expandir).
- `TablaDatos.claveAjustes`: los anchos de columna que el usuario arrastra se recuerdan en QSettings (el pendiente
  de `docs/componentes.md` §3).
- La galería muestra `ArbolDatos` (página propia) y `CampoRuta` (en Formularios); pruebas de los modelos y de la
  carga de los dos componentes.
- `gui_comun.qt` exporta también `QDir`, `QFileInfo` y `QMimeDatabase` (el explorador de Filesystem Studio).

### Fixed

- `Accion.textoPlano` avisa al cambiar el texto (era constante): un botón de la barra cuyo texto cambia con el
  contexto («Ejecutar» según la herramienta) se actualiza.
- `MenuAcciones`: el atajo se dibujaba encima del texto. El `MenuItem` de `org.kde.desktop` (KF 6.24, Qt 6.10) no suma
  el ancho del atajo ni en un menú estático; el elemento pinta ahora su contenido (icono, texto con mnemónico, atajo
  corto en español: «Ctrl+Mayús+N», no «Control+Mayúsculas+N») con el ancho medido, y el menú fija su ancho al abrirse.
- «Pantalla completa» pasa a Ctrl+Mayús+F (el de KDE y Dolphin): con `StandardKey.FullScreen` (F11) chocaba con el panel
  de detalles y ninguno de los dos funcionaba.
- `VentanaStudio`: el «Acerca de» crecía hasta el largo de la descripción; ahora tiene ancho fijo, el texto se ajusta y
  lleva el icono del studio.

## [2.0.1] - 2026-11-01

Lo que el piloto (Git Studio, fase 3) pidió al marco; sin cambios de API.

### Added

- `Tareas.funcion(..., silenciosa=True)`: una consulta breve (los detalles del elemento seleccionado) que no es «la
  tarea en curso»: no aparece en la barra de estado, no abre el panel inferior ni anota en el registro.

### Fixed

- `lanzador` ya no importa `diseno` (que arrastra QtWidgets y QtSvg, ausentes en el Python del sistema): los acentos
  viven en `gui_comun/acentos.py` (`diseno.ACENTOS` sigue existiendo).
- `BarraEstado`: la barra de progreso existe solo mientras hay tarea (el estilo Breeze avisaba al destruirla).
- `galeria.esquema.entorno_con_esquema` crea la carpeta temporal que se le pasa.

## [2.0.0] - 2026-11-01

La familia pasa de Qt Widgets a Qt Quick + Kirigami (`docs/arquitectura-qml-kirigami.md`). Se añade sin quitar:
un studio de 1.x no nota el cambio; uno migrado no importa nada de `widgets`.

### Added

- Módulo QML `GuiComun` (`gui_comun/qml/GuiComun/`, con `qmldir`) sobre Kirigami 6.24, Kirigami Addons 1.11 y QQC2
  `org.kde.desktop`: `VentanaStudio` (menú generado desde las acciones, barra corta con conmutadores de paneles,
  `SplitView` con ranuras navegación · centro · detalles · inferior, barra de estado, paleta Ctrl+Alt+I y Ctrl+K,
  «Acerca de», geometría y paneles en QSettings, detalles como hoja deslizante en ventanas estrechas),
  `PanelNavegacion`, `TablaDatos`, `PanelDetalles`, `PanelInferior` (con `org.kde.syntaxhighlighting`),
  `BarraEstado`, `Mensajes`, `PaletaOrdenes`, `DialogoAjustes`, `MenuAcciones`, `BotonAccion`. Cero colores, fuentes,
  radios o sombras propios.
- `gui_comun/nucleo.py` (`Aplicacion`), `gui_comun/acciones.py` (`Acciones`, `Accion`, `StandardKey`),
  `gui_comun/tareas.py` (`Tareas`), `gui_comun/consola.py` (`Consola`, `ModeloConsola`), `gui_comun/modelos.py`
  (`ModeloLista`, `ModeloFiltrado`), `gui_comun/i18n.py` (las `i18n*` de KI18n para el QML de Addons, con gettext) y
  `gui_comun/qt.py` (adaptador PySide6/PyQt6 del Qt del sistema; sin `qtpy`).
- La galería (`python3 -m gui_comun.galeria`), con `--captura` y `--esquema <archivo.colors>` (kdeglobals temporal
  por `XDG_CONFIG_HOME`, sin tocar el escritorio); `docs/componentes.md`; pruebas en `tests/` (`tests/run.sh`).

### Changed

- `pyproject.toml`: el binding ya no es dependencia obligatoria (lo pone el sistema; `pip install gui-comun[pyside6]`
  para quien lo quiera de pip); los `.qml` van como datos del paquete; `gui_comun.galeria` es paquete.
- `workers/`, `ajustes.py` e `history_service.py` importan el binding por `gui_comun.qt` (PySide6 sigue primero; con
  PyQt6 del sistema también corren). API intacta.
- `widgets/`, `diseno.py`, `theming.py` y `marco` quedan **congelados** (solo correcciones) hasta que el último
  studio migre; 3.0.0 los retirará.

### Fixed

- `README.md` citaba `widgets/*.py` sin el prefijo `gui_comun/`; `pyproject.toml` sin identidad en la línea 1; este
  archivo sin `## [Unreleased]` (hallazgos del validador heredados del nacimiento del repo).

**Migración (1.x → 2.x), studio por studio**

| 1.x (Widgets) | 2.x (QML) |
|---|---|
| `aplicar_tema(app, tema, acento=)` · `Disenador` · QSS | nada: `Kirigami.Theme`; el acento, solo en el icono del lanzador |
| `montar_studio(ventana, nombre=, logo_svg=, …)` · `Marco` | `Aplicacion(...)` + `VentanaStudio { acciones; navegacion; centro; detalles; inferior }` |
| `Comando` · `Paleta` (Ctrl+K) | `Acciones.registrar(...)` + `PaletaOrdenes` (la trae la ventana; Ctrl+Alt+I y Ctrl+K) |
| `Avisos` | `ventana.mensajes.mostrar(texto, tipo)` (`Kirigami.InlineMessage`) y la barra de estado para lo que no exige atención |
| `ConsoleDock` (`log`, `attach_*_worker`) | `Consola` (`escribir`, `registrar`, `log`) + `Tareas.funcion/proceso` + `PanelInferior` |
| `Tarjeta` · `Cifra` · `Mosaico` · `ListaConVacio` | no hay portada: resumen en `BarraEstado`, contadores en `PanelNavegacion`, `Kirigami.PlaceholderMessage` para lo vacío |
| `variante(boton, "primario")` | el botón `highlighted` del estilo / la acción en la barra |
| diálogo de preferencias `.ui` | `DialogoAjustes { modulos: [...] }` con `FormCard` |
| `preparar_plataforma()` | desaparece: Wayland nativo con el Qt del sistema |
| `python3` (Anaconda) | `/usr/bin/python3` en `main.py`, `install.sh`, `suite.yml` y el `.desktop` |

## [1.4.0] - 2026-11-01

### Added

- Acento `carmesi` (Lliphi Studio; el rojo OKLCH 25° de Lliphi: `#c53133` en claro, `#ef6661` en oscuro) y los iconos de
  trazo `paleta`, `capas`, `cursor`, `pantalla`, `ventana`, `cohete` y `ojo`.

## [1.3.0] - 2026-11-01

### Added

- Acento `indigo` (Dotfiles Studio) y los iconos de trazo `paquete`, `enlace` y `subir`.

## [1.2.0] - 2026-11-01

### Added

- Acento `grafito` (Huella Studio) y los iconos de trazo `huella`, `usuario`, `correo`, `codigo` y `globo`.

## [1.1.0] - 2026-10-31

### Added

- Acento `sepia` (Biblioteca Studio) y los iconos de trazo `libro`, `sincronizar`, `candado`, `bandeja` y `verificar`.
- `lanzador.entrada(..., esquema=)` e `instalar(..., esquema=)`: el acceso directo declara `x-scheme-handler/<esquema>`,
  recibe el enlace por `%u` y queda como aplicación por omisión de ese esquema (`xdg-mime default`).

## [1.0.0] - 2026-10-31

### Added

- Paquete propio (`pip install gui-comun`), separado de `core/py-common/gui_comun` con su historia.
- `lanzador.py`: el acceso directo de cada studio en el menú de aplicaciones.
- Acento `lima` (Simuladores Studio).

### Changed

- `rutas.py` busca `core/env.py` subiendo carpetas (desde el paquete o la carpeta actual) y, sin él, `docs_root()`
  usa `DOCS_ROOT` o `~/Documents`.
