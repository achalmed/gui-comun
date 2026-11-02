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
`cuantas` (en curso), `operacion` (3.0: el estado de la tarea activa). Señal `terminada(nivel, nombre, detalle)`.
Slot `cancelar()`.

3.0, sin cambiar lo anterior:
- `operacion=` (lectura · simulacion · preparacion · escritura · instalacion · publicacion · eliminacion; ver
  `acciones.OPERACIONES`): qué clase de operación es; la barra de estado la nombra y `resultado` la lleva.
- `verificar=`: una comprobación que corre **después** de un éxito (`verificar(valor)` → `bool` o `(bool, texto)`). El
  éxito y la verificación se notifican por separado (`terminada` y luego `verificada(nombre, ok, detalle)`): que la
  orden terminara bien no prueba que el resultado sea correcto. Debe ser breve (corre en el hilo de la interfaz).
- **Errores presentables**: si una tarea falla (excepción o código distinto de 0), además de la consola, que conserva
  toda la salida, se presenta un error con descripción, causa probable, recurso, acción y detalle en `errores` (el de
  `Aplicacion`, si no se pasa otro). `error=False` lo omite (una operación por lotes que resume sus fallos al final);
  `error={"descripcion": …, "recurso": …, "accion": …}` lo redacta. Una cancelación no es un error.
