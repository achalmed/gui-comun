---
tipo: changelog
estado: activo
---
# CHANGELOG — gui-comun

Formato: [Keep a Changelog 1.1.0](https://keepachangelog.com/es-ES/1.1.0/); versiones: [SemVer 2.0.0](https://semver.org/lang/es/).
La versión vive en `gui_comun/__init__.py` y en `pyproject.toml`. Las secciones llevan los nombres del formato
(Added · Changed · Deprecated · Removed · Fixed · Security) para que el validador las reconozca.

## [Unreleased]

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
