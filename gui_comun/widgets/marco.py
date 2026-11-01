"""widgets/marco.py — el marco común de los studios: barra lateral con marca, paleta de comandos, atajos y avisos.

Envuelve la lista de navegación que cada studio ya tiene (su `QListWidget` de páginas) sin tocar sus páginas:
le pone arriba la marca y el buscador, abajo los botones de consola, tema y preferencias, y la deja plegable a
solo iconos. Atajos: Ctrl+K paleta · Ctrl+1…9 páginas · Ctrl+B plegar · Ctrl+J consola · Ctrl+Mayús+L tema ·
Ctrl+, preferencias.

Uso (en la ventana principal del studio, después de llenar la lista de páginas):
    marco = Marco(ventana, nav=lista, nombre="Git Studio", subtitulo="Repositorios", icono=icono_app,
                  disenador=disenador, consola=dock, al_preferencias=abrir_prefs)
    marco.comandos_extra.append(Comando("Analizar estado", analizar, grupo="Repositorios", atajo="F5"))
    marco.avisar("Listo", "12 repos al día", "ok")
"""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QSettings, QSize, Qt
from PySide6.QtGui import QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (QDockWidget, QFrame, QHBoxLayout, QLabel, QListWidget, QMainWindow, QPushButton,
                               QToolButton, QVBoxLayout, QWidget)

from gui_comun.diseno import Disenador, icono, logo
from gui_comun.widgets.avisos import Avisos
from gui_comun.widgets.paleta import Comando, Paleta

ANCHO_ABIERTA = 232
ANCHO_PLEGADA = 64


