"""test_translucidez.py — 4.3: la ventana translúcida y desenfocada de Kvantum, sin pantalla.

La lectura de `kdeglobals` y del `.kvconfig`, la decisión opaca/translúcida y el desenfoque de KWin con una biblioteca
falsa: ninguna llamada por ctypes si el efecto no está disponible (ni siquiera la carga, si la decisión no lo permite).
La reacción del QML (`VentanaBase`, `FondoVentana`, las zonas de lectura opacas), en un proceso hijo.
"""

from __future__ import annotations

import json
import ctypes
from pathlib import Path

import pytest

from conftest import correr_hijo, requiere_binding, requiere_kirigami
from gui_comun import translucidez as tr

KVCONFIG = """[%General]
author=prueba
translucent_windows={translucida}
blurring={desenfoque}
popup_blurring=true
opaque=kaffeine,vlc,QtCreator,{extra}
reduce_window_opacity={reduccion}

[GeneralColors]
window.color=#1b1c1e
# un comentario
sin igual
"""


def casa(tmp_path: Path, *, estilo="kvantum", tema="Lliphi", variante_oscura=True, translucida="true",
         desenfoque="true", reduccion="25", extra="", en_kdedefaults=False, aplicaciones="") -> dict:
    """Una carpeta de configuración falsa como la del autor: `kdeglobals` y `Kvantum/<tema>/`; devuelve el entorno."""
    config = tmp_path / "config"
    (config / "kdedefaults").mkdir(parents=True)
    kdeglobals = config / ("kdedefaults" if en_kdedefaults else "") / "kdeglobals"
    kdeglobals.write_text(f"[General]\nColorScheme=X\n\n[KDE]\nLookAndFeelPackage=org.x\nwidgetStyle={estilo}\n")
    carpeta = config / "Kvantum" / tema
    carpeta.mkdir(parents=True)
    (config / "Kvantum" / "kvantum.kvconfig").write_text(f"[General]\ntheme={tema}\n" +
                                                         (f"\n[Applications]\n{aplicaciones}\n" if aplicaciones else ""))
    contenido = KVCONFIG.format(translucida=translucida, desenfoque=desenfoque, reduccion=reduccion, extra=extra)
    (carpeta / f"{tema}.kvconfig").write_text(contenido.replace(f"reduce_window_opacity={reduccion}", "reduce_window_opacity=10"))
    if variante_oscura:
        (carpeta / f"{tema}Dark.kvconfig").write_text(contenido)
    return {"HOME": str(tmp_path), "XDG_CONFIG_HOME": str(config), "XDG_CONFIG_DIRS": str(tmp_path / "nada"),
            "WAYLAND_DISPLAY": "wayland-0", "QT_QPA_PLATFORM": "wayland"}


NOMBRES = ("biblioteca-studio", "BibliotecaStudio", "Biblioteca Studio", "main.py")


# ---------------------------------------------------------------------- lectura de la configuración
def test_leer_ini_tolerante(tmp_path):
    ruta = tmp_path / "a.kvconfig"
    ruta.write_text("[%General]\nclave=1\nclave=2\n; nota\nsin igual\nvalor=a=b\n[Otra]\nx = y \n")
    ini = tr.leer_ini(ruta)
    assert ini["%General"] == {"clave": "2", "valor": "a=b"} and ini["Otra"] == {"x": "y"}
    assert tr.leer_ini(tmp_path / "no-existe") == {}


def test_estilo_de_programas_sigue_la_cascada_de_kconfig(tmp_path):
    e = casa(tmp_path, estilo="kvantum-dark", en_kdedefaults=True)       # como lo deja el aspecto global de Plasma
    assert tr.estilo_de_programas(e) == "kvantum-dark"
    assert tr.estilo_de_programas({**e, "QT_STYLE_OVERRIDE": "Breeze"}) == "breeze"
    assert tr.estilo_de_programas({"XDG_CONFIG_HOME": str(tmp_path / "vacia"), "XDG_CONFIG_DIRS": ""}) == "breeze"


