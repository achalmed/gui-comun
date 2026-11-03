"""test_visor_qtpdf.py — lo que `VistaPdf` hace con el texto del PDF cuando QtQuick.Pdf está instalado (3.2; de LaTeX
Studio, `tests/test_visor_qtpdf.py` y decisiones §1.11): seleccionar arrastrando con el ratón y copiar, seguir los
enlaces del PDF (internos: la página y el punto; externos: `VisorPdf.abrirEnlace`, que solo abre http, https y mailto)
y buscar con los resultados resaltados; el doble clic sigue llegando a la vista (`dobleClic`: SyncTeX en LaTeX) y la
marca de un recuadro sigue apareciendo.

La interacción es de verdad: un PDF con `hyperref` compilado con LuaLaTeX en una carpeta temporal, en una ventana sin
pantalla del Python del sistema, con el ratón movido por eventos de `QMouseEvent` (el PySide6 del sistema no trae
QtTest). Dos niveles: la capa sola (`CapaQtPdf` y `BusquedaQtPdf`, la misma prueba que LaTeX Studio) y la `VistaPdf`
entera con su controlador.
"""

from __future__ import annotations

import json
import shutil
import subprocess

import pytest

from conftest import PYTHON_SISTEMA, QML, REPO, entorno_hijo, requiere_kirigami

TEX = r"""\documentclass{article}
\usepackage{hyperref}
\begin{document}
\section{Inicio}\label{sec:inicio}
Texto de prueba con la palabra cometa. Véase la sección~\ref{sec:fin} y la página \url{https://example.org}.
\newpage
\section{Fin}\label{sec:fin}
Otra vez la palabra cometa y otra cometa más. Volver a~\ref{sec:inicio}.
\end{document}
"""

# el ratón, a mano (lo comparten los dos guiones)
RATON = r"""
from PySide6.QtCore import QEvent, QPointF
from PySide6.QtGui import QMouseEvent, QGuiApplication
from gui_comun.qt import Qt
reloj = [1000]
def raton(ventana, tipo, x, y, apretado=True, paso=40, boton_derecho=False):
    p = QPointF(x, y)
    izquierdo = Qt.MouseButton.RightButton if boton_derecho else Qt.MouseButton.LeftButton
    boton = izquierdo if tipo != QEvent.Type.MouseMove else Qt.MouseButton.NoButton
    botones = izquierdo if apretado else Qt.MouseButton.NoButton
    evento = QMouseEvent(tipo, p, ventana.mapToGlobal(p), boton, botones, Qt.KeyboardModifier.NoModifier)
    reloj[0] += paso
    evento.setTimestamp(reloj[0])           # el doble clic y el toque se miden con la marca de tiempo del evento
    QGuiApplication.sendEvent(ventana, evento)
def clic(ventana, x, y, paso=1000):
    raton(ventana, QEvent.Type.MouseButtonPress, x, y, paso=paso); raton(ventana, QEvent.Type.MouseButtonRelease, x, y, False)
def doble(ventana, x, y):
    clic(ventana, x, y); raton(ventana, QEvent.Type.MouseButtonPress, x, y)
    raton(ventana, QEvent.Type.MouseButtonDblClick, x, y, paso=0); raton(ventana, QEvent.Type.MouseButtonRelease, x, y, False)
def arrastrar(ventana, x0, y0, x1, y1):
    raton(ventana, QEvent.Type.MouseButtonPress, x0, y0)
    for k in range(1, 9):
        raton(ventana, QEvent.Type.MouseMove, x0 + (x1 - x0) * k / 8, y0 + (y1 - y0) * k / 8)
    raton(ventana, QEvent.Type.MouseButtonRelease, x1, y1, False)
"""

