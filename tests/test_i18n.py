"""test_i18n.py — las funciones i18n* de KI18n desde Python: catálogo, contexto, plural y sustitución."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import requiere_binding

HAY_CATALOGO = Path("/usr/share/locale/es/LC_MESSAGES/kirigami-addons6.mo").is_file()


def test_sustituir():
    from gui_comun.i18n import sustituir
    assert sustituir("Hola %1 y %2", ["a", "b"]) == "Hola a y b"
    assert sustituir("%1 de %2", [3]) == "3 de %2"
    assert sustituir("sin marcas", []) == "sin marcas"


@requiere_binding
def test_contexto_traduccion(app):
    from gui_comun.i18n import ContextoTraduccion
    c = ContextoTraduccion("es")
    assert c.i18n("texto sin catálogo %1", 7) == "texto sin catálogo 7"
    assert c.i18np("%1 elemento", "%1 elementos", 1) == "1 elemento"
    assert c.i18np("%1 elemento", "%1 elementos", 3) == "3 elementos"
    assert c.i18ndc("dominio-inexistente", "ctx", "Igual") == "Igual"
    if HAY_CATALOGO:
        assert c.i18ndc("kirigami-addons6", "@action:button", "Cancel") == "Cancelar"
    assert all(hasattr(c, n) for n in ("i18nc", "i18nd", "i18ncp", "i18ndp", "i18ndcp", "xi18n", "xi18ndc"))


@requiere_binding
def test_contexto_en_el_motor(app, tmp_path):
    """Instalado como objeto de contexto, `i18ndc(...)` es una función global del QML."""
    pytest.importorskip("gui_comun.qt", reason="sin binding")
    from gui_comun.i18n import instalar
    from gui_comun.qt import QQmlApplicationEngine, QUrl
    motor = QQmlApplicationEngine()
    contexto = instalar(motor, "es")
    qml = tmp_path / "T.qml"
    qml.write_text('import QtQml\nQtObject { property string t: i18ndc("kirigami-addons6", "@action:button", "Cancel")\n'
                   '  property string p: i18np("%1 item", "%1 items", 2) }', encoding="utf-8")
    motor.load(QUrl.fromLocalFile(str(qml)))
    raices = motor.rootObjects()
    assert raices, "no cargó"
    assert raices[0].property("p") == "2 items"
    if HAY_CATALOGO:
        assert raices[0].property("t") == "Cancelar"
    del contexto
