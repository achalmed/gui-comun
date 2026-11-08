"""tests/test_editor_disco.py — un cambio hecho fuera se avisa con el archivo quieto y lleno (4.1, 2026-11-08). Antes,
quien escribía truncando y luego escribiendo dejaba un instante el archivo vacío; el editor lo leía en ese instante y la
ventana recargaba la pestaña vacía (se veía el documento borrado, y Ctrl+S lo habría borrado de verdad)."""

from __future__ import annotations

import time

from gui_comun.consola import Consola
from gui_comun.editor import ControladorEditor


def _esperar(app, condicion, segundos):
    inicio = time.monotonic()
    while not condicion() and time.monotonic() - inicio < segundos:
        app.processEvents()
        time.sleep(0.02)


def test_no_avisa_a_mitad_de_una_escritura(app, tmp_path):
    archivo = tmp_path / "doc.tex"
    archivo.write_text("contenido original\n" * 50)
    editor = ControladorEditor(Consola())
    assert editor.abrir(str(archivo)) >= 0
    editor.leer(str(archivo))                             # la ventana lee el contenido (y su firma)
    avisos = []
    editor.cambioExterno.connect(lambda r: avisos.append(archivo.read_text()))

    archivo.write_text("")                                   # quien escribe trunca…
    _esperar(app, lambda: avisos, 1.2)                       # …y tarda en escribir: nadie recarga un vacío
    assert avisos == []
    archivo.write_text("contenido nuevo\n" * 60)            # …y por fin escribe
    _esperar(app, lambda: avisos, 6)
    assert len(avisos) == 1 and avisos[0].startswith("contenido nuevo")
    editor.soltar()


def test_un_archivo_que_de_verdad_queda_vacio_se_avisa(app, tmp_path):
    archivo = tmp_path / "doc.tex"
    archivo.write_text("algo\n")
    editor = ControladorEditor(Consola())
    editor.abrir(str(archivo))
    editor.leer(str(archivo))
    avisos = []
    editor.cambioExterno.connect(avisos.append)
    archivo.write_text("")
    _esperar(app, lambda: avisos, 8)                         # tras esperar a que se llene, se acepta
    assert avisos == [str(archivo)]
    editor.soltar()