def test_tema_y_variante_oscura(tmp_path):
    e = casa(tmp_path)
    assert tr.tema_kvantum(NOMBRES, e) == "Lliphi"
    oscuro = tr.ruta_tema("Lliphi", True, e, datos=())
    claro = tr.ruta_tema("Lliphi", False, e, datos=())
    assert oscuro.name == "LliphiDark.kvconfig" and oscuro.parent.name == "Lliphi"
    assert claro.name == "Lliphi.kvconfig"
    tema = tr.leer_tema("Lliphi", oscuro)
    assert tema.translucida and tema.desenfoque and tema.reduccion == 25 and tema.opacidad == 0.75
    assert "QtCreator" in tema.opacas


def test_sin_variante_oscura_usa_el_tema(tmp_path):
    e = casa(tmp_path, variante_oscura=False)
    assert tr.ruta_tema("Lliphi", True, e, datos=()).name == "Lliphi.kvconfig"


def test_tema_por_aplicacion(tmp_path):
    e = casa(tmp_path, aplicaciones="KvArc=dolphin, biblioteca-studio")
    assert tr.tema_kvantum(NOMBRES, e) == "KvArc"
    assert tr.tema_kvantum(("git-studio",), e) == "Lliphi"


def test_tema_del_sistema(tmp_path):
    e = casa(tmp_path)
    sistema = tmp_path / "share"
    (sistema / "Kvantum" / "KvArc").mkdir(parents=True)
    (sistema / "Kvantum" / "KvArc" / "KvArc.kvconfig").write_text("[%General]\ntranslucent_windows=false\n")
    assert tr.ruta_tema("KvArc", False, e, datos=(str(sistema),)) == sistema / "Kvantum" / "KvArc" / "KvArc.kvconfig"
    assert tr.ruta_tema("NoHay", False, e, datos=(str(sistema),)) is None


@pytest.mark.parametrize("reduccion, opacidad", [("25", 0.75), ("0", 1.0), ("-30", 1.0), ("95", 0.1), ("x", 1.0)])
def test_opacidad_de_kvantum(reduccion, opacidad):
    assert tr.TemaKvantum("t", None, True, True, tr._entero(reduccion)).opacidad == opacidad


# ---------------------------------------------------------------------- la decisión
def test_translucida_como_dolphin(tmp_path):
    d = tr.decidir(NOMBRES, entorno=casa(tmp_path, estilo="kvantum-dark"))
    assert d.posible and d.activa and d.opacidad == 0.75 and d.motivo == ""
    d = tr.decidir(NOMBRES, entorno=casa(tmp_path / "claro", estilo="kvantum"))     # sin -dark: el tema claro (10 %)
    assert d.activa and d.opacidad == 0.9


@pytest.mark.parametrize("cambio, motivo", [
    ({"estilo": "breeze"}, "no Kvantum"),
    ({"translucida": "false"}, "no tiene ventanas translúcidas"),
    ({"desenfoque": "false"}, "no desenfoca"),
    ({"extra": "Biblioteca-Studio"}, "opaque="),            # la lista opaque=, sin distinguir mayúsculas
    ({"reduccion": "0"}, "no reduce la opacidad"),
])
def test_opaca_si_kvantum_no_la_pide(tmp_path, cambio, motivo):
    d = tr.decidir(NOMBRES, entorno=casa(tmp_path, estilo=cambio.pop("estilo", "kvantum-dark"), **cambio))
    assert not d.posible and not d.activa and d.opacidad == 1.0 and motivo in d.motivo


@pytest.mark.parametrize("entorno, motivo", [
    ({"QT_QPA_PLATFORM": "offscreen"}, "sin compositor"),
    ({"WAYLAND_DISPLAY": "", "DISPLAY": ""}, "sin sesión gráfica"),
    ({"GUI_COMUN_TRANSLUCIDA": "0"}, "GUI_COMUN_TRANSLUCIDA=0"),
])
def test_opaca_sin_pantalla_o_apagada_por_entorno(tmp_path, entorno, motivo):
    d = tr.decidir(NOMBRES, entorno={**casa(tmp_path, estilo="kvantum-dark"), **entorno})
    assert not d.posible and motivo in d.motivo


