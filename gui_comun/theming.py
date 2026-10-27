"""gui_comun/theming.py — aplicación de temas QSS (oscuro / claro / sistema) de Filesystem Studio y Git Studio.

Cada studio pasa su carpeta de temas (`resources/themes/`, con `dark.qss` y `light.qss`). «sistema» no aplica
hoja de estilos y deja que Qt use la paleta del escritorio.
"""

from pathlib import Path

from PySide6.QtWidgets import QApplication

THEMES = ("oscuro", "claro", "sistema")


def aplicar_tema(app: QApplication, theme: str, themes_dir: Path) -> None:
    if theme not in ("oscuro", "claro"):
        app.setStyleSheet("")
        return
    qss_file = Path(themes_dir) / ("dark.qss" if theme == "oscuro" else "light.qss")
    if qss_file.exists():
        app.setStyleSheet(qss_file.read_text(encoding="utf-8"))
