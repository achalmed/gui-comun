"""widgets/paleta.py — paleta de comandos (Ctrl+K): buscar y lanzar cualquier página o acción del studio por su nombre.

Filtra por coincidencia difusa (las letras en orden, no necesariamente juntas), se maneja entero con el teclado
(↑ ↓ Intro Esc) y muestra el atajo de cada comando a la derecha.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from PySide6.QtCore import QEvent, QRect, QSize, Qt
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import (QDialog, QFrame, QGraphicsDropShadowEffect, QLabel, QLineEdit, QListWidget,
                               QListWidgetItem, QStyle, QStyledItemDelegate, QVBoxLayout, QWidget)

from gui_comun import diseno

_ROL_ATAJO = Qt.UserRole + 1
_ROL_GRUPO = Qt.UserRole + 2


class _Delegado(QStyledItemDelegate):
    """Fila de la paleta: icono y título a la izquierda; grupo y atajo, tenues, a la derecha."""

    def sizeHint(self, opcion, indice) -> QSize:
        return QSize(opcion.rect.width(), 38)

    def paint(self, pintor, opcion, indice) -> None:
        t = diseno._ACTUAL or diseno.tokens("oscuro", "azul")
        pintor.save()
        r = opcion.rect.adjusted(2, 1, -2, -1)
        if opcion.state & QStyle.State_Selected:
            pintor.setRenderHint(pintor.RenderHint.Antialiasing)
            pintor.setPen(Qt.NoPen)
            c = QColor(t["acento"])
            c.setAlphaF(0.16)
            pintor.setBrush(c)
            pintor.drawRoundedRect(r, 8, 8)
        icono = indice.data(Qt.DecorationRole)
        x = r.x() + 12
        if isinstance(icono, QIcon) and not icono.isNull():
            modo = QIcon.Selected if opcion.state & QStyle.State_Selected else QIcon.Normal
            icono.paint(pintor, QRect(x, r.center().y() - 9, 18, 18), Qt.AlignCenter, modo)
        x += 30
        derecha = r.right() - 12
        atajo = indice.data(_ROL_ATAJO) or ""
        grupo = indice.data(_ROL_GRUPO) or ""
        fuente = opcion.font
        pintor.setFont(fuente)
        if atajo:
            ancho = pintor.fontMetrics().horizontalAdvance(atajo) + 14
            caja = QRect(derecha - ancho, r.center().y() - 10, ancho, 20)
            pintor.setPen(Qt.NoPen)
            pintor.setBrush(QColor(t["hover"]))
            pintor.drawRoundedRect(caja, 5, 5)
            pintor.setPen(QColor(t["texto_suave"]))
            pintor.drawText(caja, Qt.AlignCenter, atajo)
            derecha = caja.left() - 10
        if grupo:
            pintor.setPen(QColor(t["texto_tenue"]))
            ancho = pintor.fontMetrics().horizontalAdvance(grupo)
            pintor.drawText(QRect(derecha - ancho, r.y(), ancho, r.height()), Qt.AlignVCenter | Qt.AlignRight, grupo)
            derecha -= ancho + 12
        pintor.setPen(QColor(t["texto"]))
        titulo = pintor.fontMetrics().elidedText(indice.data(Qt.DisplayRole) or "", Qt.ElideRight, max(40, derecha - x))
        pintor.drawText(QRect(x, r.y(), derecha - x, r.height()), Qt.AlignVCenter | Qt.AlignLeft, titulo)
        pintor.restore()


@dataclass
class Comando:
    titulo: str
    accion: Callable[[], None]
    grupo: str = "Acciones"
    icono: QIcon = field(default_factory=QIcon)
    atajo: str = ""
    palabras: str = ""   # sinónimos que también encuentran el comando


def _puntaje(consulta: str, texto: str) -> int | None:
    """Coincidencia difusa: None si no están todas las letras en orden; más puntos si van juntas o al inicio."""
    if not consulta:
        return 0
    texto, consulta = texto.lower(), consulta.lower()
    if consulta in texto:
        return 1000 - texto.index(consulta)
    pos, puntos, anterior = 0, 0, -2
    for letra in consulta:
        pos = texto.find(letra, pos)
        if pos < 0:
            return None
        puntos += 8 if pos == anterior + 1 else 1
        anterior = pos
        pos += 1
    return puntos


class Paleta(QDialog):
    def __init__(self, padre: QWidget, comandos: Callable[[], list[Comando]]):
        super().__init__(padre, Qt.FramelessWindowHint | Qt.Popup)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self._comandos = comandos
        self._lista_actual: list[Comando] = []

        exterior = QVBoxLayout(self)
        exterior.setContentsMargins(24, 24, 24, 24)
        marco = QFrame()
        marco.setObjectName("paleta")
        sombra = QGraphicsDropShadowEffect(marco)
        sombra.setBlurRadius(40)
        sombra.setOffset(0, 12)
        sombra.setColor(Qt.black)
        marco.setGraphicsEffect(sombra)
        exterior.addWidget(marco)

        caja = QVBoxLayout(marco)
        caja.setContentsMargins(0, 0, 0, 0)
        caja.setSpacing(0)
        self.entrada = QLineEdit()
        self.entrada.setObjectName("paletaEntrada")
        self.entrada.setPlaceholderText("Buscar páginas y acciones…")
        self.entrada.textChanged.connect(self._filtrar)
        self.entrada.installEventFilter(self)
        caja.addWidget(self.entrada)
        self.lista = QListWidget()
        self.lista.setObjectName("paletaLista")
        self.lista.setIconSize(QSize(18, 18))
        self.lista.setItemDelegate(_Delegado(self.lista))
        self.lista.itemActivated.connect(self._ejecutar)
        self.lista.itemClicked.connect(self._ejecutar)
        caja.addWidget(self.lista)
        pie = QLabel("↑ ↓ para moverse  ·  Intro para abrir  ·  Esc para cerrar")
        pie.setObjectName("paletaPie")
        caja.addWidget(pie)

    def abrir(self) -> None:
        padre = self.parentWidget()
        ancho = min(640, max(480, padre.width() // 2))
        self.resize(ancho + 48, 440)
        esquina = padre.mapToGlobal(padre.rect().topLeft())
        self.move(esquina.x() + (padre.width() - self.width()) // 2, esquina.y() + max(60, padre.height() // 8))
        self.entrada.clear()
        self._filtrar("")
        self.show()
        self.entrada.setFocus()

    def _filtrar(self, consulta: str) -> None:
        candidatos = []
        for c in self._comandos():
            p = _puntaje(consulta.strip(), f"{c.titulo} {c.grupo} {c.palabras}")
            if p is not None:
                candidatos.append((p, c))
        if consulta.strip():
            candidatos.sort(key=lambda x: -x[0])
        self.lista.clear()
        self._lista_actual = [c for _, c in candidatos]
        for c in self._lista_actual:
            item = QListWidgetItem(c.icono, c.titulo)
            item.setData(_ROL_ATAJO, c.atajo)
            item.setData(_ROL_GRUPO, c.grupo)
            self.lista.addItem(item)
        if self.lista.count():
            self.lista.setCurrentRow(0)

    def _ejecutar(self, item: QListWidgetItem | None = None) -> None:
        fila = self.lista.row(item) if item is not None else self.lista.currentRow()
        if 0 <= fila < len(self._lista_actual):
            comando = self._lista_actual[fila]
            self.close()
            comando.accion()

    def eventFilter(self, objeto, evento) -> bool:
        if objeto is self.entrada and evento.type() == QEvent.KeyPress:
            tecla = evento.key()
            if tecla in (Qt.Key_Down, Qt.Key_Up):
                n = self.lista.count()
                if n:
                    paso = 1 if tecla == Qt.Key_Down else -1
                    self.lista.setCurrentRow((self.lista.currentRow() + paso) % n)
                return True
            if tecla in (Qt.Key_Return, Qt.Key_Enter):
                self._ejecutar()
                return True
            if tecla == Qt.Key_Escape:
                self.close()
                return True
        return super().eventFilter(objeto, evento)
