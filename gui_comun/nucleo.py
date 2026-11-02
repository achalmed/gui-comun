"""gui_comun/nucleo.py — `Aplicacion`: lo que un studio QML necesita para arrancar, en una sola llamada.

    from gui_comun.nucleo import Aplicacion
    app = Aplicacion("git-studio", "Git Studio", version="2.0.0")
    app.exponer("repos", modelo_repos)            # propiedades de contexto para QML
    sys.exit(app.ejecutar(RUTA / "qml" / "Main.qml", humo="--smoke" in sys.argv))

Hace, en este orden: fija el estilo de QtQuick Controls (`org.kde.desktop`, el de Plasma, que trae Breeze y el
esquema de color del usuario) y el idioma de la interfaz; crea la `QApplication` con organización, nombre,
versión y nombre de escritorio (la ventana se agrupa con su lanzador en Wayland); carga las traducciones al español
de Qt y de Kirigami (las de Kirigami Addons las lee KI18n del entorno `LANGUAGE`); crea el motor QML y le añade la
ruta del módulo `GuiComun` (`gui_comun/qml`); crea el registro de errores (`errores`) y la integración con el
escritorio (`escritorio`) y los expone. Si un módulo QML falta (Kirigami no instalado), lo dice con claridad.

**Por qué `QApplication` y no `QGuiApplication` (3.0).** El tema de plataforma de KDE (`KDEPlasmaPlatformTheme6`)
solo ofrece su diálogo de archivos nativo (el de Dolphin: lugares, vista previa, filtros, la barra de rutas) cuando
la aplicación es una `QApplication`: es un widget (`KFileWidget`). Con una `QGuiApplication`, `FileDialog` y
`FolderDialog` de `QtQuick.Dialogs` caen a su implementación en QML, que no se parece a nada del escritorio (el
«selector de archivos extraño» que vio el autor; comprobado en Plasma 6.6 Wayland el 2026-11-02, ver
`docs/integracion-kde.md`). El estilo `org.kde.desktop` también pinta sus controles con el `QStyle` del sistema solo si
hay `QApplication`. Así lo hacen las aplicaciones de Kirigami de KDE. La interfaz sigue siendo QML: de `QtWidgets`
solo se usa la clase de la aplicación.

No construye interfaz ni conoce ningún studio: la presentación es del QML de cada uno.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from gui_comun import __version__ as _VERSION_GUI_COMUN
from gui_comun import errores as _errores
from gui_comun import i18n
from gui_comun.escritorio import Escritorio
from gui_comun.qt import (BINDING, Property, QApplication, QEvent, QGuiApplication, QIcon, QObject,
                          QQmlApplicationEngine, QQmlPropertyMap, QQuickWindow, QTimer, QTranslator, QUrl, cast,
                          version_qt)

RUTA_QML = Path(__file__).resolve().parent / "qml"          # el módulo QML GuiComun vive en gui_comun/qml/GuiComun/
ESTILO = "org.kde.desktop"
ORGANIZACION = "EdisonAchalma"

# dónde están las traducciones instaladas (Kubuntu/Debian/Fedora); se prueban todas y se cargan las que existan
_RUTAS_QT = ("/usr/share/qt6/translations", "/usr/lib/qt6/translations", "/usr/lib64/qt6/translations")
_RUTAS_KDE = ("/usr/share/locale/{idioma}/LC_MESSAGES",)
_MODULOS_MINIMOS = ("org.kde.kirigami", "org.kde.kirigamiaddons.formcard")


def preparar_entorno(idioma: str = "es") -> None:
    """Variables que deben estar antes de crear la aplicación: estilo de Controls y lengua de la interfaz.

    `QT_QUICK_CONTROLS_STYLE` solo si el usuario no fijó otro. `LANGUAGE` se antepone (no se pisa): es lo que leen
    KI18n (Kirigami Addons) y QLocale::uiLanguages; las cadenas propias de los studios ya están en español."""
    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", ESTILO)
    if idioma:
        previo = os.environ.get("LANGUAGE", "")
        if not previo.split(":")[0].startswith(idioma):
            os.environ["LANGUAGE"] = ":".join(p for p in (idioma, previo) if p)


def cargar_traducciones(app, idioma: str = "es") -> list[str]:
    """Instala las traducciones de Qt (diálogos, atajos, menús contextuales) y de Kirigami. Devuelve las cargadas."""
    cargadas: list[str] = []
    pedidas = [(f"qtbase_{idioma}", _RUTAS_QT), (f"qtdeclarative_{idioma}", _RUTAS_QT),
               ("libkirigami6_qt", tuple(r.format(idioma=idioma) for r in _RUTAS_KDE))]
    for nombre, rutas in pedidas:
        for ruta in rutas:
            traductor = QTranslator(app)
            if Path(ruta).is_dir() and traductor.load(nombre, ruta):
                app.installTranslator(traductor)
                cargadas.append(nombre)
                break
    return cargadas


class Aplicacion:
    """La aplicación de un studio QML: `QApplication` + motor QML con el módulo `GuiComun`, `errores` y `escritorio`."""

    def __init__(self, app_id: str, nombre: str, *, version: str = "", organizacion: str = ORGANIZACION,
                 idioma: str = "es", argv: list[str] | None = None, nombre_ajustes: str | None = None):
        """`app_id` es el nombre del `.desktop` (`git-studio`); `nombre_ajustes`, el `applicationName` de QSettings
        (por omisión el que ya usaba el studio en 1.x, para conservar sus preferencias: p. ej. `GitStudio`)."""
        preparar_entorno(idioma)
        self.app_id, self.nombre, self.version, self.idioma = app_id, nombre, version, idioma
        QGuiApplication.setOrganizationName(organizacion)
        QGuiApplication.setApplicationName(nombre_ajustes or app_id)
        QGuiApplication.setApplicationDisplayName(nombre)
        if version:
            QGuiApplication.setApplicationVersion(version)
        QGuiApplication.setDesktopFileName(app_id)
        # QApplication (no QGuiApplication): el diálogo de archivos de KDE y el QStyle de org.kde.desktop la necesitan
        # (ver el docstring del módulo); sin QtWidgets en el binding, la de siempre
        clase = QApplication if QApplication is not None else QGuiApplication
        self.app = clase.instance() or clase(argv if argv is not None else sys.argv)
        if not QIcon.themeName():               # sin tema de escritorio (offscreen, otro entorno): el de Plasma
            QIcon.setThemeName("breeze")
        self.traducciones = cargar_traducciones(self.app, idioma)
        self.motor = QQmlApplicationEngine()
        self.motor.addImportPath(str(RUTA_QML))
        self.motor.quit.connect(self.app.quit)
        self.traduccion = i18n.instalar(self.motor, idioma)      # i18n* de KI18n para el QML de Kirigami Addons
        self.studio = QQmlPropertyMap()                           # todo lo expuesto, también como `studio.<nombre>`
        self.motor.rootContext().setContextProperty("studio", self.studio)
        self._avisos: list[str] = []
        self.motor.warnings.connect(self._anotar_avisos)
        self._raiz = None
        self.errores = _errores.Errores()                         # 3.0: errores presentables
        _errores.fijar_predeterminado(self.errores)               # Tareas y Escritorio lo usan sin que nadie se lo pase
        self.escritorio = Escritorio(self.errores)                # 3.0: abrir, mostrar en Dolphin, abrir carpeta
        self.exponer("errores", self.errores)
        self.exponer("escritorio", self.escritorio)
        self.datos = DatosStudio(self)
        self.exponer("aplicacionStudio", self.datos)

    # ------------------------------------------------------------------ QML
    def exponer(self, nombre: str, objeto) -> None:
        """Un objeto que todo el QML ve como `nombre` y como `studio.<nombre>` (controladores, modelos, acciones).

        La segunda forma evita la sombra de una propiedad homónima del componente (`acciones: studio.acciones`)."""
        self.motor.rootContext().setContextProperty(nombre, objeto)
        self.studio.insert(nombre, objeto)

    def error(self, descripcion: str, causa: str = "", recurso: str = "", accion: str = "", detalle: str = "",
              nivel: str = "error") -> dict:
        """Presenta un error al usuario (la ventana lo muestra en un `DialogoError`): qué pasó, la causa probable, el
        archivo o recurso, la acción recomendada y el detalle técnico desplegable. Atajo de `self.errores.presentar`."""
        return self.errores.presentar(descripcion, causa, recurso, accion, detalle, nivel)

    def cargar(self, ruta_qml: str | Path) -> bool:
        """Carga el `Main.qml` del studio; False (con el motivo en stderr) si no se pudo."""
        ruta = Path(ruta_qml)
        if not ruta.is_file():
            print(f"{self.nombre}: no existe {ruta}", file=sys.stderr)
            return False
        self.motor.load(QUrl.fromLocalFile(str(ruta)))
        raices = self.motor.rootObjects()
        if not raices:
            print(self.mensaje_de_fallo(), file=sys.stderr)
            return False
        self._raiz = raices[0]
        return True

    def ejecutar(self, ruta_qml: str | Path, humo: bool = False) -> int:
        """Carga y entra al bucle de eventos; con `humo`, cierra en cuanto arranca (prueba de humo)."""
        if not self.cargar(ruta_qml):
            return 1
        if humo:
            QTimer.singleShot(0, self.app.quit)
        codigo = self.app.exec()
        self.cerrar()
        return codigo

    def cerrar(self) -> None:
        """Destruye el motor (y con él la ventana) antes de que Python libere los objetos expuestos: así ninguna
        ligadura de QML ve un objeto nulo al salir ni la salida termina en violación de segmento."""
        if self.motor is None:
            return
        self._raiz = None
        for raiz in self.motor.rootObjects():      # primero la ventana (sus ligaduras aún ven el contexto entero)
            raiz.deleteLater()
        self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.motor.deleteLater()                   # después el motor
        self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.motor = None
        if _errores.predeterminado() is self.errores:
            _errores.fijar_predeterminado(None)

    def ventana(self):
        """La ventana raíz como `QQuickWindow` (para capturas, geometría, foco)."""
        return cast(self._raiz, QQuickWindow) if self._raiz is not None else None

    def capturar(self, ruta_png: str | Path, espera_ms: int = 1500, salir: bool = True) -> None:
        """Guarda una captura de la ventana cuando lleve `espera_ms` dibujándose (documentación y galería)."""
        def _capturar():
            ventana = self.ventana()
            if ventana is not None:
                ventana.grabWindow().save(str(ruta_png))
            if salir:
                self.app.quit()
        QTimer.singleShot(espera_ms, _capturar)

    # ------------------------------------------------------------- errores
    def _anotar_avisos(self, avisos) -> None:
        for aviso in avisos:
            self._avisos.append(aviso.toString())

    def mensaje_de_fallo(self) -> str:
        faltan = [m for m in _MODULOS_MINIMOS if any(m in a and "is not installed" in a for a in self._avisos)]
        lineas = [f"{self.nombre}: no se pudo cargar la interfaz QML ({BINDING}, Qt {version_qt()})."]
        lineas += self._avisos[-8:]
        if faltan:
            lineas.append("Falta un módulo QML de KDE. En Kubuntu/Debian: sudo apt install qml6-module-org-kde-kirigami "
                          "qml6-module-org-kde-kirigamiaddons-formcard qml6-module-org-kde-desktop")
        lineas.append("Los studios corren con el Python del sistema (/usr/bin/python3), cuyo Qt es el que trae Kirigami.")
        return "\n".join(lineas)


class DatosStudio(QObject):
    """Lo que `aplicacionStudio` ofrece a QML: identidad y versiones (para «Acerca de» y el título de la ventana)."""

    def __init__(self, aplicacion: Aplicacion):
        super().__init__()
        self._a = aplicacion

    @Property(str, constant=True)
    def appId(self) -> str:
        return self._a.app_id

    @Property(str, constant=True)
    def nombre(self) -> str:
        return self._a.nombre

    @Property(str, constant=True)
    def version(self) -> str:
        return self._a.version

    @Property(str, constant=True)
    def binding(self) -> str:
        return BINDING

    @Property(str, constant=True)
    def versionGuiComun(self) -> str:
        return _VERSION_GUI_COMUN

    @Property(str, constant=True)
    def versionQt(self) -> str:
        return version_qt()

    @Property(QObject, constant=True)
    def errores(self):
        """3.0: el registro de errores (`gui_comun.errores.Errores`); `VentanaBase` lo muestra."""
        return self._a.errores

    @Property(QObject, constant=True)
    def escritorio(self):
        """3.0: la integración con el escritorio (`gui_comun.escritorio.Escritorio`)."""
        return self._a.escritorio
