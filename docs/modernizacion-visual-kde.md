---
tipo: doc
estado: borrador
forma: explicacion
titulo: "Modernización visual de la familia de studios: auditoría, inventario, sistema de diseño KDE y plan por etapas"
creado: 2026-11-01
---
# Modernización visual de los studios: auditoría y propuesta

Fase 1 del encargo del autor (2026-11-01): **revisar y proponer, no implementar**. Este documento recoge la auditoría de
la arquitectura visual de los diez studios y de `gui-comun`, el inventario de lo compartido y lo divergente, el sistema
de diseño común que se propone y el plan de migración. No se ha cambiado una línea de código; el autor decide (§8) y
recién entonces empieza la fase 2. Las rutas son relativas a `~/Documents/` salvo `~/.dotfiles`; la evidencia va como
`archivo:línea`, tal como estaba el 2026-11-01 (`gui-comun` 1.4.0, commit `c9ec7fe`).

> Nota (2026-11-01, misma tarde): el autor replanteó el encargo hacia **QML + Qt Quick + Kirigami** sin Qt Widgets
> como tecnología principal. Las secciones 1–4 (entorno, auditoría de `gui-comun`, auditoría por studio e inventario)
> siguen vigentes como **diagnóstico de la arquitectura actual**; las secciones 5–8 (sistema de diseño sobre Qt
> Widgets, plan y decisiones) quedan superadas por `arquitectura-qml-kirigami.md`.

## 0. Resumen para decidir

1. **El aspecto de aplicación web no lo impone el entorno: lo fabrica `gui-comun`.** El Qt con que corren los studios ya
   recibe de KDE la paleta de Lliphi, la fuente Inter 10, la fuente fija JetBrainsMono Nerd Font y el tema de iconos
   Colloid (§1.3); `gui_comun.diseno` la descarta y pone encima su propia paleta (gris azulado estilo Tailwind), diez
   acentos propios, una hoja QSS de 160 líneas que redibuja todos los widgets con radios de 8–14 px y tipografía en
   píxeles, un estilo Fusion forzado y un conmutador claro/oscuro propio (§2).
2. **El sistema de diseño propuesto es, en esencia, dejar de pintar**: ningún color, fuente ni icono propio; todo sale
   del esquema de color activo, de las fuentes de `kdeglobals` y del tema de iconos freedesktop; lenguaje de ventana KDE
   (menú, barra de herramientas, paneles acoplables, barra de estado, acciones con atajos estándar); cambio en vivo al
   pasar de Lliphi Claro a Lliphi Oscuro sin reiniciar (§5). El acento por studio sobrevive solo como **marca** (icono
   del lanzador y «Acerca de»), nunca como color de interfaz (§5.2).
3. **Lo que cada studio conserva** es su área de trabajo (árbol de archivos, tabla de repos, formulario de compilación,
   fases OSINT, editor de tema, laboratorio de modelos, paquetes stow…) y su marca; lo que se unifica es el marco
   (§5.9).
4. **Piloto recomendado: Git Studio** (§7.3), con Filesystem Studio como gemelo que confirma que la receta se transfiere.
5. **Hay siete decisiones del autor (D1–D7, §8)**. La más estructural es D5: seguir con el PySide6 de Anaconda (Fusion con
   la paleta del sistema, sin Kvantum) o instalar `python3-pyside6` del sistema, con el que los studios ganan Kvantum
   «Lliphi», Breeze y el tema de plataforma de KDE sin escribir nada. La propuesta funciona en los dos casos y detecta
   cuál tiene.

## 1. El punto de partida: el entorno en que corren

### 1.1 Lo que el autor tiene en pantalla

| pieza | valor en esta máquina | de dónde sale |
|---|---|---|
| Sesión | KDE Plasma 6.6 sobre Wayland (`XDG_SESSION_TYPE=wayland`, `XDG_CURRENT_DESKTOP=KDE`) | entorno |
| Tema global | `org.lliphi.oscuro`; esquema de color `LliphiOscuro` | `~/.config/kdeglobals` `[KDE] LookAndFeelPackage`, `[General] ColorScheme` |
| Estilo de widgets | Kvantum, tema `Lliphi` (con `LliphiClaro` y `LliphiOscuro`) | `~/.config/Kvantum/kvantum.kvconfig` |
| Fuentes | Inter 10 (general, menús), JetBrainsMono Nerd Font 10 (fija), Inter 8 (mínima legible) | `kdeglobals` `[General] font / fixed / smallestReadableFont` |
| Iconos | `Colloid-Grey-Dark-Lliphi` (hereda de Breeze) | `kdeglobals` `[Icons] Theme` |
| Acento | `#e22529` (el rojo de Nothing) en el oscuro; `#315bef` en el claro | `lliphi/tokens/tokens.json`; `generado/esquema/*.colors` |
| Cambio claro/oscuro | `plasma-apply-colorscheme`; KDE emite `org.kde.KGlobalSettings.notifyChange` por D-Bus; `seguir-variante.py --vigilar` lo escucha para el fondo y Konsole | `lliphi/generado/fondo-variante/seguir-variante.py:196` |

Lliphi decidió **no depender de Kvantum** para el tema (`lliphi/docs/decisiones.md` §3.2: «Breeze lee el esquema; un tema
que exige Kvantum se rompe con cada Qt»), aunque el autor lo tiene activo. Eso importa para D5: el sistema de diseño
no puede exigir Kvantum; debe verse bien con Breeze y, como último recurso, con Fusion.

### 1.2 Con qué Qt corren los studios

Los diez studios se lanzan con el `python3` de Anaconda (`~/anaconda3/bin/python3`) y su PySide6 **6.9.2**, que trae su
propio Qt. Ese Qt **no puede cargar** los complementos del Qt del sistema (6.10.2, en `/usr/lib/x86_64-linux-gnu/qt6/plugins`):

| complemento | Qt del sistema (6.10.2) | Qt de Anaconda (6.9.2) |
|---|---|---|
| Estilos | `breeze6.so`, `libkvantum.so`, `oxygen6.so` | solo `Windows` y `Fusion` (sin carpeta `styles/`) |
| Tema de plataforma | `KDEPlasmaPlatformTheme6.so`, `libqgtk3.so` | `libqxdgdesktopportal.so` |
| Plataformas | wayland, xcb… | `xcb`, offscreen, minimal… (sin Wayland: por eso `preparar_plataforma()` fuerza XWayland) |
| Iconos | `libqsvgicon.so` | `libqsvgicon.so` |

El `python3` del sistema trae **PyQt6 6.10.2** (`python3-pyqt6`), no PySide6; `python3-pyside6.*` 6.10.2 está en los
repositorios de Ubuntu como candidato, sin instalar. Con PySide6 del sistema, los studios cargarían Breeze, Kvantum y el
tema de plataforma de KDE tal cual (es lo que ya hace `lliphi/herramientas/lamina.py` con PyQt6 para sus muestras).

### 1.3 Lo que Qt ya recibe de KDE sin ayuda (hallazgo clave)

Sonda ejecutada el 2026-11-01 con el PySide6 de Anaconda sobre `xcb`, **antes** de que `gui_comun` toque nada:

```text
plataforma: xcb | tema plataforma: (ninguno) | estilo: fusion | estilos: ['Windows', 'Fusion']
paleta: Window #363636  Base #242424  Button #656565  Text #fcfcfc  Highlight #e22529  Link #ff968b
fuente general: Inter 10 | fija: JetBrainsMono Nerd Font 10 | pequeña: 12
tema de iconos: Colloid-Grey-Dark-Lliphi | document-open: True | edit-undo: True
esquema (styleHints().colorScheme()): Unknown          ← con QT_QPA_PLATFORMTHEME=xdgdesktopportal: Dark
```

Es decir: el tema genérico de Qt para KDE (`QKdeTheme`) lee `kdeglobals` y construye la QPalette de **Lliphi Oscuro**
(`Window` 54,54,54 y `Highlight` 226,37,41 son los de `lliphi/generado/esquema/LliphiOscuro.colors`), las fuentes del
autor y el tema de iconos. Los 48 nombres freedesktop que necesitaría el marco (§5.4) resuelven en Colloid y en Breeze.
Dos fallos conocidos de esa paleta genérica que habrá que corregir desde el esquema: `PlaceholderText` sale negro y el
texto inactivo demasiado claro (`#cacaca`); `QPalette.Accent` queda en el azul de Breeze (`#308cc6`) porque el tema
genérico no lo lee. Límites: la paleta se lee una sola vez al arrancar (sin tema de plataforma de KDE nadie la
refresca) y `colorScheme()` solo sabe claro/oscuro con el tema `xdgdesktopportal` (que además trae los diálogos de
archivo del portal, es decir, los de KDE). Las tres cosas tienen solución barata (§5.11).

