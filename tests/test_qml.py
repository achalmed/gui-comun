"""test_qml.py — el módulo QML GuiComun con el Python y el Qt del sistema (Kirigami), sin pantalla:

- cada componente de `gui_comun/qml/GuiComun/` se instancia solo (con las propiedades mínimas) sin errores;
- la galería arranca, se cierra limpia y produce una captura;
- `Aplicacion` carga traducciones, expone `studio.<nombre>`, y explica el fallo cuando falta el QML.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import QML, correr_hijo, requiere_kirigami

AUXILIARES = ("ResaltadoSalida", "ResaltadoEditor", "GraficoQuickCharts", "DocumentoQtPdf", "PaginaQtPdf", "CapaQtPdf", "BusquedaQtPdf")      # los carga un Loader
COMPONENTES = sorted(p.stem for p in QML.glob("*.qml") if p.stem not in AUXILIARES)

# lo mínimo que cada componente necesita para instanciarse; `studio.*` lo pone el guion
PROPIEDADES = {
    "VentanaStudio": 'acciones: studio.acciones; tareas: studio.tareas; consola: studio.consola; visible: false',
    "MenuAcciones": 'acciones: studio.acciones; elementos: [{tipo: "accion", nombre: "a.uno"}, {tipo: "separador"}, {tipo: "menu", titulo: "Más", elementos: [{tipo: "accion", nombre: "a.dos"}]}]',
    "BotonAccion": 'accion: studio.acciones.accion("a.uno")',
    "PanelNavegacion": 'secciones: [{titulo: "Estado", filas: [{nombre: "t", texto: "Todos", icono: "folder", contador: 3}]}]',
    "TablaDatos": 'modelo: studio.tabla; columnas: [{ancho: 0, minimo: 8, conIcono: true}, {ancho: 6, semantica: true}]',
    "PanelDetalles": 'titulo: "uno"; subtitulo: "~/uno"; icono: "folder-git"; pestanas: [{titulo: "A"}, {titulo: "B", contador: 2}]',
    "PanelInferior": 'consola: studio.consola',
    "Mensajes": '',
    "PaletaOrdenes": 'acciones: studio.acciones',
    "DialogoAjustes": 'modulos: [{titulo: "General", icono: "configure", pagina: null}]',
    "BarraEstado": 'resumen: "3 cosas"; contexto: "uno · main"; tareas: studio.tareas',
    "ArbolDatos": 'modelo: studio.arbol; columnas: [{ancho: 0, minimo: 8, conIcono: true}, {ancho: 6, semantica: true}]; expandirAlCargar: -1',
    "CampoRuta": 'texto: "/tmp"; carpeta: true',
    "VistaTexto": 'texto: "# Hola\\n\\nun *documento*"; markdown: true; mensajeVacio: "nada"',
    "ListaDiagnosticos": 'modelo: studio.diagnosticos; mensajeVacio: "sin problemas"',
    "PaginaFormulario": 'campos: [{clave: "a", etiqueta: "A", tipo: "texto", defecto: "x"}, {clave: "n", etiqueta: "N", tipo: "entero", defecto: 3, minimo: 0, maximo: 10}, {clave: "o", etiqueta: "O", tipo: "opcion", defecto: "b", opciones: [["a", "Alfa"], ["b", "Beta"]]}, {clave: "c", etiqueta: "C", tipo: "casilla", defecto: true}, {clave: "k", etiqueta: "K", tipo: "color", defecto: "#ff0000"}, {clave: "r", etiqueta: "R", tipo: "carpeta"}, {clave: "m", etiqueta: "M", tipo: "multilinea"}, {clave: "d", etiqueta: "D", tipo: "decimal", defecto: 1.5}, {clave: "p", etiqueta: "P", tipo: "clave"}]',
    "VentanaBase": 'acciones: studio.acciones; tareas: studio.tareas; consola: studio.consola; visible: false; Rectangle { anchors.fill: parent; color: Kirigami.Theme.backgroundColor }',
    "TarjetaError": 'width: 600; error: ({descripcion: "No se pudo sincronizar", causa: "La rama divergió", recurso: "/tmp", accion: "Traiga los cambios", detalle: "$ git push\\nrejected", nivel: "error"}); detalleAbierto: true',
    "DialogoError": 'errores: studio.errores',
    "DialogoConfirmacion": 'acciones: studio.acciones; peticion: ({titulo: "Publicar", consecuencias: "Se subirá", operacionTexto: "Publicación", textoAceptar: "Publicar"})',
    "ElegirArchivos": 'multiple: true; filtros: ["Documentos PDF (*.pdf)", {nombre: "LaTeX", patrones: ["*.tex", "*.bib"]}]; carpetaInicial: "/tmp"',
    "ElegirCarpeta": 'carpetaInicial: "/tmp"',
    "GuardarComo": 'nombreSugerido: "informe.pdf"; sufijo: "pdf"; carpetaInicial: "/tmp"',
    "VistaComparacion": 'diferencia: studio.diferencia; accionesTrozo: [{clave: "preparar", texto: "Preparar trozo", icono: "list-add"}, {clave: "descartar", texto: "Descartar", icono: "edit-undo", noEnNuevo: true}]; seleccionable: true; filasElegidas: [2]',
    "EditorTexto": 'controlador: studio.editor; ruta: studio.rutaMuestra; definicion: "LaTeX"; width: 600; height: 400; Component.onCompleted: { cargar(); comentar(); irALinea(2, 1) }',
    "BarraBuscarReemplazar": 'visible: true; conReemplazo: true',
    "VistaPdf": 'visor: studio.visor; width: 600; height: 400; mensajeVacio: "Sin PDF"',
    "ListaErrores": 'modelo: studio.problemas; actual: 0; cabecera: [Text { text: "filtros" }]',
    "PasosEscritura": 'alcanzado: 3; actual: 2; cuentas: ["", "12", "1", "", "", ""]; bloqueado: true',
    "LineaPasos": 'titulo: "La puerta"; resumen: "en curso"; elegible: true; actual: 1; pasos: [{titulo: "Plan", explicacion: "qué", estado: "hecho", detalle: "listo"}, {titulo: "Ejecutar", explicacion: "la escritura", estado: "en_curso", detalle: ""}, {titulo: "Verificar", explicacion: "en el disco", estado: "pendiente", detalle: ""}]',
    "GraficoXY": 'width: 500; height: 300; datos: ({lineas: [{nombre: "IS", rol: "azul", x: [0, 1, 2], y: [2, 1, 0]}, {nombre: "LM", rol: "rojo", x: [0, 2], y: [0, 2]}], equilibrio: {x: 1, y: 1}, verticales: [{x: 1.5, nombre: "Y*", rol: "verde"}], limites: {xMin: 0, xMax: 2, yMin: 0, yMax: 2}, etiquetaX: "Y", etiquetaY: "r"}); base: ({lineas: [{nombre: "IS0", rol: "morado", x: [0, 2], y: [1.5, 0]}], limites: {xMin: 0, xMax: 2, yMin: 0, yMax: 2}}); invalido: "SIN VERIFICAR"',
    "PaletaCategorica": 'property color c0: indice(0); property color c1: indice(1); property color azul: rol("azul"); property color cian: rol("cian")',
    "EtiquetaNivel": 'text: "conflicto"; nivel: "negativo"; icono: "data-warning"',
    "Grafico": 'series: [{nombre: "a", y: [1, 2, 3]}, {nombre: "b", y: [3, 2, 1]}]; etiquetasX: ["0", "1", "2"]; xMaximo: 2; yMaximo: 3; equilibrio: ({x: 1, y: 2, etiqueta: "E"}); marcas: [{x: 1, etiqueta: "x"}]; anotacion: "nota"',
}

GUION = r'''
import os, sys, json
sys.path.insert(0, sys.argv[1])
from gui_comun.nucleo import Aplicacion
from gui_comun.acciones import Acciones
from gui_comun.consola import Consola
from gui_comun.tareas import Tareas
from gui_comun.modelos import ModeloLista, ModeloFiltrado, ModeloArbol
from gui_comun.qt import QUrl, QTimer, Qt
from gui_comun import diferencias as _dif
from gui_comun.editor import ControladorEditor
from gui_comun.visor_pdf import VisorPdf
app = Aplicacion("gui-comun-prueba", "Prueba", version="0")
acciones = Acciones(); acciones.estandar("Prueba")
acciones.registrar("a.uno", "&Uno", "list-add", "F5", "G", descripcion="la primera")
acciones.registrar("a.dos", "&Dos", "", None, "G", marcable=True)
acciones.definir_menus([("&Archivo", ["a.uno", "|", "a.dos", "|", "app.salir"]), ("&Ver", ["ventana.navegacion", "ventana.detalles", "ventana.inferior", ("Sub", ["a.dos"])])])
acciones.definir_barra(["a.uno", "|", "a.dos"])
consola = Consola(); tareas = Tareas(consola)
tabla = ModeloFiltrado(ModeloLista(("display", "nivel", "icono"), [{"display": "uno", "nivel": "positivo", "icono": "vcs-normal"}, {"display": "dos", "nivel": "negativo", "icono": "vcs-conflicting"}]))
arbol = ModeloArbol(("Nombre", "Estado"), [{"valores": ["uno", "ok"], "nivel": "positivo", "icono": "folder", "hijos": [{"valores": ["uno/a", ""]}]}, {"valores": ["dos", "mal"], "nivel": "negativo"}])
diagnosticos = ModeloLista(("nivel", "mensaje", "archivo", "linea"), [{"nivel": "error", "mensaje": "Undefined control sequence.", "archivo": "./a.tex", "linea": 4}, {"nivel": "aviso", "mensaje": "Reference `x' undefined", "archivo": "./a.tex", "linea": 3}])
muestra = os.path.join(os.environ["PRUEBA_TMP"], "muestra.tex")
open(muestra, "w").write("\\documentclass{article}\n\\begin{document}\nHola\n\\end{document}\n")
editor = ControladorEditor(consola)
visor = VisorPdf(cache=os.path.join(os.environ["PRUEBA_TMP"], "cache-visor"))
problemas = ModeloLista(("nivel", "titulo", "mensaje", "causa", "accion", "detalle", "ubicacion", "linea"), [{"nivel": "error", "titulo": "Orden desconocida", "mensaje": "Undefined control sequence.", "causa": "Una errata", "accion": "Corríjala", "detalle": "l.4 \\holaa", "ubicacion": "a.tex", "linea": 4}, {"nivel": "aviso", "titulo": "", "mensaje": "Reference undefined", "causa": "", "accion": "", "detalle": "", "ubicacion": "", "linea": 0}])
diferencia = _dif.comparar("uno\ndos\ntres\n", "uno\nDOS\ntres\ncuatro\n", ruta="a.txt", izquierda="Instalado", derecha="Generado")
diferencia["notas"] = ["Un secreto oculto"]
app.exponer("rutaMuestra", muestra)
for n, o in (("acciones", acciones), ("consola", consola), ("tareas", tareas), ("tabla", tabla), ("arbol", arbol), ("diagnosticos", diagnosticos),
             ("editor", editor), ("visor", visor), ("problemas", problemas), ("diferencia", diferencia)): app.exponer(n, o)
componente, props = sys.argv[2], sys.argv[3]
ruta = os.path.join(os.environ["PRUEBA_TMP"], "Prueba_" + componente + ".qml")
cuerpo = "import QtQuick\nimport org.kde.kirigami as Kirigami\nimport GuiComun\n%s { id: raiz; %s }\n" % (componente, props)
if componente not in ("VentanaStudio", "VentanaBase"):
    cuerpo = "import QtQuick\nimport org.kde.kirigami as Kirigami\nimport GuiComun\nWindow { visible: false; width: 900; height: 600; %s { id: raiz; %s } }\n" % (componente, props)
open(ruta, "w").write(cuerpo)
errores = []
app.motor.warnings.connect(lambda avisos: errores.extend(a.toString() for a in avisos))
ok = app.cargar(ruta)
QTimer.singleShot(400, app.app.quit)
app.app.exec()
editor.soltar(); visor.apagar()
app.cerrar()
print(json.dumps({"ok": ok, "errores": errores, "traducciones": app.traducciones, "studio": app.studio.keys()}))
'''


@requiere_kirigami
@pytest.mark.parametrize("componente", COMPONENTES)
def test_carga_cada_componente(componente, tmp_path):
    import json
    r = correr_hijo(GUION, tmp_path, componente, PROPIEDADES.get(componente, ""), plazo=120)
    assert r.returncode == 0, r.stderr[-3000:]
    datos = json.loads(r.stdout.strip().splitlines()[-1])
    assert datos["ok"], r.stderr[-3000:]
    graves = [e for e in datos["errores"] if "TypeError" in e or "ReferenceError" in e or "is not a type" in e or "Cannot assign" in e]
    assert not graves, "\n".join(graves)
    assert "qtbase_es" in datos["traducciones"] and "libkirigami6_qt" in datos["traducciones"]
    assert {"acciones", "consola", "tareas", "tabla", "errores", "escritorio", "aplicacionStudio"} <= set(datos["studio"])


def test_qmldir_declara_cada_componente():
    declarados = {l.split()[0] for l in (QML / "qmldir").read_text(encoding="utf-8").splitlines() if l and not l.startswith("module")}
    assert declarados == set(COMPONENTES)


def test_sin_colores_propios():
    """Cero colores, fuentes o tamaños propios en el módulo: solo Kirigami.Theme y Kirigami.Units."""
    import re
    malos = []
    for qml in QML.glob("*.qml"):
        for n, linea in enumerate(qml.read_text(encoding="utf-8").splitlines(), 1):
            sin_comentario = linea.split("//")[0]
            if re.search(r'"#[0-9a-fA-F]{3,8}"', sin_comentario) or re.search(r'\bfont\.(pointSize|pixelSize|family)\s*:\s*["\d]', sin_comentario):
                malos.append(f"{qml.name}:{n}: {linea.strip()}")
    assert not malos, "\n".join(malos)


@requiere_kirigami
def test_galeria_arranca_y_captura(tmp_path):
    import subprocess
    from conftest import PYTHON_SISTEMA, REPO, entorno_hijo
    captura = tmp_path / "galeria.png"
    r = subprocess.run([PYTHON_SISTEMA, "-m", "gui_comun.galeria", "--captura", str(captura)], cwd=REPO,
                       env=entorno_hijo(tmp_path), capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr[-3000:]
    assert captura.is_file() and captura.stat().st_size > 10_000
    ruido = [l for l in r.stderr.splitlines() if "TypeError" in l or "ReferenceError" in l]
    assert not ruido, "\n".join(ruido)


@requiere_kirigami
def test_aplicacion_explica_el_fallo(tmp_path):
    guion = r'''
import sys; sys.path.insert(0, sys.argv[1])
from gui_comun.nucleo import Aplicacion
import os
app = Aplicacion("gui-comun-prueba", "Prueba")
ruta = os.path.join(os.environ["PRUEBA_TMP"], "Mal.qml")
open(ruta, "w").write("import org.kde.noexiste\nItem {}\n")
print("CARGA", app.cargar(ruta))
print(app.mensaje_de_fallo())
'''
    r = correr_hijo(guion, tmp_path)
    assert r.returncode == 0, r.stderr[-2000:]
    assert "CARGA False" in r.stdout and "no se pudo cargar la interfaz QML" in r.stderr


@requiere_kirigami
def test_panel_detalles_conserva_las_pestanas(tmp_path):
    """Cambiar un contador o la visibilidad de una pestaña no recrea los botones ni mueve la pestaña actual; si la actual
    pasa a oculta, salta a la primera visible (2.4.0: Biblioteca Studio cambia la lista de pestañas por vista)."""
    guion = r'''
import sys, os, json; sys.path.insert(0, sys.argv[1])
from gui_comun.nucleo import Aplicacion
from gui_comun.qt import QTimer
app = Aplicacion("gui-comun-prueba", "Prueba")
ruta = os.path.join(os.environ["PRUEBA_TMP"], "Detalles.qml")
open(ruta, "w").write("""import QtQuick
import GuiComun
Window { visible: false; width: 900; height: 600
  PanelDetalles { id: raiz; titulo: "uno"; pestanas: [{titulo: "A"}, {titulo: "B", contador: 2}, {titulo: "C"}]
    Item { objectName: "a" } Item { objectName: "b" } Item { objectName: "c" } } }
