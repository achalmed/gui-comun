"""gui_comun/icons.py — acceso a los iconos SVG de un studio, repintados con el color del tema (gui_comun.diseno).

Intenta usar los recursos Qt compilados (`resources_rc.py` en la carpeta del studio, generado con pyside6-rcc
desde `resources/resources.qrc`). Si no se han compilado, carga los .svg del disco, de modo que el studio
funciona sin paso de build.
"""

from pathlib import Path
from typing import Callable

from PySide6.QtCore import QFile, QIODevice
from PySide6.QtGui import QIcon

from gui_comun.diseno import icono_svg

try:
    import resources_rc  # noqa: F401  (registra el prefijo :/ en Qt; vive en la carpeta del studio)
    _USE_QRC = True
except ImportError:
    _USE_QRC = False


def cargador_iconos(icons_dir: Path) -> Callable[[str], QIcon]:
    """`get_icon(nombre)` atado a la carpeta `resources/icons/` de un studio."""
    def get_icon(name: str) -> QIcon:
        texto = svg_de(icons_dir, name)
        return icono_svg(texto) if texto else QIcon()
    return get_icon


def svg_de(icons_dir: Path, name: str) -> str:
    """El texto del SVG (de los recursos compilados o del disco): los iconos se repintan con el tema."""
    if _USE_QRC:
        f = QFile(f":/icons/{name}.svg")
        if f.open(QIODevice.ReadOnly):
            texto = bytes(f.readAll()).decode()
            f.close()
            return texto
    path = Path(icons_dir) / f"{name}.svg"
    return path.read_text(encoding="utf-8") if path.exists() else ""