Conclusión de la auditoría: **la paleta, las fuentes y los iconos del escritorio ya llegan al proceso; el aspecto web es
lo que `gui_comun.diseno` pone encima.** `Disenador._pintar()` (`gui_comun/diseno.py:366-384`) sustituye esa paleta con
`app.setPalette(paleta)` desde sus tokens y aplica `app.setStyleSheet(hoja(t))`; `Disenador.__init__`
(`diseno.py:323-327`) fuerza `Fusion` y una fuente elegida entre Inter, IBM Plex Sans, Noto Sans y Cantarell.

## 2. Auditoría de `gui-comun` 1.4.0

2 299 líneas en 19 módulos; sin pruebas propias (`CLAUDE.md` verifica con `py_compile` y con los tests de cuatro
studios). Pieza por pieza, qué hace, de dónde salen sus colores y el juicio.

| pieza | qué hace | colores, fuentes, medidas | juicio |
|---|---|---|---|
| `diseno.py` (541) | tokens claro/oscuro (`_BASE`), diez acentos, `hoja()` QSS, `Disenador` (Fusion + QPalette + QSS + modo «sistema»), 50 iconos de trazo estilo Lucide (`_TRAZOS`), motor `_MotorSvg` que repinta SVG con el tema, `logo()` (losa redondeada con el acento), `variante()` y `clase()` | Paleta propia: fondo `#f5f6f8`/`#0e1014`, superficies, bordes y textos que **no son los de Lliphi ni los de Breeze**; los acentos son los de Tailwind CSS v3 (`#0d9488` teal-600, `#ea580c` orange-600, `#2563eb` blue-600, `#7c3aed` violet-600, `#db2777` pink-600, `#65a30d` lime-600…) — la firma de la web. QSS: `QWidget { font-size: 13px }` (píxeles, ignora el tamaño del usuario), radios 8–14 px, `* { outline: 0 }` (`diseno.py:145`, borra el indicador de foco del teclado en toda la aplicación), `QPushButton:default` con fondo de acento. `fuente_mono()` 9,5 pt fijos. Flechas y marcas escritas como SVG en `~/.cache/gui_comun/` para el QSS | **Lo más web**. Es un sistema de diseño de página: paleta y hoja propias que reemplazan al sistema; «sistema» solo decide claro u oscuro y aplica *su* claro u oscuro. Valioso y reutilizable: el motor de iconos que sigue a un color, el modo en vivo, `preparar_plataforma()`, la disciplina de no guardar la `QApplication` |
| `widgets/marco.py` (357) | `Marco`: barra lateral de 232/64 px fijos con marca, botón «Buscar o ir a… Ctrl K», lista de páginas con filas de 38 px, pie con cuatro `QToolButton` (plegar, consola, tema, preferencias); `QShortcut` literales Ctrl+K, Ctrl+B, Ctrl+J, Ctrl+Mayús+L, Ctrl+`,`, Ctrl+1…9; `montar_studio()`: `resize(1280, 820)`, mínimo 980×640, **`menuBar().hide()`** (`marco.py:303`), chip de tarea en la barra de estado, `pagina_con_margenes()` (28 px, oculta cabeceras verticales, filas de 34 px) | todo por `objectName` y la hoja; iconos de `icono()` con `texto_suave` | Patrón «app Electron/VS Code»: menú oculto, barra lateral de anchura fija, atajos en `QShortcut` (no existen como `QAction`: no aparecen en ningún menú, no son configurables, y en Filesystem y Git el `Ctrl+,` del `.ui` y el del marco conviven en la misma ventana: posible atajo ambiguo, por comprobar). Lo bueno: la idea de una paleta de órdenes, la consola acoplada, el chip de tarea con avisos al terminar |
| `widgets/paleta.py` (188) | paleta de órdenes Ctrl+K: `QDialog` `Popup` sin marco y translúcido, sombra, delegado que pinta con `diseno._ACTUAL`, filtro difuso | tokens al pintar; 440 px de alto, 480–640 de ancho | Lo más «web» en su pintura, pero el concepto existe en KDE (`KCommandBar`, Ctrl+Alt+I en Kate y Dolphin). Se conserva; se repinta con `palette()` y se alimenta de las `QAction` |
| `widgets/avisos.py` (112) | «toasts» de 340 px en la esquina inferior derecha con opacidad animada | círculo de color por nivel con tokens | Patrón web. KDE usa `KMessageWidget` en línea, la barra de estado y las notificaciones del sistema |
| `widgets/console_dock.py` (214) | `QDockWidget` inferior con progreso, pestañas Consola y Registro, señales `tarea_*` | `_COLORS` Tokyo Night fijos (`#7aa2f7`, `#9ece6a`…) que `actualizar_tokens` sustituye; fuente `fuente_mono()` 9,5 pt | **Ya es escritorio** (un dock de Qt Creator). Falta: fuente fija del sistema y colores de la paleta |
| `widgets/tarjetas.py` (178) | `Tarjeta`, `Cifra`, `Mosaico` (84 px mínimo, icono en losa), `ListaConVacio`, `rejilla_pareja`, `pagina_desplazable` | clases de la hoja; `setStyleSheet("font-weight: 600; font-size: 14px;")` en línea (`tarjetas.py:115`) | El «dashboard» de tarjetas y cifras: la portada web. Lo que aporta (acceso a herramientas, estado vacío amable, página que desplaza) se puede dar con widgets estándar (§5.8) |
| `widgets/grafico_barras.py` (77) | barras horizontales con `QPainter` | lee `diseno._ACTUAL` al pintar | Correcto como widget; debe leer `self.palette()` |
| `lanzador.py` (124) | `.desktop` + icono SVG (losa redondeada con el acento) en `~/.local/share`, `xdg-mime` para esquemas, `kbuildsycoca6` | acento «claro» del studio | **Escritorio**: integración freedesktop bien hecha. La losa es la marca de cada studio (se conserva, D2) |
| `theming.py`, `ajustes.py`, `icons.py`, `ui_loader.py`, `format.py`, `history_service.py`, `rutas.py`, `workers/` | contrato anterior, `QSettings` tipado (`ui/theme`, `ui/icon_size` 22), carga de SVG del studio por `icono_svg`, `QUiLoader`, formatos, historial, rutas, workers de función y de proceso | sin color | Neutros. `ajustes.theme()` deja de tener sentido cuando el tema lo dicta el sistema (migración en §6) |

Resumen de lo que ya está bien y se conserva: el `QDockWidget` de consola con sus señales, la barra de estado y el chip,
`QSettings`, los workers con cancelación, el modo «sistema» como idea, los iconos vectoriales con estados, el lanzador,
el contrato de nombres y la disciplina de ciclo de vida (nadie guarda la `QApplication`, nadie usa `layout.itemAt()`).

## 3. Auditoría por studio

Resumen de las dos auditorías de detalle (los informes completos, con todas las citas, están en el registro de la
sesión; aquí va lo que pesa para la decisión). «Marco» significa lo que pone `gui_comun`; cada fila dice lo que el
studio añade por encima.

### 3.1 Tabla comparativa

| studio | líneas UI | ventana | `setStyleSheet` propios | colores fijos propios | tamaños fijos | atajos propios | `fromTheme` | menú | toolbar | dock | barra de estado |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Biblioteca (`biblioteca-studio/studio`) | 594 | a mano | 1 | 1 (logo) | 5 | 0 | no | no tiene | no | consola | creada, sin uso |
| Filesystem (`filesystem-studio/studio`) | 2 499 (1 736 py + 763 `.ui`) | `.ui` + a mano | 6 | 10 (SVG) | 7 | 2 (`.ui`: Ctrl+Q, Ctrl+,) | no | en `.ui`, **oculto** | no | consola + acción Ver › Consola | **con uso real** |
| Git (`git-studio/studio`) | 1 960 (1 261 + 699) | `.ui` + a mano | 4 | 14 (9 SVG + **5 Tokyo Night en el modelo**) | 6 | 2 (`.ui`) | no | en `.ui`, oculto | no | consola | con uso real |
| Huella (`huella-studio/studio`) | 448 | a mano | 1 | 1 | 1 | 0 | no | no tiene | no | consola | creada, sin uso |
| LaTeX (`latex-studio/studio`) | 508 | a mano | 0 | 1 | 3 | 3 literales (F5, Ctrl+O, Ctrl+Intro) | no | no tiene | no | consola | creada, sin uso |
| Quarto (`quarto-studio/studio`) | 1 811 | a mano + 1 `.ui` | 1 | 5 (One Dark en su consola) + 13 SVG | 12 | 5 (2 estándar: Quit, Refresh) | no | construido, **oculto** | construida, **oculta** | explorador propio; consola en `QTabWidget` propio | **propia y útil** (progreso) |
| Raphi (`raphi/escritorio/studio`) | 1 000 (+405 ventana web) | a mano | 4 | 2 (+ámbar rgba) | 12 | 1 (Ctrl+Intro) | **sí** (ventana web, 3) | no | no | consola | creada, sin uso |
| Lliphi (`lliphi/studio`) | 3 833 | a mano | 12 | 11 (defaults de lienzos: dominio) | 16 | 0 | no | no | no | consola | **usada** |
| Simuladores (`simuladores/studio`) | 674 | a mano | 4 | 2 (+figura blanca) | 4 | 0 | no | no | no | consola (sin uso real) | creada, sin uso |
| Dotfiles (`~/.dotfiles/studio`) | 459 | a mano | 1 | 1 | 1 | 0 | no | no | no | consola | creada, sin uso |

