"""widgets/grafico_barras.py — gráfico de barras horizontales pintado a mano, con los colores del tema.

Sin QtCharts (que no viene en todas las instalaciones de PySide6): una fila por categoría, etiqueta a la izquierda,
barra con el acento y el valor a la derecha. Pensado para «las N extensiones más frecuentes» y parecidos.
"""

from __future__ import annotations

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFontMetrics, QPainter
from PySide6.QtWidgets import QSizePolicy, QWidget

from gui_comun import diseno


class GraficoBarras(QWidget):
    ALTO_FILA = 30

    def __init__(self, titulo: str = "", vacio: str = "Sin datos todavía."):
        super().__init__()
        self.titulo = titulo
        self.vacio = vacio
        self._filas: list[tuple[str, float, str]] = []
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumWidth(260)

    def poner(self, filas: list[tuple[str, float, str]]) -> None:
        """filas: (etiqueta, valor, texto del valor). Se dibujan en el orden dado."""
        self._filas = list(filas)
        self.updateGeometry()
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(360, 48 + self.ALTO_FILA * max(4, len(self._filas)))

    def paintEvent(self, _evento) -> None:
        t = diseno._ACTUAL or diseno.tokens("oscuro", "azul")
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        y = 4
        if self.titulo:
            f = self.font()
            f.setBold(True)
            p.setFont(f)
            p.setPen(QColor(t["texto"]))
            p.drawText(QRectF(0, 0, self.width(), 24), Qt.AlignLeft | Qt.AlignVCenter, self.titulo)
            y = 34
        p.setFont(self.font())
        if not self._filas:
            p.setPen(QColor(t["texto_tenue"]))
            p.drawText(QRectF(0, y, self.width(), self.height() - y), Qt.AlignCenter, self.vacio)
            return
        fm = QFontMetrics(self.font())
        ancho_etq = min(140, max(fm.horizontalAdvance(e) for e, _, _ in self._filas) + 12)
        ancho_val = max(fm.horizontalAdvance(v) for _, _, v in self._filas) + 12
        maximo = max(v for _, v, _ in self._filas) or 1
        espacio = max(20, self.width() - ancho_etq - ancho_val)
        acento = QColor(t["acento"])
        fondo = QColor(t["hover"])
        for i, (etiqueta, valor, texto) in enumerate(self._filas):
            fila = QRectF(0, y + i * self.ALTO_FILA, self.width(), self.ALTO_FILA)
            p.setPen(QColor(t["texto_suave"]))
            p.drawText(QRectF(0, fila.y(), ancho_etq - 8, fila.height()), Qt.AlignRight | Qt.AlignVCenter,
                       fm.elidedText(etiqueta, Qt.ElideMiddle, ancho_etq - 8))
            barra = QRectF(ancho_etq, fila.y() + 8, espacio, fila.height() - 16)
            p.setPen(Qt.NoPen)
            p.setBrush(fondo)
            p.drawRoundedRect(barra, 4, 4)
            lleno = QRectF(barra.x(), barra.y(), max(4.0, barra.width() * valor / maximo), barra.height())
            color = QColor(acento)
            color.setAlphaF(1.0 - 0.06 * min(i, 8))   # las primeras, más intensas
            p.setBrush(color)
            p.drawRoundedRect(lleno, 4, 4)
            p.setPen(QColor(t["texto"]))
            p.drawText(QRectF(ancho_etq + espacio + 8, fila.y(), ancho_val, fila.height()),
                       Qt.AlignLeft | Qt.AlignVCenter, texto)
        p.end()