GUION_CAPA = r"""
import sys, json, os
sys.path.insert(0, sys.argv[1])
from gui_comun.qt import QGuiApplication, QTimer, QUrl
from PySide6.QtCore import QEvent, QMetaObject, Q_ARG, Q_RETURN_ARG
from PySide6.QtQuick import QQuickView
app = QGuiApplication(sys.argv)
sys.excepthook = lambda *e: (sys.__excepthook__(*e), app.exit(1))     # un fallo en un paso termina, no cuelga
""" + RATON + r"""
capas, pdf, ruta = sys.argv[2], sys.argv[3], sys.argv[4]
open(ruta, "w").write('''import QtQuick
import "file://%s"
Item {
    id: raiz
    width: 612; height: 792
    property var enlaces: []
    property int dobles: 0
    property var capa: null
    DocumentoQtPdf { id: doc; source: "%s" }
    BusquedaQtPdf { id: busqueda; document: doc }
    TapHandler { onDoubleTapped: raiz.dobles++ }
    ListView {
        id: lista
        anchors.fill: parent
        model: 2
        delegate: Item { width: 612; height: 792 }
        header: CapaQtPdf {
            id: capa
            width: 612; height: 792
            Component.onCompleted: raiz.capa = capa
            document: doc
            pagina: 1
            zoom: 1
            busqueda: busqueda
            onIrA: (p, y) => raiz.enlaces = raiz.enlaces.concat(["pagina " + p + " y " + Math.round(y)])
            onEnlaceExterno: (url) => raiz.enlaces = raiz.enlaces.concat([url])
        }
    }
    function buscar(texto) { busqueda.searchString = texto }
    function ir(n) { busqueda.currentResult = n }
    function cuenta() { return JSON.stringify({texto: capa.texto, desplazada: lista.contentY + 792, enlaces: enlaces, dobles: dobles, total: busqueda.count,
        resultados: busqueda.boundingPolygonsOnPage(0).length, actual: busqueda.currentResult,
        pagina: busqueda.currentResultLink.page, y: Math.round(busqueda.currentResultLink.location.y)}) }
}
''' % (capas, QUrl.fromLocalFile(pdf).toString()))
vista = QQuickView()
errores = []
vista.engine().warnings.connect(lambda avisos: errores.extend(a.toString() for a in avisos))
vista.setSource(QUrl.fromLocalFile(ruta))
if vista.status() != QQuickView.Status.Ready:
    print(json.dumps({"ok": False, "errores": [e.toString() for e in vista.errors()]})); sys.exit(0)
vista.show()
raiz = vista.rootObject()
pasos = {}
def leer():
    return json.loads(QMetaObject.invokeMethod(raiz, "cuenta", Q_RETURN_ARG("QVariant")))
# las posiciones (en puntos) salen del propio PDF: el texto empieza en x≈134 y la línea en y≈150; los enlaces, en la
# misma línea (el 2 de la sección en x≈385, la URL en x≈445)
def paso_arrastre():
    arrastrar(vista, 136, 152, 300, 155)
    QTimer.singleShot(200, paso_enlaces)
def paso_enlaces():
    pasos["arrastre"] = leer()
    clic(vista, 388, 154)                                       # el \ref interno
    QTimer.singleShot(600, lambda: clic(vista, 460, 154))       # la URL (pasado el intervalo de doble clic)
    QTimer.singleShot(1200, paso_clic)
def paso_clic():
    pasos["enlaces"] = leer()
    clic(vista, 300, 500)                                       # un clic fuera: borra la selección
    QTimer.singleShot(700, paso_doble)
def paso_doble():
    pasos["clic"] = leer()
    doble(vista, 300, 600)
    QTimer.singleShot(200, paso_buscar)
def paso_buscar():
    pasos["doble"] = leer()
    QMetaObject.invokeMethod(raiz, "buscar", Q_ARG("QVariant", "cometa"))
    QTimer.singleShot(1200, paso_siguiente)
def paso_siguiente():
    QMetaObject.invokeMethod(raiz, "ir", Q_ARG("QVariant", 2))
    QTimer.singleShot(200, paso_fin)
def paso_fin():
    pasos["busqueda"] = leer()
    app.quit()
QTimer.singleShot(800, paso_arrastre)
app.exec()
print(json.dumps({"ok": True, "errores": errores, **pasos}))
"""