def test_el_ajuste_la_apaga_pero_sigue_siendo_posible(tmp_path):
    e = casa(tmp_path, estilo="kvantum-dark")
    d = tr.decidir(NOMBRES, preferida=False, entorno=e)
    assert d.posible and not d.activa and "ajuste" in d.motivo          # posible: se pide el canal alfa igual
    assert tr.decidir(NOMBRES, preferida=False, entorno={**e, "GUI_COMUN_TRANSLUCIDA": "1"}).activa


# ---------------------------------------------------------------------- KWin por ctypes, con una biblioteca falsa
class FuncionFalsa:
    def __init__(self, devuelve=None, error=None):
        self.llamadas, self.devuelve, self.error = [], devuelve, error
        self.restype = self.argtypes = None

    def __call__(self, *args):
        self.llamadas.append(args)
        if self.error:
            raise self.error
        return self.devuelve


class BibliotecaFalsa:
    def __init__(self, disponible: bool, error_al_desenfocar=None):
        setattr(self, tr.SIMBOLO_DISPONIBLE, FuncionFalsa(disponible))
        setattr(self, tr.SIMBOLO_DESENFOQUE, FuncionFalsa(error=error_al_desenfocar))

    @property
    def consulta(self) -> FuncionFalsa:
        return getattr(self, tr.SIMBOLO_DISPONIBLE)

    @property
    def desenfoque(self) -> FuncionFalsa:
        return getattr(self, tr.SIMBOLO_DESENFOQUE)


class Cargador:
    def __init__(self, biblioteca=None, error=None):
        self.biblioteca, self.error, self.veces = biblioteca, error, 0

    def __call__(self):
        self.veces += 1
        if self.error:
            raise self.error
        return self.biblioteca


@requiere_binding
def test_sin_efecto_ninguna_llamada_de_desenfoque(app):
    from gui_comun.qt import QObject
    lib = BibliotecaFalsa(disponible=False)
    d = tr.DesenfoqueKWin(Cargador(lib))
    assert d.disponible() is False and d.aplicar(QObject()) is False
    assert lib.consulta.llamadas == [(tr.EFECTO_DESENFOQUE,)] and lib.desenfoque.llamadas == []
    assert "no ofrece" in d.motivo


@requiere_binding
def test_con_efecto_pide_el_desenfoque_de_toda_la_ventana(app):
    from gui_comun.qt import QObject
    lib = BibliotecaFalsa(disponible=True)
    d = tr.DesenfoqueKWin(Cargador(lib))
    ventana = QObject()
    assert d.aplicar(ventana) is True and d.disponible() is True
    (puntero, activo, region), = lib.desenfoque.llamadas
    assert puntero.value == tr.puntero_cpp(ventana) and activo is True and region.value
    assert lib.desenfoque.argtypes == [ctypes.c_void_p, ctypes.c_bool, ctypes.c_void_p]
    assert len(lib.consulta.llamadas) == 1                            # se pregunta una sola vez


def test_sin_biblioteca_no_hay_desenfoque():
    d = tr.DesenfoqueKWin(Cargador(error=OSError("libKF6WindowSystem.so.6: no existe")))
    assert d.disponible() is False and d.aplicar(object()) is False and "no se pudo usar" in d.motivo


# ---------------------------------------------------------------------- el objeto que ve QML
POSIBLE = tr.Decision(True, True, 0.75)
IMPOSIBLE = tr.Decision(False, False, 1.0, "el estilo de los programas es breeze, no Kvantum")


@pytest.fixture
def guardadas(monkeypatch):
    """El ajuste, en memoria (las pruebas en proceso no tocan la configuración del autor)."""
    valores = []
    monkeypatch.setattr(tr, "guardar_preferencia", lambda org, valor: valores.append(valor))
    return valores