Ningún studio define una QPalette propia; ninguno usa `QKeySequence.StandardKey` salvo Quarto (Quit y Refresh); ninguno
usa `QIcon.fromTheme` en su ventana nativa (Raphi lo usa en la ventana web y en los menús de Dolphin); todos usan
`QFileDialog` y `QMessageBox` nativos; todos tienen pruebas con `QT_QPA_PLATFORM=offscreen` y `main.py --smoke`.

### 3.2 Lo que hace cada uno por encima del marco

- **Biblioteca Studio.** Catálogo declarativo de acciones (`biblioteca_app/acciones.py:126-242`) que corren las CLI
  de las suites con simular/aplicar; cada acción es una `Tarjeta` en rejilla de dos columnas con «Simular» y «Aplicar».
  Portada con cuatro `Cifra`. Ficha del libro con portada (`QPixmap` de Calibre), abierta por enlaces
  `biblioteca-studio://libro/<id>` con instancia única (`QLocalServer`). Bloqueo de «Aplicar» mientras Calibre o Zotero
  estén abiertos. Preferencias = navegar a «Puerta». Ya escritorio: `QDesktopServices` a `calibre://` y `zotero://`,
  `setDesktopFileName`. Complementos: el de Calibre usa el Qt de Calibre (`QMenu`, `QDialog`, sin QSS), el de KOReader es
  Lua con los widgets de KOReader y el de Zotero es XUL/Fluent con SVG `context-fill`: **los tres siguen el tema de su
  anfitrión y quedan fuera de esta propuesta.**
- **Filesystem Studio.** `mainwindow.ui` con `QMenuBar` (Archivo, Ver, Ayuda), acciones Salir/Preferencias/Consola/Acerca
  de, `QStatusBar` que sí usa (`ctx.status()`), barra lateral de 200 px fijos en el `.ui`. Diálogo de preferencias real
  (`QDialog` con pestañas y `QDialogButtonBox`), diálogo de propiedades, menú contextual `QMenu` en el explorador
  (`QFileSystemModel` + `QTreeView` ordenable), `QSplitter`, `QTabWidget`, `QSortFilterProxyModel`. Portada de 3 `Cifra`
  + mosaicos + 3 tarjetas. Títulos `font-size: 18px; font-weight: bold` en 6 sitios. Unicode como estado (`✓ • ✗ ⚠`,
  «↑ Subir»). **El más escritorio del grupo junto con Git**; su esqueleto es idéntico al de Git (`mainwindow.ui`
  difiere solo en el título; `context.py`, `controllers/base.py`, `utils/*` son copias).
- **Git Studio.** Mismo esqueleto `.ui`. Tabla de repos con modelo propio (`repo_status_model.py`) que pinta el
  estado con **cinco colores Tokyo Night fijos** (`:25-29`) que no cambian entre claro y oscuro; `QInputDialog`,
  `QMessageBox` de confirmación; formulario de clonado con lista marcable; sincronización con tabla de resultados y modo
  CLI en la consola. Portada de 4 `Cifra` + 4 `Mosaico` + botón primario con cursor de mano.
- **Huella Studio.** Fases OSINT declarativas sobre `objetivos.yml` como tarjetas con «Simular»/«Ejecutar»; `QSplitter`
  con lista y `QTextBrowser` (auditorías), manual Markdown; SpiderFoot como proceso hijo; sin atajos ni preferencias.
- **LaTeX Studio.** Arrastrar y soltar `.tex`, `.tex` por argumento y MIME `text/x-tex`, `QFileSystemWatcher` para
  «recompilar al guardar», errores del `.log` con archivo y línea que abren Kate o VS Code en la línea; atajos F5,
  Ctrl+O y Ctrl+Intro literales (no `StandardKey.Open`). Opciones en un `QFormLayout` dentro de una tarjeta.
- **Quarto Studio.** Lo más divergente: construye **menú completo y toolbar y los oculta** (`main_window.py:135-195,
  238-240`), tiene su propia barra lateral (`widgets/sidebar.py`, 170 px), **su propia consola** (`QPlainTextEdit` con
  colores One Dark fijos) y registro (`QTableWidget`) en un `QSplitter` en lugar de `ConsoleDock`, **sus propios
  ajustes** (`settings.py`), un dock real (explorador de proyectos sobre `QFileSystemModel`), barra de estado con
  `QProgressBar`, diálogo de preferencias real, asistente APAQuarto con pestañas, un `.ui` de Designer, ~30 emojis en
  los textos de los botones que se quitan en ejecución con una expresión regular (`main_window.py:48,264-267`). Es el
  que más piezas de escritorio tiene y el que más duplica al marco.
- **Raphi Studio.** Dos ventanas: la nativa (`escritorio/studio/`, por omisión) y la web (`escritorio/ventana.py`,
  `QWebEngineView` con `--web`). La nativa: páginas de familia como rejilla de mosaicos con buscador de 240 px, página
  genérica de herramienta generada de la ficha (`formulario.py`: `QSpinBox`, `QComboBox`, `QColorDialog`…) con «Volver»
  sin historial, «¿qué hacemos con esto?» al soltar, bandeja `QSystemTrayIcon`, instancia única, menús de servicio de
  Dolphin (`dolphin.py`), vigilancia de carpetas. Aviso ámbar con `rgba(217,119,6,0.14)` fijo (`herramienta.py:114`).
  Regla propia valiosa: **ninguna pantalla se escribe a mano** (`tests/test_studio.py:89-99`).
- **Lliphi Studio.** El área de trabajo más rica: disposición de editor (`comun.py:64-112`: biblioteca `QTreeWidget`,
  lienzo `QPainter`/`QSvgRenderer` con zoom, propiedades con deslizadores y spinboxes, pestañas Código/Cambios con
  `QSyntaxHighlighter`), `QQuickWidget` con el QML real del splash, sesión de Plasma anidada, `ksplashqml` y
  `sddm-greeter`. Usa `gui_comun` solo como paquete de pip (`v1.4.0`). 39 lecturas de `disenador.tokens` para pintar
  los lienzos (y sí se reconecta a `cambiado`). `QFont("JetBrains Mono")` y `QFont("Inter")` fijadas (37 líneas), 16
  tamaños fijos, **tema por defecto «oscuro», no «sistema»** (`ventana.py:50`), 8 veces el título
  `font-weight: 600; font-size: 14px`, sin un solo atajo. Los colores fijos de sus lienzos son **datos del tema que
  edita**, no interfaz: se quedan.
- **Simuladores Studio.** `PaginaDisciplina` de mosaicos con buscador (calca `PaginaRejilla` de Raphi); `PaginaModelo`
  con `QSplitter`, `QTabWidget` (ficha, ecuaciones LaTeX con `mathtext`, escenarios, verificaciones) y lienzo
  **matplotlib** con deslizadores. Lee `diseno._ACTUAL` **una sola vez** al crear la página (`pagina_modelo.py:161,346`)
  y no se conecta a `cambiado`: el HTML y las fórmulas no siguen al tema. Figura con fondo blanco fijo. Consola sin uso.
- **Dotfiles Studio.** El más sobrio: 1 `setStyleSheet`, 1 tamaño fijo. Tarjetas por paquete stow con cuatro botones,
  `QSplitter` con lista y visor de diff (`QFont("monospace")`), guía Markdown, `QInputDialog` para el commit.

### 3.3 Qué es «web» y qué es «KDE» en toda la familia

