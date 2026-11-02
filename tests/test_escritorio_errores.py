"""test_escritorio_errores.py — 3.0: la integración con el escritorio (sin abrir nada: se inyecta el lanzador) y los
errores presentables (explicar causas, la cola, las tareas que fallan, la verificación aparte del éxito)."""

from __future__ import annotations

import errno
import time

import pytest

from conftest import requiere_binding


class Lanzador:
    """Anota lo que se lanzaría y lo que se abriría con la aplicación asociada; no arranca nada."""

    def __init__(self, programas=("dolphin", "xdg-open"), lanza=True, abre=True):
        self.programas, self.lanza, self.abre = set(programas), lanza, abre
        self.lanzados: list[list[str]] = []
        self.urls: list[str] = []

    def lanzar(self, argv):
        self.lanzados.append(list(argv))
        return self.lanza

    def abrir_url(self, url):
        self.urls.append(bytes(url.toEncoded()).decode())
        return self.abre

    def buscar(self, nombre):
        return f"/usr/bin/{nombre}" if nombre in self.programas else None


def _escritorio(l: Lanzador, errores=None):
    from gui_comun.escritorio import Escritorio
    return Escritorio(errores, lanzar=l.lanzar, abrir_url=l.abrir_url, buscar=l.buscar)


@requiere_binding
def test_tres_operaciones_distintas(app, tmp_path):
    archivo = tmp_path / "un informe con espacio.pdf"
    archivo.write_text("x")
    l = Lanzador()
    e = _escritorio(l)
    assert e.hayDolphin
    assert e.abrirConAplicacion(str(archivo))                       # su aplicación: la URL al escritorio, nada lanzado
    assert l.urls == [f"file://{tmp_path}/un%20informe%20con%20espacio.pdf"] and l.lanzados == []
    assert e.mostrarEnDolphin(str(archivo))                         # Dolphin, señalándolo
    assert l.lanzados[-1] == ["/usr/bin/dolphin", "--select", str(archivo)]
    assert e.abrirCarpeta(str(archivo))                             # la carpeta del archivo, con xdg-open
    assert l.lanzados[-1] == ["/usr/bin/xdg-open", str(tmp_path)]
    assert e.abrirCarpeta(str(tmp_path)) and l.lanzados[-1] == ["/usr/bin/xdg-open", str(tmp_path)]
    assert e.abrirConAplicacion("https://kde.org") and l.urls[-1] == "https://kde.org"


@requiere_binding
def test_sin_dolphin_abre_la_carpeta(app, tmp_path):
    archivo = tmp_path / "a.txt"
    archivo.write_text("x")
    l = Lanzador(programas=("xdg-open",))
    e = _escritorio(l)
    assert not e.hayDolphin
    assert e.mostrarEnDolphin(str(archivo)) and l.lanzados == [["/usr/bin/xdg-open", str(tmp_path)]]


@requiere_binding
def test_rutas_y_urls(app, tmp_path):
    e = _escritorio(Lanzador())
    assert e.rutaDeUrl("file:///home/x/00%20metodo/a.tex") == "/home/x/00 metodo/a.tex"
    assert e.urlDeRuta("/home/x/00 metodo") == "file:///home/x/00%20metodo"
    assert e.existe(str(tmp_path)) and not e.existe(str(tmp_path / "no"))


@requiere_binding
def test_lo_que_no_existe_se_presenta(app, tmp_path):
    from gui_comun.errores import Errores
    errores = Errores()
    l = Lanzador()
    e = _escritorio(l, errores)
    assert not e.mostrarEnDolphin(str(tmp_path / "se fue.pdf"))
    assert not e.abrirConAplicacion("")
    assert l.lanzados == [] and l.urls == []                        # no se lanzó nada
    assert errores.cuantos == 2
    primero = errores.actual
    assert primero["descripcion"] == "No se pudo mostrar en Dolphin" and primero["recurso"].endswith("se fue.pdf")
    assert "ya no existe" in primero["causa"] and primero["accion"] and primero["nivel"] == "aviso"
    l.abre = False
    (tmp_path / "x.raro").write_text("x")
    assert not e.abrirConAplicacion(str(tmp_path / "x.raro"))       # sin aplicación asociada
    assert "aplicación asociada" in errores.pendientes()[-1]["causa"]


@requiere_binding
def test_explicar_causas(app):
    import subprocess
    from gui_comun.errores import explicar, explicar_codigo
    assert "no existe" in explicar(FileNotFoundError(errno.ENOENT, "x", "/a"))[0]
    assert "lleno" in explicar(OSError(errno.ENOSPC, "x"))[0]
    assert "permiso" in explicar(PermissionError(errno.EACCES, "x"))[0]
    assert "código de salida 3" in explicar(subprocess.CalledProcessError(3, ["x"]))[0]
    assert "rechazó la clave SSH" in explicar_codigo(128, "git@github.com: Permission denied (publickey).")[0]
    assert "no está instalado" in explicar_codigo(127)[0]
    assert "bloqueada" in explicar_codigo(1, "sqlite3.OperationalError: database is locked")[0]
    assert explicar(ValueError("x")) == ("", "")