""")
errores = []
app.motor.warnings.connect(lambda avisos: errores.extend(a.toString() for a in avisos))
ok = app.cargar(ruta)
panel = app.motor.rootObjects()[0].findChild(type(app.motor.rootObjects()[0]).__mro__[0], "") if False else None
raiz = app.motor.rootObjects()[0]
from gui_comun.qt import QObject
panel = [c for c in raiz.findChildren(QObject) if c.property("pestanas") is not None and c.property("anchoPreferido") is not None][0]
panel.setProperty("pestanaActual", 1)
panel.setProperty("pestanas", [{"titulo": "A"}, {"titulo": "B", "contador": 5}, {"titulo": "C"}])
sigue = panel.property("pestanaActual")
panel.setProperty("pestanas", [{"titulo": "A", "visible": False}, {"titulo": "B", "visible": False}, {"titulo": "C"}])
salta = panel.property("pestanaActual")
QTimer.singleShot(300, app.app.quit); app.app.exec()
app.cerrar()
print(json.dumps({"ok": ok, "sigue": sigue, "salta": salta, "errores": errores}))
'''
    import json
    r = correr_hijo(guion, tmp_path)
    assert r.returncode == 0, r.stderr[-3000:]
    datos = json.loads(r.stdout.strip().splitlines()[-1])
    assert datos["ok"] and datos["sigue"] == 1 and datos["salta"] == 2
    assert not [e for e in datos["errores"] if "TypeError" in e], "\n".join(datos["errores"])


@requiere_kirigami
def test_pagina_formulario_valores(tmp_path):
    """Los valores son lo escrito sin los vacíos; `poner` y `fijar` los cambian y cada edición emite `cambiado` (2.7.0: Raphi
    Studio arma sus opciones desde las fichas del motor)."""
    guion = r'''
import sys, os, json; sys.path.insert(0, sys.argv[1])
from gui_comun.nucleo import Aplicacion
from gui_comun.qt import QTimer, QObject
app = Aplicacion("gui-comun-prueba", "Prueba")
ruta = os.path.join(os.environ["PRUEBA_TMP"], "Formulario.qml")
open(ruta, "w").write("""import QtQuick
import GuiComun
Window { visible: false; width: 900; height: 600
  PaginaFormulario { id: raiz; objectName: "f"; width: 800; campos: [{clave: "a", etiqueta: "A", tipo: "texto", defecto: "x"}, {clave: "n", etiqueta: "N", tipo: "entero", defecto: 3}, {clave: "c", etiqueta: "C", tipo: "casilla", defecto: true}, {clave: "o", etiqueta: "O", tipo: "opcion", opciones: [["a", "Alfa"], ["b", "Beta"]]}] } }
