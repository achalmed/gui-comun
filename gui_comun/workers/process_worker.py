"""
workers/process_worker.py — Ejecución de procesos externos (scripts backend).

Ejecuta un comando (p. ej. script_proyect_tree/main.sh de SCRIPTS_LINUX) en un
QThread, transmitiendo stdout/stderr línea a línea hacia la Consola
integrada. Nada de la salida del backend se oculta.
"""

import subprocess

from PySide6.QtCore import QThread, Signal


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
        if self._proc and self._proc.poll() is None:
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
