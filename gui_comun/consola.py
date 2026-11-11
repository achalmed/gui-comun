"""gui_comun/consola.py — la salida y el registro de un studio como modelos que QML pinta.

`Consola` tiene dos canales: `salida` (lo que escriben las operaciones: órdenes, stdout, stderr; nada se oculta) y
`registro` (los eventos de la aplicación: inicio y fin de cada tarea, avisos, errores). Cada canal es un
`ModeloConsola`: modelo de lista (roles `texto`, `nivel`, `hora`) y, para pintarlo en un `TextArea` con resaltado,
la propiedad `texto` con las últimas líneas. La ventana abre el panel inferior cuando llega algo nuevo
(`escrita`), como hace la consola de Kate.

`textoCambiado` se agrupa (4.1): avisa al instante de la primera escritura y, mientras sigan llegando, a lo sumo una
vez cada `INTERVALO_MS` (o cuatro veces lo que tardó el aviso anterior en pintarse, si es más: la ventana atiende al
usuario al menos cuatro quintas partes del tiempo), con una última al final de la ráfaga. El `TextArea` del panel
rehace y resalta el texto entero en cada aviso: con un aviso por línea, miles de líneas seguidas congelaban la
ventana durante minutos.
`texto` y `textoConHora` se calculan una vez por cambio; `lineas`, `ultimas` y el modelo de lista están siempre al día.

    consola = Consola()
    consola.escribir("$ git status", "cmd"); consola.registrar("ok", "Preferencias guardadas")
    app.exponer("consola", consola)
"""

from __future__ import annotations

import time
from datetime import datetime

from gui_comun.qt import QAbstractListModel, QByteArray, QModelIndex, QObject, Qt, QTimer, Property, Signal, Slot, rol

NIVELES = ("cmd", "out", "err", "info", "ok", "warn", "error")
_PREFIJOS = {"info": "•", "ok": "✓", "warn": "!", "error": "✗", "cmd": "", "out": "", "err": ""}


