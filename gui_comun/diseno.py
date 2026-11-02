"""gui_comun/diseno.py — el sistema de diseño de los studios: tokens claro/oscuro, acento por studio y la hoja QSS.

Una sola fuente para los tres studios (Filesystem, Git y Quarto): cada uno elige su acento y el modo (claro, oscuro o
sistema); la hoja se genera aquí y no se mantiene a mano por studio. «sistema» sigue el esquema de color del escritorio
y cambia en vivo cuando el escritorio cambia.

Uso:
    from gui_comun.diseno import Disenador
    disenador = Disenador(app, acento="verde")
    disenador.aplicar("sistema")            # claro · oscuro · sistema
    disenador.tokens["texto_suave"]          # para pintar a mano (avisos, gráficos)
"""

from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtCore import QByteArray, QObject, QPoint, QRect, QRectF, QStandardPaths, Qt, Signal
from PySide6.QtGui import (QColor, QFont, QFontDatabase, QGuiApplication, QIcon, QIconEngine, QPainter, QPalette,
                           QPixmap)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication, QStyleFactory, QWidget

MODOS = ("sistema", "claro", "oscuro")

from gui_comun.acentos import ACENTOS  # noqa: E402  (el acento por studio; también lo usa el lanzador)

# --- Tokens neutros: superficies, bordes y texto ---
_BASE = {
    "claro": {
        "fondo": "#f5f6f8", "lateral": "#eef0f3", "superficie": "#ffffff", "superficie_2": "#f8f9fb",
        "hover": "#e9ecf0", "borde": "#e2e5ea", "borde_fuerte": "#cdd2da", "entrada": "#ffffff",
        "texto": "#111827", "texto_suave": "#566070", "texto_tenue": "#8b93a1",
        "exito": "#16a34a", "aviso": "#d97706", "error": "#dc2626", "info": "#2563eb",
        "consola": "#fbfbfc", "sombra": "rgba(15, 23, 42, 0.10)",
    },
    "oscuro": {
        "fondo": "#0e1014", "lateral": "#121419", "superficie": "#171a20", "superficie_2": "#1c2027",
        "hover": "#22262e", "borde": "#262a33", "borde_fuerte": "#353b46", "entrada": "#111318",
        "texto": "#e7e9ee", "texto_suave": "#a0a8b6", "texto_tenue": "#6c7482",
        "exito": "#4ade80", "aviso": "#fbbf24", "error": "#f87171", "info": "#60a5fa",
        "consola": "#0b0d10", "sombra": "rgba(0, 0, 0, 0.45)",
    },
}

# Fuentes preferidas, en orden; la primera instalada gana (la del escritorio si ninguna está)
FUENTES = ("Inter", "Inter Variable", "IBM Plex Sans", "Noto Sans", "Cantarell")
FUENTES_MONO = ("JetBrains Mono", "IBM Plex Mono", "Fira Code", "Noto Sans Mono", "DejaVu Sans Mono")


def preparar_plataforma() -> None:
    """Antes de crear la QApplication: si este Qt no trae el plugin de Wayland (el de Anaconda no lo trae), ir directo a
    XWayland (`xcb`). Sin esto Qt prueba Wayland, avisa «Could not find the Qt platform plugin "wayland"» y recién
    entonces cae a `xcb`. Respeta una plataforma fijada a mano que no sea Wayland."""
    import os
    from PySide6.QtCore import QLibraryInfo
    actual = os.environ.get("QT_QPA_PLATFORM", "")
    if actual and not actual.startswith("wayland"):
        return
    if os.environ.get("XDG_SESSION_TYPE") != "wayland" and not os.environ.get("WAYLAND_DISPLAY"):
        return
    plataformas = Path(QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath)) / "platforms"
    if not any(plataformas.glob("libqwayland*")):
        os.environ["QT_QPA_PLATFORM"] = "xcb"


def _mezclar(c1: str, c2: str, t: float) -> str:
    """Color entre c1 y c2 (t = 0 → c1, t = 1 → c2)."""
    a, b = QColor(c1), QColor(c2)
    return QColor(round(a.red() + (b.red() - a.red()) * t), round(a.green() + (b.green() - a.green()) * t),
                  round(a.blue() + (b.blue() - a.blue()) * t)).name()


def _rgba(color: str, alfa: float) -> str:
    c = QColor(color)
    return f"rgba({c.red()}, {c.green()}, {c.blue()}, {alfa:.2f})"


