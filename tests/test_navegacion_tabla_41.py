"""test_navegacion_tabla_41.py — lo que 4.1 añadió a la tabla y al panel de navegación, con el ratón de verdad (eventos
`QMouseEvent` en una ventana sin pantalla del Python del sistema, que no trae QtTest):

- `TablaDatos`: un clic elige la fila entera (Ctrl añade, Mayús el tramo); arrastrar el borde derecho de una cabecera cambia el ancho de su columna (antes solo se podía en el
  cuerpo, donde nadie lo busca), sin ordenar; doble clic en el borde lo devuelve; una columna con `lineas` parte el
  texto largo y su fila crece lo justo, las cortas no;
- `PanelNavegacion`: las filas hijas se ven solo con su rama desplegada; elegir una escondida despliega sus ancestros;
  el contenido deja sitio a la barra de desplazamiento (los contadores no quedan debajo).
"""

from __future__ import annotations

import json

from conftest import correr_hijo, requiere_kirigami

GUION = r'''
import os, sys, json
os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, sys.argv[1])
from gui_comun.qt import QGuiApplication, QQmlApplicationEngine, QUrl, QTimer
from PySide6.QtCore import QEvent, QPointF, Qt, QMetaObject, Q_RETURN_ARG, Q_ARG
from PySide6.QtGui import QMouseEvent
from gui_comun.nucleo import RUTA_QML
from gui_comun.modelos import ModeloTabla

app = QGuiApplication(sys.argv[:1])
app.setOrganizationName("prueba-gui-comun"); app.setApplicationName("tabla-41")
modelo = ModeloTabla([("Proyecto", "a"), ("Estado", "b"), ("Motor", "c")])
modelo.poner([{"a": "representacion/2026-11_SR-04_documento-de-la-semana-de-representacion/principal.tex" if i == 0 else "corto.tex",
               "b": "x", "c": "y"} for i in range(40)])
motor = QQmlApplicationEngine()
motor.addImportPath(str(RUTA_QML))
motor.rootContext().setContextProperty("datosPrueba", modelo)
motor.loadData("""
import QtQuick
import QtQuick.Window
import GuiComun
Window {
    width: 800; height: 400; visible: true
    function medir() {
        tabla.vista.forceLayout()
        return JSON.stringify({anchos: [0, 1, 2].map(c => tabla.vista.columnWidth(c)), orden: tabla.columnaOrden,
                               altos: [tabla.vista.rowHeight(0), tabla.vista.rowHeight(1)], altoFila: tabla.altoFila,
                               elegidas: tabla.filasSeleccionadas(), actual: tabla.filaActual})
    }
    function centroFila(r) {     // la y de la mitad de una fila, en la ventana
        let y = tabla.vista.mapToItem(null, 0, 0).y
        for (let i = 0; i < r; i++) y += tabla.vista.rowHeight(i)
        return JSON.stringify(y + tabla.vista.rowHeight(r) / 2)
    }
    function panelEstado() {
        const vistos = []
        function recorrer(item) {
            for (const h of item.children) {
                if (h.modelData !== undefined && h.modelData.nombre !== undefined && h.visible) vistos.push(h.modelData.nombre)
                recorrer(h)
            }
        }
        recorrer(panel)
        return JSON.stringify({vistos: vistos, abiertos: Object.keys(panel.abiertos).sort()})
    }
    property string elegida: ""
    onElegidaChanged: panel.actual = elegida
    Row {
        anchors.fill: parent
        PanelNavegacion {
            id: panel
            width: 200; height: 120
            secciones: [{ titulo: "Proyectos", filas: [
                { nombre: "Todas", texto: "Todos", icono: "folder", contador: 9 },
                { nombre: "A", texto: "Categoría A", icono: "folder", contador: 5, nivel: 0, plegable: true, ancestros: [] },
                { nombre: "A › x", texto: "x", icono: "folder", contador: 3, nivel: 1, plegable: true, ancestros: ["A"] },
                { nombre: "A › x › 2026", texto: "2026", icono: "folder", contador: 2, nivel: 2, ancestros: ["A", "A › x"] },
                { nombre: "A › y", texto: "y", icono: "folder", contador: 2, nivel: 1, ancestros: ["A"] },
                { nombre: "B", texto: "Categoría B", icono: "folder", contador: 4 },
                { nombre: "C", texto: "Categoría C", icono: "folder", contador: 4 },
                { nombre: "D", texto: "Categoría D", icono: "folder", contador: 4 } ] }]
        }
        TablaDatos {
            id: tabla
            width: 600; height: 400
            modelo: datosPrueba
            columnas: [{ancho: 0, minimo: 8, lineas: 3, cortarTras: "/"}, {ancho: 10}, {ancho: 10}]
        }
    }
}
""".encode())
ventana = motor.rootObjects()[0]
reloj = [1000]
def raton(tipo, x, y, apretado=True, paso=40, mod=Qt.NoModifier):
    p = QPointF(x, y)
    boton = Qt.LeftButton if tipo != QEvent.MouseMove else Qt.NoButton
    ev = QMouseEvent(tipo, p, ventana.mapToGlobal(p), boton, Qt.LeftButton if apretado else Qt.NoButton, mod)
    reloj[0] += paso
    ev.setTimestamp(reloj[0])
    QGuiApplication.sendEvent(ventana, ev)
    app.processEvents()
def arrastrar(x0, y, dx):
    raton(QEvent.MouseMove, x0, y, False)
    raton(QEvent.MouseButtonPress, x0, y, paso=1000)
    for k in range(1, 11):
        raton(QEvent.MouseMove, x0 + dx * k / 10, y)
    raton(QEvent.MouseButtonRelease, x0 + dx, y, False)
def llamar(nombre, *args):
    return json.loads(QMetaObject.invokeMethod(ventana, nombre, Q_RETURN_ARG("QVariant"), *args))
salida = {}
def correr():
    try:
        X = 200                                    # la tabla empieza tras el panel
        salida["inicio"] = llamar("medir")
        a = salida["inicio"]["anchos"]
        arrastrar(X + a[0] - 2, 10, -150)          # el borde de la primera cabecera
        salida["estrecha"] = llamar("medir")
        a = salida["estrecha"]["anchos"]
        arrastrar(X + a[0] + a[1] - 2, 10, 60)     # el de la segunda
        salida["segunda"] = llamar("medir")
        a = salida["segunda"]["anchos"]
        x = X + a[0] - 2                           # doble clic en el borde: vuelve a su ancho
        raton(QEvent.MouseMove, x, 10, False)
        raton(QEvent.MouseButtonPress, x, 10, paso=1000); raton(QEvent.MouseButtonRelease, x, 10, False)
        raton(QEvent.MouseButtonPress, x, 10); raton(QEvent.MouseButtonDblClick, x, 10, paso=0); raton(QEvent.MouseButtonRelease, x, 10, False)
        salida["doble"] = llamar("medir")
        def clic_fila(r, mod=Qt.NoModifier):
            y = llamar("centroFila", Q_ARG("QVariant", r))
            raton(QEvent.MouseMove, X + 300, y, False)
            raton(QEvent.MouseButtonPress, X + 300, y, paso=1000, mod=mod); raton(QEvent.MouseButtonRelease, X + 300, y, False, mod=mod)
        clic_fila(2)
        salida["clic"] = llamar("medir")
        clic_fila(4, Qt.ControlModifier)
        salida["ctrl"] = llamar("medir")
        clic_fila(6, Qt.ShiftModifier)
        salida["mayus"] = llamar("medir")
        salida["panel_inicio"] = llamar("panelEstado")
        ventana.setProperty("elegida", "A › x › 2026")
        app.processEvents()
        salida["panel_elegida"] = llamar("panelEstado")
    except Exception as e:
        salida["error"] = repr(e)
    finally:
        print("RESULTADO " + json.dumps(salida))
        app.quit()
QTimer.singleShot(400, correr)
app.exec()
'''


