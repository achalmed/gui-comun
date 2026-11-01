"""widgets/avisos.py — avisos flotantes («toasts») en la esquina inferior derecha de una ventana.

No bloquean ni piden clic: dicen que algo terminó, salió mal o quedó guardado, y se van solos. Se apilan y se
reacomodan cuando la ventana cambia de tamaño. La consola sigue teniendo el detalle completo.
"""

from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QEvent, QObject, QPropertyAnimation, Qt, QTimer
from PySide6.QtWidgets import QFrame, QGraphicsOpacityEffect, QHBoxLayout, QLabel, QVBoxLayout, QWidget

# nivel → (símbolo, token de color)
_NIVELES = {"ok": ("✓", "exito"), "error": ("✕", "error"), "aviso": ("!", "aviso"), "warn": ("!", "aviso"), "info": ("i", "info")}


class _Aviso(QFrame):
    def __init__(self, padre: QWidget, titulo: str, texto: str, nivel: str, tokens: dict):
        super().__init__(padre)
        self.setObjectName("aviso")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedWidth(340)
        simbolo, token = _NIVELES.get(nivel, _NIVELES["info"])
        color = tokens.get(token, "#888")
        fila = QHBoxLayout(self)
        fila.setContentsMargins(12, 10, 14, 10)
        fila.setSpacing(10)
        marca = QLabel(simbolo)
        marca.setFixedSize(22, 22)
        marca.setAlignment(Qt.AlignCenter)
        marca.setStyleSheet(f"background: {color}; color: {tokens.get('superficie', '#fff')}; border-radius: 11px; font-weight: 800;")
        fila.addWidget(marca, 0, Qt.AlignTop)
        textos = QVBoxLayout()
        textos.setSpacing(2)
        t = QLabel(titulo)
        t.setObjectName("avisoTitulo")
        t.setWordWrap(True)
        textos.addWidget(t)
        if texto:
            d = QLabel(texto)
            d.setObjectName("avisoTexto")
            d.setWordWrap(True)
            textos.addWidget(d)
        fila.addLayout(textos, 1)
        self.efecto = QGraphicsOpacityEffect(self)
        self.efecto.setOpacity(0.0)
        self.setGraphicsEffect(self.efecto)

    def mousePressEvent(self, _evento) -> None:   # un clic lo descarta
        self.parent().property("_avisos").cerrar(self)


class Avisos(QObject):
    """Gestor de avisos de una ventana: `avisos.mostrar("Listo", "Se crearon 12 carpetas", "ok")`."""

    MARGEN = 18

    def __init__(self, ventana: QWidget, tokens: dict | None = None):
        super().__init__(ventana)
        self.ventana = ventana
        self.tokens = tokens or {}
        self._vivos: list[_Aviso] = []
        ventana.setProperty("_avisos", self)
        ventana.installEventFilter(self)

    def actualizar_tokens(self, tokens: dict) -> None:
        self.tokens = tokens

    def mostrar(self, titulo: str, texto: str = "", nivel: str = "info", duracion_ms: int = 4200) -> None:
        aviso = _Aviso(self.ventana, titulo, texto, nivel, self.tokens)
        aviso.adjustSize()
        aviso.show()
        aviso.raise_()
        self._vivos.append(aviso)
        self._reacomodar()
        anim = QPropertyAnimation(aviso.efecto, b"opacity", aviso)
        anim.setDuration(180)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()
        if nivel == "error":
            duracion_ms = max(duracion_ms, 7000)   # un error se lee con más calma
        QTimer.singleShot(duracion_ms, lambda: self.cerrar(aviso))

    def cerrar(self, aviso: _Aviso) -> None:
        if aviso not in self._vivos:
            return
        self._vivos.remove(aviso)
        anim = QPropertyAnimation(aviso.efecto, b"opacity", aviso)
        anim.setDuration(160)
        anim.setStartValue(aviso.efecto.opacity())
        anim.setEndValue(0.0)
        anim.finished.connect(aviso.deleteLater)
        anim.start()
        self._reacomodar()

    def _reacomodar(self) -> None:
        y = self.ventana.height() - self.MARGEN
        barra = getattr(self.ventana, "statusBar", None)
        if callable(barra) and self.ventana.statusBar().isVisible():
            y -= self.ventana.statusBar().height()
        for aviso in reversed(self._vivos):
            aviso.adjustSize()
            y -= aviso.height()
            aviso.move(self.ventana.width() - aviso.width() - self.MARGEN, y)
            aviso.raise_()
            y -= 10

    def eventFilter(self, objeto, evento) -> bool:
        if objeto is self.ventana and evento.type() == QEvent.Resize:
            self._reacomodar()
        return False