def tokens(modo: str, acento: str) -> dict[str, str]:
    """Los tokens resueltos de un modo concreto (claro u oscuro) con el acento elegido."""
    t = dict(_BASE[modo])
    a = ACENTOS.get(acento, ACENTOS["azul"])[modo]
    t["acento"] = a
    t["acento_hover"] = _mezclar(a, "#ffffff" if modo == "oscuro" else "#000000", 0.12)
    t["acento_presion"] = _mezclar(a, "#000000", 0.18)
    t["acento_suave"] = _rgba(a, 0.16 if modo == "oscuro" else 0.10)
    t["acento_borde"] = _rgba(a, 0.45)
    t["sobre_acento"] = "#0b0d10" if modo == "oscuro" else "#ffffff"
    t["seleccion"] = _rgba(a, 0.30 if modo == "oscuro" else 0.20)
    t["modo"] = modo
    return t


def fuente_disponible(candidatas: tuple[str, ...]) -> str | None:
    familias = set(QFontDatabase.families())
    return next((f for f in candidatas if f in familias), None)


def fuente_mono() -> QFont:
    f = QFont(fuente_disponible(FUENTES_MONO) or "Monospace")
    f.setStyleHint(QFont.TypeWriter)
    f.setPointSizeF(9.5)
    return f


def _iconos_estilo(t: dict[str, str]) -> dict[str, str]:
    """Flechas y marcas de la hoja como SVG en la caché del usuario (QSS solo acepta url() a archivos)."""
    base = Path(QStandardPaths.writableLocation(QStandardPaths.GenericCacheLocation)) / "gui_comun" / t["modo"]
    base.mkdir(parents=True, exist_ok=True)
    trazo = 'fill="none" stroke-linecap="round" stroke-linejoin="round"'
    svgs = {
        "abajo": f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><path d="M4 6l4 4 4-4" stroke="{t["texto_suave"]}" stroke-width="1.6" {trazo}/></svg>',
        "arriba": f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><path d="M4 10l4-4 4 4" stroke="{t["texto_suave"]}" stroke-width="1.6" {trazo}/></svg>',
        "derecha": f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><path d="M6 4l4 4-4 4" stroke="{t["texto_tenue"]}" stroke-width="1.6" {trazo}/></svg>',
        "marca": f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><path d="M3.5 8.5l3 3 6-7" stroke="{t["sobre_acento"]}" stroke-width="2" {trazo}/></svg>',
        "punto": f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><circle cx="8" cy="8" r="3.2" fill="{t["sobre_acento"]}"/></svg>',
        "guion": f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><path d="M4 8h8" stroke="{t["sobre_acento"]}" stroke-width="2" {trazo}/></svg>',
    }
    rutas = {}
    for nombre, svg in svgs.items():
        p = base / f"{nombre}-{t['acento'].lstrip('#')}.svg"
        if not p.exists() or p.read_text(encoding="utf-8") != svg:
            p.write_text(svg, encoding="utf-8")
        rutas[nombre] = p.as_posix()
    return rutas


