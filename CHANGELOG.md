---
tipo: changelog
estado: activo
---
# CHANGELOG — gui-comun

Formato: [Keep a Changelog 1.1.0](https://keepachangelog.com/es-ES/1.1.0/); versiones: [SemVer 2.0.0](https://semver.org/lang/es/).
La versión vive en `gui_comun/__init__.py` y en `pyproject.toml`. Las secciones llevan los nombres del formato
(Added · Changed · Deprecated · Removed · Fixed · Security) para que el validador las reconozca.

## [Unreleased]

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
