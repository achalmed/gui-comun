"""gui_comun/tareas.py — las operaciones largas de un studio vistas desde QML: progreso, salida, fin, cancelar.

Envuelve los workers de 1.x (`FunctionWorker` para una función de Python con `progress_cb`/`cancel_cb`/`message_cb`;
`ProcessWorker` para un proceso externo con su salida línea a línea) en un `QObject` que la ventana observa: la
barra de estado muestra la tarea activa con su progreso, el panel inferior recibe cada línea y, al terminar, el
studio recibe el resultado.

    tareas = Tareas(consola)                      # la consola recibe las líneas y el registro
    tareas.funcion("Analizando repositorios…", status_service.collect_all, config, fetch=True,
                   al_terminar=self._analizado)    # al_terminar(resultado)
    tareas.proceso("sync.sh", [ruta, "-c"], cwd=carpeta, al_terminar=lambda codigo: ...)

Propiedades para QML: `activa`, `nombre`, `progreso` (−1 indeterminado, 0–100), `elemento` (lo que procesa ahora),
`cuantas` (en curso). Señal `terminada(nivel, nombre, detalle)`. Slot `cancelar()`.
"""

from __future__ import annotations

import time
from typing import Callable

from gui_comun.format import format_duration
from gui_comun.qt import QObject, Property, Signal, Slot
from gui_comun.workers.function_worker import FunctionWorker
from gui_comun.workers.process_worker import ProcessWorker


class Tareas(QObject):
    cambiada = Signal()                       # cualquier propiedad de la tarea activa
    iniciada = Signal(str)                    # nombre
    terminada = Signal(str, str, str)         # nivel (ok · warn · error), nombre, detalle
    linea = Signal(str, str)                  # texto, nivel (cmd · out · err · info · ok · warn · error)

    def __init__(self, consola=None, parent=None):
        super().__init__(parent)
        self._consola = consola
        self._vivos: list = []               # workers en marcha (si el recolector los destruyera, Qt abortaría)
        self._activo = None
        self._nombre = ""
        self._progreso = -1
        self._elemento = ""
        self._inicio = 0.0

    # ----------------------------------------------------------- lanzar
    def funcion(self, nombre: str, fn: Callable, *args, al_terminar: Callable | None = None,
                al_fallar: Callable | None = None, descripcion: str = "", silenciosa: bool = False, **kwargs) -> FunctionWorker:
        """Corre `fn(*args, progress_cb=, cancel_cb=, message_cb=, **kwargs)` en un hilo.

        `silenciosa`: una consulta breve (los detalles del elemento seleccionado) que no es «la tarea en curso»: no
        aparece en la barra de estado, no abre el panel inferior ni anota en el registro; sus mensajes sí van a la salida."""
        worker = FunctionWorker(fn, *args, description=descripcion or nombre, **kwargs)
        worker.silenciosa = silenciosa
        if not silenciosa:
            worker.progress.connect(self._progreso_de)
        worker.message.connect(lambda nivel, texto: self._linea(texto, nivel))
        worker.result_ready.connect(lambda resultado, w=worker: self._fin(w, "ok", "", al_terminar, resultado))
        worker.failed.connect(lambda error, w=worker: self._fin(w, "error", error, al_fallar, error))
        worker.cancelled.connect(lambda w=worker: self._fin(w, "warn", "cancelada", None, None))
        self._arrancar(worker, nombre)
        return worker

    def proceso(self, nombre: str, argv: list[str], cwd: str | None = None, al_terminar: Callable | None = None) -> ProcessWorker:
        """Corre un proceso externo y pasa su salida, íntegra, a la consola; `al_terminar(codigo)`."""
        worker = ProcessWorker(argv, cwd=cwd, description=nombre)
        worker.line.connect(lambda texto, es_err: self._linea(texto, "err" if es_err else "out"))
        worker.finished_with_code.connect(
            lambda codigo, w=worker: self._fin(w, "ok" if codigo == 0 else "error",
                                               "" if codigo == 0 else f"código de salida {codigo}", al_terminar, codigo))
        self._linea("$ " + " ".join(argv), "cmd")
        self._arrancar(worker, nombre)
        return worker

    def _arrancar(self, worker, nombre: str) -> None:
        self._vivos.append(worker)
        worker.inicio = time.perf_counter()
        if not getattr(worker, "silenciosa", False):
            self._activo, self._nombre, self._progreso, self._elemento = worker, nombre, -1, ""
            self._inicio = worker.inicio
            self.cambiada.emit()
            self.iniciada.emit(nombre)
            if self._consola is not None:
                self._consola.registrar("info", f"Inicia: {nombre}")
        worker.start()

    # ------------------------------------------------------------ eventos
    def _progreso_de(self, porcentaje: int, elemento: str) -> None:
        self._progreso, self._elemento = porcentaje, elemento
        self.cambiada.emit()

    def _linea(self, texto: str, nivel: str) -> None:
        self.linea.emit(texto, nivel)
        if self._consola is not None:
            self._consola.escribir(texto, nivel)

    def _fin(self, worker, nivel: str, detalle: str, retorno: Callable | None, valor) -> None:
        nombre = self._nombre if worker is self._activo else getattr(worker, "description", "")
        duracion = format_duration(time.perf_counter() - getattr(worker, "inicio", self._inicio))
        silenciosa = getattr(worker, "silenciosa", False)
        if worker in self._vivos:
            worker.wait(2000)
            self._vivos.remove(worker)
        if worker is self._activo:
            ruidosos = [w for w in self._vivos if not getattr(w, "silenciosa", False)]
            self._activo = ruidosos[-1] if ruidosos else None
            if self._activo is None:
                self._nombre, self._progreso, self._elemento = "", -1, ""
            else:
                self._nombre = getattr(self._activo, "description", "")
            self.cambiada.emit()
        if silenciosa:
            if nivel == "error" and self._consola is not None:
                self._consola.registrar("error", f"{nombre}: {detalle}")
            if retorno is not None:
                retorno(valor)
            return
        if self._consola is not None:
            self._consola.registrar(nivel, f"Termina: {nombre} ({duracion})" + (f" · {detalle}" if detalle else ""))
        if retorno is not None:
            retorno(valor)
        self.terminada.emit(nivel, nombre, detalle or duracion)

    # ---------------------------------------------------------------- QML
    @Slot()
    def cancelar(self) -> None:
        if self._activo is not None:
            self._activo.cancel()

    @Property(bool, notify=cambiada)
    def activa(self) -> bool:
        return self._activo is not None

    @Property(str, notify=cambiada)
    def nombre(self) -> str:
        return self._nombre

    @Property(int, notify=cambiada)
    def progreso(self) -> int:
        return self._progreso

    @Property(str, notify=cambiada)
    def elemento(self) -> str:
        return self._elemento

    @Property(int, notify=cambiada)
    def cuantas(self) -> int:
        return sum(1 for w in self._vivos if not getattr(w, "silenciosa", False))

    def esperar(self, ms: int = 30000) -> None:
        """Para las pruebas: espera a que terminen los hilos (el bucle de eventos debe correr aparte)."""
        for w in list(self._vivos):
            w.wait(ms)