- `resultado(mapa)`: {nombre, nivel, detalle, operacion, duracion, verificacion} de cada tarea no silenciosa.
Los nombres `operacion`, `verificar` y `error` quedan reservados: no llegan a la función.
"""

from __future__ import annotations

import collections
import re
import time
from typing import Callable

from gui_comun import errores as _errores
from gui_comun.format import format_duration
from gui_comun.qt import QObject, Property, Signal, Slot
from gui_comun.workers.function_worker import FunctionWorker
from gui_comun.workers.process_worker import ProcessWorker


_ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07]*\x07|\x1b[()][A-Za-z0-9]|\r")


class Tareas(QObject):
    cambiada = Signal()                       # cualquier propiedad de la tarea activa
    iniciada = Signal(str)                    # nombre
    terminada = Signal(str, str, str)         # nivel (ok · warn · error), nombre, detalle
    linea = Signal(str, str)                  # texto, nivel (cmd · out · err · info · ok · warn · error)
    verificada = Signal(str, bool, str)       # 3.0: nombre, si la comprobación pasó, qué se comprobó o qué falló
    resultado = Signal("QVariantMap")         # 3.0: {nombre, nivel, detalle, operacion, duracion, verificacion}

    def __init__(self, consola=None, parent=None, errores=None):
        super().__init__(parent)
        self._consola = consola
        self._errores = errores
        self._vivos: list = []               # workers en marcha (si el recolector los destruyera, Qt abortaría)
        self._activo = None
        self._nombre = ""
        self._progreso = -1
        self._elemento = ""
        self._inicio = 0.0
        self._operacion = ""

    # ----------------------------------------------------------- lanzar
    def funcion(self, nombre: str, fn: Callable, *args, al_terminar: Callable | None = None,
                al_fallar: Callable | None = None, descripcion: str = "", silenciosa: bool = False,
                operacion: str = "", verificar: Callable | None = None, error=None, **kwargs) -> FunctionWorker:
        """Corre `fn(*args, progress_cb=, cancel_cb=, message_cb=, **kwargs)` en un hilo.

        `silenciosa`: una consulta breve (los detalles del elemento seleccionado) que no es «la tarea en curso»: no
        aparece en la barra de estado, no abre el panel inferior ni anota en el registro; sus mensajes sí van a la salida.
        `operacion`, `verificar` y `error` (3.0): ver el docstring del módulo."""
        worker = FunctionWorker(fn, *args, description=descripcion or nombre, **kwargs)
        worker.silenciosa = silenciosa
        self._anotar(worker, operacion, verificar, error)
        if not silenciosa:
            worker.progress.connect(self._progreso_de)
        worker.message.connect(lambda nivel, texto: self._linea(texto, nivel))
        worker.result_ready.connect(lambda resultado, w=worker: self._fin(w, "ok", "", al_terminar, resultado))
        worker.failed.connect(lambda texto, w=worker: self._fin(w, "error", texto, al_fallar, texto))
        worker.cancelled.connect(lambda w=worker: self._fin(w, "warn", "cancelada", None, None))
        self._arrancar(worker, nombre)
        return worker

    def proceso(self, nombre: str, argv: list[str], cwd: str | None = None, al_terminar: Callable | None = None,
                progreso_de: Callable[[str], tuple | None] | None = None, entrada: str | None = None,
                entorno: dict | None = None, operacion: str = "", verificar: Callable | None = None,
                error=None) -> ProcessWorker:
        """Corre un proceso externo y pasa su salida, íntegra, a la consola; `al_terminar(codigo)`.

        `progreso_de(texto)` (2.3): se llama con cada línea de la salida y, si devuelve `(porcentaje, elemento)`
        (o solo `(porcentaje,)`), la barra de estado lo muestra: el progreso de un proceso que anuncia sus pasos
        («Pasada 2/3 con lualatex…») sin que el proceso sepa nada de la ventana. `None` deja el progreso como está.
        `entrada` (2.5): lo que se escribe en la entrada estándar del proceso (las respuestas a las confirmaciones de
        un guion que la ventana ya confirmó con el usuario); sin ella, la entrada está cerrada. `entorno` (2.5):
        variables que se añaden al entorno del proceso. `operacion`, `verificar` y `error` (3.0): ver el módulo."""
        worker = ProcessWorker(argv, cwd=cwd, description=nombre, entrada=entrada, entorno=entorno)
        self._anotar(worker, operacion, verificar, error)
        worker.cwd_tarea = cwd or ""

        def linea(texto: str, es_err: bool, w=worker) -> None:
            w.salida_reciente.append(_ANSI.sub("", texto))
            self._linea(texto, "err" if es_err else "out")
            if progreso_de is not None and w is self._activo:
                p = progreso_de(texto)
                if p:
                    self._progreso_de(int(p[0]), str(p[1]) if len(p) > 1 else self._elemento)
        worker.line.connect(linea)
        worker.finished_with_code.connect(
            lambda codigo, w=worker: self._fin(w, "ok" if codigo == 0 else ("warn" if w.cancelado else "error"),
                                               "" if codigo == 0 else ("cancelada" if w.cancelado else f"código de salida {codigo}"),
                                               al_terminar, codigo))
        self._linea("$ " + " ".join(argv), "cmd")
        self._arrancar(worker, nombre)
        return worker

    def _anotar(self, worker, operacion: str, verificar: Callable | None, error) -> None:
        from gui_comun.acciones import OPERACIONES
        if operacion and operacion not in OPERACIONES:
            raise ValueError(f"operación desconocida: {operacion} (una de {', '.join(OPERACIONES)})")
        worker.operacion, worker.verificar, worker.error_presentable = operacion, verificar, error
        worker.cancelado = False
        worker.salida_reciente = collections.deque(maxlen=60)          # para el detalle del error presentable

    def _arrancar(self, worker, nombre: str) -> None:
        self._vivos.append(worker)
        worker.inicio = time.perf_counter()
        if not getattr(worker, "silenciosa", False):
            self._activo, self._nombre, self._progreso, self._elemento = worker, nombre, -1, ""
            self._operacion = getattr(worker, "operacion", "")
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
        texto = _ANSI.sub("", texto)          # 2.5: los colores y controles de terminal de un guion no llegan a la consola
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
                self._nombre, self._progreso, self._elemento, self._operacion = "", -1, "", ""
            else:
                self._nombre = getattr(self._activo, "description", "")
                self._operacion = getattr(self._activo, "operacion", "")
            self.cambiada.emit()
        if silenciosa:
            if nivel == "error" and self._consola is not None:
                self._consola.registrar("error", f"{nombre}: {detalle}")
            if retorno is not None:
                retorno(valor)
            return
        if self._consola is not None:
            self._consola.registrar(nivel, f"Termina: {nombre} ({duracion})" + (f" · {detalle}" if detalle else ""))
        if nivel == "error":
            self._presentar_error(worker, nombre, detalle, valor)
        if retorno is not None:
            retorno(valor)
        self.terminada.emit(nivel, nombre, detalle or duracion)
        verificacion = None
        if nivel == "ok" and getattr(worker, "verificar", None) is not None:
            verificacion = self._verificar(worker, nombre, valor)
        self.resultado.emit({"nombre": nombre, "nivel": nivel, "detalle": detalle, "duracion": duracion,
                             "operacion": getattr(worker, "operacion", ""), "verificacion": verificacion})

    def _verificar(self, worker, nombre: str, valor) -> dict:
        """La comprobación posterior a un éxito, notificada aparte: `verificada(nombre, ok, detalle)`."""
        try:
            r = worker.verificar(valor)
            ok, texto = (bool(r[0]), str(r[1]) if len(r) > 1 else "") if isinstance(r, tuple) else (bool(r), "")
        except Exception as exc:     # noqa: BLE001 — una verificación que revienta es una verificación fallida
            ok, texto = False, f"la verificación falló: {exc}"
        if self._consola is not None:
            self._consola.registrar("ok" if ok else "warn",
                                    f"Verificación de {nombre}: " + ("correcta" if ok else "NO superada") + (f" · {texto}" if texto else ""))
        if not ok:
            self._errores_de(worker, nombre, f"«{nombre}» terminó, pero su verificación no se superó",
                             texto or "El resultado no es el esperado.", "Revise el resultado antes de darlo por bueno.", "",
                             redactar=False)
        self.verificada.emit(nombre, ok, texto)
        return {"ok": ok, "detalle": texto}

    def _presentar_error(self, worker, nombre: str, detalle: str, valor) -> None:
        if getattr(worker, "silenciosa", False) or getattr(worker, "error_presentable", None) is False:
            return
        excepcion = getattr(worker, "excepcion", None)
        if excepcion is not None:
            causa, accion = _errores.explicar(excepcion)
            import traceback
            tecnico = "".join(traceback.format_exception(type(excepcion), excepcion, excepcion.__traceback__))
            recurso = str(getattr(excepcion, "filename", "") or "")
            self._errores_de(worker, nombre, f"No se pudo completar «{nombre}»", causa or detalle, accion, tecnico, recurso)
            return
        argv = getattr(worker, "argv", None)
        if argv is not None:
            salida = "\n".join(worker.salida_reciente)
            codigo = valor if isinstance(valor, int) else -1
            causa, accion = _errores.explicar_codigo(codigo, salida)
            tecnico = "$ " + " ".join(argv) + f"\n(código de salida {codigo})\n\n" + salida
            self._errores_de(worker, nombre, f"Falló «{nombre}»", causa, accion, tecnico,
                             getattr(worker, "cwd_tarea", "") or (argv[0] if argv else ""))
            return
        self._errores_de(worker, nombre, f"No se pudo completar «{nombre}»", detalle, "", detalle)

    def _errores_de(self, worker, nombre: str, descripcion: str, causa: str, accion: str, tecnico: str,
                    recurso: str = "", redactar: bool = True) -> None:
        destino = self._errores or _errores.predeterminado()
        if destino is None or getattr(worker, "error_presentable", None) is False:
            return
        redaccion = getattr(worker, "error_presentable", None)
        if redactar and isinstance(redaccion, dict):
            descripcion = redaccion.get("descripcion", descripcion)
            causa = redaccion.get("causa", causa)
            recurso = redaccion.get("recurso", recurso)
            accion = redaccion.get("accion", accion)
        destino.presentar(descripcion, causa=causa, recurso=recurso, accion=accion, detalle=tecnico)

    # ---------------------------------------------------------------- QML
    @Slot()
    def cancelar(self) -> None:
        if self._activo is not None:
            self._activo.cancelado = True
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

    @Property(str, notify=cambiada)
    def operacion(self) -> str:
        """3.0: el estado de la tarea activa (`lectura`, `escritura`…; vacío si no lo declaró)."""
        return self._operacion

    @Property(str, notify=cambiada)
    def operacionTexto(self) -> str:
        """3.0: el estado de la tarea activa en palabras («Escritura»)."""
        from gui_comun.acciones import texto_operacion
        return texto_operacion(self._operacion)

    @Property(int, notify=cambiada)
    def cuantas(self) -> int:
        return sum(1 for w in self._vivos if not getattr(w, "silenciosa", False))

    def esperar(self, ms: int = 30000) -> None:
        """Para las pruebas: espera a que terminen los hilos (el bucle de eventos debe correr aparte)."""
        for w in list(self._vivos):
            w.wait(ms)