GUION_VISTA = r"""
import sys, json, os
sys.path.insert(0, sys.argv[1])
from gui_comun.nucleo import Aplicacion
from gui_comun.visor_pdf import VisorPdf
from gui_comun.qt import QTimer, QDesktopServices
from PySide6.QtCore import QEvent, QPointF, QObject
from PySide6.QtQuick import QQuickItem
""" + RATON + r"""
pdf, ruta = sys.argv[2], sys.argv[3]
app = Aplicacion("gui-comun-prueba", "Prueba", version="0")
sys.excepthook = lambda *e: (sys.__excepthook__(*e), app.app.exit(1))
abiertos = []
QDesktopServices.openUrl = staticmethod(lambda url: abiertos.append(url.toString()) or True)   # ningún navegador de verdad
visor = VisorPdf(cache=os.path.join(os.environ["PRUEBA_TMP"], "cache-visor"))
visor.ajustarAncho = False
visor.zoom = 1.0
app.exponer("visor", visor)
open(ruta, "w").write('''import QtQuick
import GuiComun
Window {
    id: w
    visible: true; width: 760; height: 900
    property int dobles: 0
    property var ultimoDoble: []
    VistaPdf {
        id: v
        objectName: "vista"
        anchors.fill: parent
        visor: studio.visor
        textoPunto: "Ir al código de este punto"
        onDobleClic: (p, x, y) => { w.dobles++; w.ultimoDoble = [p, Math.round(x), Math.round(y)] }
    }
}
''')
errores = []
app.motor.warnings.connect(lambda avisos: errores.extend(a.toString() for a in avisos))
visor.abrir(pdf)
assert app.cargar(ruta), "no carga"
ventana = app.ventana()
raiz = app._raiz
vista = raiz.findChild(QQuickItem, "vista")
pasos = {}
def origen():
    # la esquina de la página 1 en la ventana, según la propia vista (aVentana)
    from PySide6.QtCore import QMetaObject, Q_ARG, Q_RETURN_ARG
    p = QMetaObject.invokeMethod(vista, "aVentana", Q_RETURN_ARG("QVariant"), Q_ARG("QVariant", 1), Q_ARG("QVariant", 0), Q_ARG("QVariant", 0))
    return p.x(), p.y()
def estado():
    b = vista.property("busqueda")
    return {"texto": vista.property("textoSeleccionado"), "dobles": raiz.property("dobles"),
            "ultimoDoble": raiz.property("ultimoDoble").toVariant() if hasattr(raiz.property("ultimoDoble"), "toVariant") else raiz.property("ultimoDoble"),
            "abiertos": list(abiertos), "pagina": vista.property("paginaActual"),
            "total": b.property("count") if b else -1, "actual": b.property("currentResult") if b else -9,
            "marca": vista.findChild(QObject, "marca").property("visible")}
def paso_arrastre():
    x, y = origen()
    pasos["origen"] = [round(x), round(y)]
    arrastrar(ventana, x + 136, y + 152, x + 300, y + 155)
    QTimer.singleShot(250, paso_copiar)
def paso_copiar():
    pasos["arrastre"] = estado()
    x, y = origen()
    clic(ventana, x + 460, y + 154)                        # la URL externa → abrirEnlace (sustituido arriba)
    QTimer.singleShot(700, paso_doble)
def paso_doble():
    pasos["enlace"] = estado()
    x, y = origen()
    doble(ventana, x + 300, y + 600)                       # doble clic en la página: llega a la vista (SyncTeX)
    QTimer.singleShot(300, paso_buscar)
def paso_buscar():
    pasos["doble"] = estado()
    vista.setProperty("buscando", True)
    vista.property("busqueda").setProperty("searchString", "cometa")
    QTimer.singleShot(1200, paso_resultado)
def paso_resultado():
    from PySide6.QtCore import QMetaObject, Q_ARG
    for _ in range(3):
        QMetaObject.invokeMethod(vista, "resultado", Q_ARG("QVariant", 1))     # 0 → 1 → 2: el tercero, en la página 2
    QTimer.singleShot(500, paso_marca)
def paso_marca():
    pasos["busqueda"] = estado()
    visor.marcarRecuadro(1, 100, 140, 200, 20)
    QTimer.singleShot(200, paso_fin)
def paso_fin():
    pasos["marca"] = estado()
    app.app.quit()
QTimer.singleShot(1500, paso_arrastre)
app.app.exec()
visor.apagar()
app.cerrar()
print(json.dumps({"ok": True, "errores": errores, "motor": visor.motor, **pasos}, default=str))
"""


@pytest.fixture(scope="module")
def pdf_con_enlaces(tmp_path_factory):
    if not shutil.which("lualatex"):
        pytest.skip("sin LuaLaTeX para el PDF con enlaces")
    carpeta = tmp_path_factory.mktemp("enlaces")
    (carpeta / "enlaces.tex").write_text(TEX, encoding="utf-8")
    for _ in range(2):                       # dos pasadas: la referencia cruzada resuelta
        subprocess.run(["lualatex", "-interaction=batchmode", "enlaces.tex"], cwd=carpeta, capture_output=True, timeout=180)
    pdf = carpeta / "enlaces.pdf"
    assert pdf.is_file()
    return pdf


def _hay_qtpdf() -> bool:
    r = subprocess.run([PYTHON_SISTEMA, "-c", "import sys; sys.path.insert(0, sys.argv[1]); from gui_comun.visor_pdf import hay_qtpdf; print(hay_qtpdf())",
                        str(REPO)], capture_output=True, text=True, timeout=60)
    return r.stdout.strip() == "True"


