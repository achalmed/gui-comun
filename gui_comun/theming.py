"""gui_comun/theming.py — aplicación del tema (sistema / claro / oscuro) de los studios.

Desde el 2026-10-31 el tema lo genera `gui_comun.diseno` (tokens, acento y hoja QSS únicos para los tres studios);
`aplicar_tema` se conserva por contrato y delega en él. `themes_dir` ya no se lee: las hojas `.qss` por studio se
retiraron.
"""

from pathlib import Path

from PySide6.QtWidgets import QApplication

from gui_comun.diseno import MODOS, Disenador

THEMES = MODOS
_DISENADOR: Disenador | None = None   # uno por proceso (hijo de la QApplication: muere con ella)


def aplicar_tema(app: QApplication, theme: str, themes_dir: Path | None = None, acento: str = "azul") -> Disenador:
    """Aplica el diseño común y devuelve el `Disenador` (uno por aplicación; si ya hay uno, lo reutiliza)."""
    global _DISENADOR
    if _DISENADOR is None or _DISENADOR.parent() is not app:
        _DISENADOR = Disenador(app, acento=acento)
    disenador = _DISENADOR
    disenador.acento = acento
    disenador.aplicar(theme)
    return disenador


def disenador_de(app: QApplication) -> Disenador | None:
    return _DISENADOR if _DISENADOR is not None and _DISENADOR.parent() is app else None