**Aspecto de aplicación web (en todos, por el marco):** menú oculto; barra lateral de anchura fija tipo app web;
portada «dashboard» de cifras y mosaicos; tarjetas con borde redondeado como unidad de composición (acciones, fases,
paquetes, opciones); botones de color plano por «variante»; chips (`navAtajo`, `chipTarea`, chips de estado en Lliphi
y Raphi); avisos flotantes; QSS que reemplaza la paleta del sistema; tipografía en píxeles (13 px base, 14 y 18 px de
títulos); cursor de mano en botones; glifos Unicode como estado (`✓ ✕ ⚠ ● ↑ ↓ ■ ▶`); «Volver» sin historial en las
páginas de desglose (Biblioteca, Raphi, Simuladores); «Preferencias» que solo navega a una página (seis studios).

**Ya se comporta como KDE:** diálogos nativos (`QFileDialog`, `QMessageBox`, `QInputDialog`, `QColorDialog`) en todos;
`QDockWidget` de consola en nueve; docks y splitters de verdad en Quarto, Lliphi, Huella, Simuladores y Dotfiles;
`QMenuBar` y `QAction` con mnemónicos en Filesystem, Git y Quarto (ocultos); barra de estado con uso real en
Filesystem, Git, Quarto y Lliphi; menú contextual en Filesystem; arrastrar y soltar, MIME y argumento en LaTeX y
Raphi; instancia única y esquema de URL en Biblioteca y Raphi; bandeja y menús de Dolphin en Raphi; `QIcon.fromTheme` en
la ventana web de Raphi; `QDesktopServices` en casi todos; vistas sobre modelos (`QFileSystemModel`,
`QSortFilterProxyModel`, modelos propios) en Filesystem y Git.

## 4. Inventario de componentes

### 4.1 Compartido hoy (vive en `gui-comun`)

`Disenador`/`aplicar_tema`, `Marco`/`montar_studio`, `Paleta`/`Comando`, `Avisos`, `ConsoleDock`, `Tarjeta`/`Cifra`/
`Mosaico`/`ListaConVacio`/`encabezado`/`seccion`/`rejilla_pareja`/`pagina_desplazable`, `GraficoBarras`,
`icono_trazo`/`icono_svg`/`logo`/`variante`/`clase`, `cargador_iconos`, `AjustesBase`, `load_ui`, `FunctionWorker`/
`ProcessWorker`, `lanzador`, `rutas`, `format`, `history_service`.

### 4.2 Repetido entre studios (debería subir a `gui-comun`)

| qué | dónde se repite | propuesta |
|---|---|---|
| La clase envoltorio `Ventana` (`ui`, `console`, `settings`, `controllers`, `_page_order`, `navigate`, `_pagina`, `run_function_worker`, `_open_preferences`, `_about`) que `montar_studio` exige | casi idéntica en Raphi, Lliphi, Simuladores, Dotfiles, Huella, LaTeX y Biblioteca; variante `.ui` en Filesystem y Git | `gui_comun.ventana.VentanaStudio(QMainWindow)` (§5.12): el studio hereda y añade páginas |
| El esqueleto `.ui` (`mainwindow.ui`, `context.py`, `controllers/base.py`, `utils/theming.py`, `utils/icons.py`) | Filesystem y Git, copias byte a byte salvo el título | lo cubre `VentanaStudio`; el `.ui` de la ventana desaparece, los `.ui` de páginas y diálogos se quedan |
| Título de sección `setStyleSheet("font-weight: 600; font-size: 14px;")` | 9 veces (Lliphi 8, Dotfiles 1) + `tarjetas.py:115`; 18 px en bold en Filesystem (6) y Git (4) | `gui_comun.widgets.titulos.titulo()` con `QFont` relativa (§5.3) |
| Portada de `Cifra` + `Mosaico` + listas | los diez studios | `PaginaInicio` estándar (§5.8) |
| Rejilla de mosaicos con buscador de 240 px | Raphi `paginas.py:41`, Simuladores `ventana.py:61` | `QListView` en modo iconos con filtro (§5.8) |
| Tarjeta de acción con «Simular» y «Aplicar»/«Ejecutar» | Biblioteca, Huella, Dotfiles, Lliphi (`TarjetaOrden`), Raphi (herramienta) | `AccionSimulable` como par de `QAction` en toolbar/menú + formulario estándar (§5.5) |
| «Preferencias» que solo navega a una página | Biblioteca, Huella, LaTeX, Raphi, Lliphi, Simuladores, Dotfiles | diálogo de ajustes estándar (§5.5); la «página Sistema» se queda como página si tiene contenido propio |
| Consola propia | Quarto (`console_widget.py`, `log_panel.py`) | `ConsoleDock` con registro en tabla (absorber lo que Quarto añadió) |
| Ajustes propios | Quarto `settings.py` | `AjustesBase` |
| Glifos Unicode como estado | Filesystem, Git, LaTeX, Quarto, Huella, Lliphi, Raphi | iconos del tema `dialog-ok`, `dialog-error`, `dialog-warning`, `emblem-*`, `go-up` (§5.4) |
| Colores fijos de estado | Git `repo_status_model.py:25-29`, Quarto `console_widget.py:57-70` y `log_panel.py:63`, `ConsoleDock._COLORS`, Raphi `herramienta.py:114` | roles del esquema: `ForegroundPositive/Negative/Neutral/Active` de `KColorScheme` (§5.2) |
| Lectura de tokens de una vez (no sigue al tema) | Simuladores `pagina_modelo.py:161,346` | pintar con `self.palette()` en `paintEvent`/al refrescar; `QEvent.PaletteChange` |

### 4.3 Propio de cada studio (no se toca más que para usar la paleta)

Biblioteca: catálogo de acciones, ficha del libro, bloqueo por Calibre/Zotero, Puerta. Filesystem: explorador,
árbol, extensiones, carpetas en lote, hardlinks, reportes. Git: tabla de repos, clonado, sincronización, reportes.
Huella: fases y la regla ética (ningún campo para escribir un objetivo), visor de auditorías, herramientas. LaTeX:
formulario de compilación, lista de errores, recompilar al guardar, historial. Quarto: ciclo de blogs, APAQuarto,
metadatos por Excel, YAML, índices. Raphi: ~60 herramientas generadas de fichas, recetas, vigilancia, soltar, Dolphin,
bandeja, ventana web. Lliphi: editor OKLCH, lienzos de Plasma/Aurorae/iconos/splash/disposición, sesión anidada,
despliegue. Simuladores: `Laboratorio`, página de modelo con matplotlib. Dotfiles: estado stow, órdenes por paquete,
confirmación archivo por archivo, híbridos de KDE.

## 5. Propuesta: sistema de diseño común «aplicación de escritorio KDE»

### 5.1 Principios

1. **El sistema manda.** Color, superficie, borde, texto, fuente, métrica e icono salen del tema activo; el studio no
   declara ninguno. Si Lliphi cambia, los studios cambian; si el autor cambia de tema, también.
2. **Nada de hojas globales.** Cero `app.setStyleSheet`. Un `setStyleSheet` local solo cuando el estilo no pueda
   expresarlo y siempre con colores de `palette()`; en la práctica, ninguno.
3. **Widgets estándar antes que widgets propios.** `QMainWindow`, `QMenuBar`, `QToolBar`, `QDockWidget`, `QStatusBar`,
   `QTabWidget`, `QSplitter`, `QGroupBox`, `QFormLayout`, `QDialogButtonBox`, vistas sobre modelos.
4. **Acciones antes que botones.** Toda orden es una `QAction` con icono del tema, texto, atajo, `statusTip` y
   `whatsThis`; de ahí salen menú, barra de herramientas, menú contextual, paleta de órdenes y botones.
5. **Un mismo lenguaje, no copias.** El marco da la ventana y las piezas; cada studio aporta sus páginas, sus acciones,
   su marca (nombre, icono, subtítulo) y conserva lo que lo hace distinto (§5.9).
6. **Accesible por construcción.** Foco visible, teclado completo, nombres accesibles, tamaños que siguen a la fuente,
   estados con icono y texto (nunca solo color).

### 5.2 Color: el esquema de color activo

Fuente única: la paleta que el tema de plataforma entrega (`QApplication.palette()`), corregida y mantenida al día por
`gui_comun.sistema` cuando el tema de plataforma sea el genérico (caso Anaconda, §1.3). Los roles que un studio puede
pedir, y de dónde salen (`KColorScheme`, los grupos `[Colors:*]` de `kdeglobals` o del `.colors` activo):

