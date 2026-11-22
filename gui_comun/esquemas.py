"""gui_comun/esquemas.py — el esquema de color de la ventana, elegible como en Kate, y la variante «como Dolphin».

Por qué la familia no tenía los colores de Dolphin: con Kvantum, Dolphin y las demás aplicaciones de Qt Widgets toman
la paleta del tema de Kvantum (`[GeneralColors]` del `.kvconfig`, p. ej. `window.color=#1b1c1e` en LliphiDark),
mientras que las ventanas QML (estilo `org.kde.desktop` de Kirigami) toman la del esquema de color de KDE
(`LliphiOscuro.colors`: `#363636`). Son dos fuentes de color distintas en el mismo escritorio.

Lo que hace este módulo, para toda la familia:

- **Predeterminado**: el esquema de color del sistema, como hasta ahora (no se toca nada).
- **Como Dolphin (Kvantum)**: genera un `.colors` a partir del esquema del sistema con los colores del tema de Kvantum
  activo (el claro o el oscuro, según `kvantum`/`kvantum-dark`) en ventana, vista, botones, cabecera, selección y
  ayudas emergentes, y lo usa. Lo elegido se marca entonces con un bloque lleno, como en Dolphin.
- **Cualquier esquema instalado** (`/usr/share/color-schemes`, `~/.local/share/color-schemes`), como el menú
  «Window Color Scheme» de Kate.

El mecanismo es el de `KColorSchemeManager` de KDE: la propiedad `KDE_COLOR_SCHEME_PATH` de la aplicación (que
`KColorScheme`, y con él Kirigami, lee en lugar de `kdeglobals`) y una paleta nueva para que todo se repinte al momento.
La elección es un ajuste de la familia (`ventana/esquema` en `~/.config/<organización>/gui-comun.conf`): vacío, el
predeterminado; `kvantum`, como Dolphin; si no, el nombre del archivo `.colors` sin extensión. Las acciones
`ventana.esquema.<id>` las registra `Acciones.estandar` y `Acciones.definir_menus` las pone en un submenú
«Esquema de color de la ventana» tras «Configurar…» (`app.ajustes`).
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from gui_comun import translucidez as _tr

CLAVE_AJUSTE = "ventana/esquema"
PREDETERMINADO = ""
KVANTUM = "kvantum"
PREFIJO_ACCION = "ventana.esquema."
ALFA_SELECCION = 0.65        # el bloque lleno: la selección de Kvantum sobre la vista, como la pinta Dolphin

# lo que el tema de Kvantum dice de cada grupo del esquema de KDE: {grupo: {clave del esquema: clave de Kvantum}}
_MAPA_KVANTUM = {
    "Colors:Window": {"BackgroundNormal": "window.color", "BackgroundAlternate": "alt.base.color",
                      "ForegroundNormal": "window.text.color", "ForegroundInactive": "disabled.text.color",
                      "ForegroundLink": "link.color", "ForegroundVisited": "link.visited.color",
                      "DecorationFocus": "highlight.color", "DecorationHover": "highlight.color"},
    "Colors:View": {"BackgroundNormal": "base.color", "BackgroundAlternate": "alt.base.color",
                    "ForegroundNormal": "text.color", "ForegroundInactive": "disabled.text.color",
                    "ForegroundLink": "link.color", "ForegroundVisited": "link.visited.color",
                    "DecorationFocus": "highlight.color", "DecorationHover": "highlight.color"},
    "Colors:Button": {"BackgroundNormal": "button.color", "BackgroundAlternate": "mid.color",
                      "ForegroundNormal": "button.text.color", "ForegroundInactive": "disabled.text.color",
                      "ForegroundLink": "link.color", "ForegroundVisited": "link.visited.color",
                      "DecorationFocus": "highlight.color", "DecorationHover": "highlight.color"},
    "Colors:Header": {"BackgroundNormal": "window.color", "BackgroundAlternate": "alt.base.color",
                      "ForegroundNormal": "window.text.color", "ForegroundInactive": "disabled.text.color",
                      "ForegroundLink": "link.color", "ForegroundVisited": "link.visited.color",
                      "DecorationFocus": "highlight.color", "DecorationHover": "highlight.color"},
    "Colors:Header][Inactive": {"BackgroundNormal": "inactive.window.color", "BackgroundAlternate": "alt.base.color"},
    "Colors:Selection": {"BackgroundNormal": "highlight.color", "BackgroundAlternate": "inactive.highlight.color",
                         "ForegroundNormal": "highlight.text.color", "ForegroundInactive": "inactive.highlight.text.color",
                         "DecorationFocus": "highlight.color", "DecorationHover": "highlight.color"},
    "Colors:Tooltip": {"BackgroundNormal": "tooltip.base.color", "ForegroundNormal": "tooltip.text.color"},
}


# ---------------------------------------------------------------------- archivos
def dirs_datos(entorno: dict | None = None) -> list[Path]:
    e = os.environ if entorno is None else entorno
    casa = Path(e.get("XDG_DATA_HOME") or Path(e.get("HOME") or Path.home()) / ".local" / "share")
    return [casa] + [Path(d) for d in (e.get("XDG_DATA_DIRS") or "/usr/local/share:/usr/share").split(":") if d]


def esquemas_instalados(entorno: dict | None = None) -> list[dict]:
    """Los esquemas de color de KDE instalados: [{id, nombre, ruta}] por nombre; el del usuario tapa al del sistema."""
    vistos: dict[str, dict] = {}
    for carpeta in dirs_datos(entorno):
        for ruta in sorted((carpeta / "color-schemes").glob("*.colors")):
            if ruta.stem in vistos:
                continue
            nombre = _tr.leer_ini(ruta).get("General", {}).get("Name") or ruta.stem
            vistos[ruta.stem] = {"id": ruta.stem, "nombre": nombre, "ruta": str(ruta)}
    return sorted(vistos.values(), key=lambda d: d["nombre"].casefold())


def esquema_del_sistema(entorno: dict | None = None) -> str:
    """El id del esquema de color del escritorio (`[General] ColorScheme` de la cascada de `kdeglobals`)."""
    for carpeta in _tr.dirs_config(entorno):
        nombre = _tr.leer_ini(carpeta / "kdeglobals").get("General", {}).get("ColorScheme")
        if nombre:
            return nombre
    return "BreezeLight"


def escribir_ini(secciones: dict[str, dict[str, str]], ruta: Path, cabecera: str = "") -> None:
    lineas = [cabecera] if cabecera else []
    for seccion, claves in secciones.items():
        if not seccion and not claves:
            continue
        if seccion:
            lineas.append(f"[{seccion}]")
        lineas += [f"{clave}={valor}" for clave, valor in claves.items()]
        lineas.append("")
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text("\n".join(lineas), encoding="utf-8")


def rgb(color: str) -> str | None:
    """`#rrggbb` (o `#rrggbbaa`, el alfa de Kvantum se ignora) → «r,g,b» como en los `.colors`; None si no es un color."""
    m = re.fullmatch(r"#?([0-9a-fA-F]{6})([0-9a-fA-F]{2})?", (color or "").strip())
    if not m:
        return None
    h = m.group(1)
    return ",".join(str(int(h[i:i + 2], 16)) for i in (0, 2, 4))


# ---------------------------------------------------------------------- la variante de Kvantum
def tema_kvantum_activo(nombres_app, entorno: dict | None = None) -> Path | None:
    """El `.kvconfig` que Kvantum usa ahora para esta aplicación, o None si los programas no usan Kvantum."""
    estilo = _tr.estilo_de_programas(entorno)
    if not estilo.startswith("kvantum"):
        return None
    return _tr.ruta_tema(_tr.tema_kvantum(nombres_app, entorno), estilo == "kvantum-dark", entorno)


def esquema_kvantum(nombres_app, entorno: dict | None = None, destino: Path | None = None) -> Path | None:
    """Genera el esquema «como Dolphin»: el del sistema con los colores del tema de Kvantum activo. Devuelve su ruta
    (en `$XDG_CACHE_HOME/gui-comun/esquemas/`), o None sin Kvantum o sin `[GeneralColors]` en el tema."""
    e = os.environ if entorno is None else entorno
    kvconfig = tema_kvantum_activo(nombres_app, e)
    if kvconfig is None:
        return None
    colores = _tr.leer_ini(kvconfig).get("GeneralColors", {})
    if not colores:
        return None
    instalados = {d["id"]: d for d in esquemas_instalados(e)}
    sistema = esquema_del_sistema(e)
    base = Path(instalados[sistema]["ruta"]) if sistema in instalados else _tr.dirs_config(e)[0] / "kdeglobals"
    secciones = {k: dict(v) for k, v in _tr.leer_ini(base).items() if k.startswith(("Colors:", "ColorEffects:"))}
    for grupo, claves in _MAPA_KVANTUM.items():
        destino_grupo = secciones.setdefault(grupo, {})
        for clave, clave_kv in claves.items():
            valor = rgb(colores.get(clave_kv, ""))
            if valor:
                destino_grupo[clave] = valor
    nombre = f"{instalados.get(sistema, {}).get('nombre', sistema)} como Dolphin ({kvconfig.stem})"
    salida = {"General": {"Name": nombre, "ColorScheme": f"{kvconfig.stem}Kvantum"}, **secciones}
    cache = Path(e.get("XDG_CACHE_HOME") or Path(e.get("HOME") or Path.home()) / ".cache")
    ruta = destino or cache / "gui-comun" / "esquemas" / f"{kvconfig.stem}-kvantum.colors"
    escribir_ini(salida, ruta, f"# generado por gui_comun.esquemas desde {kvconfig} y el esquema {sistema}; no editar")
    return ruta


def ruta_de(eleccion: str, nombres_app, entorno: dict | None = None) -> Path | None:
    """El archivo del esquema elegido (None: el del sistema, sin tocar nada)."""
    if not eleccion:
        return None
    if eleccion == KVANTUM:
        return esquema_kvantum(nombres_app, entorno)
    for d in esquemas_instalados(entorno):
        if d["id"] == eleccion:
            return Path(d["ruta"])
    return None


def opciones(nombres_app, entorno: dict | None = None) -> list[dict]:
    """Lo que muestra el submenú, en orden: predeterminado, como Dolphin (si hay Kvantum) y los instalados."""
    sistema = esquema_del_sistema(entorno)
    instalados = esquemas_instalados(entorno)
    nombre_sistema = next((d["nombre"] for d in instalados if d["id"] == sistema), sistema)
    salida = [{"id": PREDETERMINADO, "nombre": f"Predeterminado ({nombre_sistema})"}]
    kvconfig = tema_kvantum_activo(nombres_app, entorno)
    if kvconfig is not None:
        salida.append({"id": KVANTUM, "nombre": f"Como Dolphin (Kvantum: {kvconfig.stem})"})
    return salida + [{"id": d["id"], "nombre": d["nombre"]} for d in instalados]


def nombre_accion(eleccion: str) -> str:
    return PREFIJO_ACCION + (eleccion or "predeterminado")


# ---------------------------------------------------------------------- Qt: la paleta y el objeto de QML
try:
    from gui_comun.qt import BINDING, Property, QObject, QSettings, Signal, Slot
except ImportError:          # pragma: no cover
    QObject = None

_predeterminado = None


def predeterminado():
    """Los `Esquemas` de la aplicación en curso (los fija `nucleo.Aplicacion`); None fuera de una."""
    return _predeterminado


def fijar_predeterminado(esquemas) -> None:
    global _predeterminado
    _predeterminado = esquemas


def paleta_de(ruta: Path):
    """Una `QPalette` del esquema (lo esencial de `KColorScheme::createApplicationPalette`)."""
    gui = __import__(f"{BINDING}.QtGui", fromlist=["QPalette", "QColor"])
    QPalette, QColor = gui.QPalette, gui.QColor
    ini = _tr.leer_ini(ruta)

    def color(grupo: str, clave: str, omision: str = "128,128,128"):
        partes = [int(p) for p in (ini.get(f"Colors:{grupo}", {}).get(clave) or omision).split(",")[:3]]
        return QColor(*partes)

    p = QPalette()
    R, G = QPalette.ColorRole, QPalette.ColorGroup
    papeles = {R.Window: ("Window", "BackgroundNormal"), R.WindowText: ("Window", "ForegroundNormal"),
               R.Base: ("View", "BackgroundNormal"), R.AlternateBase: ("View", "BackgroundAlternate"),
               R.Text: ("View", "ForegroundNormal"), R.Button: ("Button", "BackgroundNormal"),
               R.ButtonText: ("Button", "ForegroundNormal"), R.Highlight: ("Selection", "BackgroundNormal"),
               R.HighlightedText: ("Selection", "ForegroundNormal"), R.ToolTipBase: ("Tooltip", "BackgroundNormal"),
               R.ToolTipText: ("Tooltip", "ForegroundNormal"), R.Link: ("View", "ForegroundLink"),
               R.LinkVisited: ("View", "ForegroundVisited"), R.PlaceholderText: ("View", "ForegroundInactive"),
               R.BrightText: ("Button", "ForegroundNormal")}
    for papel, (grupo, clave) in papeles.items():
        p.setColor(papel, color(grupo, clave))
    boton = color("Button", "BackgroundNormal")
    for papel, c in ((R.Light, boton.lighter(150)), (R.Midlight, boton.lighter(125)), (R.Mid, boton.darker(130)),
                     (R.Dark, boton.darker(160)), (R.Shadow, QColor(0, 0, 0))):
        p.setColor(papel, c)
    apagado = color("View", "ForegroundInactive")
    for papel in (R.WindowText, R.Text, R.ButtonText):
        p.setColor(G.Disabled, papel, apagado)
    return p


if QObject is not None:
    class Esquemas(QObject):
        """`aplicacionStudio.esquemas`: el esquema de color elegido para la familia y cómo se marca lo elegido."""
        cambiado = Signal()

        def __init__(self, app, nombres_app, organizacion: str, entorno: dict | None = None):
            super().__init__()
            self._app, self._nombres, self._organizacion, self._entorno = app, tuple(nombres_app), organizacion, entorno
            self._opciones = opciones(self._nombres, entorno)
            valor = QSettings(organizacion, _tr.APLICACION_AJUSTES).value(CLAVE_AJUSTE, "")
            self._actual = str(valor or "")
            if self._actual not in {o["id"] for o in self._opciones}:
                self._actual = PREDETERMINADO
            self._acciones = None
            self._ruta: Path | None = None
            self._poner(self._actual, al_arrancar=True)

        # --- aplicar
        def _poner(self, eleccion: str, al_arrancar: bool = False) -> None:
            ruta = ruta_de(eleccion, self._nombres, self._entorno)
            if eleccion and ruta is None:                  # el esquema ya no existe: el del sistema
                eleccion = PREDETERMINADO
            if ruta is None and self._ruta is None and al_arrancar:
                self._actual = eleccion
                return                                     # el predeterminado al arrancar: nada que tocar
            self._ruta = ruta
            self._actual = eleccion
            self._app.setProperty("KDE_COLOR_SCHEME_PATH", str(ruta) if ruta else "")
            sistema = ruta_de(esquema_del_sistema(self._entorno), self._nombres, self._entorno)
            origen = ruta or sistema
            if origen is not None:                         # una paleta nueva: Kirigami y los estilos se repintan
                self._app.setPalette(paleta_de(origen))

        @Slot(str)
        def elegir(self, eleccion: str) -> None:
            """Elige un esquema (`""`, `"kvantum"` o el id de un `.colors`): se guarda para toda la familia y se ve ya."""
            if eleccion not in {o["id"] for o in self._opciones}:
                return
            ajustes = QSettings(self._organizacion, _tr.APLICACION_AJUSTES)
            ajustes.setValue(CLAVE_AJUSTE, eleccion)
            ajustes.sync()
            self._poner(eleccion)
            self._marcar()
            self.cambiado.emit()

        # --- acciones (Acciones.estandar las pide)
        def registrar_acciones(self, acciones) -> list[str]:
            """Una acción marcable por opción (`ventana.esquema.<id>`), en el grupo «Esquema de color»."""
            self._acciones = acciones
            nombres = []
            for o in self._opciones:
                nombre = nombre_accion(o["id"])
                if acciones.existe(nombre):
                    continue
                acciones.registrar(nombre, o["nombre"].replace("&", "&&"), "", None, "Esquema de color", marcable=True,
                                   marcada=o["id"] == self._actual,
                                   descripcion="Esquema de color de las ventanas de la familia",
                                   al_disparar=lambda _m=None, i=o["id"]: self.elegir(i))
                nombres.append(nombre)
            return nombres

        def _marcar(self) -> None:
            if self._acciones is None:
                return
            for o in self._opciones:
                nombre = nombre_accion(o["id"])
                if self._acciones.existe(nombre):
                    self._acciones.marcar(nombre, o["id"] == self._actual)

        # --- QML
        @Property(str, notify=cambiado)
        def actual(self) -> str:
            return self._actual

        @Property("QVariantList", constant=True)
        def opciones(self) -> list:
            return list(self._opciones)

        @Property(bool, notify=cambiado)
        def seleccionLlena(self) -> bool:
            """Lo elegido como bloque lleno (la variante «como Dolphin»); si no, el tinte con su marca (4.2)."""
            return self._actual == KVANTUM

        @Property(float, constant=True)
        def alfaSeleccion(self) -> float:
            return ALFA_SELECCION

        @Property(str, notify=cambiado)
        def ruta(self) -> str:
            return str(self._ruta or "")
