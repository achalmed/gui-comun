"""gui_comun/translucidez.py — la ventana translúcida y desenfocada que Kvantum da a Dolphin, para las ventanas QML.

Kvantum es un `QStyle` de Qt Widgets: vuelve translúcidas las `QWidget` de primer nivel (Dolphin, Kate) y pide el
desenfoque a KWin, pero no toca una `QQuickWindow`, cuyo fondo pinta QML opaco. Este módulo hace lo mismo para la
familia, con la configuración del propio Kvantum, en tres pasos que `nucleo.Aplicacion` llama en orden:

1. `decidir()` (Python puro, antes de crear la aplicación): lee el estilo de los programas (`widgetStyle` de
   `kdeglobals`), el tema de Kvantum (`kvantum.kvconfig`, con sus `[Applications]` y la variante oscura de
   `kvantum-dark`) y su `[%General]`: `translucent_windows`, `blurring`, `reduce_window_opacity` y la lista
   `opaque=`. Sin Kvantum, sin ventanas translúcidas o sin desenfoque en el tema, con la aplicación en `opaque=`, sin
   pantalla o con `GUI_COMUN_TRANSLUCIDA=0`, la ventana es opaca como siempre. La opacidad del fondo es la de Kvantum:
   `1 - reduce_window_opacity/100` (de 0 a 90; 0 o menos es opaca).
2. `preparar_superficie()` (antes de crear la ventana): pide un búfer con canal alfa (`QSurfaceFormat`, alfa de 8
   bits, y `QQuickWindow.setDefaultAlphaBuffer`). Solo si el paso 1 lo permite: sin él, nada cambia.
3. `DesenfoqueKWin` (con la ventana creada): `KWindowEffects::enableBlurBehind(ventana, true, QRegion())` por ctypes
   sobre `libKF6WindowSystem.so.6` (no hay bindings de Python de KF6 ni API de desenfoque en el QML de
   `org.kde.kwindowsystem`); la región vacía es la ventana entera. Solo se llama si
   `KWindowEffects::isEffectAvailable(BlurBehind)` dice que KWin lo ofrece; si no, o si la llamada falla, ni desenfoque
   ni transparencia: nunca texto sobre el escritorio sin desenfocar.

QML lee el resultado en `aplicacionStudio.translucidez` (`activa`, `opacidad`, `posible`, `motivo`, `preferida`,
`preferir(bool)`): `VentanaBase` pinta el marco, la barra de menú y las barras de herramientas con el color de ventana
a esa opacidad, y `FondoVentana` hace lo mismo en los paneles laterales; las zonas de lectura (`colorSet: View`: la
hoja del PDF, los editores, las tablas) siguen opacas, como la vista de archivos de Dolphin.

El ajuste para apagarlo es de toda la familia: `ventana/translucida` en `~/.config/<organización>/gui-comun.conf`,
que cambia la acción `ventana.translucida` (Ver ▸ Ventana translúcida, o Ctrl+K) y se aplica al momento.
"""

from __future__ import annotations

import ctypes
import os
from dataclasses import dataclass, field
from pathlib import Path

EFECTO_DESENFOQUE = 7                     # KWindowEffects::Effect::BlurBehind
BIBLIOTECA_KWINDOWSYSTEM = "libKF6WindowSystem.so.6"
SIMBOLO_DISPONIBLE = "_ZN14KWindowEffects17isEffectAvailableENS_6EffectE"         # isEffectAvailable(Effect)
SIMBOLO_DESENFOQUE = "_ZN14KWindowEffects16enableBlurBehindEP7QWindowbRK7QRegion"  # enableBlurBehind(QWindow*, bool, const QRegion&)
VARIABLE = "GUI_COMUN_TRANSLUCIDA"        # 0 la apaga; 1 la pide aunque el ajuste la tenga apagada
CLAVE_AJUSTE = "ventana/translucida"
APLICACION_AJUSTES = "gui-comun"          # QSettings(organización, "gui-comun"): un ajuste para toda la familia
REDUCCION_MAXIMA = 90                     # Kvantum no deja pasar de 90
_PLATAFORMAS_SIN_COMPOSITOR = ("offscreen", "minimal", "vnc", "eglfs", "linuxfb")


