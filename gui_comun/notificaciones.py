"""gui_comun/notificaciones.py — los avisos de un studio como notificaciones del escritorio (las de KDE Plasma).

Pedido del autor el 2026-11-08: los mensajes en línea apilados arriba del centro abrumaban y quitaban espacio. Un aviso
sin acciones («compilado en 3 s», «recargado», «configuración aplicada») va ahora al servicio de notificaciones del
escritorio (`org.freedesktop.Notifications`, el de Plasma) con el nombre y el icono del studio; solo lo que pide una
decisión (un aviso con botones: «¿guardar?», «¿recargar?») sigue en la ventana (`Mensajes.qml`).

- Se envía con `notify-send` (libnotify) en un `QProcess`, sin esperar: PySide6 no sabe pasar a D-Bus el `uint32` y
  el `as` que pide `Notify` (manda `int` y `av`, y Plasma responde «No such method»).
- Información y éxito son transitorios (no quedan en el historial de Plasma) y cada uno **reemplaza** al anterior del
  mismo studio (`-r`): nunca se apilan. Un aviso dura más; un error es crítico y queda en el historial.
- Sin `notify-send`, sin pantalla (`QT_QPA_PLATFORM=offscreen`: pruebas y capturas) o con `GUI_COMUN_SIN_NOTIFICACIONES=1`,
  `disponible` es falso y `Mensajes` vuelve a mostrar el aviso en la ventana.
- 4.1 (2026-11-18, lo pidió Git Studio): `notificarConAcciones(texto, tipo, [{clave, texto}])` pone botones en la
  notificación (`notify-send --action=clave=texto`, que espera a que se cierre e imprime la clave elegida); al pulsar uno,
  `accionElegida(id, clave)`; al cerrarse, `notificacionCerrada(id)`. No es transitoria ni reemplaza a otra: quien la
  ve tarde la encuentra en el historial mientras `notify-send` espere.
"""

from __future__ import annotations

import os
import shutil

from gui_comun.qt import QObject, QProcess, Property, Signal, Slot

URGENCIA = {"error": "critical", "aviso": "normal", "positivo": "low", "informacion": "low"}
DURACION_MS = {"error": 0, "aviso": 8000, "positivo": 4000, "informacion": 4000}     # 0: hasta que se cierre
TITULO = {"error": "Error", "aviso": "Atención", "positivo": "Hecho", "informacion": ""}
ICONO_TIPO = {"error": "dialog-error", "aviso": "dialog-warning"}


DURACION_CON_ACCIONES_MS = 15000      # 4.1: con botones, tiempo para leerlos (el error, hasta que se cierre)


def orden(texto: str, tipo: str, nombre: str, app_id: str, icono: str = "", reemplazar: int = 0,
          acciones: list | None = None) -> list[str]:
    """La orden de `notify-send` para un aviso (sin efectos: la prueba la mira). 4.1: `acciones` = [(clave, texto)]."""
    tipo = tipo if tipo in URGENCIA else "informacion"
    duracion = DURACION_MS[tipo] if not acciones or tipo == "error" else max(DURACION_MS[tipo], DURACION_CON_ACCIONES_MS)
    argv = ["notify-send", "--app-name", nombre, "--icon", ICONO_TIPO.get(tipo, icono or app_id),
            "--urgency", URGENCIA[tipo], "--expire-time", str(duracion),
            "--hint", f"string:desktop-entry:{app_id}", "--print-id"]
    if acciones:
        argv += [f"--action={clave}={texto_boton}" for clave, texto_boton in acciones]
    elif tipo in ("informacion", "positivo"):
        argv.append("--transient")
        if reemplazar:
            argv += ["--replace-id", str(reemplazar)]
    titulo = TITULO[tipo] or nombre
    return argv + [titulo, texto]


class Notificador(QObject):
    """`notificador.notificar(texto, tipo)` desde QML o Python; devuelve False si no hay escritorio que lo muestre."""

    enviado = Signal(str, str)          # texto, tipo (la consola del studio puede anotarlo)
    accionElegida = Signal(int, str)    # 4.1: id (el de notificarConAcciones), clave del botón pulsado
    notificacionCerrada = Signal(int)   # 4.1: id; tras accionElegida si se pulsó un botón

    def __init__(self, app_id: str, nombre: str, icono: str = "", parent=None):
        super().__init__(parent)
        self.app_id, self.nombre, self.icono = app_id, nombre, icono or app_id
        self._ultimo = 0                # el id del último aviso transitorio: el siguiente lo reemplaza
        self._procesos: list[QProcess] = []
        self._siguiente = 0             # 4.1: los id locales de las notificaciones con acciones

    @Property(bool, constant=True)
    def disponible(self) -> bool:
        if os.environ.get("GUI_COMUN_SIN_NOTIFICACIONES") == "1":
            return False
        if os.environ.get("QT_QPA_PLATFORM", "") in ("offscreen", "minimal"):
            return False
        if not (os.environ.get("WAYLAND_DISPLAY") or os.environ.get("DISPLAY")):
            return False
        return shutil.which("notify-send") is not None

    @Slot(str, str, result=bool)
    def notificar(self, texto: str, tipo: str = "informacion") -> bool:
        if not texto or not self.disponible:
            return False
        argv = orden(texto, tipo, self.nombre, self.app_id, self.icono, self._ultimo)
        proceso = QProcess(self)
        transitorio = "--transient" in argv
        proceso.finished.connect(lambda *_: self._terminado(proceso, transitorio))
        self._procesos.append(proceso)
        proceso.start(argv[0], argv[1:])
        self.enviado.emit(texto, tipo)
        return True

    @Slot(str, str, "QVariantList", result=int)
    def notificarConAcciones(self, texto: str, tipo: str, acciones: list) -> int:
        """Un aviso con botones (`acciones` = [{clave, texto}]); devuelve su id (> 0) o 0 si no hay escritorio."""
        botones = [(str(a.get("clave", i)), str(a.get("texto", ""))) for i, a in enumerate(acciones or [])
                   if isinstance(a, dict) and a.get("texto")]
        if not texto or not botones or not self.disponible:
            return 0
        self._siguiente += 1
        ident = self._siguiente
        argv = orden(texto, tipo, self.nombre, self.app_id, self.icono, acciones=botones)
        proceso = QProcess(self)
        proceso.finished.connect(lambda *_: self._elegida(proceso, ident, {c for c, _ in botones}))
        self._procesos.append(proceso)
        proceso.start(argv[0], argv[1:])
        self.enviado.emit(texto, tipo)
        return ident

    def _elegida(self, proceso: QProcess, ident: int, claves: set) -> None:
        lineas = bytes(proceso.readAllStandardOutput()).decode(errors="replace").split()
        elegida = next((l for l in lineas[1:] if l in claves), "")     # la primera línea es el id de Plasma
        if proceso in self._procesos:
            self._procesos.remove(proceso)
        proceso.deleteLater()
        if elegida:
            self.accionElegida.emit(ident, elegida)
        self.notificacionCerrada.emit(ident)

    def _terminado(self, proceso: QProcess, transitorio: bool) -> None:
        salida = bytes(proceso.readAllStandardOutput()).decode(errors="replace").strip()
        if transitorio and salida.isdigit():
            self._ultimo = int(salida)
        if proceso in self._procesos:
            self._procesos.remove(proceso)
        proceso.deleteLater()