def hoja(t: dict[str, str]) -> str:
    """La hoja QSS completa a partir de los tokens."""
    i = _iconos_estilo(t)
    return f"""
* {{ outline: 0; }}
QMainWindow, QDialog {{ background: {t['fondo']}; color: {t['texto']}; }}
QWidget {{ color: {t['texto']}; font-size: 13px; }}
QStackedWidget, QScrollArea, QScrollArea > QWidget > QWidget, QTabWidget > QStackedWidget > QWidget {{ background: transparent; }}
QLabel {{ background: transparent; }}
QToolTip {{ background: {t['superficie_2']}; color: {t['texto']}; border: 1px solid {t['borde_fuerte']}; border-radius: 6px; padding: 5px 8px; }}

/* --- Barra lateral --- */
QFrame#navLateral {{ background: {t['lateral']}; border: none; border-right: 1px solid {t['borde']}; }}
QLabel#navNombre {{ font-size: 15px; font-weight: 700; }}
QLabel#navSubtitulo {{ color: {t['texto_tenue']}; font-size: 11px; }}
QPushButton#navBuscar {{ background: {t['superficie']}; border: 1px solid {t['borde']}; border-radius: 8px; color: {t['texto_tenue']};
    text-align: left; padding: 7px 10px; font-size: 12px; }}
QPushButton#navBuscar:hover {{ border-color: {t['borde_fuerte']}; color: {t['texto_suave']}; }}
QLabel#navBuscarTexto {{ color: {t['texto_tenue']}; font-size: 12px; }}
QLabel#navAtajo {{ color: {t['texto_tenue']}; font-size: 11px; background: {t['hover']}; border-radius: 4px; padding: 1px 5px; }}
QListWidget#sidebar {{ background: transparent; border: none; padding: 4px 0; }}
QListWidget#sidebar::item {{ color: {t['texto_suave']}; border-radius: 8px; padding: 8px 10px; margin: 1px 8px; border: none; }}
QListWidget#sidebar::item:hover {{ background: {t['hover']}; color: {t['texto']}; }}
QListWidget#sidebar::item:selected {{ background: {t['acento_suave']}; color: {t['acento']}; font-weight: 600; }}
QToolButton#navPie {{ background: transparent; border: none; border-radius: 8px; padding: 6px; }}
QToolButton#navPie:hover {{ background: {t['hover']}; }}
QToolButton#navPie:checked {{ background: {t['acento_suave']}; }}

/* --- Títulos de página --- */
QLabel#lblTitle, QLabel#tituloPagina {{ font-size: 22px; font-weight: 700; padding: 2px 0 0 0; }}
QLabel#lblSubtitle, QLabel#subtituloPagina, QLabel#descripcionPagina {{ color: {t['texto_suave']}; font-size: 13px; padding-bottom: 6px; }}
QLabel[clase="seccion"] {{ color: {t['texto_tenue']}; font-size: 11px; font-weight: 700; letter-spacing: 0.6px; }}
QLabel[clase="tenue"] {{ color: {t['texto_tenue']}; }}
QLabel[clase="suave"] {{ color: {t['texto_suave']}; }}
QLabel[clase="cifra"] {{ font-size: 28px; font-weight: 700; }}
QLabel[clase="vacio"] {{ color: {t['texto_tenue']}; font-size: 13px; padding: 18px; }}

/* --- Tarjetas y grupos --- */
QFrame[clase="tarjeta"] {{ background: {t['superficie']}; border: 1px solid {t['borde']}; border-radius: 12px; }}
QFrame[clase="tarjeta"]:hover[interactiva="true"] {{ border-color: {t['acento_borde']}; background: {t['superficie_2']}; }}
QGroupBox {{ background: {t['superficie']}; border: 1px solid {t['borde']}; border-radius: 12px; margin-top: 26px;
    padding: 14px 12px 12px 12px; font-weight: 600; }}
QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left; left: 4px; top: 2px; padding: 0 2px;
    color: {t['texto_suave']}; font-size: 12px; font-weight: 600; }}

/* --- Botones --- */
QPushButton {{ background: {t['superficie']}; color: {t['texto']}; border: 1px solid {t['borde_fuerte']}; border-radius: 8px;
    padding: 7px 14px; min-height: 18px; font-weight: 500; }}
QPushButton:hover {{ background: {t['hover']}; }}
QPushButton:pressed {{ background: {t['borde']}; }}
QPushButton:disabled {{ color: {t['texto_tenue']}; background: {t['superficie_2']}; border-color: {t['borde']}; }}
QPushButton:default, QPushButton[variante="primario"] {{ background: {t['acento']}; color: {t['sobre_acento']}; border: 1px solid {t['acento']}; font-weight: 600; }}
QPushButton:default:hover, QPushButton[variante="primario"]:hover {{ background: {t['acento_hover']}; border-color: {t['acento_hover']}; }}
QPushButton:default:pressed, QPushButton[variante="primario"]:pressed {{ background: {t['acento_presion']}; }}
QPushButton[variante="primario"]:disabled {{ background: {t['acento_suave']}; color: {t['texto_tenue']}; border-color: transparent; }}
QPushButton[variante="fantasma"] {{ background: transparent; border-color: transparent; color: {t['texto_suave']}; }}
QPushButton[variante="fantasma"]:hover {{ background: {t['hover']}; color: {t['texto']}; }}
QPushButton[variante="peligro"] {{ color: {t['error']}; border-color: {_rgba(t['error'], 0.45)}; }}
QPushButton[variante="peligro"]:hover {{ background: {_rgba(t['error'], 0.10)}; }}
QPushButton[variante="mosaico"] {{ background: {t['superficie']}; border: 1px solid {t['borde']}; border-radius: 12px; text-align: left;
    padding: 14px 16px; font-size: 14px; font-weight: 600; }}
QPushButton[variante="mosaico"]:hover {{ border-color: {t['acento_borde']}; background: {t['superficie_2']}; }}
QToolButton {{ background: transparent; border: 1px solid transparent; border-radius: 8px; padding: 5px; }}
QToolButton:hover {{ background: {t['hover']}; }}
QToolButton:checked {{ background: {t['acento_suave']}; }}

/* --- Entradas --- */
QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit {{ background: {t['entrada']};
    border: 1px solid {t['borde_fuerte']}; border-radius: 8px; padding: 6px 10px; selection-background-color: {t['seleccion']};
    selection-color: {t['texto']}; }}
QPlainTextEdit, QTextEdit {{ padding: 6px; }}
QLineEdit:hover, QSpinBox:hover, QComboBox:hover, QDoubleSpinBox:hover {{ border-color: {t['texto_tenue']}; }}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
    border: 1px solid {t['acento']}; }}
QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled {{ color: {t['texto_tenue']}; background: {t['superficie_2']}; }}
QLineEdit[clase="busqueda"] {{ border-radius: 18px; padding-left: 14px; }}
QComboBox {{ padding-right: 28px; }}
QComboBox::drop-down {{ border: none; width: 26px; }}
QComboBox::down-arrow {{ image: url({i['abajo']}); width: 14px; height: 14px; }}
QComboBox QAbstractItemView {{ background: {t['superficie']}; border: 1px solid {t['borde_fuerte']}; border-radius: 8px; padding: 4px;
    selection-background-color: {t['acento_suave']}; selection-color: {t['texto']}; }}
QSpinBox, QDoubleSpinBox {{ padding-right: 22px; }}
QSpinBox::up-button, QDoubleSpinBox::up-button {{ subcontrol-position: top right; width: 20px; border: none; background: transparent; }}
QSpinBox::down-button, QDoubleSpinBox::down-button {{ subcontrol-position: bottom right; width: 20px; border: none; background: transparent; }}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{ image: url({i['arriba']}); width: 12px; height: 12px; }}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{ image: url({i['abajo']}); width: 12px; height: 12px; }}

QCheckBox, QRadioButton {{ spacing: 8px; background: transparent; }}
QCheckBox::indicator, QRadioButton::indicator {{ width: 16px; height: 16px; border: 1.5px solid {t['borde_fuerte']}; background: {t['entrada']}; }}
QCheckBox::indicator {{ border-radius: 5px; }}
QRadioButton::indicator {{ border-radius: 9px; }}
QCheckBox::indicator:hover, QRadioButton::indicator:hover {{ border-color: {t['acento']}; }}
QCheckBox::indicator:checked {{ background: {t['acento']}; border-color: {t['acento']}; image: url({i['marca']}); }}
QCheckBox::indicator:indeterminate {{ background: {t['acento']}; border-color: {t['acento']}; image: url({i['guion']}); }}
QRadioButton::indicator:checked {{ background: {t['acento']}; border-color: {t['acento']}; image: url({i['punto']}); }}

/* --- Tablas, árboles y listas --- */
QTableView, QTreeView, QListView, QTableWidget, QTreeWidget, QListWidget {{ background: {t['superficie']}; border: 1px solid {t['borde']};
    border-radius: 10px; alternate-background-color: {t['superficie_2']}; gridline-color: transparent;
    selection-background-color: {t['acento_suave']}; selection-color: {t['texto']}; }}
QTableView::item, QTreeView::item, QListView::item {{ padding: 5px 6px; border: none; }}
QTableView::item:hover, QTreeView::item:hover, QListView::item:hover {{ background: {t['hover']}; }}
QTableView::item:selected, QTreeView::item:selected, QListView::item:selected {{ background: {t['acento_suave']}; color: {t['texto']}; }}
QTreeView::branch {{ background: transparent; }}
QTreeView::branch:has-children:!has-siblings:closed, QTreeView::branch:closed:has-children:has-siblings {{ image: url({i['derecha']}); }}
QTreeView::branch:open:has-children:!has-siblings, QTreeView::branch:open:has-children:has-siblings {{ image: url({i['abajo']}); }}
QHeaderView {{ background: transparent; border: none; }}
QHeaderView::section {{ background: {t['superficie_2']}; color: {t['texto_suave']}; border: none; border-bottom: 1px solid {t['borde']};
    padding: 8px 8px; font-weight: 600; font-size: 12px; }}
QHeaderView::section:first {{ border-top-left-radius: 10px; }}
QHeaderView::section:last {{ border-top-right-radius: 10px; }}
QTableCornerButton::section {{ background: {t['superficie_2']}; border: none; }}

/* --- Pestañas --- */
QTabWidget::pane {{ border: none; background: transparent; top: -1px; }}
QTabBar {{ background: transparent; }}
QTabBar::tab {{ background: transparent; color: {t['texto_suave']}; padding: 8px 14px; margin-right: 4px; border: none;
    border-bottom: 2px solid transparent; font-weight: 500; }}
QTabBar::tab:hover {{ color: {t['texto']}; }}
QTabBar::tab:selected {{ color: {t['texto']}; border-bottom: 2px solid {t['acento']}; font-weight: 600; }}

/* --- Barras de desplazamiento --- */
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
QScrollBar::handle {{ background: {t['borde_fuerte']}; border-radius: 3px; min-height: 28px; min-width: 28px; }}
QScrollBar::handle:hover {{ background: {t['texto_tenue']}; }}
QScrollBar::add-line, QScrollBar::sub-line, QScrollBar::add-page, QScrollBar::sub-page {{ background: none; border: none; width: 0; height: 0; }}

/* --- Progreso, divisores, menús y barra de estado --- */
QProgressBar {{ background: {t['hover']}; border: none; border-radius: 4px; text-align: center; color: transparent; max-height: 8px; }}
QProgressBar::chunk {{ background: {t['acento']}; border-radius: 4px; }}
QProgressBar[clase="con-texto"] {{ max-height: 20px; color: {t['texto']}; font-size: 11px; border-radius: 6px; }}
QSplitter::handle {{ background: {t['borde']}; }}
QSplitter::handle:horizontal {{ width: 1px; }}
QSplitter::handle:vertical {{ height: 1px; }}
QMenuBar {{ background: {t['fondo']}; border-bottom: 1px solid {t['borde']}; padding: 2px 4px; }}
QMenuBar::item {{ background: transparent; padding: 5px 10px; border-radius: 6px; color: {t['texto_suave']}; }}
QMenuBar::item:selected {{ background: {t['hover']}; color: {t['texto']}; }}
QMenu {{ background: {t['superficie']}; border: 1px solid {t['borde_fuerte']}; border-radius: 10px; padding: 6px; }}
QMenu::item {{ padding: 6px 24px 6px 12px; border-radius: 6px; }}
QMenu::item:selected {{ background: {t['acento_suave']}; color: {t['texto']}; }}
QMenu::separator {{ height: 1px; background: {t['borde']}; margin: 5px 8px; }}
QStatusBar {{ background: {t['lateral']}; border-top: 1px solid {t['borde']}; color: {t['texto_suave']}; font-size: 12px; }}
QStatusBar::item {{ border: none; }}
QDockWidget {{ titlebar-close-icon: none; color: {t['texto_suave']}; font-weight: 600; }}
QDockWidget::title {{ background: {t['lateral']}; padding: 7px 12px; border-top: 1px solid {t['borde']}; }}
QToolBar {{ background: {t['fondo']}; border: none; border-bottom: 1px solid {t['borde']}; spacing: 4px; padding: 4px 8px; }}

/* --- Consola --- */
QTextEdit[clase="consola"], QPlainTextEdit[clase="consola"] {{ background: {t['consola']}; border: 1px solid {t['borde']}; border-radius: 10px;
    padding: 8px; }}

/* --- Paleta de comandos y avisos --- */
QFrame#paleta {{ background: {t['superficie']}; border: 1px solid {t['borde_fuerte']}; border-radius: 14px; }}
QLineEdit#paletaEntrada {{ background: transparent; border: none; border-bottom: 1px solid {t['borde']}; border-radius: 0;
    padding: 14px 16px; font-size: 15px; }}
QListWidget#paletaLista {{ background: transparent; border: none; padding: 6px; }}
QListWidget#paletaLista::item {{ padding: 8px 10px; border-radius: 8px; margin: 1px 0; }}
QListWidget#paletaLista::item:selected {{ background: {t['acento_suave']}; }}
QLabel#paletaPie {{ color: {t['texto_tenue']}; font-size: 11px; padding: 8px 14px; border-top: 1px solid {t['borde']}; }}
QFrame#aviso {{ background: {t['superficie']}; border: 1px solid {t['borde_fuerte']}; border-radius: 12px; }}
QLabel#avisoTitulo {{ font-weight: 600; }}
QLabel#avisoTexto {{ color: {t['texto_suave']}; font-size: 12px; }}
QPushButton#chipTarea {{ background: transparent; border: none; border-radius: 6px; padding: 2px 8px; color: {t['texto_suave']}; font-size: 12px; }}
QLabel#mosaicoIcono {{ background: {t['acento_suave']}; border-radius: 10px; }}
QPushButton#chipTarea:hover {{ background: {t['hover']}; color: {t['texto']}; }}
"""


