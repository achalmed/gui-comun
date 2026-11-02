"""test_consola_tareas.py — la consola (salida y registro) y las tareas (función y proceso) con sus señales."""

from __future__ import annotations

import time

from conftest import requiere_binding


def _esperar(app, tareas, plazo=10.0):
    fin = time.time() + plazo
    while tareas.activa and time.time() < fin:
        app.processEvents()
        time.sleep(0.01)
    app.processEvents()
    assert not tareas.activa, "la tarea no terminó a tiempo"


@requiere_binding
def test_consola_modelos(app):
    from gui_comun.consola import Consola
    c = Consola()
    escritas = []
    c.escrita.connect(lambda texto, nivel: escritas.append(nivel))
    c.escribir("$ git status", "cmd")
    c.escribir("hola\nmundo", "out")
    c.registrar("ok", "Preferencias guardadas")
    c.log("warn", "cuidado")             # el nombre de 1.x: al registro y, por ser aviso, también a la salida
    assert c.salida.lineas == 4 and c.salida.texto.splitlines() == ["$ git status", "hola", "mundo", "! cuidado"]
    assert c.registro.lineas == 2 and "✓ Preferencias guardadas" in c.registro.texto
    assert c.registro.textoConHora.count(":") >= 4
    assert escritas == ["cmd", "out", "warn"]
    assert c.salida.data(c.salida.index(0, 0), c.salida.R_NIVEL) == "cmd"
    c.salida.limpiar()
    assert c.salida.lineas == 0 and c.salida.texto == ""


@requiere_binding
def test_consola_recorta(app):
    from gui_comun.consola import ModeloConsola
    m = ModeloConsola(maximo=5)
    for i in range(8):
        m.escribir(f"l{i}")
    assert m.lineas == 5 and m.texto.splitlines()[0] == "l3"


@requiere_binding
def test_tarea_funcion(app):
    from gui_comun.consola import Consola
    from gui_comun.tareas import Tareas
    c = Consola()
    t = Tareas(c)
    estados, resultados, fines = [], [], []
    t.cambiada.connect(lambda: estados.append((t.activa, t.progreso, t.elemento)))
    t.terminada.connect(lambda nivel, nombre, detalle: fines.append((nivel, nombre)))

    def trabajo(n, progress_cb=None, cancel_cb=None, message_cb=None):
        for i in range(n):
            progress_cb(int((i + 1) * 100 / n), f"e{i}")
            message_cb("info", f"paso {i}")
        return n * 2

    t.funcion("Prueba", trabajo, 3, al_terminar=resultados.append)
    assert t.activa and t.nombre == "Prueba" and t.cuantas == 1
    _esperar(app, t)
    assert resultados == [6] and fines == [("ok", "Prueba")]
    assert (True, 100, "e2") in estados and estados[-1][0] is False
    assert c.salida.texto.count("paso") == 3
    assert "Inicia: Prueba" in c.registro.texto and "Termina: Prueba" in c.registro.texto


@requiere_binding
def test_tarea_falla_y_cancela(app):
    from gui_comun.tareas import Tareas
    from gui_comun.workers.function_worker import OperationCancelled
    t = Tareas()
    fines, errores = [], []
    t.terminada.connect(lambda nivel, nombre, detalle: fines.append((nivel, detalle)))

    def rompe(progress_cb=None, cancel_cb=None, message_cb=None):
        raise RuntimeError("se rompió")

    t.funcion("Rota", rompe, al_fallar=errores.append)
    _esperar(app, t)
    assert errores == ["se rompió"] and fines == [("error", "se rompió")]

    def lenta(progress_cb=None, cancel_cb=None, message_cb=None):
        for _ in range(200):
            if cancel_cb():
                raise OperationCancelled()
            time.sleep(0.01)

    t.funcion("Lenta", lenta)
    t.cancelar()
    _esperar(app, t)
    assert fines[-1][0] == "warn" and fines[-1][1] == "cancelada"


@requiere_binding
def test_tarea_proceso(app):
    from gui_comun.consola import Consola
    from gui_comun.tareas import Tareas
    c = Consola()
    t = Tareas(c)
    codigos = []
    t.proceso("eco", ["sh", "-c", "echo hola; echo err 1>&2; exit 3"], al_terminar=codigos.append)
    _esperar(app, t)
    assert codigos == [3]
    lineas = c.salida.texto.splitlines()
    assert lineas[0].startswith("$ sh -c") and "hola" in lineas and "err" in lineas
    assert "código de salida 3" in c.registro.texto