# ---------------------------------------------------------------------- la configuración de KDE y Kvantum
def leer_ini(ruta: Path) -> dict[str, dict[str, str]]:
    """Un `.ini` de KDE o Kvantum como {sección: {clave: valor}}, tolerante: claves repetidas (gana la última),
    comentarios con «#» o «;», líneas sin «=» ignoradas; sin el archivo, {}."""
    secciones: dict[str, dict[str, str]] = {}
    try:
        texto = Path(ruta).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return secciones
    actual = secciones.setdefault("", {})
    for linea in texto.splitlines():
        linea = linea.strip()
        if not linea or linea[0] in "#;":
            continue
        if linea.startswith("[") and linea.endswith("]"):
            actual = secciones.setdefault(linea[1:-1].strip(), {})
            continue
        if "=" in linea:
            clave, valor = linea.split("=", 1)
            actual[clave.strip()] = valor.strip()
    return secciones


def _verdadero(valor: str | None) -> bool:
    return str(valor or "").strip().lower() in ("true", "1", "yes", "on")


def _entero(valor: str | None, omision: int = 0) -> int:
    try:
        return int(str(valor).strip())
    except (TypeError, ValueError):
        return omision


def dirs_config(entorno: dict | None = None) -> list[Path]:
    """Dónde busca KConfig, del usuario a lo del sistema: XDG_CONFIG_HOME, `kdedefaults` (lo que fija el aspecto
    global de Plasma) y XDG_CONFIG_DIRS."""
    e = os.environ if entorno is None else entorno
    casa = Path(e.get("XDG_CONFIG_HOME") or Path(e.get("HOME") or Path.home()) / ".config")
    sistema = [Path(d) for d in (e.get("XDG_CONFIG_DIRS") or "/etc/xdg").split(":") if d]
    return [casa, casa / "kdedefaults", *sistema]


def estilo_de_programas(entorno: dict | None = None) -> str:
    """El estilo de Qt Widgets del escritorio (`kvantum`, `kvantum-dark`, `breeze`…), en minúsculas:
    `QT_STYLE_OVERRIDE` si está, si no el primer `[KDE] widgetStyle` de la cascada de `kdeglobals`."""
    e = os.environ if entorno is None else entorno
    if e.get("QT_STYLE_OVERRIDE"):
        return e["QT_STYLE_OVERRIDE"].strip().lower()
    for carpeta in dirs_config(e):
        estilo = leer_ini(carpeta / "kdeglobals").get("KDE", {}).get("widgetStyle")
        if estilo:
            return estilo.strip().lower()
    return "breeze"


def tema_kvantum(nombres_app: tuple[str, ...] | list[str], entorno: dict | None = None) -> str:
    """El tema de Kvantum de esta aplicación: el de `[Applications]` que la nombre o, si ninguno, `[General] theme`
    de `~/.config/Kvantum/kvantum.kvconfig`; sin archivo, el tema de serie («Kvantum», que no es translúcido)."""
    e = os.environ if entorno is None else entorno
    ini = leer_ini(dirs_config(e)[0] / "Kvantum" / "kvantum.kvconfig")
    nombres = {n.lower() for n in nombres_app if n}
    for tema, apps in ini.get("Applications", {}).items():
        if nombres & {a.strip().lower() for a in apps.split(",")}:
            return tema
    return ini.get("General", {}).get("theme", "").strip() or "Kvantum"


def ruta_tema(tema: str, oscuro: bool = False, entorno: dict | None = None,
              datos: tuple[str, ...] = ("/usr/share", "/usr/local/share")) -> Path | None:
    """El `.kvconfig` del tema como lo busca Kvantum: el del usuario (`~/.config/Kvantum/<tema>/<tema>.kvconfig`;
    una variante «<tema>Dark» vive en la carpeta de «<tema>») y luego el del sistema (`/usr/share/Kvantum`). Con
    `kvantum-dark` (`oscuro`) se prueba antes la variante oscura, si existe."""
    e = os.environ if entorno is None else entorno
    nombres = [tema + "Dark", tema] if oscuro and not tema.endswith("Dark") else [tema]
    raices = [dirs_config(e)[0] / "Kvantum"] + [Path(d) / "Kvantum" for d in datos]
    for nombre in nombres:
        carpetas = [nombre] + ([nombre[:-4]] if nombre.endswith("Dark") and len(nombre) > 4 else [])
        for raiz in raices:
            for carpeta in carpetas:
                ruta = raiz / carpeta / f"{nombre}.kvconfig"
                if ruta.is_file():
                    return ruta
    return None


