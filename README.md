---
tipo: readme
estado: activo
---
# gui-comun/ — el marco común de la familia de studios PySide6 (paquete `gui_comun`)

## Qué es

Lo que comparten las aplicaciones de escritorio de la familia —Filesystem, Git, Quarto, Raphi, LaTeX y Simuladores
Studio— para verse y comportarse como una sola familia: un sistema de diseño claro/oscuro con un acento por
aplicación y el marco de la ventana. Cada studio pone sus páginas; el marco, la barra lateral, la paleta, los avisos y
la consola salen de aquí.

| pieza | qué hace |
|---|---|
| `diseno.py` | tokens claro/oscuro, acentos (verde, naranja, azul, violeta, rosa, lima, sepia, grafito, indigo, carmesi), hoja QSS generada, modo «sistema» en vivo, iconos SVG que se repintan con el tema, la losa del logo, `preparar_plataforma()` (XWayland sin aviso si el Qt no trae Wayland) |
| `widgets/marco.py` | barra lateral con marca, buscador y pie (consola, tema, preferencias), plegable a iconos; atajos Ctrl+K · Ctrl+1…9 · Ctrl+B · Ctrl+J · Ctrl+Mayús+L · Ctrl+,; `montar_studio()` para una ventana con consola acoplada |
| `widgets/paleta.py` · `avisos.py` | paleta de comandos con búsqueda difusa; avisos flotantes que se apilan |
| `widgets/tarjetas.py` · `grafico_barras.py` | encabezado, tarjetas, cifras, mosaicos, listas con estado vacío; gráfico de barras sin QtCharts |
| `widgets/console_dock.py` · `workers/` | consola con progreso y señales de tarea; workers de función y de proceso |
| `lanzador.py` | el acceso directo en el menú de aplicaciones (`.desktop` e icono con el acento) y, si el studio lo pide, su esquema de enlaces (`esquema=`) |
| `rutas.py` · `ajustes.py` · `theming.py` · `icons.py` · `ui_loader.py` · `format.py` · `history_service.py` | rutas del espacio de trabajo, ajustes, tema (contrato anterior), iconos, `.ui`, formatos e historial |

## Uso

```bash
pip install gui-comun                       # o: pip install -e ~/Documents/gui-comun (desarrollo)
python3 -c "import gui_comun; print(gui_comun.__version__)"
```

```python
from gui_comun.theming import aplicar_tema
from gui_comun.widgets.marco import montar_studio
disenador = aplicar_tema(app, "sistema", acento="verde")
marco = montar_studio(ventana, nombre="Mi Studio", subtitulo="…", logo_svg=SVG, disenador=disenador)
```

Dentro del espacio de trabajo no hace falta instalarlo: cada studio lo busca subiendo carpetas hasta `gui-comun/`.

## Límite honesto

- **Depende de PySide6** (6.6 o más; probado con 6.9) y del estilo Fusion: la hoja no se adapta a otros estilos.
- **`rutas` conoce el espacio de trabajo de su autor** (`core/env.py`); fuera de él solo sabe `DOCS_ROOT`.
- **Los acentos y la tipografía son fijos** (Inter, IBM Plex Sans o la del escritorio); no hay editor de temas.