class Disenador(QObject):
    """Aplica el diseño a la aplicación y lo mantiene al día si el modo es «sistema»."""

    cambiado = Signal(dict)   # los tokens nuevos, cada vez que cambia el modo efectivo

    def __init__(self, app: QApplication, acento: str = "azul"):
        # no se guarda `app`: una referencia fuerte la haría sobrevivir a main() y Python la destruiría al final,
        # después de sus ventanas (violación de segmento al salir); se pide con QApplication.instance()
        super().__init__(app)
        app.aboutToQuit.connect(self._soltar)
        self.acento = acento
        self.modo = "sistema"
        self.tokens: dict[str, str] = {}
        app.setStyle(QStyleFactory.create("Fusion"))   # base uniforme: la hoja no depende del estilo del escritorio
        familia = fuente_disponible(FUENTES)
        fuente = QFont(familia) if familia else app.font()
        fuente.setPointSizeF(max(fuente.pointSizeF(), 10.0))
        app.setFont(fuente)
        estilo = QGuiApplication.styleHints()
        if hasattr(estilo, "colorSchemeChanged"):
            estilo.colorSchemeChanged.connect(lambda _esquema: self.modo == "sistema" and self._pintar())

    def _soltar(self) -> None:
        """Al salir, suelta a quien escucha `cambiado` (ventanas, consolas): si no, sus envoltorios Python sobreviven a
        la QApplication y se destruyen después de ella."""
        try:
            self.cambiado.disconnect()
        except (RuntimeError, TypeError):
            pass
        from gui_comun import theming
        if theming._DISENADOR is self:
            theming._DISENADOR = None

    def modo_efectivo(self) -> str:
        if self.modo in ("claro", "oscuro"):
            return self.modo
        estilo = QGuiApplication.styleHints()
        esquema = estilo.colorScheme() if hasattr(estilo, "colorScheme") else Qt.ColorScheme.Unknown
        if esquema == Qt.ColorScheme.Light:
            return "claro"
        if esquema == Qt.ColorScheme.Dark:
            return "oscuro"
        return "oscuro" if QApplication.instance().palette().color(QPalette.Window).lightness() < 128 else "claro"

    def aplicar(self, modo: str) -> None:
        # los nombres viejos de los ajustes («dark», «light», «system») siguen valiendo
        self.modo = {"dark": "oscuro", "light": "claro", "system": "sistema"}.get(modo, modo)
        if self.modo not in MODOS:
            self.modo = "sistema"
        self._pintar()

    def alternar(self) -> str:
        """Pasa de claro a oscuro y viceversa (fija el modo; deja de seguir al sistema)."""
        self.aplicar("claro" if self.modo_efectivo() == "oscuro" else "oscuro")
        return self.modo

    def _pintar(self) -> None:
        self.tokens = tokens(self.modo_efectivo(), self.acento)
        _ACTUAL.clear()
        _ACTUAL.update(self.tokens)
        t = self.tokens
        paleta = QPalette()
        for rol, color in ((QPalette.Window, t["fondo"]), (QPalette.WindowText, t["texto"]), (QPalette.Base, t["entrada"]),
                           (QPalette.AlternateBase, t["superficie_2"]), (QPalette.Text, t["texto"]),
                           (QPalette.Button, t["superficie"]), (QPalette.ButtonText, t["texto"]),
                           (QPalette.Highlight, t["acento"]), (QPalette.HighlightedText, t["sobre_acento"]),
                           (QPalette.ToolTipBase, t["superficie_2"]), (QPalette.ToolTipText, t["texto"]),
                           (QPalette.PlaceholderText, t["texto_tenue"]), (QPalette.Link, t["acento"])):
            paleta.setColor(rol, QColor(color))
        paleta.setColor(QPalette.Disabled, QPalette.Text, QColor(t["texto_tenue"]))
        paleta.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(t["texto_tenue"]))
        app = QApplication.instance()
        app.setPalette(paleta)
        app.setStyleSheet(hoja(t))
        self.cambiado.emit(t)


