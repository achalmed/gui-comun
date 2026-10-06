"""
workers/function_worker.py — Worker genérico basado en QThread.

Toda operación larga de la app (escaneos, hashing, creación de enlaces,
árboles) se ejecuta a través de este worker para no bloquear la UI.

La función envuelta recibe dos callbacks estándar:
    progress_cb(percent: int, current: str)  # percent -1 = indeterminado
    cancel_cb() -> bool                      # True si el usuario canceló

y debe lanzar OperationCancelled cuando cancel_cb() sea True.
"""

import threading
import time

from PySide6.QtCore import QThread, Signal


class OperationCancelled(Exception):
    """Señala que el usuario canceló la operación en curso."""


class FunctionWorker(QThread):
    # percent (-1 = indeterminado), elemento actual (archivo, carpeta…)
    progress = Signal(int, str)
    # nivel ("info"|"warn"|"error"|"ok"), mensaje
    message = Signal(str, str)
    # resultado devuelto por la función
    result_ready = Signal(object)
    # texto del error si la función lanzó una excepción
    failed = Signal(str)
    # True si terminó por cancelación del usuario
    cancelled = Signal()

    def __init__(self, fn, *args, description: str = "", **kwargs):
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs
        self.description = description
        self._cancel_event = threading.Event()
        self.started_at: float = 0.0
        self.elapsed: float = 0.0

    # ------------------------------------------------------------------ API
    def cancel(self) -> None:
        self._cancel_event.set()

    def is_cancelled(self) -> bool:
        return self._cancel_event.is_set()

    # ------------------------------------------------------------------ run
    def run(self) -> None:
        self.started_at = time.perf_counter()
        try:
            result = self._fn(
                *self._args,
                progress_cb=self._emit_progress,
                cancel_cb=self.is_cancelled,
                message_cb=self._emit_message,
                **self._kwargs,
            )
        except OperationCancelled:
            self.elapsed = time.perf_counter() - self.started_at
            self.cancelled.emit()
            return
        except Exception as exc:  # noqa: BLE001 — el worker es la frontera
            self.elapsed = time.perf_counter() - self.started_at
            self.failed.emit(str(exc))
            return
        self.elapsed = time.perf_counter() - self.started_at
        self.result_ready.emit(result)

    def _emit_progress(self, percent: int, current: str) -> None:
        self.progress.emit(percent, current)

    def _emit_message(self, level: str, text: str) -> None:
        self.message.emit(level, text)
