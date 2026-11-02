"""test_modelos.py — ModeloLista (roles por nombre) y ModeloFiltrado (orden, filtro de texto y criterio)."""

from __future__ import annotations

from conftest import requiere_binding


@requiere_binding
def test_modelo_lista(app):
    from gui_comun.modelos import ModeloLista
    from gui_comun.qt import Qt
    m = ModeloLista(("nombre", "n"), [{"nombre": "b", "n": 2}])
    assert m.filas == 1 and m.fila(0) == {"nombre": "b", "n": 2} and m.fila(9) == {}
    assert set(v.data().decode() for v in m.roleNames().values()) == {"nombre", "n", "display"}
    m.anadir({"nombre": "a", "n": 1})
    assert m.rowCount() == 2 and m.data(m.index(1, 0), Qt.ItemDataRole.DisplayRole) == "a"
    rol_n = [r for r, v in m.roleNames().items() if v.data() == b"n"][0]
    assert m.data(m.index(0, 0), rol_n) == 2
    m.actualizar(0, n=5)
    assert m.fila(0)["n"] == 5
    m.quitar(0)
    assert m.todas() == [{"nombre": "a", "n": 1}]
    m.poner([])
    assert m.filas == 0


@requiere_binding
def test_modelo_filtrado(app):
    from gui_comun.modelos import ModeloFiltrado, ModeloLista
    from gui_comun.qt import Qt
    origen = ModeloLista(("nombre",), [{"nombre": "gamma"}, {"nombre": "alfa"}, {"nombre": "beta"}])
    f = ModeloFiltrado(origen)
    assert f.filas == 3 and f.roleNames() == origen.roleNames()
    f.ordenar(0, False)
    assert [f.data(f.index(i, 0), Qt.ItemDataRole.DisplayRole) for i in range(3)] == ["alfa", "beta", "gamma"]
    assert f.columnaOrden == 0 and f.descendente is False
    f.ordenar(0, True)
    assert f.data(f.index(0, 0), Qt.ItemDataRole.DisplayRole) == "gamma"
    f.filtrar("A")
    assert f.filas == 3                 # sin distinguir mayúsculas: las tres llevan «a»
    f.filtrar("bet")
    assert f.filas == 1 and f.filaOrigen(0) == 2 and f.filaVisible(2) == 0 and f.filaVisible(0) == -1
    f.filtrar("")
    f.aceptar_con(lambda fila: origen.fila(fila)["nombre"] != "alfa")
    assert f.filas == 2
    f.aceptar_con(None)
    assert f.filas == 3
