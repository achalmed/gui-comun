"""comun/icons.py — acceso a los iconos SVG de un studio.

Intenta usar los recursos Qt compilados (`resources_rc.py` en la carpeta del studio, generado con pyside6-rcc
desde `resources/resources.qrc`). Si no se han compilado, carga los .svg del disco, de modo que el studio
funciona sin paso de build.
"""

from pathlib import Path
from typing import Callable

from PySide6.QtGui import QIcon

try:
    import resources_rc  # noqa: F401  (registra el prefijo :/ en Qt; vive en la carpeta del studio)
    _USE_QRC = True
except ImportError:
    _USE_QRC = False


def cargador_iconos(icons_dir: Path) -> Callable[[str], QIcon]:
    """`get_icon(nombre)` atado a la carpeta `resources/icons/` de un studio."""
    def get_icon(name: str) -> QIcon:
        if _USE_QRC:
            icon = QIcon(f":/icons/{name}.svg")
            if not icon.isNull():
                return icon
        path = Path(icons_dir) / f"{name}.svg"
        return QIcon(str(path)) if path.exists() else QIcon()
    return get_icon