| rol para los studios | `QPalette` | `KColorScheme` | sustituye al token de 1.x |
|---|---|---|---|
| fondo de ventana | `Window` | `Colors:Window BackgroundNormal` | `fondo`, `lateral` |
| fondo de vista o entrada | `Base` / `AlternateBase` | `Colors:View BackgroundNormal/Alternate` | `superficie`, `superficie_2`, `entrada` |
| botón | `Button` / `ButtonText` | `Colors:Button` | `superficie`, `borde_fuerte` |
| texto | `WindowText`, `Text` | `ForegroundNormal` | `texto` |
| texto secundario | `PlaceholderText`; o `ForegroundInactive` leído del esquema | `ForegroundInactive` | `texto_suave`, `texto_tenue` |
| selección y foco (el acento del sistema) | `Highlight` / `HighlightedText` | `Colors:Selection`; `DecorationFocus`, `DecorationHover` | `acento`, `sobre_acento`, `seleccion`, `acento_suave`, `acento_borde` |
| enlace | `Link` / `LinkVisited` | `ForegroundLink/Visited` | `acento` |
| positivo, negativo, neutro, activo | leídos del esquema (no tienen rol en `QPalette`) | `ForegroundPositive/Negative/Neutral/Active` | `exito`, `error`, `aviso`, `info` |
| cabecera (barra de herramientas y título) | leído del esquema | `Colors:Header` | — |
| inactivo y desactivado | grupos `Inactive` y `Disabled` de `QPalette` | `ColorEffects:Inactive`, `ColorEffects:Disabled` | `texto_tenue` |

Reglas: el **acento por studio desaparece de la interfaz** (botones, selección, pestañas, iconos de la barra lateral);
el «botón primario» es `setDefault(True)` y lo pinta el estilo; «peligro» es un `QAction` con icono `edit-delete`/
`dialog-warning` y confirmación, no un botón rojo. Lo que se pinta a mano (gráfico de barras, delegados, lienzos de
Lliphi) lee `self.palette()` en el momento de pintar. Los **únicos colores propios** que quedan en la familia son los
de la marca (icono del lanzador y «Acerca de») y los datos de dominio que un studio muestra (los tokens que Lliphi
edita, un color elegido en Raphi).

### 5.3 Tipografía y métricas

- Fuente general: `QApplication.font()` tal como llega del sistema (`Inter 10` hoy); el marco **no llama a
  `app.setFont`**. Fija: `QFontDatabase.systemFont(QFontDatabase.FixedFont)` (`JetBrainsMono Nerd Font 10` hoy) para
  consola, diff y código, en lugar de `fuente_mono()` 9,5 pt, `QFont("Monospace")` y `QFont("JetBrains Mono")`.
- Jerarquía con tamaños **relativos**: título de página = fuente general × 1,5 en negrita; título de sección = × 1,15
  en negrita; texto secundario = `smallestReadableFont` o la general en color `ForegroundInactive`. Todo por `QFont`,
  nunca `font-size: Npx`.
- Espaciado y márgenes: los de la disposición por omisión (que Breeze y Fusion toman de `pixelMetric`:
  `PM_LayoutHorizontalSpacing`, `PM_LayoutLeftMargin`…); nada de `setContentsMargins(28, …)` en cada página. Alturas de
  fila de tablas y listas: las del estilo. Tamaños de icono: `PM_SmallIconSize` (16) en menús y listas,
  `PM_ToolBarIconSize` (24) en la barra de herramientas, `ui/icon_size` deja de existir.
- Prohibido: `setFixedWidth/Height/Size` salvo en lienzos de vista previa; `resize()` fijo de la ventana (se usa
  `saveGeometry`/`restoreGeometry` y un tamaño inicial relativo a la pantalla disponible); alturas mínimas de 200–380 px
  (`QSizePolicy` y `setStretch` las sustituyen).

### 5.4 Iconos

`QIcon.fromTheme("<nombre freedesktop>", <reserva>)` en toda la familia. Verificado el 2026-11-01 en Colloid-Grey-Dark-
Lliphi y en Breeze: los 48 nombres de la tabla resuelven en los dos.

| trazo propio de 1.x | nombre freedesktop | trazo propio | nombre freedesktop |
|---|---|---|---|
| terminal | `utilities-terminal` | libro | `x-office-address-book` (o `document-open-recent`) |
| ajustes | `configure` | sincronizar | `view-refresh` |
| panel | `view-sidetree` | candado | `object-locked` |
| buscar | `edit-find` | bandeja | `mail-folder-inbox` |
| info | `dialog-information` | verificar | `checkmark` |
| cargando | `view-refresh` | huella | `fingerprint` |
| inicio | `go-home` | usuario | `user` |
| documento | `document-new` / `x-office-document` | correo | `mail-message` |
| pdf | `application-pdf` | codigo | `text-x-script` |
| imagen | `image-x-generic` | globo | `internet-services` |
| audio | `audio-x-generic` | paquete | `package` |
| video | `video-x-generic` | enlace | `insert-link` |
| archivo | `package-x-generic` | subir | `go-up` |
| descarga | `download` | paleta | `preferences-desktop-color` |
| receta | `view-list-details` | capas | `layer-visible-on` |
| sistema | `computer` | cursor | `preferences-desktop-cursors` |
| carpeta | `folder` | pantalla | `video-display` |
| subtitulos | `media-view-subtitles-symbolic` | ventana | `preferences-system-windows` |
| texto | `text-x-generic` | cohete | `system-run` |
| volver | `go-previous` | ojo | `view-visible` |
| tendencia | `office-chart-line` | jugar | `media-playback-start` |
| barras | `office-chart-bar` | mas / quitar | `list-add` / `list-remove` |
| sol, luna | se retiran (no hay conmutador) | abrir | `document-open` |

Los glifos Unicode de estado se cambian por `dialog-ok-apply`, `dialog-error`, `dialog-warning`, `emblem-information`,
`go-up`/`go-down`, `media-playback-stop`. La reserva, para un tema de iconos incompleto, son los trazos actuales pintados
con `palette().windowText()` (se conserva `_MotorSvg` con color de la paleta en vez de tokens). Los SVG propios de
Filesystem, Git y Quarto (`resources/icons/`) pasan a ser reserva de sus nombres freedesktop. El icono de aplicación
sigue siendo la losa con el acento de `lanzador.icono_svg` (marca), instalada en `hicolor`, y la ventana lo toma con
`QIcon.fromTheme(app_id)`. En las pruebas con `offscreen` el tema de iconos no resuelve (comprobado): las pruebas fijan
`QIcon.setThemeName` o aceptan la reserva.

### 5.5 Estructura de ventana (lenguaje KDE)