class Marco:
    def __init__(self, ventana: QMainWindow, *, nav: QListWidget, nombre: str, subtitulo: str, icono_app: QIcon | str,
                 disenador: Disenador, consola: QDockWidget | None = None,
                 al_preferencias: Callable[[], None] | None = None, al_acerca: Callable[[], None] | None = None,
                 consola_visible: Callable[[], bool] | None = None, alternar_consola: Callable[[bool], None] | None = None,
                 guardar_tema: Callable[[str], None] | None = None):
        self.ventana = ventana
        self.nav = nav
        self.disenador = disenador
        self.consola = consola
        self.al_preferencias = al_preferencias
        self.comandos_extra: list[Comando] = []
        self._guardar_tema = guardar_tema or (lambda modo: self._ajustes.setValue("marco/tema", modo))
        self._ajustes = QSettings()
        # la consola puede ser un dock (Filesystem, Git) o un panel propio (Quarto): basta con saber verla y mostrarla
        self._consola_visible = consola_visible or (lambda: bool(consola) and consola.isVisible())
        self._alternar_consola = alternar_consola or (lambda v: consola.setVisible(v) if consola else None)

        # --- Armado: la lista de páginas pasa a vivir dentro del panel lateral ---
        padre = nav.parentWidget()
        layout_padre = padre.layout()
        indice = layout_padre.indexOf(nav)
        self.panel = QFrame()
        self.panel.setObjectName("navLateral")
        self.panel.setAttribute(Qt.WA_StyledBackground, True)
        caja = QVBoxLayout(self.panel)
        caja.setContentsMargins(0, 14, 0, 10)
        caja.setSpacing(6)

        cabecera = QHBoxLayout()
        cabecera.setContentsMargins(16, 0, 12, 4)
        cabecera.setSpacing(10)
        # icono_app: el texto SVG (se pinta como losa del acento y sigue al tema) o un QIcon ya hecho
        self._logo_svg = icono_app if isinstance(icono_app, str) else ""
        self.logo = QLabel()
        if not self._logo_svg:
            self.logo.setPixmap(icono_app.pixmap(QSize(30, 30)))
        self.logo.setFixedSize(32, 32)
        cabecera.addWidget(self.logo)
        textos = QVBoxLayout()
        textos.setSpacing(0)
        self.lbl_nombre = QLabel(nombre)
        self.lbl_nombre.setObjectName("navNombre")
        self.lbl_sub = QLabel(subtitulo)
        self.lbl_sub.setObjectName("navSubtitulo")
        textos.addWidget(self.lbl_nombre)
        textos.addWidget(self.lbl_sub)
        cabecera.addLayout(textos, 1)
        caja.addLayout(cabecera)

        fila_buscar = QHBoxLayout()
        fila_buscar.setContentsMargins(12, 6, 12, 6)
        self.btn_buscar = QPushButton()
        self.btn_buscar.setObjectName("navBuscar")
        self.btn_buscar.setFixedHeight(34)
        interior = QHBoxLayout(self.btn_buscar)
        interior.setContentsMargins(10, 0, 8, 0)
        interior.setSpacing(8)
        self.ic_buscar = QLabel()
        self.ic_buscar.setFixedSize(16, 16)
        interior.addWidget(self.ic_buscar)
        self.lbl_buscar = QLabel("Buscar o ir a…")
        self.lbl_buscar.setObjectName("navBuscarTexto")
        self.lbl_atajo = QLabel("Ctrl K")
        self.lbl_atajo.setObjectName("navAtajo")
        interior.addWidget(self.lbl_buscar)
        interior.addStretch(1)
        self.lbl_atajo.setFixedHeight(18)
        interior.addWidget(self.lbl_atajo, 0, Qt.AlignVCenter)
        self.btn_buscar.setCursor(Qt.PointingHandCursor)
        self.btn_buscar.clicked.connect(self.abrir_paleta)
        fila_buscar.addWidget(self.btn_buscar)
        caja.addLayout(fila_buscar)

        layout_padre.removeWidget(nav)
        nav.setParent(self.panel)
        nav.setObjectName("sidebar")
        nav.setMinimumWidth(0)
        nav.setMaximumWidth(16777215)
        nav.setIconSize(QSize(18, 18))
        nav.setSpacing(0)
        nav.setCursor(Qt.PointingHandCursor)
        nav.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        nav.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        for i in range(nav.count()):
            nav.item(i).setSizeHint(QSize(0, 38))
        caja.addWidget(nav, 1)

        pie = QHBoxLayout()
        pie.setContentsMargins(10, 0, 10, 0)
        pie.setSpacing(2)
        self.btn_plegar = self._boton_pie("Plegar la barra (Ctrl+B)", self.alternar_plegado)
        self.btn_consola = self._boton_pie("Consola (Ctrl+J)", lambda: self._alternar_consola(not self._consola_visible()),
                                           marcable=True)
        self.btn_tema = self._boton_pie("Tema claro u oscuro (Ctrl+Mayús+L)", self.alternar_tema)
        self.btn_prefs = self._boton_pie("Preferencias (Ctrl+,)", lambda: al_preferencias and al_preferencias())
        for b in (self.btn_plegar, self.btn_consola, self.btn_tema, self.btn_prefs):
            pie.addWidget(b)
        pie.addStretch(1)
        self._hay_consola = consola is not None or consola_visible is not None
        self.btn_consola.setVisible(self._hay_consola)
        self.btn_prefs.setVisible(al_preferencias is not None)
        caja.addLayout(pie)

        layout_padre.insertWidget(indice, self.panel)
        layout_padre.setContentsMargins(0, 0, 0, 0)
        layout_padre.setSpacing(0)
        self.panel.setFixedWidth(ANCHO_ABIERTA)
        self._etiquetas = [nav.item(i).text() for i in range(nav.count())]
        if consola is not None:
            consola.visibilityChanged.connect(self.btn_consola.setChecked)

        # --- Paleta, avisos y atajos ---
        self.paleta = Paleta(ventana, self._comandos)
        self.avisos = Avisos(ventana, disenador.tokens)
        disenador.cambiado.connect(self._al_cambiar_tema)
        self._al_cambiar_tema(disenador.tokens)
        atajos = [("Ctrl+K", self.abrir_paleta), ("Ctrl+B", self.alternar_plegado),
                  ("Ctrl+J", lambda: self._alternar_consola(not self._consola_visible())),
                  ("Ctrl+Shift+L", self.alternar_tema)]
        if al_preferencias:
            atajos.append(("Ctrl+,", al_preferencias))
        for n in range(min(9, nav.count())):
            atajos.append((f"Ctrl+{n + 1}", lambda fila=n: self.nav.setCurrentRow(fila)))
        self._atajos = []
        for secuencia, accion in atajos:
            s = QShortcut(QKeySequence(secuencia), ventana)
            s.setContext(Qt.WindowShortcut)
            s.activated.connect(accion)
            self._atajos.append(s)
        self._al_acerca = al_acerca
        if self._ajustes.value("marco/plegada", False, type=bool):
            self.alternar_plegado()
        from PySide6.QtWidgets import QApplication
        QApplication.instance().aboutToQuit.connect(self._al_salir)

    # ------------------------------------------------------------------ API
    def avisar(self, titulo: str, texto: str = "", nivel: str = "info") -> None:
        self.avisos.mostrar(titulo, texto, nivel)

    def abrir_paleta(self) -> None:
        self.paleta.abrir()

    def alternar_tema(self) -> None:
        self._guardar_tema(self.disenador.alternar())

    def alternar_plegado(self) -> None:
        plegar = self.panel.width() > ANCHO_PLEGADA
        self.panel.setFixedWidth(ANCHO_PLEGADA if plegar else ANCHO_ABIERTA)
        for w in (self.lbl_nombre, self.lbl_sub):
            w.setVisible(not plegar)
        self.lbl_buscar.setVisible(not plegar)
        self.lbl_atajo.setVisible(not plegar)
        for i, etiqueta in enumerate(self._etiquetas):
            item = self.nav.item(i)
            item.setText("" if plegar else etiqueta)
            item.setToolTip(etiqueta if plegar else "")
        # plegada solo cabe un botón: el que la despliega
        for b, disponible in ((self.btn_consola, self._hay_consola), (self.btn_tema, True),
                              (self.btn_prefs, self.al_preferencias is not None)):
            b.setVisible(disponible and not plegar)
        self._ajustes.setValue("marco/plegada", plegar)

    # ------------------------------------------------------------- privado
    def _al_salir(self) -> None:
        """Destruye la ventana mientras la QApplication vive. Los atajos, botones y la paleta guardan funciones que
        apuntan a este marco, y el marco a la ventana: un ciclo que pasa por Qt y que Python no recoge. Sin esto la
        ventana sobrevive a main() y se destruye después de la aplicación (violación de segmento al salir)."""
        import shiboken6
        ventana, self.ventana = self.ventana, None
        self.comandos_extra.clear()
        self.al_preferencias = self._al_acerca = None
        if ventana is not None and shiboken6.isValid(ventana):
            shiboken6.delete(ventana)

    def _boton_pie(self, ayuda: str, accion, marcable: bool = False) -> QToolButton:
        b = QToolButton()
        b.setObjectName("navPie")
        b.setToolTip(ayuda)
        b.setIconSize(QSize(18, 18))
        b.setCursor(Qt.PointingHandCursor)
        b.setCheckable(marcable)
        b.clicked.connect(lambda _=False: accion())
        return b

    def _al_cambiar_tema(self, t: dict) -> None:
        if not t:
            return
        color = t["texto_suave"]
        if self._logo_svg:
            self.logo.setPixmap(logo(self._logo_svg, 32))
            self.ventana.setWindowIcon(QIcon(logo(self._logo_svg, 64)))
        self.nav.viewport().update()
        self.btn_plegar.setIcon(icono("panel", color))
        self.btn_consola.setIcon(icono("terminal", color))
        self.btn_tema.setIcon(icono("sol" if t["modo"] == "oscuro" else "luna", color))
        self.btn_prefs.setIcon(icono("ajustes", color))
        self.ic_buscar.setPixmap(icono("buscar", t["texto_tenue"], 16).pixmap(16, 16))
        self.avisos.actualizar_tokens(t)

    def _comandos(self) -> list[Comando]:
        paginas = [Comando(self._etiquetas[i] if i < len(self._etiquetas) else self.nav.item(i).text(),
                           lambda fila=i: self.nav.setCurrentRow(fila), grupo="Ir a", icono=self.nav.item(i).icon(),
                           atajo=f"Ctrl+{i + 1}" if i < 9 else "")
                   for i in range(self.nav.count())]
        t = self.disenador.tokens
        generales = [
            Comando("Cambiar a tema " + ("claro" if t.get("modo") == "oscuro" else "oscuro"), self.alternar_tema,
                    grupo="Vista", atajo="Ctrl+Mayús+L", palabras="tema modo oscuro claro apariencia"),
            Comando("Plegar o desplegar la barra lateral", self.alternar_plegado, grupo="Vista", atajo="Ctrl+B"),
        ]
        if self._hay_consola:
            generales.append(Comando("Mostrar u ocultar la consola", lambda: self._alternar_consola(not self._consola_visible()),
                                     grupo="Vista", atajo="Ctrl+J", palabras="terminal salida registro log"))
        if self.al_preferencias:
            generales.append(Comando("Preferencias", self.al_preferencias, grupo="Aplicación", atajo="Ctrl+,",
                                     palabras="ajustes configuración opciones"))
        if self._al_acerca:
            generales.append(Comando("Acerca de", self._al_acerca, grupo="Aplicación"))
        return paginas + self.comandos_extra + generales


