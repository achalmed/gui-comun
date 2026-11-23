"""test_esquemas.py — 4.4: el esquema de color de la ventana (como Kate) y la variante «como Dolphin» de Kvantum.

Sin pantalla: la lista de esquemas, el `.colors` generado desde el `.kvconfig`, el submenú tras «Configurar…» y, en un
proceso hijo, que Kirigami cambia de colores al elegir y que lo elegido pasa a bloque lleno.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from conftest import correr_hijo, requiere_binding, requiere_kirigami
from gui_comun import esquemas as es
from gui_comun import translucidez as tr

ESQUEMA = """[General]
ColorScheme={id}
Name={nombre}

[ColorEffects:Disabled]
ContrastAmount=0.65

[Colors:Window]
BackgroundNormal=54,54,54
ForegroundNormal=252,252,252
ForegroundNegative=237,21,21

[Colors:View]
BackgroundNormal=36,36,36
BackgroundAlternate=40,40,40
ForegroundNormal=252,252,252

[Colors:Header][Inactive]
BackgroundNormal=45,45,45

[Colors:Selection]
BackgroundNormal=226,37,41
ForegroundNormal=252,252,252
"""

KVCONFIG = """[%General]
translucent_windows=true
blurring=true
reduce_window_opacity=25

[GeneralColors]
window.color=#1b1c1e
inactive.window.color=#242424
base.color=#101012
alt.base.color=#161719
button.color=#2e2f32
highlight.color=#e22529
highlight.text.color=#fcfcfc
text.color=#eaebed
window.text.color=#eaebed
tooltip.base.color=#323335
link.color=#ff968b
"""


def casa(tmp_path: Path, estilo="kvantum-dark") -> dict:
    """Una casa falsa: kdeglobals con el esquema LliphiOscuro, dos esquemas instalados y el tema Lliphi de Kvantum."""
    config, datos, sistema = tmp_path / "config", tmp_path / "datos", tmp_path / "sistema"
    (config / "kdedefaults").mkdir(parents=True)
    (config / "kdedefaults" / "kdeglobals").write_text(f"[General]\nColorScheme=LliphiOscuro\n\n[KDE]\nwidgetStyle={estilo}\n")
    # Plasma copia los colores del esquema del sistema en kdeglobals: de ahí los lee KColorScheme sin esquema propio
    (config / "kdeglobals").write_text(ESQUEMA.format(id="LliphiOscuro", nombre="Lliphi Oscuro").split("\n", 4)[4])
    (config / "Kvantum" / "Lliphi").mkdir(parents=True)
    (config / "Kvantum" / "kvantum.kvconfig").write_text("[General]\ntheme=Lliphi\n")
    (config / "Kvantum" / "Lliphi" / "LliphiDark.kvconfig").write_text(KVCONFIG)
    (config / "Kvantum" / "Lliphi" / "Lliphi.kvconfig").write_text(KVCONFIG.replace("#1b1c1e", "#ecedef"))
    for carpeta, ident, nombre in ((datos, "LliphiOscuro", "Lliphi Oscuro"), (sistema, "BreezeDark", "Breeze Dark"),
                                    (sistema, "LliphiOscuro", "Lliphi Oscuro (del sistema)")):
        (carpeta / "color-schemes").mkdir(parents=True, exist_ok=True)
        (carpeta / "color-schemes" / f"{ident}.colors").write_text(ESQUEMA.format(id=ident, nombre=nombre))
    return {"HOME": str(tmp_path), "XDG_CONFIG_HOME": str(config), "XDG_CONFIG_DIRS": str(tmp_path / "nada"),
            "XDG_DATA_HOME": str(datos), "XDG_DATA_DIRS": str(sistema), "XDG_CACHE_HOME": str(tmp_path / "cache")}


NOMBRES = ("biblioteca-studio", "BibliotecaStudio")


def test_rgb():
    assert es.rgb("#1b1c1e") == "27,28,30" and es.rgb("e22529ff") == "226,37,41"
    assert es.rgb("rojo") is None and es.rgb("") is None


def test_esquemas_instalados_el_del_usuario_tapa_al_del_sistema(tmp_path):
    e = casa(tmp_path)
    lista = es.esquemas_instalados(e)
    assert [d["id"] for d in lista] == ["BreezeDark", "LliphiOscuro"]
    assert lista[1]["nombre"] == "Lliphi Oscuro" and lista[1]["ruta"].startswith(e["XDG_DATA_HOME"])
    assert es.esquema_del_sistema(e) == "LliphiOscuro"


def test_variante_como_dolphin_con_los_colores_de_kvantum(tmp_path):
    e = casa(tmp_path)
    ruta = es.esquema_kvantum(NOMBRES, e)
    assert ruta == tmp_path / "cache" / "gui-comun" / "esquemas" / "LliphiDark-kvantum.colors"
    ini = tr.leer_ini(ruta)
    assert ini["Colors:Window"]["BackgroundNormal"] == "27,28,30"               # window.color, no el 54,54,54
    assert ini["Colors:Window"]["ForegroundNegative"] == "237,21,21"            # lo que Kvantum no dice, del esquema
    assert ini["Colors:View"]["BackgroundNormal"] == "16,16,18" and ini["Colors:View"]["BackgroundAlternate"] == "22,23,25"
    assert ini["Colors:Header"]["BackgroundNormal"] == "27,28,30"
    assert ini["Colors:Header][Inactive"]["BackgroundNormal"] == "36,36,36"
    assert ini["Colors:Selection"]["BackgroundNormal"] == "226,37,41"
    assert ini["Colors:Tooltip"]["BackgroundNormal"] == "50,51,53"
    assert ini["ColorEffects:Disabled"]["ContrastAmount"] == "0.65"
    assert ini["General"]["Name"] == "Lliphi Dark"
    assert ruta.read_text().count("[Colors:Header][Inactive]") == 1             # la sección doble, tal cual


def test_variante_clara_con_kvantum_claro(tmp_path):
    ruta = es.esquema_kvantum(NOMBRES, casa(tmp_path, estilo="kvantum"))
    assert ruta.name == "Lliphi-kvantum.colors"
    assert tr.leer_ini(ruta)["Colors:Window"]["BackgroundNormal"] == "236,237,239"


def test_sin_kvantum_no_hay_variante(tmp_path):
    e = casa(tmp_path, estilo="breeze")
    assert es.esquema_kvantum(NOMBRES, e) is None
    assert [o["id"] for o in es.opciones(NOMBRES, e)] == ["", "BreezeDark", "LliphiOscuro"]


def test_opciones_como_kate(tmp_path):
    e = casa(tmp_path)
    ops = es.opciones(NOMBRES, e)
    assert [o["id"] for o in ops] == ["", "kvantum", "BreezeDark", "LliphiOscuro"]
    assert ops[0]["nombre"] == "Predeterminado (Lliphi Oscuro)"
    assert ops[1]["nombre"] == "Lliphi Dark"
    assert es.nombre_tema(Path("Lliphi.kvconfig")) == "Lliphi" and es.nombre_tema(Path("KvArcDark.kvconfig")) == "Kv Arc Dark"
    assert es.ruta_de("", NOMBRES, e) is None
    assert es.ruta_de("BreezeDark", NOMBRES, e).name == "BreezeDark.colors"
    assert es.ruta_de("NoExiste", NOMBRES, e) is None


# ---------------------------------------------------------------------- el submenú, en Acciones
class EsquemasFalsos:
    def __init__(self):
        self.elegidos = []

    def registrar_acciones(self, acciones):
        nombres = []
        for ident, nombre in (("", "Predeterminado"), ("kvantum", "Como Dolphin"), ("BreezeDark", "Breeze Dark")):
            acciones.registrar(es.nombre_accion(ident), nombre, "", None, "Esquema de color", marcable=True,
                               al_disparar=lambda _m=None, i=ident: self.elegidos.append(i))
            nombres.append(es.nombre_accion(ident))
        return nombres


@pytest.fixture
def con_esquemas():
    falsos = EsquemasFalsos()
    es.fijar_predeterminado(falsos)
    yield falsos
    es.fijar_predeterminado(None)


@requiere_binding
def test_submenu_tras_configurar(app, con_esquemas):
    from gui_comun.acciones import Acciones
    a = Acciones()
    a.estandar("Prueba", paneles=False)
    a.definir_menus([("&Archivo", ["app.salir"]), ("&Ajustes", ["app.ajustes", "|", "app.acerca"])])
    ajustes = a.menus[1]["elementos"]
    assert [e.get("nombre", e.get("titulo", e["tipo"])) for e in ajustes] == [
        "app.ajustes", "Es&quema de color de la ventana", "ventana.translucida", "separador", "app.acerca"]
    sub = ajustes[1]["elementos"]
    assert [e["nombre"] for e in sub] == ["ventana.esquema.predeterminado", "ventana.esquema.kvantum", "ventana.esquema.BreezeDark"]
    a.ejecutar("ventana.esquema.kvantum")
    assert con_esquemas.elegidos == ["kvantum"]


@requiere_binding
def test_submenu_dentro_de_un_submenu_y_sin_duplicar(app, con_esquemas):
    from gui_comun.acciones import Acciones
    a = Acciones()
    a.estandar("Prueba", paneles=False)
    a.definir_menus([("&Herramientas", [("&Más", ["app.ajustes"])]), ("&Ver", ["ventana.translucida"])])
    mas = a.menus[0]["elementos"][0]["elementos"]
    assert [e.get("nombre", e.get("titulo")) for e in mas] == ["app.ajustes", "Es&quema de color de la ventana"]
    assert [e["nombre"] for e in a.menus[1]["elementos"]] == ["ventana.translucida"]       # no se repite


@requiere_binding
def test_sin_aplicacion_ni_configurar_nada_cambia(app):
    from gui_comun.acciones import Acciones
    a = Acciones()
    a.estandar("Prueba", paneles=False)
    assert not any(n.startswith(es.PREFIJO_ACCION) for n in (a.data(a.index(i, 0), a.R_NOMBRE) for i in range(a.rowCount())))
    a.definir_menus([("&Archivo", ["app.salir"])])
    assert [e["nombre"] for e in a.menus[0]["elementos"]] == ["app.salir"]


# ---------------------------------------------------------------------- en vivo, en un proceso hijo
@requiere_kirigami
def test_elegir_como_dolphin_cambia_colores_y_seleccion(tmp_path):
    """Al elegir «como Dolphin», Kirigami pasa a los colores de Kvantum y lo elegido a bloque lleno; al volver al
    predeterminado, los del esquema del sistema y el tinte. La elección queda guardada para la familia."""
    entorno = casa(tmp_path / "casa")
    guion = r'''
import sys, os, json
entorno = json.loads(sys.argv[2])
os.environ.update({k: v for k, v in entorno.items() if k != "XDG_CONFIG_HOME"})
os.environ["XDG_CONFIG_HOME"] = entorno["XDG_CONFIG_HOME"]
sys.path.insert(0, sys.argv[1])
from gui_comun.nucleo import Aplicacion
from gui_comun.acciones import Acciones
from gui_comun.qt import QObject, QTimer, QSettings
app = Aplicacion("biblioteca-studio", "Prueba")
acc = Acciones(); acc.estandar("Prueba", paneles=False)
acc.definir_menus([("&Ajustes", ["app.ajustes"])])
app.exponer("acciones", acc)
ruta = os.path.join(os.environ["PRUEBA_TMP"], "Esquemas.qml")
open(ruta, "w").write("""import QtQuick
import org.kde.kirigami as Kirigami
import GuiComun
VentanaBase { id: v; visible: true; width: 700; height: 400; acciones: studio.acciones
  Item { objectName: "sonda"; anchors.fill: parent
    Kirigami.Theme.colorSet: Kirigami.Theme.View; Kirigami.Theme.inherit: false
    property color vista: Kirigami.Theme.backgroundColor
    property bool llena: EstiloSeleccion.llena
    property color elegida: EstiloSeleccion.fondo(Kirigami.Theme.backgroundColor, Kirigami.Theme.highlightColor, 0.24) } }