@requiere_binding
def test_cola_de_errores(app):
    from gui_comun.consola import Consola
    from gui_comun.errores import Errores
    c = Consola()
    e = Errores(c)
    vistos = []
    e.presentado.connect(lambda m: vistos.append(m["descripcion"]))
    try:
        open("/no/existe/de/verdad")
    except OSError as exc:
        e.desde_excepcion(exc, "No se pudo leer la ficha")
    e.presentarMapa({"descripcion": "Dos", "nivel": "aviso"})
    assert e.cuantos == 2 and vistos == ["No se pudo leer la ficha", "Dos"]
    a = e.actual
    assert a["recurso"] == "/no/existe/de/verdad" and "no existe" in a["causa"] and "Traceback" in a["detalle"]
    assert "No se pudo leer la ficha" in c.registro.texto              # también queda en el registro
    e.descartar()
    assert e.actual["descripcion"] == "Dos" and e.actual["nivel"] == "aviso"
    for i in range(30):
        e.presentar(f"ráfaga {i}")
    assert e.cuantos == 20 and e.omitidos == 11                       # una ráfaga no apila cien diálogos
    e.limpiar()
    assert e.cuantos == 0 and e.omitidos == 0 and e.actual == {}


def _esperar(app, tareas, plazo=10.0):
    fin = time.time() + plazo
    while tareas.activa and time.time() < fin:
        app.processEvents()
        time.sleep(0.01)
    app.processEvents()
    assert not tareas.activa


@requiere_binding
def test_tarea_que_falla_presenta_un_error(app, tmp_path):
    from gui_comun.consola import Consola
    from gui_comun.errores import Errores
    from gui_comun.tareas import Tareas
    c = Consola()
    e = Errores()
    t = Tareas(c, errores=e)
    t.proceso("Sincronizar", ["sh", "-c", "echo intentando; echo 'fatal: not a git repository' >&2; exit 128"], cwd=str(tmp_path))
    _esperar(app, t)
    assert e.cuantos == 1
    err = e.actual
    assert err["descripcion"] == "Falló «Sincronizar»" and "no es un repositorio de Git" in err["causa"]
    assert err["recurso"] == str(tmp_path) and "código de salida 128" in err["detalle"] and "intentando" in err["detalle"]
    assert "fatal: not a git repository" in c.salida.texto             # la consola conserva toda la salida

    def revienta(progress_cb=None, cancel_cb=None, message_cb=None):
        raise PermissionError(errno.EACCES, "Permission denied", "/root/x")
    t.funcion("Guardar la ficha", revienta, operacion="escritura")
    _esperar(app, t)
    err = e.pendientes()[-1]
    assert err["descripcion"] == "No se pudo completar «Guardar la ficha»" and "permiso" in err["causa"]
    assert err["recurso"] == "/root/x" and "PermissionError" in err["detalle"]

    t.proceso("Lote", ["sh", "-c", "exit 1"], error=False)            # quien resume sus fallos al final no presenta
    t.proceso("Redactado", ["sh", "-c", "exit 2"], error={"descripcion": "No se publicó", "accion": "Revise el dominio"})
    _esperar(app, t)
    assert e.cuantos == 3 and e.pendientes()[-1]["descripcion"] == "No se publicó"
    assert e.pendientes()[-1]["accion"] == "Revise el dominio"


@requiere_binding
def test_exito_y_verificacion_por_separado(app):
    from gui_comun.errores import Errores
    from gui_comun.tareas import Tareas
    e = Errores()
    t = Tareas(errores=e)
    orden = []
    t.terminada.connect(lambda nivel, nombre, detalle: orden.append(("terminada", nivel)))
    t.verificada.connect(lambda nombre, ok, detalle: orden.append(("verificada", ok, detalle)))
    resultados = []
    t.resultado.connect(lambda r: resultados.append(r))
    t.funcion("Escribir", lambda **kw: 3, operacion="escritura", verificar=lambda n: (n == 3, "3 archivos en disco"))
    _esperar(app, t)
    assert orden == [("terminada", "ok"), ("verificada", True, "3 archivos en disco")]
    assert resultados[-1]["operacion"] == "escritura" and resultados[-1]["verificacion"] == {"ok": True, "detalle": "3 archivos en disco"}
    t.funcion("Instalar", lambda **kw: 0, operacion="instalacion", verificar=lambda _: False)
    _esperar(app, t)
    assert orden[-1] == ("verificada", False, "") and e.cuantos == 1     # éxito, pero la verificación no pasó: error
    assert "verificación no se superó" in e.actual["descripcion"]
    with pytest.raises(ValueError):
        t.funcion("x", lambda **kw: 0, operacion="borrado")
