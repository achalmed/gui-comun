"""
widgets/console_dock.py — Consola integrada + progreso global.

Panel inferior acoplable (estilo "Output pane" de Qt Creator) con:
  • pestaña Consola : comando ejecutado, stdout, stderr y tiempos de
    toda operación (nativa o de un script backend). Nada se oculta.
  • pestaña Registro: log de eventos de la aplicación.
  • fila de progreso: porcentaje, elemento actual, tiempo estimado y
    botón Cancelar, conectados al worker activo.
"""

import html
import time

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDockWidget,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from gui_comun.format import format_duration, timestamp

_COLORS = {"info": "#7aa2f7", "ok": "#9ece6a", "warn": "#e0af68",
           "error": "#f7768e", "cmd": "#bb9af7", "out": "#c0caf5",
           "err": "#f7768e"}


class ConsoleDock(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Consola", parent)
        self.setObjectName("consoleDock")
        self.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea)

        self._worker = None
        self._progress_started = 0.0

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # ------------------------------------------------ fila de progreso
        progress_row = QHBoxLayout()
        self.lbl_task = QLabel("Sin operaciones en curso")
        self.lbl_task.setMinimumWidth(180)
        self.bar = QProgressBar()
        self.bar.setMaximumHeight(16)
        self.bar.setVisible(False)
        self.lbl_current = QLabel("")
        self.lbl_current.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.lbl_eta = QLabel("")
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setVisible(False)
        self.btn_cancel.clicked.connect(self._cancel_worker)

        progress_row.addWidget(self.lbl_task)
        progress_row.addWidget(self.bar, 2)
        progress_row.addWidget(self.lbl_current, 3)
        progress_row.addWidget(self.lbl_eta)
        progress_row.addWidget(self.btn_cancel)
        layout.addLayout(progress_row)

        # -------------------------------------------------------- pestañas
        self.tabs = QTabWidget()
        mono = QFont("Monospace")
        mono.setStyleHint(QFont.TypeWriter)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setFont(mono)
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFont(mono)

        self.tabs.addTab(self.console, "Consola")
        self.tabs.addTab(self.log_view, "Registro")
        layout.addWidget(self.tabs)

        self.setWidget(container)

    # ================================================================ logging
    def _append(self, view: QTextEdit, color: str, prefix: str,
                text: str) -> None:
        safe = html.escape(text)
        view.append(f'<span style="color:{_COLORS[color]}">'
                    f'{prefix}</span> {safe}')
        view.verticalScrollBar().setValue(
            view.verticalScrollBar().maximum())

    def log(self, level: str, text: str) -> None:
        color = level if level in _COLORS else "info"
        tag = {"info": "[INFO] ", "ok": "[OK]   ", "warn": "[WARN] ",
               "error": "[ERROR]"}.get(level, "[INFO] ")
        self._append(self.log_view, color, f"{tag} {timestamp()} —", text)

    def console_command(self, command: str) -> None:
        self._append(self.console, "cmd", "$", command)

    def console_line(self, line: str, is_stderr: bool = False) -> None:
        self._append(self.console, "err" if is_stderr else "out",
                     "‖" if is_stderr else " ", line)

    def console_note(self, text: str, level: str = "info") -> None:
        self._append(self.console, level, "•", text)

    # ============================================================== workers
    def attach_function_worker(self, worker, task_name: str) -> None:
        """Conecta un FunctionWorker a la fila de progreso y al registro."""
        self._worker = worker
        self._progress_started = time.perf_counter()
        self.lbl_task.setText(task_name)
        self.lbl_current.setText("")
        self.lbl_eta.setText("")
        self.bar.setVisible(True)
        self.bar.setRange(0, 0)  # indeterminado hasta el primer porcentaje
        self.btn_cancel.setVisible(True)
        self.console_note(f"Iniciando: {task_name}")

        worker.progress.connect(self._on_progress)
        worker.message.connect(self.log)
        worker.message.connect(
            lambda level, text: self.console_note(text, level))
        worker.result_ready.connect(lambda _res: self._finish(worker, "ok"))
        worker.failed.connect(
            lambda err: (self.console_note(f"ERROR: {err}", "error"),
                         self._finish(worker, "error")))
        worker.cancelled.connect(lambda: self._finish(worker, "warn"))

    def attach_process_worker(self, worker, task_name: str) -> None:
        """Conecta un ProcessWorker (script backend) a consola y progreso."""
        self._worker = worker
        self._progress_started = time.perf_counter()
        self.lbl_task.setText(task_name)
        self.lbl_current.setText(worker.command_line())
        self.lbl_eta.setText("")
        self.bar.setVisible(True)
        self.bar.setRange(0, 0)
        self.btn_cancel.setVisible(True)

        self.console_command(worker.command_line())
        worker.line.connect(self.console_line)
        worker.finished_with_code.connect(
            lambda code: self._finish_process(worker, code))

    def _on_progress(self, percent: int, current: str) -> None:
        if percent < 0:
            self.bar.setRange(0, 0)
        else:
            self.bar.setRange(0, 100)
            self.bar.setValue(percent)
            elapsed = time.perf_counter() - self._progress_started
            if 0 < percent < 100:
                remaining = elapsed * (100 - percent) / percent
                self.lbl_eta.setText(f"restante ≈ {format_duration(remaining)}")
            else:
                self.lbl_eta.setText("")
        self.lbl_current.setText(current)

    def _finish(self, worker, level: str) -> None:
        status = {"ok": "completada", "warn": "cancelada",
                  "error": "con errores"}[level]
        self.console_note(
            f"Operación {status} en {format_duration(worker.elapsed)}", level)
        self._reset_progress()

    def _finish_process(self, worker, code: int) -> None:
        elapsed = time.perf_counter() - self._progress_started
        level = "ok" if code == 0 else "error"
        self.console_note(
            f"Proceso terminó con código {code} en "
            f"{format_duration(elapsed)}", level)
        self._reset_progress()

    def _reset_progress(self) -> None:
        self._worker = None
        self.lbl_task.setText("Sin operaciones en curso")
        self.lbl_current.setText("")
        self.lbl_eta.setText("")
        self.bar.setVisible(False)
        self.btn_cancel.setVisible(False)

    def _cancel_worker(self) -> None:
        if self._worker is not None:
            self._worker.cancel()
            self.console_note("Cancelación solicitada por el usuario…", "warn")
