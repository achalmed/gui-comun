---
tipo: readme
estado: activo
---
# gui-comun/ — el marco común de la familia de studios (paquete `gui_comun` y módulo QML `GuiComun`)

## Qué es

Lo que comparten las aplicaciones de escritorio de la familia —Filesystem, Git, Quarto, Raphi, LaTeX, Simuladores,
Biblioteca, Huella, Dotfiles y Lliphi Studio— para verse y comportarse como una sola familia **y como aplicaciones de
KDE**: desde 2.0, un módulo QML sobre Kirigami 6 y Kirigami Addons con la anatomía de un espacio de trabajo
(Dolphin, Kate) y, en Python, lo que una ventana de esas necesita (la aplicación, el registro de acciones, las
tareas en segundo plano, la consola, los modelos). Cero colores, fuentes, radios o sombras propios: todo sale de
`Kirigami.Theme` y `Kirigami.Units`, así que cada studio luce con el esquema de color, las fuentes y los iconos del
usuario. Ningún nombre ni logotipo dentro de la ventana: la identidad de cada studio es el icono de su lanzador.

| pieza (2.x, QML) | qué hace |
|---|---|
| `gui_comun/nucleo.py` | `Aplicacion`: estilo `org.kde.desktop`, idioma, `QGuiApplication` con nombre de escritorio, traducciones de Qt y Kirigami, `i18n*` de KI18n para Addons, motor QML con el módulo `GuiComun`, `exponer()` (también como `studio.<nombre>`), `ejecutar()`, `capturar()`, mensaje claro si falta Kirigami |
| `gui_comun/acciones.py` | `Acciones`: cada operación una sola vez (nombre, texto, icono freedesktop, atajo con `StandardKey`, grupo, habilitada, marcable); describe el menú y la barra; búsqueda difusa para la paleta; `estandar()` con las acciones de toda ventana |
| `gui_comun/tareas.py` | `Tareas`: los workers de 1.x vistos desde QML (activa, nombre, progreso, elemento, cancelar; señales de línea y fin) |
| `gui_comun/consola.py` | `Consola`: salida y registro como modelos con `texto` para pintarlos con resaltado |
| `gui_comun/modelos.py` | `ModeloLista` (dicts con roles) y `ModeloFiltrado` (orden y filtro que QML maneja) |
| `gui_comun/i18n.py` · `gui_comun/qt.py` | las funciones `i18n*` de KI18n desde Python (gettext) · el adaptador PySide6/PyQt6 |
| `gui_comun/qml/GuiComun/` | `VentanaStudio` · `PanelNavegacion` · `TablaDatos` · `PanelDetalles` · `PanelInferior` · `BarraEstado` · `Mensajes` · `PaletaOrdenes` · `DialogoAjustes` · `MenuAcciones` · `BotonAccion` (ver `docs/componentes.md`) |
| `gui_comun/galeria/` | la galería: cada componente con datos de muestra; `--captura` y `--esquema` para verla en claro y oscuro |

| pieza (1.x, Qt Widgets; congelada) | qué hace |
|---|---|
| `gui_comun/diseno.py` · `gui_comun/theming.py` | tokens claro/oscuro con acento por studio, hoja QSS, `preparar_plataforma()` (XWayland) |
| `gui_comun/widgets/marco.py` · `gui_comun/widgets/paleta.py` · `gui_comun/widgets/avisos.py` | barra lateral con marca y atajos; paleta Ctrl+K; avisos flotantes |
| `gui_comun/widgets/tarjetas.py` · `gui_comun/widgets/grafico_barras.py` · `gui_comun/widgets/console_dock.py` | tarjetas, cifras, mosaicos, listas con vacío; gráfico de barras; consola acoplada |
| `gui_comun/workers/` · `gui_comun/lanzador.py` · `gui_comun/rutas.py` · `gui_comun/ajustes.py` · `gui_comun/icons.py` · `gui_comun/ui_loader.py` · `gui_comun/format.py` · `gui_comun/history_service.py` | workers (los envuelve `tareas`), el acceso directo del menú, rutas del espacio de trabajo, ajustes, iconos SVG, `.ui`, formatos, historial (sin cambio) |

## Uso

```bash
sudo apt install python3-pyside6.qtquick python3-pyside6.qtquickcontrols2 qml6-module-org-kde-kirigami \
                 qml6-module-org-kde-kirigamiaddons-formcard qml6-module-org-kde-desktop qml6-module-org-kde-syntaxhighlighting
pip install gui-comun                       # o: pip install -e ~/Documents/gui-comun (desarrollo)
/usr/bin/python3 -m gui_comun.galeria       # la galería, con el Qt del sistema (el que trae Kirigami)
```

```python
from gui_comun.nucleo import Aplicacion
from gui_comun.acciones import Acciones, StandardKey
app = Aplicacion("mi-studio", "Mi Studio", version="1.0", nombre_ajustes="MiStudio")
acciones = Acciones(); acciones.estandar("Mi Studio")
acciones.registrar("datos.analizar", "&Analizar", "view-refresh", StandardKey.Refresh, "Datos", al_disparar=analizar)
acciones.definir_menus([("&Archivo", ["app.salir"]), ("&Datos", ["datos.analizar"]), ("&Ver", ["ventana.navegacion", "ventana.detalles", "ventana.inferior"])])
acciones.definir_barra(["datos.analizar"])
app.exponer("acciones", acciones)
sys.exit(app.ejecutar(RUTA / "qml" / "Main.qml"))
```

```qml
import GuiComun
VentanaStudio { acciones: studio.acciones; navegacion: PanelNavegacion {…}; centro: TablaDatos {…}; detalles: PanelDetalles {…}; inferior: PanelInferior {…} }
```

Dentro del espacio de trabajo no hace falta instalarlo: cada studio lo busca subiendo carpetas hasta `gui-comun/`.
Los studios de 1.x siguen con `aplicar_tema` y `montar_studio` sin cambio.

## Verificar

```bash
tests/run.sh          # acciones, consola, tareas, modelos, i18n en proceso; cada .qml y la galería con /usr/bin/python3
```

## Límite honesto

- **2.x exige el Qt del sistema**: Kirigami es un módulo QML compilado contra él; un PySide6 de pip (Anaconda, venv)
  no lo carga. Mínimos: Qt 6.8, KDE Frameworks 6.10, Kirigami Addons 1.6; probado con Qt 6.10.2, KF 6.24, Addons 1.11.
- **`org.kde.kirigamiaddons.settings` (ConfigurationView) no está empaquetado en Kubuntu 26.04**: `DialogoAjustes`
  reproduce su anatomía sobre `Kirigami.Dialog`.
- **`rutas` conoce el espacio de trabajo de su autor** (`core/env.py`); fuera de él solo sabe `DOCS_ROOT`.
- **1.x depende de PySide6 y del estilo Fusion** y no recibe mejoras: 3.0 lo retira cuando el último studio migre.