```text
┌ Título de la ventana: «<documento o página> — <Studio>» ───────────────────────────────┐
│ Archivo  Editar  Ver  Ir  Herramientas  Ajustes  Ayuda                      (QMenuBar) │
│ [Icono Texto] [Icono Texto] … (QToolBar «Principal», movible, estilo de kdeglobals)   │
├──────────────┬─────────────────────────────────────────────────────────────────────────┤
│ Páginas      │  Área de trabajo del studio (QStackedWidget o QTabWidget)               │
│ (QDockWidget │                                                                         │
│  con QListView│  — la página de inicio, las páginas propias, los diálogos propios      │
│  o QTreeView;│                                                                         │
│  acoplable,  ├─────────────────────────────────────────────────────────────────────────┤
│  cerrable,   │  Consola (QDockWidget inferior, el actual ConsoleDock)                  │
│  recordado)  │                                                                         │
├──────────────┴─────────────────────────────────────────────────────────────────────────┤
│ Mensaje de estado · [QProgressBar de la tarea] · [botón de consola]      (QStatusBar)  │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

- **Menú visible**, con el orden y los nombres de KDE: Archivo (Abrir…, Recientes, Salir), Editar (Deshacer, Copiar,
  Buscar…), Ver (Páginas, Consola, Barra de herramientas, Pantalla completa, Barra de estado), Ir (las páginas,
  Atrás/Adelante), Herramientas (lo propio del studio), Ajustes (Configurar atajos…, Configurar barras…, Configurar
  <Studio>…), Ayuda (Manual, Informar de un fallo, Acerca de <Studio>, Acerca de KDE no aplica). Mnemónicos (`&Archivo`).
- **Barra de herramientas** con las cuatro a seis acciones frecuentes del studio; `Qt.ToolButtonTextBesideIcon` por
  omisión (lo que KDE usa) y respeta `ToolButtonStyle` de `kdeglobals`; movible, con «Ocultar» en su menú contextual.
- **Páginas como `QDockWidget`** a la izquierda (`QListView` con icono y texto, tamaño de icono del estilo), en lugar de
  la barra lateral fija: se pliega, se mueve, se cierra desde Ver, recuerda su anchura (`saveState`). Un studio con dos
  o tres páginas (LaTeX, Dotfiles) puede usar `QTabWidget` en lugar del dock: el marco admite las dos formas.
- **Desglose con historial** (Raphi, Simuladores, Biblioteca): el apilado de páginas lleva Atrás/Adelante
  (`QKeySequence.Back`/`Forward`, Alt+←/→) en Ir y en la barra, no un botón «Volver» por página.
- **Barra de estado** en todos: mensajes de las operaciones, `QProgressBar` de la tarea en curso (reemplaza al chip
  «● tarea…»), botón de consola a la derecha.
- **Diálogos**: `QDialog` con `QDialogButtonBox` (botones estándar: el estilo pone iconos y orden de KDE);
  confirmaciones con `QMessageBox.question` y botones con verbo («Aplicar», «Cancelar»), nunca «Sí/No» a secas;
  **diálogo de ajustes al estilo KDE** (lista de secciones a la izquierda, pila a la derecha, botones Aceptar/Aplicar/
  Cancelar/Predeterminados; la base en `gui-comun`, cada studio añade sus secciones) para los seis studios que hoy
  navegan a una página; `QFileDialog` nativo (con el portal, el de KDE).
- **Menús contextuales** (`QMenu` con las mismas `QAction`) en toda lista, tabla y árbol.
- **Ventana**: `setWindowTitle` con documento y studio; `saveGeometry`/`saveState` en `QSettings`; `setUnifiedTitleAndToolBarOnMac` no aplica; `QMainWindow.setDockOptions(AnimatedDocks | AllowTabbedDocks)`.

### 5.6 Acciones y atajos

- Todas las órdenes son `QAction` registradas en `gui_comun.acciones.Acciones` (nombre interno, texto, icono del
  tema, atajo, `statusTip`, grupo). De ese registro salen el menú, la barra, la paleta de órdenes y los menús
  contextuales; `Comando` de 1.x se vuelve un adaptador y desaparece en 3.0.
- Atajos estándar por `QKeySequence.StandardKey`: `Open` Ctrl+O, `Save` Ctrl+S, `Quit` Ctrl+Q, `Close` Ctrl+W,
  `Refresh` F5, `Find` Ctrl+F, `Undo`/`Redo`, `Copy`/`Paste`, `SelectAll`, `HelpContents` F1, `FullScreen` Ctrl+Mayús+F,
  `Preferences` (Ctrl+Mayús+`,` en KDE), `Back`/`Forward` Alt+←/→, `Cancel` Esc, `ZoomIn`/`ZoomOut`.
- Convenciones de KDE que se adoptan: paleta de órdenes **Ctrl+Alt+I** (como `KCommandBar` en Kate y Dolphin) **y se
  conserva Ctrl+K** como segundo atajo (D4); consola **F4** (el terminal de Dolphin y Kate) además de Ctrl+J; panel de
  páginas **F9**; Ctrl+1…9 para ir a la página n se conserva; «Ejecutar/Compilar» Ctrl+Intro se conserva donde ya está.
- Se retiran: Ctrl+Mayús+L (no hay conmutador de tema: el sistema manda) y Ctrl+B (el dock se pliega desde Ver o F9).
- Teclado y accesibilidad: sin `outline: 0`; orden de tabulación revisado por página; `QLabel.setBuddy` y mnemónicos
  en formularios; `setAccessibleName` en todo control sin texto (botones de icono, lienzos); búsqueda por teclado en
  listas y tablas (`QAbstractItemView` la trae); «Configurar atajos…» como diálogo estándar sobre el registro de
  acciones (en Qt puro: una tabla editable de `QKeySequenceEdit` guardada en `QSettings`).

### 5.7 Avisos, progreso y notificaciones

- **Barra de mensaje en línea** (`gui_comun.widgets.mensaje.BarraMensaje`, equivalente a `KMessageWidget`): un `QFrame`
  en la cabecera de la página o de la ventana con icono del tema, texto, botones opcionales y cierre; colores de
  `ForegroundPositive/Negative/Neutral/Active` del esquema sobre `Window`. Sustituye a los toasts.
- **Barra de estado** para lo efímero («Guardado», «12 repos al día», 6 s) y **`QProgressBar`** en ella para la tarea
  en curso, con el botón de consola al lado.
- **Notificación del sistema** (`org.freedesktop.Notifications` por `QtDBus`, disponible en el PySide6 de Anaconda)
  cuando una tarea larga termina y la ventana no está activa; respeta «No molestar».
- `ConsoleDock` se queda como está, con fuente fija del sistema y colores de la paleta.

### 5.8 Página de inicio y piezas de página

- La portada deja de ser un «dashboard» de tarjetas: una **página de inicio estándar** (`PaginaInicio`) con el nombre y
  el icono del studio, una lista de herramientas en `QListView` en modo iconos (como Preferencias del sistema) con filtro
  `QLineEdit` arriba, y las listas de recientes o pendientes en `QListView`/`QTreeView` con cabecera. Las «cifras»
  pasan a un `QFormLayout` (etiqueta : valor) o a la barra de estado.
- `Tarjeta` como contenedor se sustituye por `QGroupBox` (con título) o por secciones con `titulo()` y un separador;
  `Mosaico` por elementos de `QListView`; `Cifra` por filas de formulario; `ListaConVacio` se conserva (patrón de KDE:
  `KMessageWidget`/placeholder en vista vacía) pintada con la paleta; `pagina_desplazable` se conserva.
- Las «tarjetas de acción» (Simular/Aplicar) son un formulario con `QDialogButtonBox` (Aplicar, Simular como botón de
  rol `ActionRole`, Cancelar) o un par de acciones en la barra de herramientas de la página.

### 5.9 Lo que cada studio conserva (que no sean copias)

| studio | identidad que conserva | lenguaje que adopta |
|---|---|---|
| Biblioteca | sepia como marca; catálogo de acciones; ficha del libro con portada; Puerta | acciones por suite en Herramientas y en la barra; ficha como página con Atrás; bloqueo mostrado como `BarraMensaje` |
| Filesystem | verde como marca; explorador y árbol como centro | el dock de páginas y el explorador conviven como docks; «Usar en…» como submenú contextual (ya lo tiene) |
| Git | naranja; tabla de repos y la consola de sincronización | estados de repo con iconos `vcs-*`/`emblem-*` y colores del esquema; Sincronizar/Clonar como acciones en la barra |
| Huella | grafito; fases con la regla ética; visor de auditorías | fases como asistente (`QWizard`-like) o lista con «Ejecutar» por acción; la regla ética como `BarraMensaje` permanente |
| LaTeX | rosa; formulario de compilación y lista de errores | compilar como acción (Ctrl+Intro, F5) en barra y menú; errores en `QTreeView` que abren el editor con doble clic |
| Quarto | azul; ciclo de blogs y APAQuarto | ya tiene menú y toolbar: se muestran; su consola y ajustes se reemplazan por los del marco; sus emojis se retiran del código |
| Raphi | violeta; herramientas desde fichas; soltar; Dolphin; bandeja; ventana web opcional | familias como dock de páginas; herramienta como página con Atrás; el aviso ámbar como `BarraMensaje` |
| Lliphi | carmesí; editor con lienzos; sesión anidada | ya tiene disposición de editor; gana menú, barra y atajos (Guardar, Deshacer, Zoom); tema por omisión «sistema» |
| Simuladores | lima; página de modelo con matplotlib | figura con `facecolor` de `Base` y textos de `Text`; disciplina como dock de páginas; modelo con Atrás |
| Dotfiles | índigo; estado stow y diff | paquetes en `QTreeView` con acciones por fila en menú contextual y barra |

### 5.10 Cambio en vivo entre Lliphi Claro y Lliphi Oscuro

Tres canales, por orden de preferencia, todos en `gui_comun.sistema`:

1. **Tema de plataforma de KDE** (si el Qt es el del sistema, D5-b): KDE actualiza la paleta y Qt emite
   `QEvent.ApplicationPaletteChange`; no hay nada que hacer.
2. **D-Bus** (PySide6 de Anaconda): `QDBusConnection.sessionBus().connect("", "", "org.kde.KGlobalSettings",
   "notifyChange", …)` —la misma señal que escucha `seguir-variante.py`— y, al recibirla, releer `kdeglobals` y el
   `.colors` activo, reconstruir la QPalette (mapa de `lliphi/herramientas/lamina.py:33-70`, ampliado con `Header`,
   `Complementary` y los efectos `Inactive`/`Disabled`), las fuentes y el tema de iconos, y aplicarlos con
   `app.setPalette` (solo esto: ninguna hoja). Qt reenvía `PaletteChange` a cada widget.
3. **`QFileSystemWatcher` sobre `~/.config/kdeglobals`** como reserva sin D-Bus (KConfig escribe por archivo temporal
   y renombrado: hay que volver a añadir la ruta tras cada aviso).

Además, `preparar_plataforma()` fija `QT_QPA_PLATFORMTHEME=xdgdesktopportal` si no hay otro, para que
`colorScheme()` sepa claro/oscuro, `colorSchemeChanged` se emita y los diálogos de archivo sean los del portal.

Quien pinta a mano se suscribe a `QEvent.PaletteChange` o lee `self.palette()` en `paintEvent`; nadie guarda colores.
La señal `Disenador.cambiado(dict)` se conserva en 2.x emitiendo un diccionario de roles derivado de la paleta
(compatibilidad para Lliphi y Simuladores), y se retira en 3.0.

### 5.11 Estilo de widgets y dependencia del Qt (lo que D5 decide)

`gui_comun.sistema.preparar()` detecta al arrancar:

- si `QStyleFactory.keys()` trae `kvantum` o `Breeze` (PySide6 del sistema): no toca el estilo; el tema de plataforma
  de KDE lo pone todo (estilo, paleta, fuentes, iconos, diálogos, cambio en vivo);
- si no (Anaconda): `Fusion` (el estilo más neutro y el que mejor obedece a la paleta) + la paleta corregida desde el
  esquema (§5.2) + fuentes de `kdeglobals` + tema de iconos de `kdeglobals` + D-Bus para el cambio en vivo. Fusion con
  la paleta de Lliphi no es Kvantum «Lliphi», pero es sobrio, coherente y del color correcto; la diferencia es de
  relieve y radio, no de identidad.

Recomendación: **D5-b, instalar `python3-pyside6` (apt, 6.10.2) y lanzar los studios con `/usr/bin/python3`**, de modo
que la familia use Kvantum «Lliphi» de verdad y el tema de plataforma de KDE; la vía Anaconda queda como respaldo
automático (y como la que verán usuarios de Raphi o Lliphi Studio fuera de esta máquina). Riesgos de D5-b: Raphi tiene
`.venv` propio (habría que crearlo con `--system-site-packages` o instalar PySide6 del sistema en él), matplotlib y
las dependencias de cada studio deben estar en el Python del sistema, y las pruebas `offscreen` pasan a correr con ese
intérprete. Se mide en E0 antes de decidir en firme.

### 5.12 API de `gui-comun` 2.0 (nombres propuestos)

| módulo | contenido | sustituye a |
|---|---|---|
| `gui_comun/sistema.py` | `preparar()` (plataforma, estilo, paleta corregida, fuentes, iconos), `Tema` (`QObject` con `cambiado`, `color(rol)` para los roles sin `QPalette`: positivo, negativo, neutro, activo, cabecera), vigilancia D-Bus/archivo | `diseno.Disenador`, `theming.aplicar_tema`, tokens |
| `gui_comun/acciones.py` | `Acciones` (registro), `estandar(nombre)` (las `StandardKey` con icono y texto en español), `AccionSimulable` | `paleta.Comando`, `QShortcut` del marco |
| `gui_comun/ventana.py` | `VentanaStudio(QMainWindow)`: menú, barra, dock de páginas, consola, barra de estado con progreso, Acerca de, ajustes, geometría; `agregar_pagina(id, titulo, icono, widget)`, `abrir_subpagina(widget)` con historial | `Marco`, `montar_studio`, las `Ventana` envoltorio de los studios, el `.ui` de ventana |
| `gui_comun/widgets/mensaje.py` | `BarraMensaje` | `Avisos` |
| `gui_comun/widgets/ajustes.py` | `DialogoAjustes` (secciones + pila + botones estándar) | las «preferencias» que navegan a una página; los dos diálogos de Filesystem y Git se vuelven secciones |
| `gui_comun/widgets/titulos.py` | `titulo()`, `subtitulo()`, `seccion()` con `QFont` relativa | `encabezado`, `seccion`, los `setStyleSheet` de títulos |
| `gui_comun/widgets/inicio.py` | `PaginaInicio` (herramientas en `QListView` de iconos con filtro, listas de recientes) | `tarjetas.Cifra/Mosaico/Tarjeta`, `rejilla_pareja` |
| `gui_comun/widgets/paleta.py` | la misma paleta, alimentada de `Acciones`, pintada con `palette()`, Ctrl+Alt+I y Ctrl+K | — |
| `gui_comun/widgets/console_dock.py` | igual + registro en tabla (de Quarto), fuente fija del sistema, colores del `Tema` | `_COLORS` |
| `gui_comun/iconos.py` | `icono(nombre)` = `QIcon.fromTheme(freedesktop, reserva_trazo)`, tabla §5.4 | `diseno.icono_trazo/icono/_TRAZOS`, `icons.cargador_iconos` |
| `lanzador.py`, `workers/`, `ajustes.AjustesBase`, `ui_loader`, `format`, `history_service`, `rutas` | sin cambio (en `AjustesBase` se retiran `theme`/`icon_size`, que quedan como lectura inocua) | — |

Contrato: los nombres de 1.x (`aplicar_tema`, `Disenador`, `montar_studio`, `Marco`, `Comando`, los widgets de
`tarjetas`, las señales de `ConsoleDock`, los workers) **se conservan en 2.x como adaptadores** que delegan en lo nuevo
(regla del repo: se añade sin quitar; lo que cambia sube la mayor con migración), y se retiran en 3.0 cuando los diez
studios hayan migrado. `CHANGELOG.md` 2.0.0 lleva la tabla de migración. Pruebas propias de `gui-comun` (`tests/`,
`offscreen`), que hoy no existen: paleta desde esquema, acciones y atajos sin ambigüedad, ventana con dock y consola,
cambio de paleta en vivo (simulado escribiendo un `kdeglobals` temporal con `XDG_CONFIG_HOME`), lanzador.

### 5.13 Lo que no se hace

Hoja QSS global; colores, fuentes o tamaños en píxeles propios; menú oculto; barra lateral de anchura fija;
conmutador claro/oscuro en la aplicación; toasts; emojis o glifos como iconos; cursor de mano; «primario» por color;
tarjetas como unidad de composición; `resize(1280, 820)`; leer tokens una vez y guardarlos.

## 6. Migración de ajustes y de código que los studios tocan

- `ui/theme` (`sistema|claro|oscuro`) deja de leerse; el valor se conserva en `QSettings` sin efecto. Lliphi, que
  arranca en «oscuro», pasa a seguir al sistema.
- `ui/icon_size` deja de leerse.
- `marco/plegada` → `ventana/estado` (`saveState`).
- Los `Comando` que cada studio añade a `marco.comandos_extra` pasan a `Acciones.agregar(...)` (misma información:
  título, acción, grupo, icono, atajo, palabras).
- `clase(widget, "tenue"|"suave"|"busqueda"|"seccion"|"vacio")` y `variante(boton, …)`: en 2.x siguen existiendo pero
  solo cambian la fuente o el rol de color de la paleta (no hay hoja); en 3.0 se retiran.
- Los SVG de `resources/icons/` de Filesystem, Git y Quarto pasan a reserva de `iconos.icono(nombre)`.

## 7. Plan por etapas

Cada etapa termina con: `python3 -m py_compile` de lo tocado, las pruebas `offscreen` del repo y de los studios que
consumen `gui-comun`, el studio lanzado en Lliphi Claro y en Lliphi Oscuro con cambio en vivo
(`plasma-apply-colorscheme LliphiClaro` / `LliphiOscuro` con la ventana abierta), una captura antes/después por
página en los dos modos, `python3 core/archivos.py validar <repo>` con la línea base, `meta/doctor/main.sh --breve`,
commit en rama `wip/<fecha>-<tema>` y `estado.md` al día. Ninguna etapa toca lo generado ni las carpetas sensibles.

| etapa | qué | riesgo | pruebas y salida |
|---|---|---|---|
| **E0 Preparación** (sin código de producción) | Línea base: capturas de las portadas y de dos páginas de cada studio en claro y oscuro (`offscreen` + `grab()`); comprobar ejecutando el posible atajo ambiguo Ctrl+`,` en Filesystem y Git; medir D5 (instalar `python3-pyside6` en un entorno de prueba y lanzar Git Studio con `/usr/bin/python3`); crear `gui-comun/tests/` con la infraestructura (`conftest.py` con `XDG_CONFIG_HOME` temporal y un `kdeglobals` de Lliphi Claro y otro de Lliphi Oscuro); llevar la HIG de KDE a Calibre (D7) | bajo | capturas en `$RESPALDOS_DIR/capturas/studios-2026-11/` (fuera de los repos); informe corto en `estado.md` con el resultado de D5 |
| **E1 `gui-comun` 2.0** | `sistema.py`, `acciones.py`, `ventana.py`, `widgets/mensaje.py`, `widgets/ajustes.py`, `widgets/titulos.py`, `widgets/inicio.py`, `iconos.py`; paleta y consola adaptadas; adaptadores de 1.x; `CHANGELOG` 2.0.0 con migración; README | **medio**: diez consumidores; se mitiga con los adaptadores (ningún studio cambia en E1) y con `rg` de cada nombre del contrato en los studios antes de tocarlo | pruebas nuevas de `gui-comun`; los tests de los cuatro studios de `CLAUDE.md` y los de Raphi en verde **sin cambiar los studios** (prueba de que los adaptadores funcionan); etiqueta `v2.0.0` |
| **E2 Piloto: Git Studio** | migrar `main_window.py` y los `.ui` de página a `VentanaStudio`; menú y barra visibles; estados de repo con iconos y colores del esquema; `BarraMensaje`; diálogo de ajustes como sección; iconos `fromTheme`; atajos estándar; título de ventana; geometría | medio: es el primero; su gemelo Filesystem mide si la receta se transfiere | `git-studio/tests/run.sh`; captura antes/después; **revisión del autor**: aquí se aprueba o se corrige el lenguaje antes de seguir |
| **E3 Gemelo y pequeños** | Filesystem (misma receta); después Huella, LaTeX, Dotfiles y Biblioteca (ventanas a mano de 400–500 líneas; cada uno en una sesión) | bajo: cada uno es independiente; Biblioteca tiene el bloqueo por Calibre/Zotero y la instancia única que no se tocan | sus tests; una sesión por studio; capturas |
| **E4 Simuladores y Raphi** | Simuladores: figura con la paleta, repintado al cambiar, dock de disciplinas; Raphi: `VentanaStudio`, herramienta como subpágina con historial, aviso en línea, bandeja y Dolphin sin cambio; la ventana web no se toca | medio en Raphi (público, `.venv` propio, 60 herramientas generadas; su prueba «ninguna pantalla a mano» debe seguir pasando) | `.venv/bin/python -m pytest -q tests`; `simuladores/tests` |
| **E5 Quarto y Lliphi** | Quarto: mostrar su menú y barra, reemplazar consola, barra lateral y ajustes propios por los del marco, quitar emojis del código; Lliphi: menú y barra con Guardar/Deshacer/Zoom, tema «sistema», fuentes del sistema en código y lienzos, títulos por `titulo()`; sus lienzos siguen pintando el tema que editan | medio-alto: son los dos más grandes (1,8 k y 3,8 k líneas) y Lliphi es el escaparate del tema: debe quedar impecable | `tests -k studio` de Quarto; `studio/tests` de Lliphi (17 pruebas); capturas |
| **E6 Cierre** | retirar los adaptadores (`gui-comun` 3.0.0), `rg` final de nombres de 1.x en los diez studios, actualizar `rol:` de `gui-comun` en `meta/workspace.yml` y regenerar los derivados, `README`/`CLAUDE.md` de `gui-comun`, `docs/` (este documento pasa a `hecho` y nace `docs/sistema-de-diseno.md` como referencia) | bajo | `meta/generadores/workspace.py verificar`; doctor; etiqueta `v3.0.0` |

### 7.3 Por qué Git Studio de piloto

- Ejercita **todas** las piezas del marco: `montar_studio` completo (barra lateral, consola, chip, toasts), `.ui` con
  menú y acciones ya definidos (`actionSalir`, `actionPreferencias`, `actionConsola`, `actionAcercaDe`), diálogo de
  preferencias real, barra de estado con uso, tablas sobre modelo, `QInputDialog` y confirmaciones.
- Tiene **el caso de color más claro que resolver** (los cinco colores Tokyo Night del estado de los repos): obliga a
  definir cómo un studio pide `ForegroundPositive/Negative/Neutral` del esquema.
- Tamaño medio (1 960 líneas de UI), tests propios (`tests/run.sh`), no es público-crítico como Raphi ni el
  escaparate del tema como Lliphi.
- **Filesystem Studio es su gemelo** (mismo `.ui`, mismos `context.py`, `controllers/base.py` y `utils/`): migrarlo
  después con la misma receta mide si la receta es general antes de pasar a las ventanas hechas a mano.

Alternativas consideradas: Filesystem (equivalente, pero más grande); Quarto (ya es el más «KDE», pero duplica consola,
barra y ajustes: mejor consolidarlo cuando el marco 2.0 esté probado); Dotfiles o Huella (demasiado pequeños para
probar el marco entero; irían rápido después).

## 8. Decisiones del autor

| id | decisión | recomendación |
|---|---|---|
| D1 | Aprobar el sistema de diseño (§5): colores, fuentes e iconos solo del sistema; sin hoja global; lenguaje de ventana KDE | sí |
| D2 | El acento por studio sobrevive solo como marca (icono del lanzador, «Acerca de», nombre); desaparece de botones, selección y barra lateral | sí; la losa del lanzador se conserva tal cual |
| D3 | Retirar el conmutador claro/oscuro (Ctrl+Mayús+L) y los avisos flotantes; en su lugar, barra de mensaje en línea, barra de estado y notificaciones del sistema | sí |
| D4 | Atajos: paleta de órdenes Ctrl+Alt+I **y** Ctrl+K; consola F4 **y** Ctrl+J; panel de páginas F9; Ctrl+1…9 se conserva; atajos estándar por `StandardKey` | sí |
| D5 | Qt: (a) seguir con el PySide6 de Anaconda (Fusion + paleta del sistema) o (b) instalar `python3-pyside6` del sistema y lanzar los studios con `/usr/bin/python3` (Kvantum «Lliphi», Breeze y tema de plataforma de KDE reales); el marco detecta cuál tiene | **b**, medido en E0; a como respaldo automático |
| D6 | Piloto: Git Studio, con Filesystem como gemelo de verificación | sí |
| D7 | Fuentes a la biblioteca antes de citarlas (R11): la HIG de KDE, la especificación de nombres de iconos de freedesktop, la documentación de `QPalette`/`QStyle`/`QKeySequence::StandardKey`/`QIcon::fromTheme` y de `KColorScheme`. Este documento **no las cita** (no están en Calibre); las nombra como lo que hay que ingerir en E0 | sí |
| D8 | Sede de este documento: `gui-comun` es un repo público que por regla no lleva el espacio de trabajo, y este texto nombra `core/`, `meta/` y rutas de esta máquina. Opciones: dejarlo aquí (es la auditoría del marco y no contiene nada sensible) o moverlo a `meta/` y dejar en `gui-comun/docs/` solo el sistema de diseño (§5) como referencia | dejarlo aquí hasta E6; en E6 nace `docs/sistema-de-diseno.md` (público) y esta auditoría pasa a `hecho` |

Hasta que el autor decida, no se cambia código en ningún studio ni en `gui-comun`. El pendiente está en
`gui-comun/estado.md` §Por hacer.

## 9. Evidencia y método

- Lectura íntegra de `gui-comun/gui_comun/` (19 módulos) y auditoría de los diez studios con citas `archivo:línea`
  (dos informes de detalle en la sesión del 2026-11-01); conteos con `rg` excluyendo `__pycache__`, `.venv` y `tests`.
- Sondas ejecutadas con el PySide6 de Anaconda sobre `xcb` (`QT_QPA_PLATFORMTHEME` vacío, `xdgdesktopportal` y
  `gtk3`): estilo, paleta, fuentes, tema de iconos, resolución de 48 nombres freedesktop en Colloid y Breeze,
  `QFontDatabase.systemFont`, `pixelMetric`, disponibilidad de `QtDBus`.
- `~/.config/kdeglobals`, `~/.config/Kvantum/kvantum.kvconfig`, `lliphi/generado/esquema/LliphiOscuro.colors`,
  `lliphi/docs/decisiones.md` §2–3, `lliphi/herramientas/lamina.py`, `lliphi/generado/fondo-variante/seguir-variante.py`,
  `core/docs/decisiones.md` §2.9–2.12, `meta/workspace.yml`.
- Fuera de alcance: los complementos de Calibre, KOReader y Zotero (siguen el tema de su anfitrión) y la ventana web de
  Raphi (`QWebEngineView`, por diseño).