@requiere_kirigami
def test_tabla_redimensiona_desde_la_cabecera_y_panel_en_arbol(tmp_path):
    r = correr_hijo(GUION, tmp_path)
    linea = next((l for l in r.stdout.splitlines() if l.startswith("RESULTADO ")), None)
    assert linea, r.stdout + r.stderr
    s = json.loads(linea[len("RESULTADO "):])
    assert "error" not in s, s
    inicio, estrecha, segunda, doble = s["inicio"], s["estrecha"], s["segunda"], s["doble"]
    # la cabecera redimensiona y no ordena
    assert abs(estrecha["anchos"][0] - (inicio["anchos"][0] - 150)) <= 3, s
    assert estrecha["orden"] == -1, s
    assert abs(segunda["anchos"][1] - (inicio["anchos"][1] + 60)) <= 3, s
    assert abs(doble["anchos"][0] - (600 - doble["anchos"][1] - doble["anchos"][2])) <= 1, s   # vuelve a tomar el resto
    # el nombre largo se parte en varias líneas cuando no cabe; el corto no
    assert estrecha["altos"][0] > estrecha["altoFila"] and estrecha["altos"][1] == estrecha["altoFila"], s
    # un clic elige la fila entera (antes solo movía la celda actual); Ctrl añade; Mayús, el tramo
    assert (s["clic"]["elegidas"], s["clic"]["actual"]) == ([2], 2), s
    assert s["ctrl"]["elegidas"] == [2, 4], s
    assert s["mayus"]["elegidas"] == [4, 5, 6], s           # desde la última elegida, como en Dolphin
    # el panel: plegado al inicio; elegir una fila escondida despliega sus ancestros
    assert "A › x" not in s["panel_inicio"]["vistos"] and "A" in s["panel_inicio"]["vistos"], s
    assert s["panel_elegida"]["abiertos"] == ["A", "A › x"], s
    assert {"A › x", "A › x › 2026", "A › y"} <= set(s["panel_elegida"]["vistos"]), s