""")
errores = []
app.motor.warnings.connect(lambda avisos: errores.extend(a.toString() for a in avisos))
ok = app.cargar(ruta)
f = app.motor.rootObjects()[0].findChild(QObject, "f")
avisos = []
f.cambiado.connect(lambda clave, valor: avisos.append([clave, valor]))
vacios = f.property("valores").toVariant()
f.poner({"a": "hola", "n": 7, "vacio": ""})
puestos = f.property("valores").toVariant()
f.fijar("c", False); f.fijar("a", "")
fijados = f.property("valores").toVariant()
defecto = f.valor("a")
f.restablecer()
campos = f.property("nCampos")
QTimer.singleShot(300, app.app.quit); app.app.exec()
app.cerrar()
print(json.dumps({"ok": ok, "vacios": vacios, "puestos": puestos, "fijados": fijados, "defecto": defecto, "avisos": avisos, "campos": campos, "errores": errores}))
'''
    import json
    r = correr_hijo(guion, tmp_path)
    assert r.returncode == 0, r.stderr[-3000:]
    datos = json.loads(r.stdout.strip().splitlines()[-1])
    assert datos["ok"] and datos["campos"] == 4
    assert datos["vacios"] == {} and datos["puestos"] == {"a": "hola", "n": 7}
    assert datos["fijados"] == {"n": 7, "c": False} and datos["defecto"] == "x"
    assert datos["avisos"] == [["c", False], ["a", ""]]
    assert not [e for e in datos["errores"] if "TypeError" in e or "ReferenceError" in e], "\n".join(datos["errores"])


@requiere_kirigami
def test_ventana_base_confirma_y_presenta_errores(tmp_path):
    """3.0: en VentanaBase, una publicación no se ejecuta al dispararla sino al aceptar su diálogo; un error presentado
    abre el diálogo de errores; el contenido es libre; las rutas con espacios van y vuelven de URL sin «%20»."""
    guion = r'''
import sys, os, json; sys.path.insert(0, sys.argv[1])
from gui_comun.nucleo import Aplicacion
from gui_comun.acciones import Acciones
from gui_comun.qt import QTimer, QObject
from gui_comun.qt import QMetaObject
app = Aplicacion("gui-comun-prueba", "Prueba")
acc = Acciones(); acc.estandar("Prueba", paneles=False)
hechos = []
acc.registrar("sitio.publicar", "&Publicar el sitio", "document-send", "Ctrl+Shift+P", "Sitio", operacion="publicacion",
              consecuencias="Se subirán 3 archivos", al_disparar=lambda: hechos.append("publicado"))
acc.definir_menus([("&Archivo", ["sitio.publicar", "|", "app.salir"])])
app.exponer("acciones", acc)
ruta = os.path.join(os.environ["PRUEBA_TMP"], "Base.qml")
modulo = os.path.join(sys.argv[1], "gui_comun", "qml", "GuiComun", "rutas.js")
open(ruta, "w").write("""import QtQuick
import GuiComun
import "file://%s" as Rutas
VentanaBase { id: v; visible: true; width: 900; height: 600; acciones: studio.acciones
  property string ida: Rutas.aUrl("/home/x/00 metodo/a#b.tex")
  property string vuelta: Rutas.deUrl(ida)
  property var filtros: Rutas.filtros(["PDF (*.pdf)", {nombre: "LaTeX", patrones: ["*.tex", "*.bib"]}], true)
  Rectangle { objectName: "lienzo"; anchors.fill: parent } }