# --- Iconos de línea (trazos de 24×24 al estilo Lucide) para los controles del marco ---
_TRAZOS = {
    "sol": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    "luna": '<path d="M20.5 14.5A8.5 8.5 0 1 1 9.5 3.5a7 7 0 0 0 11 11z"/>',
    "terminal": '<rect x="3" y="4" width="18" height="16" rx="3"/><path d="M7 9l3 3-3 3M13 15h4"/>',
    "ajustes": '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>',
    "panel": '<rect x="3" y="4" width="18" height="16" rx="3"/><path d="M9 4v16"/>',
    "buscar": '<circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 16v-4M12 8h.01"/>',
    "cargando": '<path d="M21 12a9 9 0 1 1-6.2-8.6"/>',
    "inicio": '<path d="M3 11l9-7 9 7"/><path d="M5 10v10h14V10"/><path d="M10 20v-6h4v6"/>',
    "documento": '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h6"/>',
    "pdf": '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/><path d="M8 16v-4h1.5a1.5 1.5 0 0 1 0 3H8M13 12v4h1a2 2 0 0 0 0-4z"/>',
    "imagen": '<rect x="3" y="4" width="18" height="16" rx="3"/><circle cx="9" cy="10" r="2"/><path d="M21 16l-5-5-9 9"/>',
    "audio": '<path d="M9 18V6l11-2v12"/><circle cx="6" cy="18" r="3"/><circle cx="17" cy="16" r="3"/>',
    "video": '<rect x="2" y="6" width="14" height="12" rx="2"/><path d="M16 10l6-3v10l-6-3"/>',
    "archivo": '<path d="M21 8v12a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V8"/><rect x="2" y="3" width="20" height="5" rx="1"/><path d="M10 12h4"/>',
    "descarga": '<path d="M12 3v12M7 10l5 5 5-5"/><path d="M5 21h14"/>',
    "receta": '<path d="M9 5h11M9 12h11M9 19h11"/><path d="M4 5l1 1 2-2M4 12l1 1 2-2M4 19l1 1 2-2"/>',
    "sistema": '<rect x="4" y="4" width="16" height="16" rx="2"/><path d="M9 9h6v6H9zM9 1v3M15 1v3M9 20v3M15 20v3M20 9h3M20 14h3M1 9h3M1 14h3"/>',
    "carpeta": '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    "subtitulos": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M7 15h4M13 15h4M7 11h10"/>',
    "texto": '<path d="M4 6h16M4 12h16M4 18h10"/>',
    "volver": '<path d="M15 18l-6-6 6-6"/>',
    "libro": '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V3H6.5A2.5 2.5 0 0 0 4 5.5z"/><path d="M4 19.5A2.5 2.5 0 0 0 6.5 22H20v-5"/>',
    "sincronizar": '<path d="M20 11a8 8 0 0 0-14.3-4.9L4 8M4 4v4h4M4 13a8 8 0 0 0 14.3 4.9L20 16M20 20v-4h-4"/>',
    "candado": '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    "bandeja": '<path d="M22 12h-6l-2 3h-4l-2-3H2"/><path d="M5.5 5h13l3.5 7v6a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-6z"/>',
    "verificar": '<path d="M9 12l2 2 4-4"/><path d="M12 3l8 4v5c0 5-3.5 8-8 9-4.5-1-8-4-8-9V7z"/>',
    "huella": '<path d="M12 10a2 2 0 0 0-2 2c0 1.02-.1 2.51-.26 4"/><path d="M14 13.12c0 2.38 0 6.38-1 8.88"/><path d="M17.29 21.02c.12-.6.43-2.3.5-3.02"/><path d="M2 12a10 10 0 0 1 18-6"/><path d="M2 16h.01"/><path d="M21.8 16c.2-2 .131-5.354 0-6"/><path d="M5 19.5C5.5 18 6 15 6 12a6 6 0 0 1 .34-2"/><path d="M8.65 22c.21-.66.45-1.32.57-2"/><path d="M9 6.8a6 6 0 0 1 9 5.2v2"/>',
    "usuario": '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    "correo": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>',
    "codigo": '<path d="M16 18l6-6-6-6"/><path d="M8 6l-6 6 6 6"/>',
    "globo": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3a14 14 0 0 1 0 18a14 14 0 0 1 0-18"/>',
    "paquete": '<path d="M21 8l-9-5-9 5v8l9 5 9-5z"/><path d="M3 8l9 5 9-5"/><path d="M12 13v8"/>',
    "enlace": '<path d="M10 14a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1"/><path d="M14 10a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1"/>',
    "subir": '<path d="M12 16V4"/><path d="M7 9l5-5 5 5"/><path d="M4 20h16"/>',
    "paleta": '<path d="M12 3a9 9 0 0 0 0 18c1.1 0 1.6-.8 1.6-1.6 0-.5-.2-.8-.5-1.2-.3-.3-.5-.7-.5-1.2 0-.9.7-1.6 1.6-1.6H16a5 5 0 0 0 5-5c0-4-4-7.4-9-7.4z"/><circle cx="7.5" cy="11" r="1"/><circle cx="10" cy="7" r="1"/><circle cx="14.5" cy="7" r="1"/><circle cx="17" cy="11" r="1"/>',
    "capas": '<path d="M12 3l9 5-9 5-9-5z"/><path d="M3 13l9 5 9-5"/>',
    "cursor": '<path d="M5 3l14 7-6 2-2 6z"/>',
    "pantalla": '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/>',
    "ventana": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18"/><circle cx="6.5" cy="6.5" r=".6"/><circle cx="9" cy="6.5" r=".6"/>',
    "cohete": '<path d="M12 15l-3-3c1-4 4-8 10-9-1 6-5 9-9 10z"/><path d="M9 12l-4 1-2 3 4 1M12 15l-1 4-3 2-1-4"/><circle cx="15" cy="9" r="1.5"/>',
    "ojo": '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    "tendencia": '<path d="M3 17l6-6 4 4 8-8"/><path d="M14 7h7v7"/>',
    "barras": '<path d="M4 20V11M10 20V5M16 20v-6M2 20h20"/>',
    "jugar": '<path d="M7 4l13 8-13 8z"/>',
    "mas": '<path d="M12 5v14M5 12h14"/>',
    "quitar": '<path d="M6 6l12 12M18 6L6 18"/>',
    "abrir": '<path d="M14 4h6v6M20 4l-9 9"/><path d="M19 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h5"/>',
}


