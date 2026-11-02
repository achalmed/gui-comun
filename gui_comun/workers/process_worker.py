"""
workers/process_worker.py — Ejecución de procesos externos (scripts backend).

Ejecuta un comando (p. ej. el main.sh de una suite) en un QThread, transmitiendo stdout/stderr línea a línea hacia
la Consola integrada. Nada de la salida del backend se oculta.

El proceso arranca en su propia sesión (grupo de procesos) y `cancel()` avisa al grupo entero: un `main.sh` que
lanza un guion que lanza una herramienta (Huella Studio: `main.sh fase12 --aplicar` → sherlock) se detiene completo,
no solo el hijo directo (2.2.0).
"""

import os
import signal
import subprocess

from gui_comun.qt import QThread, Signal


class ProcessWorker(QThread):
    # línea de salida, es_stderr
    line = Signal(str, bool)
    # código de retorno del proceso
    finished_with_code = Signal(int)

    def __init__(self, argv: list[str], cwd: str | None = None,
                 description: str = ""):
        super().__init__()
        self.argv = argv
        self.cwd = cwd
        self.description = description
        self._proc: subprocess.Popen | None = None

    def command_line(self) -> str:
        return " ".join(self.argv)

    def cancel(self) -> None:
        """Termina el proceso y todo lo que lanzó (SIGTERM al grupo); si el grupo ya no existe, al proceso."""
        if self._proc and self._proc.poll() is None:
            try:
                os.killpg(self._proc.pid, signal.SIGTERM)
            except (ProcessLookupError, PermissionError, OSError):
                self._proc.terminate()

    def run(self) -> None:
        try:
            self._proc = subprocess.Popen(
                self.argv,
                cwd=self.cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                errors="replace",
                start_new_session=True,      # su propio grupo: cancel() lo termina entero
            )
        except OSError as exc:
            self.line.emit(f"No se pudo ejecutar el comando: {exc}", True)
            self.finished_with_code.emit(127)
            return

        # stderr se lee en un hilo auxiliar para no bloquear el pipe
        import threading

        def _pump_stderr() -> None:
            assert self._proc and self._proc.stderr
            for err_line in self._proc.stderr:
                self.line.emit(err_line.rstrip("\n"), True)

        stderr_thread = threading.Thread(target=_pump_stderr, daemon=True)
        stderr_thread.start()

        assert self._proc.stdout
        for out_line in self._proc.stdout:
            self.line.emit(out_line.rstrip("\n"), False)

        self._proc.wait()
        stderr_thread.join(timeout=2)
        self.finished_with_code.emit(self._proc.returncode)