def _correr(guion: str, tmp_path, *args: str) -> dict:
    r = subprocess.run([PYTHON_SISTEMA, "-c", guion, str(REPO), *args], env=entorno_hijo(tmp_path, GUI_COMUN_VISOR=""),
                       capture_output=True, text=True, timeout=180)
    assert r.returncode == 0, r.stderr[-3000:]
    datos = json.loads(r.stdout.strip().splitlines()[-1])
    assert datos["ok"], datos
    graves = [e for e in datos["errores"] if "TypeError" in e or "ReferenceError" in e or "is not a type" in e or "Cannot assign" in e]
    assert not graves, "\n".join(graves)
    return datos


@requiere_kirigami
def test_capa_seleccion_enlaces_y_busqueda_con_el_raton(pdf_con_enlaces, tmp_path):
    """La prueba de LaTeX Studio sobre las capas de la base: arrastre, enlaces, clic suelto, doble clic y búsqueda."""
    if not _hay_qtpdf():
        pytest.skip("QtQuick.Pdf no está instalado (qml6-module-qtquick-pdf)")
    capas = tmp_path / "capas"
    capas.mkdir()
    for nombre in ("DocumentoQtPdf", "BusquedaQtPdf", "CapaQtPdf"):      # sin qmldir: la carpeta como importación
        shutil.copy2(QML / f"{nombre}.qml", capas / f"{nombre}.qml")
    datos = _correr(GUION_CAPA, tmp_path, str(capas), str(pdf_con_enlaces), str(tmp_path / "Prueba.qml"))
    assert datos["arrastre"]["texto"].startswith("Texto de prueba con la palabra"), datos["arrastre"]
    assert datos["arrastre"]["desplazada"] == 0                     # la lista no se movió con el arrastre
    assert datos["enlaces"]["enlaces"][0].startswith("pagina 2 y "), datos["enlaces"]
    assert datos["enlaces"]["enlaces"][1] == "https://example.org"
    assert datos["clic"]["texto"] == ""
    assert datos["doble"]["dobles"] == 1 and datos["doble"]["texto"] == ""
    b = datos["busqueda"]
    assert b["total"] == 3 and b["resultados"] == 1
    assert b["actual"] == 2 and b["pagina"] == 1 and b["y"] > 0


@requiere_kirigami
def test_vista_pdf_entera_con_el_raton(pdf_con_enlaces, tmp_path):
    """La VistaPdf de la base con su controlador: el arrastre selecciona (textoSeleccionado), la URL va a abrirEnlace,
    el doble clic emite dobleClic con el punto en puntos, la búsqueda cuenta y salta a la página 2, la marca aparece."""
    if not _hay_qtpdf():
        pytest.skip("QtQuick.Pdf no está instalado (qml6-module-qtquick-pdf)")
    d = _correr(GUION_VISTA, tmp_path, str(pdf_con_enlaces), str(tmp_path / "Vista.qml"))
    assert d["motor"] == "qtpdf", d
    assert "arrastre" in d, d
    assert d["arrastre"]["texto"].startswith("Texto de prueba con la palabra"), d["arrastre"]
    assert d["enlace"]["abiertos"] == ["https://example.org"], d["enlace"]
    assert d["doble"]["dobles"] == 1, d["doble"]
    pagina, x, y = d["doble"]["ultimoDoble"]
    assert pagina == 1 and abs(x - 300) <= 2 and abs(y - 600) <= 2
    assert d["busqueda"]["total"] == 3 and d["busqueda"]["actual"] == 2 and d["busqueda"]["pagina"] == 2, str(d["busqueda"]) + str(d["doble"])
    assert d["marca"]["marca"] is True


def test_abrir_enlace_solo_web_y_correo(app, tmp_path, monkeypatch):
    """Un enlace del PDF a `file:` o a una orden no se sigue; http, https y mailto van a la aplicación del escritorio."""
    from gui_comun import visor_pdf as vp
    abiertos = []
    monkeypatch.setattr(vp.QDesktopServices, "openUrl", staticmethod(lambda url: abiertos.append(url.toString()) or True))
    v = vp.VisorPdf(cache=tmp_path)
    avisos = []
    v.aviso.connect(lambda texto, nivel: avisos.append(nivel))
    assert v.abrirEnlace("https://example.org/a") and v.abrirEnlace("mailto:alguien@example.org")
    assert not v.abrirEnlace("file:///etc/hosts") and not v.abrirEnlace("javascript:alert(1)") and not v.abrirEnlace("relativo.pdf")
    assert abiertos == ["https://example.org/a", "mailto:alguien@example.org"]
    assert avisos == ["aviso", "aviso", "aviso"]
    v.apagar()