""")
assert app.cargar(ruta)
v = app.motor.rootObjects()[0]
s = v.findChild(QObject, "sonda")
leer = lambda: {"vista": s.property("vista").name(), "llena": s.property("llena"), "elegida": s.property("elegida").name(),
                "marcada": acc["ventana.esquema.kvantum"].marcada, "pred": acc["ventana.esquema.predeterminado"].marcada}
r = {"antes": None}
def paso0():
    r["antes"] = leer(); acc.ejecutar("ventana.esquema.kvantum"); QTimer.singleShot(300, paso1)
def paso1():
    r["kvantum"] = leer()
    r["guardado"] = QSettings("EdisonAchalma", "gui-comun").value("ventana/esquema")
    acc.ejecutar("ventana.esquema.predeterminado"); QTimer.singleShot(300, paso2)
def paso2():
    r["despues"] = leer(); print(json.dumps(r)); app.app.quit()
QTimer.singleShot(300, paso0)
app.app.exec()
'''
    r = correr_hijo(guion, tmp_path, json.dumps(entorno))
    datos = json.loads(r.stdout.strip().splitlines()[-1])
    antes, kv, despues = datos["antes"], datos["kvantum"], datos["despues"]
    assert antes["vista"] == "#242424" and not antes["llena"] and antes["pred"], (datos, r.stderr[-2000:])
    assert kv["vista"] == "#101012" and kv["llena"] and kv["marcada"] and not kv["pred"]
    assert kv["elegida"] == "#991e21"      # #e22529 al 65 % sobre #101012 (Dolphin, medido en pantalla: #992024)
    assert datos["guardado"] == "kvantum"
    assert despues["vista"] == "#242424" and not despues["llena"] and despues["pred"] and not despues["marcada"]