@requiere_binding
def test_decision_opaca_no_carga_la_biblioteca(app, guardadas):
    from gui_comun.qt import QObject
    cargador = Cargador(BibliotecaFalsa(disponible=True))
    t = tr.Translucidez(IMPOSIBLE, "Prueba", tr.DesenfoqueKWin(cargador))
    assert t.aplicar(QObject()) and not t.activa and t.opacidad == 1.0 and "breeze" in t.motivo
    t.preferir(True)
    assert not t.activa and cargador.veces == 0 and guardadas == [True]


@requiere_binding
def test_efecto_ausente_deja_la_ventana_opaca(app, guardadas):
    from gui_comun.qt import QObject
    lib = BibliotecaFalsa(disponible=False)
    t = tr.Translucidez(POSIBLE, "Prueba", tr.DesenfoqueKWin(Cargador(lib)))
    t.aplicar(QObject())
    assert not t.posible and not t.activa and t.opacidad == 1.0 and lib.desenfoque.llamadas == []


@requiere_binding
def test_si_el_desenfoque_falla_tampoco_hay_transparencia(app, guardadas):
    from gui_comun.qt import QObject
    lib = BibliotecaFalsa(disponible=True, error_al_desenfocar=ctypes.ArgumentError("puntero"))
    t = tr.Translucidez(POSIBLE, "Prueba", tr.DesenfoqueKWin(Cargador(lib)))
    avisos = []
    t.cambiada.connect(lambda: avisos.append(t.activa))
    assert t.aplicar(QObject()) is False
    assert not t.activa and not t.posible and t.opacidad == 1.0 and "enableBlurBehind" in t.motivo and avisos


@requiere_binding
def test_el_ajuste_la_apaga_y_la_enciende_al_momento(app, guardadas):
    from gui_comun.qt import QObject
    lib = BibliotecaFalsa(disponible=True)
    t = tr.Translucidez(POSIBLE, "Prueba", tr.DesenfoqueKWin(Cargador(lib)))
    t.aplicar(QObject())
    assert t.activa and t.opacidad == 0.75 and [a[1] for a in lib.desenfoque.llamadas] == [True]
    t.preferir(False)
    assert not t.activa and not t.preferida and t.opacidad == 1.0 and [a[1] for a in lib.desenfoque.llamadas] == [True, False]
    t.preferir(True)
    assert t.activa and [a[1] for a in lib.desenfoque.llamadas] == [True, False, True] and guardadas == [False, True]


@requiere_binding
def test_apagada_desde_el_inicio_no_llama_a_kwin(app, guardadas):
    from gui_comun.qt import QObject
    lib = BibliotecaFalsa(disponible=True)
    t = tr.Translucidez(tr.Decision(True, False, 0.75, "apagada en el ajuste"), "Prueba", tr.DesenfoqueKWin(Cargador(lib)),
                        preferida=False)
    t.aplicar(QObject())
    assert t.posible and not t.activa and lib.desenfoque.llamadas == []


# ---------------------------------------------------------------------- el QML, en un proceso hijo
@requiere_kirigami
def test_aplicacion_sin_pantalla_no_toca_kwin(tmp_path):
    """Sin pantalla (offscreen) la decisión es opaca y `libKF6WindowSystem` ni se carga."""
    guion = r'''
import sys, os, json, ctypes; sys.path.insert(0, sys.argv[1])
cargadas = []
original = ctypes.CDLL
def espia(nombre, *a, **k):
    cargadas.append(str(nombre)); return original(nombre, *a, **k)
ctypes.CDLL = espia
from gui_comun.nucleo import Aplicacion
app = Aplicacion("gui-comun-prueba", "Prueba")
t = app.datos.property("translucidez")
print(json.dumps({"activa": t.property("activa"), "motivo": t.property("motivo"),
                  "kf6": [c for c in cargadas if "KF6WindowSystem" in c]}))
'''
    r = correr_hijo(guion, tmp_path)
    datos = json.loads(r.stdout.strip().splitlines()[-1])
    assert datos == {"activa": False, "motivo": "sin compositor (plataforma offscreen)", "kf6": []}, r.stderr