def icono_trazo(nombre: str) -> QIcon:
    """Un icono de línea de este archivo que sigue al tema (suave, acento si está seleccionado)."""
    return icono_svg(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#888888" '
                     f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{_TRAZOS[nombre]}</svg>')


def icono(nombre: str, color: str, tam: int = 18) -> QIcon:
    """Un icono de línea en el color pedido (se dibuja en vectorial: nítido a cualquier escala)."""
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" '
           f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{_TRAZOS[nombre]}</svg>')
    render = QSvgRenderer(QByteArray(svg.encode()))
    resultado = QIcon()
    for escala in (1, 2):
        pix = QPixmap(tam * escala, tam * escala)
        pix.fill(Qt.transparent)
        pintor = QPainter(pix)
        render.render(pintor, QRectF(0, 0, tam * escala, tam * escala))
        pintor.end()
        pix.setDevicePixelRatio(escala)
        resultado.addPixmap(pix)
    return resultado


# Los tokens vigentes: los iconos temáticos los leen al pintarse, así siguen al tema sin recargarse
_ACTUAL: dict[str, str] = {}
_TRAZO = re.compile(r'(stroke|fill)="(#[0-9a-fA-F]{3,8}|currentColor)"')


class _MotorSvg(QIconEngine):
    """Pinta un SVG de línea con el color del tema: suave en reposo, acento si está seleccionado, tenue si inactivo."""

    def __init__(self, svg: str, color_fijo: str | None = None):
        super().__init__()
        self.svg = svg
        self.fijo = color_fijo

    def _color(self, modo) -> str:
        if self.fijo:
            return self.fijo
        t = _ACTUAL or tokens("oscuro", "azul")
        if modo == QIcon.Selected:
            return t["acento"]
        if modo == QIcon.Disabled:
            return t["texto_tenue"]
        return t["texto_suave"]

    def paint(self, pintor, rect, modo, estado) -> None:
        color = self._color(modo)
        svg = _TRAZO.sub(lambda m: f'{m.group(1)}="{color}"', self.svg)
        QSvgRenderer(QByteArray(svg.encode())).render(pintor, QRectF(rect))

    def pixmap(self, tam, modo, estado) -> QPixmap:
        pix = QPixmap(tam)
        pix.fill(Qt.transparent)
        pintor = QPainter(pix)
        self.paint(pintor, QRect(QPoint(0, 0), tam), modo, estado)
        pintor.end()
        return pix

    def clone(self) -> QIconEngine:
        return _MotorSvg(self.svg, self.fijo)


def icono_svg(svg: str, color: str | None = None) -> QIcon:
    """Un icono SVG de línea que se repinta con el tema (o con `color`, si se fija)."""
    return QIcon(_MotorSvg(svg, color))


def logo(icono_app_svg: str, tam: int = 32) -> QPixmap:
    """La marca del studio: su icono en una losa redondeada del color del acento."""
    t = _ACTUAL or tokens("oscuro", "azul")
    escala = 2
    pix = QPixmap(tam * escala, tam * escala)
    pix.fill(Qt.transparent)
    pintor = QPainter(pix)
    pintor.setRenderHint(QPainter.Antialiasing)
    pintor.setPen(Qt.NoPen)
    pintor.setBrush(QColor(t["acento"]))
    pintor.drawRoundedRect(QRectF(0, 0, tam * escala, tam * escala), 9 * escala, 9 * escala)
    margen = tam * escala * 0.2
    svg = _TRAZO.sub(lambda m: f'{m.group(1)}="{t["sobre_acento"]}"', icono_app_svg)
    QSvgRenderer(QByteArray(svg.encode())).render(pintor, QRectF(margen, margen, tam * escala - 2 * margen,
                                                                  tam * escala - 2 * margen))
    pintor.end()
    pix.setDevicePixelRatio(escala)
    return pix


def variante(widget: QWidget, nombre: str) -> QWidget:
    """Marca un botón como primario, fantasma, peligro o mosaico (la hoja hace el resto)."""
    widget.setProperty("variante", nombre)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    return widget


def clase(widget: QWidget, nombre: str) -> QWidget:
    """Marca un widget con una clase de la hoja (tarjeta, seccion, tenue, cifra, vacio, consola…)."""
    widget.setProperty("clase", nombre)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    return widget
