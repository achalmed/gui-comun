"""gui_comun/ajustes.py — base tipada sobre QSettings que comparten Filesystem Studio y Git Studio.

Cada studio hereda `AjustesBase` en su `services/settings_service.py`, fija sus valores por defecto
(`DEFAULT_EXPORT_FORMAT`, `REPORTS_DIR`) y añade sus preferencias propias. QSettings usa la organización y
la aplicación que fija cada `main.py`, así que las preferencias de antes de la ola 4 se conservan.
"""

import json
import os
from pathlib import Path

from PySide6.QtCore import QSettings

DEFAULT_THEME = "oscuro"


class AjustesBase:
    DEFAULT_EXPORT_FORMAT = "md"
    REPORTS_DIR: Path | None = None

    def __init__(self):
        self._s = QSettings()

    # -------------------------------------------------------------- helpers
    def _get_list(self, key: str, default: list[str]) -> list[str]:
        raw = self._s.value(key, "")
        if not raw:
            return list(default)
        try:
            value = json.loads(raw)
            return value if isinstance(value, list) else list(default)
        except (json.JSONDecodeError, TypeError):
            return list(default)

    def _set_list(self, key: str, value: list[str]) -> None:
        self._s.setValue(key, json.dumps(value, ensure_ascii=False))

    # ------------------------------------------------------------- generales
    def export_format(self) -> str:
        return str(self._s.value("defaults/export_format", self.DEFAULT_EXPORT_FORMAT))

    def set_export_format(self, fmt: str) -> None:
        self._s.setValue("defaults/export_format", fmt)

    def theme(self) -> str:
        return str(self._s.value("ui/theme", DEFAULT_THEME))

    def set_theme(self, theme: str) -> None:
        self._s.setValue("ui/theme", theme)

    def icon_size(self) -> int:
        return int(self._s.value("ui/icon_size", 22))

    def set_icon_size(self, size: int) -> None:
        self._s.setValue("ui/icon_size", size)

    # ----------------------------------------------------------------- rutas
    def reports_dir(self) -> str:
        return str(self._s.value("paths/reports_dir", str(self.REPORTS_DIR or "")))

    def set_reports_dir(self, path: str) -> None:
        self._s.setValue("paths/reports_dir", path)

    def last_directory(self) -> str:
        return str(self._s.value("paths/last_directory", os.path.expanduser("~")))

    def set_last_directory(self, path: str) -> None:
        self._s.setValue("paths/last_directory", path)
