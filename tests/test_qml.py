"""test_qml.py — el módulo QML GuiComun con el Python y el Qt del sistema (Kirigami), sin pantalla:

- cada componente de `gui_comun/qml/GuiComun/` se instancia solo (con las propiedades mínimas) sin errores;
- la galería arranca, se cierra limpia y produce una captura;
- `Aplicacion` carga traducciones, expone `studio.<nombre>`, y explica el fallo cuando falta el QML.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import QML, correr_hijo, requiere_kirigami

COMPONENTES = sorted(p.stem for p in QML.glob("*.qml") if p.stem != "ResaltadoSalida")

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
for n, o in (("acciones", acciones), ("consola", consola), ("tareas", tareas), ("tabla", tabla), ("arbol", arbol), ("diagnosticos", diagnosticos)): app.exponer(n, o)
componente, props = sys.argv[2], sys.argv[3]
ruta = os.path.join(os.environ["PRUEBA_TMP"], "Prueba_" + componente + ".qml")
cuerpo = "import QtQuick\nimport GuiComun\n%s { id: raiz; %s }\n" % (componente, props)
if componente != "VentanaStudio":
    cuerpo = "import QtQuick\nimport GuiComun\nWindow { visible: false; width: 900; height: 600; %s { id: raiz; %s } }\n" % (componente, props)
open(ruta, "w").write(cuerpo)
errores = []
app.motor.warnings.connect(lambda avisos: errores.extend(a.toString() for a in avisos))
ok = app.cargar(ruta)
QTimer.singleShot(400, app.app.quit)
app.app.exec()
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
    assert {"acciones", "consola", "tareas", "tabla"} <= set(datos["studio"])


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