@requiere_kirigami
def test_ventana_base_translucida_y_lectura_opaca(tmp_path):
    """Con la translucidez activa: el color de la ventana a la opacidad del tema, la barra de menú, la barra de
    herramientas del pie y el panel de navegación sin fondo propio; la tabla (View) opaca. Al apagarla, todo opaco."""
    guion = r'''
import sys, os, json; sys.path.insert(0, sys.argv[1])
from gui_comun.nucleo import Aplicacion
from gui_comun.acciones import Acciones
from gui_comun import translucidez as tr
from gui_comun.qt import QObject, QTimer
class Falso:
    motivo = ""
    def __init__(self): self.llamadas = []
    def disponible(self): return True
    def aplicar(self, ventana, activo=True): self.llamadas.append(activo); return True
app = Aplicacion("gui-comun-prueba", "Prueba")
falso = Falso()
app.translucidez = tr.Translucidez(tr.Decision(True, True, 0.75), "Prueba", falso)
acc = Acciones(); acc.estandar("Prueba", paneles=False)
acc.definir_menus([("&Ver", ["ventana.translucida"])])
app.exponer("acciones", acc)
ruta = os.path.join(os.environ["PRUEBA_TMP"], "Translucida.qml")
open(ruta, "w").write("""import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import GuiComun
VentanaBase { id: v; visible: true; width: 900; height: 600; acciones: studio.acciones
  function alfa(c) { return Math.round(c.a * 100) / 100 }
  function fondo(item) { return item && item.background ? alfa(item.background.color) : -1 }
  footer: BarraEstado { objectName: "pie"; resumen: "3 libros" }
  RowLayout { anchors.fill: parent
    PanelNavegacion { objectName: "nav"; Layout.fillHeight: true; secciones: [{nombre: "a", texto: "A", icono: "folder"}] }
    TablaDatos { objectName: "tabla"; Layout.fillWidth: true; Layout.fillHeight: true } } }
""")
app.motor.warnings.connect(lambda avisos: [print("AVISO", a.toString(), file=sys.stderr) for a in avisos])
assert app.cargar(ruta)
v = app.motor.rootObjects()[0]
r = {}
def leer():
    hijo = lambda n: v.findChild(QObject, n)
    col = v.property("color")
    return {"ventana": round(col.alphaF(), 2), "translucida": v.property("translucida"),
            "pie": hijo("pie").property("background").property("color").alphaF(),
            "nav": hijo("nav").property("background").property("color").alphaF(),
            "tabla": hijo("tabla").property("background").property("color").alphaF(),
            "menu": v.property("menuBar").property("background").property("color").alphaF(),
            "marcada": acc["ventana.translucida"].marcada, "habilitada": acc["ventana.translucida"].habilitada}
def paso1():
    r["activa"] = leer(); r["llamadas"] = list(falso.llamadas)
    acc.ejecutar("ventana.translucida")             # la apaga desde el menú, como el usuario
    QTimer.singleShot(200, paso2)
def paso2():
    r["apagada"] = leer(); r["llamadas_despues"] = list(falso.llamadas)
    print(json.dumps(r)); app.app.quit()
QTimer.singleShot(400, paso1)
app.app.exec()
'''
    r = correr_hijo(guion, tmp_path)
    datos = json.loads(r.stdout.strip().splitlines()[-1])
    activa, apagada = datos["activa"], datos["apagada"]
    assert activa["translucida"] and activa["ventana"] == 0.75, (activa, r.stderr[-2000:])
    assert activa["pie"] == 0 and activa["nav"] == 0 and activa["menu"] == 0       # dejan ver la única capa translúcida
    assert activa["tabla"] == 1                                                   # la zona de lectura, opaca
    assert activa["marcada"] and activa["habilitada"] and datos["llamadas"] == [True]
    assert not apagada["translucida"] and apagada["ventana"] == 1
    assert apagada["pie"] == apagada["nav"] == apagada["menu"] == apagada["tabla"] == 1
    assert not apagada["marcada"] and datos["llamadas_despues"] == [True, False]