@dataclass(frozen=True)
class TemaKvantum:
    """Lo que la translucidez necesita del `[%General]` de un tema de Kvantum."""
    nombre: str
    ruta: Path | None
    translucida: bool = False          # translucent_windows
    desenfoque: bool = False           # blurring
    reduccion: int = 0                 # reduce_window_opacity (porcentaje)
    opacas: tuple[str, ...] = ()       # opaque= (aplicaciones que siempre son opacas)

    @property
    def opacidad(self) -> float:
        """La opacidad del fondo de la ventana: `1 - reduce_window_opacity/100`, con la reducción entre 0 y 90."""
        return round(1.0 - max(0, min(REDUCCION_MAXIMA, self.reduccion)) / 100.0, 4)


def leer_tema(nombre: str, ruta: Path | None) -> TemaKvantum:
    general = leer_ini(ruta).get("%General", {}) if ruta else {}
    opacas = tuple(a.strip() for a in general.get("opaque", "").split(",") if a.strip())
    return TemaKvantum(nombre, ruta, _verdadero(general.get("translucent_windows")), _verdadero(general.get("blurring")),
                       _entero(general.get("reduce_window_opacity")), opacas)


# ---------------------------------------------------------------------- la decisión
@dataclass(frozen=True)
class Decision:
    """`posible`: el escritorio pide ventanas translúcidas para esta aplicación (Kvantum lo dice y hay compositor);
    `activa`: además el ajuste las quiere. `motivo` dice por qué no, en palabras para el usuario."""
    posible: bool
    activa: bool
    opacidad: float = 1.0
    motivo: str = ""
    tema: TemaKvantum | None = field(default=None, compare=False)


def _opaca(motivo: str, tema: TemaKvantum | None = None) -> Decision:
    return Decision(False, False, 1.0, motivo, tema)


def decidir(nombres_app: tuple[str, ...] | list[str], *, preferida: bool = True,
            entorno: dict | None = None) -> Decision:
    """¿Ventana translúcida? Sin efectos de lado ni Qt: solo archivos de configuración y variables de entorno."""
    e = os.environ if entorno is None else entorno
    forzada = str(e.get(VARIABLE, "")).strip().lower()
    if forzada in ("0", "false", "no", "off"):
        return _opaca(f"apagada con {VARIABLE}=0")
    plataforma = str(e.get("QT_QPA_PLATFORM", "")).split(":")[0].strip().lower()
    if plataforma in _PLATAFORMAS_SIN_COMPOSITOR:
        return _opaca(f"sin compositor (plataforma {plataforma})")
    if not (e.get("WAYLAND_DISPLAY") or e.get("DISPLAY")):
        return _opaca("sin sesión gráfica")
    estilo = estilo_de_programas(e)
    if not estilo.startswith("kvantum"):
        return _opaca(f"el estilo de los programas es {estilo}, no Kvantum")
    nombre = tema_kvantum(nombres_app, e)
    ruta = ruta_tema(nombre, estilo == "kvantum-dark", e)
    if ruta is None:
        return _opaca(f"no se encontró el tema de Kvantum «{nombre}»")
    tema = leer_tema(nombre, ruta)
    if not tema.translucida:
        return _opaca(f"el tema «{ruta.stem}» no tiene ventanas translúcidas", tema)
    if not tema.desenfoque:
        return _opaca(f"el tema «{ruta.stem}» no desenfoca el fondo", tema)
    nombres = {n.lower() for n in nombres_app if n}
    if nombres & {a.lower() for a in tema.opacas}:
        return _opaca(f"la aplicación está en la lista opaque= de «{ruta.stem}»", tema)
    if tema.opacidad >= 1.0:
        return _opaca(f"el tema «{ruta.stem}» no reduce la opacidad (reduce_window_opacity)", tema)
    preferida = preferida or forzada in ("1", "true", "yes", "on")
    return Decision(True, preferida, tema.opacidad, "" if preferida else "apagada en el ajuste", tema)


