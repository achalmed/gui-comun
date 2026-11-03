"""gui_comun — el marco común de la familia de studios: en 2.x, el módulo QML `GuiComun` sobre Kirigami y su núcleo
Python (aplicación, acciones, tareas, consola, modelos); en 1.x, los widgets de Qt Widgets, que siguen aquí congelados
(solo correcciones) hasta que el último studio migre.

Lo importan Filesystem, Git, Quarto, Raphi, LaTeX, Simuladores, Biblioteca, Huella, Dotfiles y Lliphi Studio. Se
instala con pip (`pip install gui-comun`, o desde su repo) o, dentro del espacio de trabajo, cada studio lo encuentra
subiendo carpetas hasta el repo `gui-comun/`. Los studios QML corren con el Python del sistema, cuyo Qt trae Kirigami.
"""

__version__ = "3.2.0"
