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


@requiere_binding
def test_tarea_proceso_con_progreso_leido_de_la_salida(app):
    """2.3: `progreso_de(texto)` convierte las líneas del proceso en progreso y elemento de la barra de estado."""
    import re
    from gui_comun.consola import Consola
    from gui_comun.tareas import Tareas
    t = Tareas(Consola())
    vistos = []
    t.cambiada.connect(lambda: vistos.append((t.progreso, t.elemento)))

    def progreso(texto):
        m = re.search(r"Pasada (\d+)/(\d+)", texto)
        return (int((int(m[1]) - 1) * 100 / int(m[2])), f"pasada {m[1]} de {m[2]}") if m else None
    t.proceso("pasadas", ["sh", "-c", "echo 'Pasada 1/2 con lualatex'; echo otra; echo 'Pasada 2/2 con lualatex'"], progreso_de=progreso)
    _esperar(app, t)
    assert (0, "pasada 1 de 2") in vistos and (50, "pasada 2 de 2") in vistos
    assert not t.activa and t.progreso == -1 and t.elemento == ""


@requiere_binding
def test_tarea_proceso_con_entrada_y_entorno(app):
    """2.5: `entrada` responde a las confirmaciones de un guion (la ventana ya confirmó) y `entorno` añade variables."""
    from gui_comun.consola import Consola
    from gui_comun.tareas import Tareas
    c = Consola()
    t = Tareas(c)
    codigos = []
    t.proceso("confirma", ["sh", "-c", "read -r r; echo \"leido=$r\"; echo \"var=$PRUEBA_VAR\"; [ \"$r\" = s ]"],
              entrada="s\n", entorno={"PRUEBA_VAR": "valor"}, al_terminar=codigos.append)
    _esperar(app, t)
    assert codigos == [0]
    assert "leido=s" in c.salida.texto and "var=valor" in c.salida.texto
    t.proceso("sin entrada", ["sh", "-c", "read -r r; echo \"leido=[$r]\""], al_terminar=codigos.append)
    _esperar(app, t)
    assert "leido=[]" in c.salida.texto                       # sin `entrada`, la entrada está cerrada: no se cuelga
    t.proceso("colores", ["sh", "-c", "printf '\\033[1m\\033[34m[4/4] index.qmd\\033[0m\\n'"], al_terminar=codigos.append)
    _esperar(app, t)
    assert "[4/4] index.qmd" in c.salida.texto.splitlines() and "\x1b" not in c.salida.texto   # 2.5: sin secuencias ANSI


@requiere_binding
def test_cancelar_un_proceso_termina_a_sus_hijos(app, tmp_path):
    """2.2.0: `cancel()` avisa al grupo entero; el nieto (`sleep`) no sobrevive a la cancelación del `sh` padre.
    3.0: la tarea cancelada termina en «warn · cancelada», como una función cancelada, y no presenta un error."""
    import os
    import time
    from gui_comun.consola import Consola
    from gui_comun.tareas import Tareas
    pid_nieto = tmp_path / "nieto.pid"
    c = Consola()
    t = Tareas(c)
    fines = []
    t.terminada.connect(lambda nivel, nombre, detalle: fines.append((nivel, detalle)))
    t.proceso("dormir", ["sh", "-c", f"sh -c 'echo $$ > {pid_nieto}; exec sleep 60' & wait"], al_terminar=lambda *_: None)
    limite = time.time() + 10
    while not pid_nieto.is_file() and time.time() < limite:
        app.processEvents()
        time.sleep(0.05)
    pid = int(pid_nieto.read_text().strip())
    time.sleep(0.2)
    t.cancelar()
    _esperar(app, t)
    assert fines and fines[-1] == ("warn", "cancelada")    # 3.0: cancelar no es un error (antes «error», por la señal)
    for _ in range(50):                                 # el nieto debe haber muerto con el grupo
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            break
        time.sleep(0.05)
    else:
        os.kill(pid, 9)
        raise AssertionError("el nieto siguió vivo tras cancelar")
