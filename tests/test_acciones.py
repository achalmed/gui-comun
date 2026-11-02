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


@requiere_binding
def test_operaciones_de_riesgo_piden_confirmacion(app):
    """3.0: instalación, publicación y eliminación siempre piden confirmación redactada; disparar no ejecuta."""
    from gui_comun.acciones import Acciones, OPERACIONES
    assert list(OPERACIONES) == ["lectura", "simulacion", "preparacion", "escritura", "instalacion", "publicacion", "eliminacion"]
    a = Acciones()
    hechos, pedidas = [], []
    a.confirmacionPedida.connect(lambda p: pedidas.append(p))
    destino = {"dominio": "a.example"}
    a.registrar("sitio.publicar", "&Publicar…", "document-send", None, "Sitio", operacion="publicacion",
                consecuencias=lambda: f"Se publicará en {destino['dominio']}", al_disparar=lambda: hechos.append("publicado"))
    a.registrar("sitio.leer", "&Leer", "", None, "Sitio", operacion="lectura", al_disparar=lambda: hechos.append("leido"))
    a.registrar("doc.sobrescribir", "&Sobrescribir", "", None, "Doc", operacion="escritura", confirmar=True,
                consecuencias="Sustituye el archivo", al_disparar=lambda: hechos.append("escrito"))
    assert a["sitio.publicar"].requiereConfirmacion and not a["sitio.leer"].requiereConfirmacion
    assert a["sitio.publicar"].operacionTexto == "Publicación"
    a.ejecutar("sitio.leer")
    a.ejecutar("sitio.publicar")
    assert hechos == ["leido"] and pedidas[-1]["nombre"] == "sitio.publicar"
    destino["dominio"] = "b.example"                                  # las consecuencias se calculan al pedir
    assert a.peticion("sitio.publicar")["consecuencias"] == "Se publicará en b.example"
    assert pedidas[-1]["consecuencias"] == "Se publicará en a.example" and pedidas[-1]["textoAceptar"] == "Publicar"
    a.confirmar("sitio.publicar")
    assert hechos == ["leido", "publicado"]
    a.ejecutar("doc.sobrescribir")
    assert hechos[-1] == "publicado" and pedidas[-1]["operacion"] == "escritura"
    a.habilitar("sitio.publicar", False)
    a.confirmar("sitio.publicar")
    assert hechos[-1] == "publicado"                                  # deshabilitada: ni confirmada se ejecuta

    with pytest.raises(ValueError):                                   # sin consecuencias redactadas
        a.registrar("x.borrar", "&Borrar", "", None, "X", operacion="eliminacion")
    with pytest.raises(ValueError):                                   # no se puede saltar la confirmación
        a.registrar("x.instalar", "&Instalar", "", None, "X", operacion="instalacion", consecuencias="y", confirmar=False)
    with pytest.raises(ValueError):
        a.registrar("x.otro", "&Otro", "", None, "X", operacion="borrado")
    assert a.buscar("sobresc")[0]["operacion"] == "Escritura"                # la paleta nombra el estado


@requiere_binding
def test_atajos_por_disciplina(app):
    """3.0: la base no impone F5 ni paneles; el studio fija sus atajos y comprueba que no se repiten."""
    from gui_comun.acciones import Acciones
    a = Acciones()
    a.estandar("Libre", paneles=False, atajos={"ventana.paleta": "Ctrl+Shift+P"})
    assert not a.existe("ventana.navegacion") and not a.existe("ventana.detalles")
    assert all(x.atajo != "F5" for x in (a[n] for n in a.nombres()))
    assert a["ventana.paleta"].atajo == "Ctrl+Shift+P"
    cambios = []
    a["ventana.paleta"].atajoCambiado.connect(lambda: cambios.append(1))
    a.registrar("tex.compilar", "&Compilar", "", "Ctrl+B", "LaTeX")
    a.registrar("tex.negrita", "&Negrita", "", "Ctrl+B", "Formato")
    assert a.conflictos() == {"Ctrl+B": ["tex.compilar", "tex.negrita"]}
    a.fijar_atajo("tex.negrita", "")
    a.fijar_atajo("ventana.paleta", "Ctrl+Alt+I")
    assert a.conflictos() == {} and cambios == [1] and a["ventana.paleta"].atajoTexto == "Ctrl+Alt+I"
    with pytest.raises(KeyError):
        a.fijar_atajo("no.existe", "F1")