class ModeloConsola(QAbstractListModel):
    R_TEXTO, R_NIVEL, R_HORA = rol(1), rol(2), rol(3)
    INTERVALO_MS = 100              # entre dos avisos de `textoCambiado` durante una ráfaga, como mínimo
    INTERVALO_MAXIMO_MS = 2000      # y como máximo, aunque pintar cueste mucho

    textoCambiado = Signal()
    escrita = Signal(str, str)      # texto, nivel: algo nuevo

    def __init__(self, maximo: int = 5000, parent=None):
        super().__init__(parent)
        self._lineas: list[tuple[str, str, str]] = []
        self._maximo = maximo
        self._cache: dict[str, str] = {}            # texto y textoConHora, hasta el próximo cambio
        self._pendiente = False                     # hubo cambios desde el último aviso
        self._pausa = QTimer(self)                  # mientras corre, los avisos esperan
        self._pausa.setSingleShot(True)
        self._pausa.setInterval(self.INTERVALO_MS)
        self._pausa.timeout.connect(self._fin_pausa)

    def _cambio(self) -> None:
        """Un cambio en las líneas: el texto se recalcula al leerlo y el aviso sale ahora o al final de la pausa."""
        self._cache.clear()
        if self._pausa.isActive():
            self._pendiente = True
            return
        self._avisar()

    def _fin_pausa(self) -> None:
        if self._pendiente:
            self._avisar()                          # la ráfaga sigue: otra pausa antes del próximo aviso

    def _avisar(self) -> None:
        """Emite `textoCambiado` (lo que tarda es lo que tardan en pintarlo las vistas enlazadas) y abre la pausa."""
        self._pendiente = False
        inicio = time.monotonic()
        self.textoCambiado.emit()
        costo_ms = (time.monotonic() - inicio) * 1000
        self._pausa.setInterval(int(min(self.INTERVALO_MAXIMO_MS, max(self.INTERVALO_MS, 4 * costo_ms))))
        self._pausa.start()

    @Slot(str, str)
    def escribir(self, texto: str, nivel: str = "out") -> None:
        if nivel not in NIVELES:
            nivel = "out"
        hora = datetime.now().strftime("%H:%M:%S")
        nuevas = texto.split("\n") if "\n" in texto else [texto]
        fila = len(self._lineas)
        self.beginInsertRows(QModelIndex(), fila, fila + len(nuevas) - 1)
        self._lineas.extend((t, nivel, hora) for t in nuevas)
        self.endInsertRows()
        if len(self._lineas) > self._maximo:           # se recorta por delante, sin que la vista salte
            sobran = len(self._lineas) - self._maximo
            self.beginRemoveRows(QModelIndex(), 0, sobran - 1)
            del self._lineas[:sobran]
            self.endRemoveRows()
        self._cambio()
        self.escrita.emit(texto, nivel)

    @Slot()
    def limpiar(self) -> None:
        self.beginResetModel()
        self._lineas.clear()
        self.endResetModel()
        self._cache.clear()
        self._pausa.stop()                          # limpiar se ve enseguida, aunque hubiera una ráfaga
        self._pendiente = False
        self.textoCambiado.emit()

    @Property(str, notify=textoCambiado)
    def texto(self) -> str:
        if "texto" not in self._cache:
            self._cache["texto"] = "\n".join(self._formato(t, n) for t, n, _ in self._lineas)
        return self._cache["texto"]

    @Property(str, notify=textoCambiado)
    def textoConHora(self) -> str:
        if "hora" not in self._cache:
            self._cache["hora"] = "\n".join(f"{h}  {self._formato(t, n)}" for t, n, h in self._lineas)
        return self._cache["hora"]

    @Property(int, notify=textoCambiado)
    def lineas(self) -> int:
        return len(self._lineas)

    @staticmethod
    def _formato(texto: str, nivel: str) -> str:
        prefijo = _PREFIJOS.get(nivel, "")
        return f"{prefijo} {texto}" if prefijo else texto

    # ------------------------------------------------------------- modelo
    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._lineas)

    def roleNames(self):
        return {self.R_TEXTO: QByteArray(b"texto"), self.R_NIVEL: QByteArray(b"nivel"), self.R_HORA: QByteArray(b"hora"),
                Qt.ItemDataRole.DisplayRole: QByteArray(b"display")}

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._lineas):
            return None
        t, n, h = self._lineas[index.row()]
        return {Qt.ItemDataRole.DisplayRole: t, self.R_TEXTO: t, self.R_NIVEL: n, self.R_HORA: h}.get(role)

    def ultimas(self, cuantas: int = 20) -> list[tuple[str, str, str]]:
        return self._lineas[-cuantas:]


class Consola(QObject):
    """Los dos canales juntos, con la API que los controladores usan (`escribir`, `registrar`, `log`)."""

    escrita = Signal(str, str)     # algo nuevo en la salida (texto, nivel): la ventana abre el panel

    def __init__(self, parent=None):
        super().__init__(parent)
        self._salida = ModeloConsola(parent=self)
        self._registro = ModeloConsola(maximo=2000, parent=self)
        self._salida.escrita.connect(self.escrita)

    @Property(QObject, constant=True)
    def salida(self) -> ModeloConsola:
        return self._salida

    @Property(QObject, constant=True)
    def registro(self) -> ModeloConsola:
        return self._registro

    @Slot(str, str)
    def escribir(self, texto: str, nivel: str = "out") -> None:
        self._salida.escribir(texto, nivel)

    @Slot(str, str)
    def registrar(self, nivel: str, texto: str) -> None:
        self._registro.escribir(texto, nivel)

    def log(self, nivel: str, texto: str) -> None:
        """El nombre que usaban los controladores de 1.x (`ConsoleDock.log`)."""
        self.registrar(nivel, texto)
        if nivel in ("warn", "error"):
            self._salida.escribir(texto, nivel)

    @Slot()
    def limpiar(self) -> None:
        self._salida.limpiar()
        self._registro.limpiar()
