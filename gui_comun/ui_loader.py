"""gui_comun/ui_loader.py — carga de archivos .ui de Qt Designer en tiempo de ejecución.

Se usa QUiLoader (en vez de compilar con pyside6-uic) para que los .ui sigan siendo la única fuente de verdad
editable desde Qt Designer, sin paso de compilación intermedio. Cada studio crea su cargador con su carpeta `ui/`.
"""

from pathlib import Path
from typing import Callable

from PySide6.QtCore import QFile, QIODevice
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QWidget

_loader = QUiLoader()


def cargar_ui(path: Path, parent: QWidget | None = None) -> QWidget:
    """Carga el .ui de `path` y devuelve el widget raíz."""
    ui_file = QFile(str(path))
    if not ui_file.open(QIODevice.ReadOnly):
        raise FileNotFoundError(f"No se pudo abrir el archivo UI: {path}")
    try:
        widget = _loader.load(ui_file, parent)
    finally:
        ui_file.close()
    if widget is None:
        raise RuntimeError(f"QUiLoader no pudo cargar: {path}")
    return widget


def cargador(ui_dir: Path) -> Callable[..., QWidget]:
    """`load_ui(nombre, parent)` atado a la carpeta `ui/` de un studio."""
    def load_ui(filename: str, parent: QWidget | None = None) -> QWidget:
        return cargar_ui(Path(ui_dir) / filename, parent)
    return load_ui
