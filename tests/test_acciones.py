"""test_acciones.py — el registro de acciones: alta, atajos, menús, barra, búsqueda difusa y disparo."""

from __future__ import annotations

import pytest

from conftest import requiere_binding


@requiere_binding
def test_registro_menus_y_barra(app):
    from gui_comun.acciones import Acciones, StandardKey
    a = Acciones()
    a.estandar("Prueba Studio")
    hechos = []
    a.registrar("repo.analizar", "&Analizar estado", "view-refresh", StandardKey.Refresh, "Repositorio",
                descripcion="Relee el estado", al_disparar=lambda: hechos.append("analizar"))
    a.registrar("repo.sinc", "&Sincronizar", "folder-sync", "Ctrl+Shift+S", "Repositorio")
    a.definir_menus([("&Archivo", ["repo.analizar", "|", "app.salir"]),
                     ("&Ver", ["ventana.navegacion", ("C&olumnas", ["repo.sinc"])])])
    a.definir_barra(["repo.analizar", "|", "repo.sinc"])

    assert a["repo.analizar"].atajo == "F5" and a["repo.analizar"].atajoTexto == "F5"
    assert a["repo.sinc"].atajoTexto == "Ctrl+Mayús+S"
    assert a["app.ajustes"].atajo == "Ctrl+Shift+," and a["app.salir"].atajo == "Ctrl+Q"
    assert a["ventana.paleta"].atajo == "Ctrl+Alt+I"
    assert a["app.ajustes"].textoPlano == "Configurar Prueba Studio"
    assert a.menus[0]["elementos"][1] == {"tipo": "separador"}
    assert a.menus[1]["elementos"][1]["tipo"] == "menu" and a.menus[1]["elementos"][1]["elementos"][0]["nombre"] == "repo.sinc"
    assert a.barra == ["repo.analizar", "|", "repo.sinc"]
    assert a.rowCount() == 10 and a.data(a.index(8, 0), a.R_NOMBRE) == "repo.analizar"

    a.ejecutar("repo.analizar")
    assert hechos == ["analizar"]
    assert a["ventana.navegacion"].marcada is True
    a.ejecutar("ventana.navegacion")
    assert a["ventana.navegacion"].marcada is False

    with pytest.raises(ValueError):
        a.registrar("repo.sinc", "otra vez")
    with pytest.raises(KeyError):
        a.definir_barra(["no.existe"])


@requiere_binding
def test_habilitar_y_senales(app):
    from gui_comun.acciones import Acciones
    a = Acciones()
    x = a.registrar("x", "&X", "", None, "G")
    recibidas = []
    a.disparada.connect(lambda nombre, marcada: recibidas.append((nombre, marcada)))
    cambios = []
    x.habilitadaCambiada.connect(lambda: cambios.append(x.habilitada))
    a.habilitar("x", False)
    a.ejecutar("x")                 # deshabilitada: no se dispara
    assert recibidas == [] and cambios == [False]
    a.habilitar("x", True)
    a.ejecutar("x")
    assert recibidas == [("x", False)]


@requiere_binding
def test_busqueda_difusa_y_fuentes(app):
    from gui_comun.acciones import Acciones
    a = Acciones()
    a.registrar("repo.sinc", "&Sincronizar seleccionados", "folder-sync", "Ctrl+Shift+S", "Repositorio")
    a.registrar("repo.obtener", "&Obtener cambios (pull)", "download", None, "Repositorio")
    a.registrar("ver.nav", "Panel de &navegación", "", "F9", "Ver", marcable=True)
    idos = []
    a.anadir_fuente(lambda texto: [{"nombre": "ir.gui-comun", "texto": "Ir a gui-comun", "grupo": "Repositorios",
                                    "ejecutar": lambda: idos.append("gui-comun")}] if "gui" in texto or not texto else [])
    assert [c["texto"] for c in a.buscar("sinc")] == ["Sincronizar seleccionados"]
    assert [c["texto"] for c in a.buscar("pnv")] == ["Panel de navegación"]
    assert a.buscar("pull")[0]["texto"] == "Obtener cambios (pull)"
    assert a.buscar("zzz") == []
    todas = a.buscar("")
    assert len(todas) == 4 and todas[-1]["grupo"] == "Repositorios"
    assert a.buscar("gui")[0]["nombre"] == "ir.gui-comun"
    a.ejecutar("ir.gui-comun")
    assert idos == ["gui-comun"]


def test_atajo_legible():
    from gui_comun.acciones import atajo_legible
    assert atajo_legible("Ctrl+Shift+S") == "Ctrl+Mayús+S"
    assert atajo_legible("Ctrl+Return") == "Ctrl+Intro"
    assert atajo_legible("Shift+F4") == "Mayús+F4"
    assert atajo_legible("Del") == "Supr"
    assert atajo_legible("") == ""


@requiere_binding
def test_atajos_estandar_sin_repetir(app):
    """Ningún atajo repetido entre las acciones de toda ventana (F11 es detalles; pantalla completa, Ctrl+Mayús+F)."""
    from gui_comun.acciones import Acciones
    a = Acciones()
    a.estandar("Prueba")
    atajos = [a[n].atajo for n in a.nombres() if a[n].atajo]
    assert len(atajos) == len(set(atajos)), atajos
    assert a["ventana.detalles"].atajo == "F11" and a["ventana.pantalla_completa"].atajo == "Ctrl+Shift+F"