def boton_tarea(ventana: QMainWindow, al_clic: Callable[[], None]) -> QPushButton:
    """Chip de la barra de estado: dice qué tarea corre (o «Consola») y abre la consola al hacer clic."""
    chip = QPushButton("Consola")
    chip.setObjectName("chipTarea")
    chip.setCursor(Qt.PointingHandCursor)
    chip.setToolTip("Mostrar u ocultar la consola (Ctrl+J)")
    chip.clicked.connect(al_clic)
    ventana.statusBar().addPermanentWidget(chip)
    return chip


def pagina_con_margenes(widget: QWidget, margen: int = 28) -> None:
    """Aire alrededor del contenido de una página (sus layouts de .ui vienen con 9 px) y el alto sobrante para la
    pieza grande (tabla, árbol, divisor, pestañas o texto), no repartido entre etiquetas y formularios."""
    from PySide6.QtWidgets import QAbstractItemView, QBoxLayout, QPlainTextEdit, QSplitter, QTabWidget, QTextEdit
    if widget is None or widget.layout() is None:
        return
    from PySide6.QtWidgets import QTableView, QTreeView
    for tabla in widget.findChildren(QTableView):      # tablas limpias: sin números de fila ni rejilla
        tabla.verticalHeader().hide()
        tabla.setShowGrid(False)
        tabla.setAlternatingRowColors(True)
        tabla.horizontalHeader().setHighlightSections(False)
        tabla.verticalHeader().setDefaultSectionSize(34)
    for arbol in widget.findChildren(QTreeView):
        arbol.setAlternatingRowColors(True)
        arbol.header().setHighlightSections(False)
    lay = widget.layout()
    lay.setContentsMargins(margen, margen - 6, margen, margen - 10)
    lay.setSpacing(max(lay.spacing(), 12))
    if isinstance(lay, QBoxLayout) and lay.direction() in (QBoxLayout.TopToBottom, QBoxLayout.BottomToTop):
        if not any(lay.stretch(i) for i in range(lay.count())):
            # por los hijos directos y indexOf, nunca con itemAt(): un envoltorio Python de QLayoutItem queda colgando
            # cuando Qt libera el layout, y el recolector de Python se cae al salir
            grandes = (QSplitter, QTabWidget, QAbstractItemView, QPlainTextEdit, QTextEdit)
            for hijo in widget.findChildren(QWidget, options=Qt.FindDirectChildrenOnly):
                i = lay.indexOf(hijo)
                if i >= 0 and isinstance(hijo, grandes):
                    lay.setStretch(i, 1)


