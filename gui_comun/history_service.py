"""
services/history_service.py — Historial de operaciones, reportes y deshacer.

Alimenta el Dashboard (operaciones recientes, últimos reportes) y la
página Reportes. Persistido en QSettings como JSON.
"""

import json

from PySide6.QtCore import QSettings

from gui_comun.format import timestamp

MAX_OPERATIONS = 60
MAX_REPORTS = 60


class HistoryService:
    def __init__(self):
        self._s = QSettings()

    def _load(self, key: str) -> list[dict]:
        raw = self._s.value(key, "")
        if not raw:
            return []
        try:
            data = json.loads(raw)
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, TypeError):
            return []

    def _save(self, key: str, items: list[dict], limit: int) -> None:
        self._s.setValue(key, json.dumps(items[-limit:], ensure_ascii=False))

    # ------------------------------------------------------------ operaciones
    def add_operation(self, module: str, description: str,
                      path: str | None = None) -> None:
        items = self._load("history/operations")
        items.append({
            "when": timestamp(),
            "module": module,
            "description": description,
            "path": path or "",
        })
        self._save("history/operations", items, MAX_OPERATIONS)

    def recent_operations(self, count: int = 10) -> list[dict]:
        return list(reversed(self._load("history/operations")))[:count]

    # --------------------------------------------------------------- reportes
    def add_report(self, module: str, path: str, description: str = "") -> None:
        items = self._load("history/reports")
        items.append({
            "when": timestamp(),
            "module": module,
            "path": path,
            "description": description,
        })
        self._save("history/reports", items, MAX_REPORTS)

    def reports(self) -> list[dict]:
        return list(reversed(self._load("history/reports")))

    def remove_report(self, path: str, when: str) -> None:
        items = [r for r in self._load("history/reports")
                 if not (r.get("path") == path and r.get("when") == when)]
        self._save("history/reports", items, MAX_REPORTS)

    # ------------------------------------------------- deshacer (carpetas)
    def set_undo_journal(self, created_paths: list[str]) -> None:
        self._s.setValue("undo/folders", json.dumps(created_paths))

    def undo_journal(self) -> list[str]:
        raw = self._s.value("undo/folders", "")
        if not raw:
            return []
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return []

    def clear_undo_journal(self) -> None:
        self._s.setValue("undo/folders", "[]")
