"""widgets/tarjetas.py — piezas de las páginas de inicio de los studios: encabezado, tarjetas, cifras y mosaicos.

Todas se pintan con la hoja de `gui_comun.diseno` (clases `tarjeta`, `cifra`, `seccion`…): aquí solo hay estructura.
"""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QListWidget, QProgressBar, QScrollArea, QSizePolicy,
                               QStackedLayout, QVBoxLayout, QWidget)

from gui_comun.diseno import clase


def encabezado(titulo: str, subtitulo: str = "") -> QWidget:
    caja = QWidget()
    v = QVBoxLayout(caja)
    v.setContentsMargins(0, 0, 0, 4)
    v.setSpacing(2)
    t = QLabel(titulo)
    t.setObjectName("tituloPagina")
    v.addWidget(t)
    if subtitulo:
        s = QLabel(subtitulo)
        s.setObjectName("subtituloPagina")
        s.setWordWrap(True)
        v.addWidget(s)
    return caja


def seccion(texto: str) -> QLabel:
    return clase(QLabel(texto.upper()), "seccion")


class Tarjeta(QFrame):
    """Superficie con borde redondeado y, si se da, un título pequeño arriba."""

    def __init__(self, titulo: str = "", accion: QWidget | None = None):
        super().__init__()
        clase(self, "tarjeta")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.cuerpo = QVBoxLayout(self)
        self.cuerpo.setContentsMargins(16, 14, 16, 14)
        self.cuerpo.setSpacing(8)
        if titulo or accion:
            fila = QHBoxLayout()
            fila.setSpacing(6)
            if titulo:
                fila.addWidget(clase(QLabel(titulo), "suave"))
            fila.addStretch(1)
            if accion:
                fila.addWidget(accion)
            self.cuerpo.addLayout(fila)


class Cifra(Tarjeta):
    """Un número grande con su etiqueta y una línea de detalle; opcionalmente, una barra de progreso."""

    def __init__(self, etiqueta: str, valor: str = "—", detalle: str = "", barra: bool = False):
        super().__init__()
        self.cuerpo.setSpacing(4)
        self.lbl_etiqueta = clase(QLabel(etiqueta), "suave")
        self.lbl_valor = clase(QLabel(valor), "cifra")
        self.lbl_detalle = clase(QLabel(detalle), "tenue")
        self.lbl_detalle.setWordWrap(True)
        self.cuerpo.addWidget(self.lbl_etiqueta)
        self.cuerpo.addWidget(self.lbl_valor)
        self.barra = None
        if barra:
            self.barra = QProgressBar()
            self.barra.setRange(0, 100)
            self.barra.setTextVisible(False)
            self.cuerpo.addWidget(self.barra)
        self.cuerpo.addWidget(self.lbl_detalle)
        self.cuerpo.addStretch(1)

    def poner(self, valor: str, detalle: str | None = None, porcentaje: int | None = None) -> None:
        self.lbl_valor.setText(valor)
        if detalle is not None:
            self.lbl_detalle.setText(detalle)
        if porcentaje is not None and self.barra is not None:
            self.barra.setValue(max(0, min(100, porcentaje)))


class Mosaico(QFrame):
    """Acceso a una herramienta: icono, nombre y una línea que dice para qué sirve. Todo él es el botón."""

    activado = Signal()

    def __init__(self, icono: QIcon, titulo: str, descripcion: str, al_clic: Callable[[], None] | None = None):
        super().__init__()
        clase(self, "tarjeta")
        self.setProperty("interactiva", True)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setToolTip(descripcion)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.setMinimumHeight(84)
        fila = QHBoxLayout(self)
        fila.setContentsMargins(14, 12, 14, 12)
        fila.setSpacing(12)
        ic = QLabel()
        ic.setPixmap(icono.pixmap(QSize(22, 22), QIcon.Selected))   # «seleccionado» = el color del acento
        ic.setFixedSize(38, 38)
        ic.setAlignment(Qt.AlignCenter)
        ic.setObjectName("mosaicoIcono")
        fila.addWidget(ic, 0, Qt.AlignTop)
        textos = QVBoxLayout()
        textos.setSpacing(2)
        t = QLabel(titulo)
        t.setStyleSheet("font-weight: 600; font-size: 14px;")
        d = clase(QLabel(descripcion), "tenue")
        d.setWordWrap(True)
        d.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)   # el ancho lo pone la rejilla, no el texto
        textos.addWidget(t)
        textos.addWidget(d)
        textos.addStretch(1)
        fila.addLayout(textos, 1)
        if al_clic:
            self.activado.connect(al_clic)

    def mouseReleaseEvent(self, evento) -> None:
        if evento.button() == Qt.LeftButton and self.rect().contains(evento.position().toPoint()):
            self.activado.emit()
        super().mouseReleaseEvent(evento)

    def keyPressEvent(self, evento) -> None:
        if evento.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.activado.emit()
            return
        super().keyPressEvent(evento)


class ListaConVacio(QWidget):
    """Una lista que, cuando no tiene filas, muestra un mensaje amable en lugar de un recuadro vacío."""

    def __init__(self, texto_vacio: str):
        super().__init__()
        self.pila = QStackedLayout(self)
        self.lista = QListWidget()
        self.lista.setFrameShape(QFrame.NoFrame)
        self.lista.setStyleSheet("QListWidget { background: transparent; border: none; }")
        self.lista.setWordWrap(True)
        self.vacio = clase(QLabel(texto_vacio), "vacio")
        self.vacio.setAlignment(Qt.AlignCenter)
        self.vacio.setWordWrap(True)
        self.pila.addWidget(self.lista)
        self.pila.addWidget(self.vacio)

    def actualizar(self) -> None:
        self.pila.setCurrentWidget(self.lista if self.lista.count() else self.vacio)


def rejilla_pareja(columnas: int = 3) -> "QGridLayout":
    """Rejilla de columnas del mismo ancho (para mosaicos y cifras)."""
    from PySide6.QtWidgets import QGridLayout
    r = QGridLayout()
    r.setSpacing(12)
    for c in range(columnas):
        r.setColumnStretch(c, 1)
    return r


def pagina_desplazable(contenido: QWidget, margen: int = 28) -> QScrollArea:
    """Envuelve una página larga para que desplace en ventanas bajas, con el aire de las demás páginas."""
    contenido.layout().setContentsMargins(margen, margen - 6, margen, margen)
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setFrameShape(QFrame.NoFrame)
    area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)   # la página se adapta al ancho; solo desplaza en alto
    area.setWidget(contenido)
    return area