def montar_studio(mw, *, nombre: str, subtitulo: str, logo_svg: str, disenador: Disenador,
                  primarios: dict[str, tuple[str, ...]] | None = None, peligro: tuple[str, ...] = (),
                  herramientas: dict[str, str] | None = None) -> Marco:
    """El marco completo para un studio de ventana `.ui` con consola acoplada (Filesystem y Git Studio).

    `mw` es el envoltorio de la ventana del studio: tiene `ui` (QMainWindow con `sidebar`, `statusbar` y las acciones
    del menú), `console` (ConsoleDock), `settings`, `controllers`, `_page_order`, `navigate`, `_open_preferences` y
    `_about`. Marca los botones primarios y de peligro de cada página, añade las herramientas a la paleta y conecta
    la consola con el chip de la barra de estado y los avisos.
    """
    ui, consola = mw.ui, mw.console
    ui.resize(1280, 820)
    ui.setMinimumSize(980, 640)
    ui.menuBar().hide()                                  # todo está en la paleta y en la barra lateral
    for nombre_accion in ("actionSalir", "actionPreferencias", "actionAcercaDe"):
        accion = getattr(ui, nombre_accion, None)
        if accion is not None:
            ui.addAction(accion)                         # sus atajos siguen vivos sin el menú
    consola.hide()                                       # se abre con Ctrl+J, con el chip o al fallar algo
    marco = Marco(ui, nav=ui.sidebar, nombre=nombre, subtitulo=subtitulo, icono_app=logo_svg, disenador=disenador,
                  consola=consola, al_preferencias=mw._open_preferences, al_acerca=mw._about,
                  guardar_tema=mw.settings.set_theme)
    disenador.cambiado.connect(consola.actualizar_tokens)
    consola.actualizar_tokens(disenador.tokens)

    chip = boton_tarea(ui, lambda: consola.setVisible(not consola.isVisible()))
    consola.tarea_iniciada.connect(lambda tarea: chip.setText(f"● {tarea}…"))
    consola.tarea_progreso.connect(lambda pct, _actual: pct >= 0 and chip.setText(f"● {consola._task_name} · {pct} %"))

    def al_terminar(nivel: str, tarea: str, detalle: str) -> None:
        chip.setText("Consola")
        if nivel == "ok":
            marco.avisar(f"{tarea}: listo", detalle, "ok")
        elif nivel == "warn":
            marco.avisar(f"{tarea}: cancelada", detalle, "aviso")
        else:
            marco.avisar(f"{tarea}: con errores", f"{detalle}. El detalle está en la consola (Ctrl+J).", "error")
        ui.statusbar.showMessage(detalle, 6000)

    consola.tarea_terminada.connect(al_terminar)
    mw.chip = chip

    from PySide6.QtWidgets import QPushButton
    from gui_comun.diseno import variante
    for page_id, controller in mw.controllers.items():
        if controller.widget is None:
            continue
        if page_id != "dashboard":
            pagina_con_margenes(controller.widget)
        for nombre_boton in (primarios or {}).get(page_id, ()):
            boton = controller.widget.findChild(QPushButton, nombre_boton)
            if boton is not None:
                variante(boton, "primario")
        for nombre_boton in peligro:
            boton = controller.widget.findChild(QPushButton, nombre_boton)
            if boton is not None:
                variante(boton, "peligro")
    for page_id, titulo in (herramientas or {}).items():
        if page_id in mw._page_order:
            fila = mw._page_order.index(page_id)
            marco.comandos_extra.append(Comando(titulo, lambda p=page_id: mw.navigate(p), grupo="Herramientas",
                                                icono=ui.sidebar.item(fila).icon()))
    return marco