# ---------------------------------------------------------------------- Qt: la superficie y KWin
def preparar_superficie(app_creada: bool) -> None:
    """Pide un búfer con canal alfa a las ventanas que se creen a partir de ahora. `QSurfaceFormat` solo antes de
    crear la aplicación (con `AA_ShareOpenGLContexts`, después no vale); `setDefaultAlphaBuffer`, en todo caso."""
    from gui_comun.qt import BINDING
    gui = __import__(f"{BINDING}.QtGui", fromlist=["QSurfaceFormat"])
    quick = __import__(f"{BINDING}.QtQuick", fromlist=["QQuickWindow"])
    if not app_creada:
        formato = gui.QSurfaceFormat.defaultFormat()
        formato.setAlphaBufferSize(8)
        gui.QSurfaceFormat.setDefaultFormat(formato)
    quick.QQuickWindow.setDefaultAlphaBuffer(True)


def puntero_cpp(objeto) -> int:
    """La dirección del objeto de C++ detrás de un objeto de PySide6 o PyQt6."""
    from gui_comun.qt import BINDING
    if BINDING == "PySide6":
        import shiboken6
        return int(shiboken6.getCppPointer(objeto)[0])
    from PyQt6 import sip
    return int(sip.unwrapinstance(objeto))


class DesenfoqueKWin:
    """`KWindowEffects` de KF6 por ctypes. `cargar` devuelve la biblioteca (por omisión `ctypes.CDLL` de
    `libKF6WindowSystem.so.6`); las pruebas pasan una falsa. Nada se carga ni se llama hasta `disponible()`."""

    def __init__(self, cargar=None):
        self._cargar = cargar or (lambda: ctypes.CDLL(BIBLIOTECA_KWINDOWSYSTEM))
        self._biblioteca = None
        self._disponible: bool | None = None
        self.motivo = ""

    def disponible(self) -> bool:
        """¿KWin ofrece el desenfoque detrás de la ventana? (`isEffectAvailable(BlurBehind)`; se pregunta una vez)."""
        if self._disponible is None:
            try:
                self._biblioteca = self._cargar()
                funcion = getattr(self._biblioteca, SIMBOLO_DISPONIBLE)
                funcion.restype, funcion.argtypes = ctypes.c_bool, [ctypes.c_int]
                self._disponible = bool(funcion(EFECTO_DESENFOQUE))
                if not self._disponible:
                    self.motivo = "el compositor no ofrece el desenfoque (efecto Desenfoque de KWin apagado o sin KWin)"
            except (OSError, AttributeError) as error:
                self._disponible = False
                self.motivo = f"no se pudo usar KWindowEffects de {BIBLIOTECA_KWINDOWSYSTEM}: {error}"
        return self._disponible

    def aplicar(self, ventana, activo: bool = True) -> bool:
        """Pide (o quita) el desenfoque detrás de toda la ventana. True si se pidió; sin efecto disponible no llama a
        nada y devuelve False."""
        if ventana is None or not self.disponible():
            return False
        try:
            from gui_comun.qt import BINDING
            region = __import__(f"{BINDING}.QtGui", fromlist=["QRegion"]).QRegion()      # vacía = toda la ventana
            funcion = getattr(self._biblioteca, SIMBOLO_DESENFOQUE)
            funcion.restype, funcion.argtypes = None, [ctypes.c_void_p, ctypes.c_bool, ctypes.c_void_p]
            funcion(ctypes.c_void_p(puntero_cpp(ventana)), bool(activo), ctypes.c_void_p(puntero_cpp(region)))
            return True
        except Exception as error:          # noqa: BLE001 — cualquier fallo deja la ventana opaca, no la tumba
            self.motivo = f"KWindowEffects::enableBlurBehind falló: {error}"
            return False