""" % modulo)
errores = []
app.motor.warnings.connect(lambda avisos: errores.extend(a.toString() for a in avisos))
ok = app.cargar(ruta)
v = app.motor.rootObjects()[0]
r = {"ok": ok}
def paso1():
    try:
        acc.ejecutar("sitio.publicar")
        c = v.findChild(QObject, "confirmacion")
        r["pedida"] = bool(c.property("visible"))
        r["antes"] = list(hechos)
        QMetaObject.invokeMethod(c, "accept")
        r["despues"] = list(hechos)
        app.error("No se pudo publicar", "Sin conexión", "/tmp", "Reintente", "detalle")
        QTimer.singleShot(300, paso2)
    except Exception as exc:
        r["fallo"] = repr(exc); app.app.quit()
def paso2():
    try:
        d = v.findChild(QObject, "dialogoError")
        r["error_abierto"] = bool(d.property("visible"))
        r["lienzo"] = v.findChild(QObject, "lienzo") is not None
        r["ida"], r["vuelta"] = v.property("ida"), v.property("vuelta")
        f = v.property("filtros")
        r["filtros"] = f.toVariant() if hasattr(f, "toVariant") else f
    except Exception as exc:
        r["fallo"] = repr(exc)
    app.app.quit()
QTimer.singleShot(300, paso1)
app.app.exec(); app.cerrar()
r["errores"] = errores
print(json.dumps(r))
'''
    import json
    r = correr_hijo(guion, tmp_path)
    assert r.returncode == 0, r.stderr[-3000:]
    datos = json.loads(r.stdout.strip().splitlines()[-1])
    assert "fallo" not in datos, datos.get("fallo")
    assert datos["ok"] and datos["pedida"] and datos["antes"] == [] and datos["despues"] == ["publicado"]
    assert datos["error_abierto"] and datos["lienzo"]
    assert datos["ida"] == "file:///home/x/00%20metodo/a%23b.tex" and datos["vuelta"] == "/home/x/00 metodo/a#b.tex"
    assert datos["filtros"] == ["PDF (*.pdf)", "LaTeX (*.tex *.bib)", "Todos los archivos (*)"]
    assert not [e for e in datos["errores"] if "TypeError" in e or "ReferenceError" in e or "Unable to assign" in e], "\n".join(datos["errores"])


GUION_VISOR = r'''
import os, sys, json
sys.path.insert(0, sys.argv[1])
from gui_comun.nucleo import Aplicacion
from gui_comun.visor_pdf import VisorPdf
from gui_comun.qt import QTimer
app = Aplicacion("gui-comun-prueba", "Prueba", version="0")
visor = VisorPdf(cache=os.path.join(os.environ["PRUEBA_TMP"], "cache-visor"))
app.exponer("visor", visor)
ruta = os.path.join(os.environ["PRUEBA_TMP"], "Visor.qml")
open(ruta, "w").write("import QtQuick\nimport GuiComun\nWindow { visible: true; width: 700; height: 500\n"
                      " VistaPdf { id: v; objectName: 'visor'; anchors.fill: parent; visor: studio.visor }\n"
                      " Timer { interval: 300; running: true; onTriggered: { studio.visor.marcarRecuadro(2, 50, 60, 100, 20) } } }\n")
errores = []
app.motor.warnings.connect(lambda avisos: errores.extend(a.toString() for a in avisos))
visor.abrir(sys.argv[2])
ok = app.cargar(ruta)
estado = {}
def mirar():
    filas = visor.paginas.todas()
    estado.update(motor=visor.motor, total=visor.total, imagenes=sum(1 for f in filas if f["imagen"]))
    app.app.quit()
QTimer.singleShot(2500, mirar)
app.app.exec()
visor.apagar()
app.cerrar()
print(json.dumps({"ok": ok, "errores": errores, **estado}))
'''


@requiere_kirigami
@pytest.mark.parametrize("motor", ["qtpdf", "pdftoppm"])
def test_visor_pdf_con_un_documento(motor, tmp_path):
    """El visor abre un PDF de dos páginas sin avisos con los dos motores; con pdftoppm, las páginas visibles se
    renderizan por demanda (QtPdf las pinta Qt: no hay imágenes en el modelo)."""
    import json
    import shutil
    from conftest import PYTHON_SISTEMA, REPO, entorno_hijo
    from test_comunes_31 import _pdf
    if motor == "pdftoppm" and not shutil.which("pdftoppm"):
        pytest.skip("sin poppler")
    pdf = _pdf(tmp_path / "doc.pdf", 2)
    env = entorno_hijo(tmp_path, GUI_COMUN_VISOR="pdftoppm" if motor == "pdftoppm" else "")
    import subprocess
    r = subprocess.run([PYTHON_SISTEMA, "-c", GUION_VISOR, str(REPO), str(pdf)], env=env, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr[-3000:]
    d = json.loads(r.stdout.strip().splitlines()[-1])
    assert d["ok"] and not d["errores"], d["errores"]
    assert d["total"] == 2
    if motor == "pdftoppm":
        assert d["motor"] == "pdftoppm" and d["imagenes"] >= 1
    elif d["motor"] != "qtpdf":
        pytest.skip("QtQuick.Pdf no está instalado")
