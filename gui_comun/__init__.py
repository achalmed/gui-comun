"""gui_comun — el marco común de la familia de studios: el módulo QML `GuiComun` sobre Kirigami y su núcleo Python
(aplicación, acciones, tareas, consola, modelos, errores, escritorio). Los widgets de Qt Widgets de 1.x se retiraron en
4.0.0, cuando ningún studio los usaba.

Lo importan Filesystem, Git, Quarto, Raphi, LaTeX, Simuladores, Biblioteca, Huella, Dotfiles y Lliphi Studio. Se
instala con pip (`pip install gui-comun`, o desde su repo) o, dentro del espacio de trabajo, cada studio lo encuentra
subiendo carpetas hasta el repo `gui-comun/`. Los studios QML corren con el Python del sistema, cuyo Qt trae Kirigami.
"""

__version__ = "4.0.0"