# ---------------------------------------------------------------------- lo que ve QML
try:
    from gui_comun.qt import Property, QObject, QSettings, Signal, Slot
except ImportError:          # pragma: no cover — sin binding, la decisión y la lectura del tema siguen sirviendo
    QObject = None


def leer_preferencia(organizacion: str) -> bool:
    """El ajuste de la familia (`ventana/translucida`, por omisión encendido)."""
    valor = QSettings(organizacion, APLICACION_AJUSTES).value(CLAVE_AJUSTE, True)
    return valor if isinstance(valor, bool) else str(valor).strip().lower() not in ("false", "0", "no", "off")


def guardar_preferencia(organizacion: str, valor: bool) -> None:
    ajustes = QSettings(organizacion, APLICACION_AJUSTES)
    ajustes.setValue(CLAVE_AJUSTE, bool(valor))
    ajustes.sync()


if QObject is not None:
    class Translucidez(QObject):
        """`aplicacionStudio.translucidez`: si la ventana es translúcida y con qué opacidad pinta su fondo.

        Se crea con la aplicación ya hecha (antes no hay plataforma a la que preguntar). Si la decisión lo permite,
        pregunta a KWin por el efecto: es el único sitio donde llega a cargarse `libKF6WindowSystem`."""
        cambiada = Signal()

        def __init__(self, decision: Decision, organizacion: str, desenfoque: DesenfoqueKWin | None = None,
                     preferida: bool = True):
            super().__init__()
            self._desenfoque = desenfoque or DesenfoqueKWin()
            self._organizacion = organizacion
            self._posible, self._preferida = decision.posible, bool(preferida)
            self._opacidad, self._motivo = decision.opacidad, decision.motivo
            if self._posible and not self._desenfoque.disponible():
                self._posible, self._motivo = False, self._desenfoque.motivo
            self._activa = self._posible and decision.activa
            self._ventana = None
            self._pedido = False             # el desenfoque está pedido a KWin

        # --- desde Python (nucleo.Aplicacion)
        def aplicar(self, ventana) -> bool:
            """Con la ventana creada: le pide a KWin el desenfoque si la translucidez está activa. Si falla, opaca."""
            self._ventana = ventana
            return self._poner(self._activa)

        def _poner(self, activa: bool) -> bool:
            antes = (self._activa, self._posible, self._motivo)
            correcto = True
            if activa and self._posible and self._ventana is not None:
                if self._desenfoque.aplicar(self._ventana, True):
                    self._pedido = True
                else:                        # sin desenfoque, tampoco transparencia
                    self._posible, self._motivo, correcto = False, self._desenfoque.motivo, False
            elif self._pedido:               # quitarlo solo si se pidió (así nada se llama sin efecto)
                self._desenfoque.aplicar(self._ventana, False)
                self._pedido = False
            self._activa = activa and self._posible
            if (self._activa, self._posible, self._motivo) != antes:
                self.cambiada.emit()
            return correcto

        # --- QML
        @Property(bool, notify=cambiada)
        def activa(self) -> bool:
            return self._activa

        @Property(bool, notify=cambiada)
        def posible(self) -> bool:
            return self._posible

        @Property(float, notify=cambiada)
        def opacidad(self) -> float:
            """La del fondo de la ventana mientras está activa; 1 si no."""
            return self._opacidad if self._activa else 1.0

        @Property(str, notify=cambiada)
        def motivo(self) -> str:
            """Por qué no es translúcida (vacío si lo es)."""
            return self._motivo

        @Property(bool, notify=cambiada)
        def preferida(self) -> bool:
            return self._preferida

        @Slot(bool)
        def preferir(self, valor: bool) -> None:
            """El ajuste de la familia (se guarda) y, si el escritorio lo permite, al momento en esta ventana."""
            valor = bool(valor)
            guardar_preferencia(self._organizacion, valor)
            cambio = valor != self._preferida
            self._preferida = valor
            if self._posible:
                self._motivo = "" if valor else "apagada en el ajuste"
            if not self._poner(valor) or cambio:
                self.cambiada.emit()
