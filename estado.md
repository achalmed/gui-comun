---
tipo: estado
estado: activo
actualizado: 2026-11-02
---
# estado.md — gui-comun

## Hecho

| fecha | qué | dónde se ve |
|---|---|---|
| 2026-11-02 | **2.2.0** con lo que pidió Huella Studio (`VistaTexto` de solo lectura en Markdown o con resaltado; `ProcessWorker` cancela al grupo de procesos): `wip/2026-11-02-qml-huella` fusionada en `main`, `v2.2.0` en el remoto público | `CHANGELOG.md` 2.2.0; `git ls-remote --tags origin` |
| 2026-11-02 | **2.2.0 (fase 5, con lo que pidió Huella Studio)**: `VistaTexto` (texto de solo lectura en Markdown o monoespaciado con resaltado, con mensaje de vacío; lo repetían Filesystem, Git y Dotfiles) y `ProcessWorker` que arranca en su propio grupo y cancela al grupo entero (cancelar `main.sh fase12 --aplicar` mataba solo a `bash`); galería y pruebas; rama `wip/2026-11-02-qml-huella`, etiqueta `v2.2.0` **local**, sin empujar hasta el visto bueno del autor | `CHANGELOG.md` 2.2.0; `docs/componentes.md`; `python3 -m gui_comun.galeria --pagina texto` |
| 2026-11-02 | **2.1.0 (fase 4, con lo que pidió Filesystem Studio)**: `ArbolDatos` (TreeView con la anatomía y los roles de `TablaDatos`, `raiz`, expansión por ratón y teclado), `CampoRuta`, `modelos.ModeloTabla` y `modelos.ModeloArbol` (hijos perezosos), anchos de columna de `TablaDatos` recordados (`claveAjustes`); galería y 33 pruebas; rama `wip/2026-11-02-qml` fusionada en `main` y empujada con la etiqueta `v2.1.0` al remoto público con el visto bueno del autor (2026-11-02) | `CHANGELOG.md` 2.1.0; `docs/componentes.md`; `python3 -m gui_comun.galeria --pagina arbol` |
| 2026-11-01 | **2.0.1**: lo que el piloto Git Studio pidió al marco (`Tareas.funcion(silenciosa=)`, `acentos.py` para que el lanzador no arrastre QtSvg, barra de progreso solo con tarea, esquema temporal) | `CHANGELOG.md` 2.0.1; etiqueta `v2.0.1` |
| 2026-11-01 | **2.0.0, fase 2 de la modernización**: módulo QML `GuiComun` (VentanaStudio, PanelNavegacion, TablaDatos, PanelDetalles, PanelInferior, BarraEstado, Mensajes, PaletaOrdenes, DialogoAjustes, MenuAcciones, BotonAccion) sobre Kirigami 6.24 + Addons 1.11 + `org.kde.desktop`, sin colores propios; núcleo Python (`nucleo`, `acciones`, `tareas`, `consola`, `modelos`, `i18n`, `qt` con PySide6/PyQt6 del sistema); la galería con `--captura` y `--esquema`; 29 pruebas (`tests/run.sh`); `widgets` congelado; hallazgos heredados del validador corregidos; F1b: el autor instaló `python3-pyside6.*` 6.10.2 | `CHANGELOG.md` 2.0.0; `docs/componentes.md`; `docs/figuras/galeria-*.png`; `python3 -m gui_comun.galeria` |
| 2026-11-01 | Fase 1 de la modernización visual de la familia (encargo del autor): auditoría de `gui-comun` y de los diez studios, inventario de lo compartido y lo divergente, sistema de diseño «escritorio KDE» (paleta, fuentes e iconos del sistema; sin hoja global) y plan E0–E6 con Git Studio de piloto; sin tocar código | `docs/modernizacion-visual-kde.md` |
| 2026-10-31 | Remoto público `achalmed/gui-comun` con la etiqueta `v1.0.0`; se instala desde GitHub (probado en un entorno limpio) | `pip install "gui-comun @ git+https://github.com/achalmed/gui-comun.git@v1.0.0"` |
| 2026-10-31 | Nace como repo y paquete propio (1.0.0), separado de `core/py-common/gui_comun` con su historia, para que Raphi Studio corra fuera del espacio de trabajo; `rutas` ya no exige `core/` | `CHANGELOG.md`; `core/docs/decisiones.md` §2.12 |

## En curso

nada en curso

## Por hacer

- 2026-11-01 · **autor**: P2, aprobar la galería (`/usr/bin/python3 -m gui_comun.galeria`; capturas en
  `docs/figuras/galeria-*.png`) como lenguaje visual de la familia; D8 de `arquitectura-qml-kirigami.md` §9 (HIG de
  KDE, documentación de Kirigami y Addons, Qt Quick, especificación freedesktop a Calibre) sigue pendiente del autor.
- 2026-11-02 · director: los `VistaTexto` propios de Filesystem (`studio/fs_app/qml/componentes/VistaTexto.qml`), Dotfiles (`studio/dotfiles_app/qml/componentes/VistaTexto.qml` y `Resaltado.qml`) y el `DialogoDiferencia` de Git pueden pasar a `GuiComun.VistaTexto` cuando cada repo se toque; no urge (funcionan).
- 2026-11-01 · director: lo que falta en 2.x (`docs/componentes.md` §3): `Grafico` (`org.kde.quickcharts`) para Simuladores; `PaginaFormulario` generada desde fichas para
  Raphi; `org.kde.kirigamiaddons.settings` cuando Kubuntu lo empaquete. Se hacen en F4 (2.1) con lo aprendido del
  piloto. Dependencias Python que faltan en el Python del sistema para los studios de F5: `openpyxl`, `matplotlib`,
  `pandas`, `coloraide`, `markdown` (Quarto, Simuladores, Lliphi): `.venv --system-site-packages` por studio o apt.
- 2026-11-01 · director: la rama `wip/2026-11-01-qml` y las etiquetas `v2.0.0` y `v2.0.1` están en el remoto público
  (empujadas con el visto bueno del autor) y la rama ya está fusionada en `main` (avance rápido, 2026-11-01). `core/validador/comun.py`
  exime los `.qml` de kebab-case (el tipo QML empieza por mayúscula); los avisos RQ-DOC-06 de `docs/arquitectura-qml-kirigami.md`
  y `docs/modernizacion-visual-kde.md` (rutas de ejemplo de otros studios) se limpian al pasar esos documentos a `hecho` en F6.

## Futuro

- Publicarlo en PyPI si un studio se distribuye fuera de GitHub.
