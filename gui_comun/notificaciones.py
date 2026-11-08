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
"""

from __future__ import annotations

import os
import shutil

from gui_comun.qt import QObject, QProcess, Property, Signal, Slot

URGENCIA = {"error": "critical", "aviso": "normal", "positivo": "low", "informacion": "low"}
DURACION_MS = {"error": 0, "aviso": 8000, "positivo": 4000, "informacion": 4000}     # 0: hasta que se cierre
TITULO = {"error": "Error", "aviso": "Atención", "positivo": "Hecho", "informacion": ""}
ICONO_TIPO = {"error": "dialog-error", "aviso": "dialog-warning"}


def orden(texto: str, tipo: str, nombre: str, app_id: str, icono: str = "", reemplazar: int = 0) -> list[str]:
    """La orden de `notify-send` para un aviso (sin efectos: la prueba la mira)."""
    tipo = tipo if tipo in URGENCIA else "informacion"
    argv = ["notify-send", "--app-name", nombre, "--icon", ICONO_TIPO.get(tipo, icono or app_id),
            "--urgency", URGENCIA[tipo], "--expire-time", str(DURACION_MS[tipo]),
            "--hint", f"string:desktop-entry:{app_id}", "--print-id"]
    if tipo in ("informacion", "positivo"):
        argv.append("--transient")
        if reemplazar:
            argv += ["--replace-id", str(reemplazar)]
    titulo = TITULO[tipo] or nombre
    return argv + [titulo, texto]


class Notificador(QObject):
    """`notificador.notificar(texto, tipo)` desde QML o Python; devuelve False si no hay escritorio que lo muestre."""

    enviado = Signal(str, str)          # texto, tipo (la consola del studio puede anotarlo)

    def __init__(self, app_id: str, nombre: str, icono: str = "", parent=None):
        super().__init__(parent)
        self.app_id, self.nombre, self.icono = app_id, nombre, icono or app_id
        self._ultimo = 0                # el id del último aviso transitorio: el siguiente lo reemplaza
        self._procesos: list[QProcess] = []

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

    def _terminado(self, proceso: QProcess, transitorio: bool) -> None:
        salida = bytes(proceso.readAllStandardOutput()).decode(errors="replace").strip()
        if transitorio and salida.isdigit():
            self._ultimo = int(salida)
        if proceso in self._procesos:
            self._procesos.remove(proceso)
        proceso.deleteLater()
