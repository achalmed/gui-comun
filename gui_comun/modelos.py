"""gui_comun/modelos.py — modelos de datos que los studios QML repiten: lista de diccionarios y tabla filtrada.

- `ModeloLista`: un `QAbstractListModel` sobre una lista de dict con roles por nombre (cambios de un repo, historial,
  informes, entradas de la paleta…). `poner(filas)` lo reemplaza entero; `fila(i)` devuelve el dict.
- `ModeloFiltrado`: un `QSortFilterProxyModel` que QML maneja: `ordenar(columna, descendente)`, `filtrar(texto)`
  sobre todas las columnas o `filtrarPor(rol, valor)`; conserva los `roleNames` del origen y expone `filas`.
  Es el que la `TablaDatos` espera para ordenar al pulsar una cabecera y filtrar desde la barra.
"""

from __future__ import annotations

from typing import Callable

from gui_comun.qt import (QAbstractListModel, QByteArray, QModelIndex, QSortFilterProxyModel, Qt, Property, Signal,
                          Slot, rol)


class ModeloLista(QAbstractListModel):
    filasCambiadas = Signal()

    def __init__(self, roles: tuple[str, ...], filas: list[dict] | None = None, parent=None):
        super().__init__(parent)
        self._roles = {rol(i + 1): r for i, r in enumerate(roles)}
        self._nombres = tuple(roles)
        self._filas: list[dict] = list(filas or [])

    def poner(self, filas: list[dict]) -> None:
        self.beginResetModel()
        self._filas = list(filas)
        self.endResetModel()
        self.filasCambiadas.emit()

    def anadir(self, fila: dict) -> None:
        n = len(self._filas)
        self.beginInsertRows(QModelIndex(), n, n)
        self._filas.append(fila)
        self.endInsertRows()
        self.filasCambiadas.emit()

    def quitar(self, indice: int) -> None:
        if 0 <= indice < len(self._filas):
            self.beginRemoveRows(QModelIndex(), indice, indice)
            del self._filas[indice]
            self.endRemoveRows()
            self.filasCambiadas.emit()

    def actualizar(self, indice: int, **cambios) -> None:
        if 0 <= indice < len(self._filas):
            self._filas[indice].update(cambios)
            i = self.index(indice, 0)
            self.dataChanged.emit(i, i)

    def todas(self) -> list[dict]:
        return list(self._filas)

    @Slot(int, result="QVariantMap")
    def fila(self, indice: int) -> dict:
        return dict(self._filas[indice]) if 0 <= indice < len(self._filas) else {}

    @Property(int, notify=filasCambiadas)
    def filas(self) -> int:
        return len(self._filas)

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._filas)

    def roleNames(self):
        nombres = {r: QByteArray(n.encode()) for r, n in self._roles.items()}
        nombres[Qt.ItemDataRole.DisplayRole] = QByteArray(b"display")
        return nombres

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._filas):
            return None
        f = self._filas[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return f.get(self._nombres[0]) if self._nombres else None
        nombre = self._roles.get(role)
        return f.get(nombre) if nombre else None


class ModeloFiltrado(QSortFilterProxyModel):
    """Orden y filtro de una tabla desde QML; el origen conserva sus roles."""

    filasCambiadas = Signal()
    ordenCambiado = Signal()

    def __init__(self, origen=None, parent=None):
        super().__init__(parent)
        self._texto = ""
        self._por_rol: tuple[int, str] | None = None
        self._aceptar: Callable[[int], bool] | None = None
        self._columna, self._descendente = -1, False
        self.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.setSortCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.setDynamicSortFilter(True)
        if origen is not None:
            self.setSourceModel(origen)
        self.rowsInserted.connect(self.filasCambiadas)
        self.rowsRemoved.connect(self.filasCambiadas)
        self.modelReset.connect(self.filasCambiadas)
        self.layoutChanged.connect(self.filasCambiadas)

    def roleNames(self):
        origen = self.sourceModel()
        return origen.roleNames() if origen is not None else super().roleNames()

    # ---------------------------------------------------------------- QML
    @Slot(int, bool)
    def ordenar(self, columna: int, descendente: bool = False) -> None:
        self._columna, self._descendente = columna, descendente
        self.sort(columna, Qt.SortOrder.DescendingOrder if descendente else Qt.SortOrder.AscendingOrder)
        self.ordenCambiado.emit()

    @Slot(str)
    def filtrar(self, texto: str) -> None:
        self._texto = texto.strip().lower()
        self.invalidateFilter()
        self.filasCambiadas.emit()

    def aceptar_con(self, criterio: Callable[[int], bool] | None) -> None:
        """Un criterio de Python sobre la fila del origen (el filtro del panel de navegación)."""
        self._aceptar = criterio
        self.invalidateFilter()
        self.filasCambiadas.emit()

    @Slot(int, result=int)
    def filaOrigen(self, fila: int) -> int:
        return self.mapToSource(self.index(fila, 0)).row()

    @Slot(int, result=int)
    def filaVisible(self, fila_origen: int) -> int:
        origen = self.sourceModel()
        return self.mapFromSource(origen.index(fila_origen, 0)).row() if origen is not None else -1

    @Property(int, notify=filasCambiadas)
    def filas(self) -> int:
        return self.rowCount()

    @Property(int, notify=ordenCambiado)
    def columnaOrden(self) -> int:
        return self._columna

    @Property(bool, notify=ordenCambiado)
    def descendente(self) -> bool:
        return self._descendente

    # -------------------------------------------------------------- filtro
    def filterAcceptsRow(self, fila: int, padre) -> bool:
        origen = self.sourceModel()
        if origen is None:
            return True
        if self._aceptar is not None and not self._aceptar(fila):
            return False
        if not self._texto:
            return True
        try:
            columnas = origen.columnCount(padre)
        except TypeError:            # un modelo de lista: columnCount es privado en el binding
            columnas = 1
        for columna in range(columnas):
            valor = origen.data(origen.index(fila, columna, padre), Qt.ItemDataRole.DisplayRole)
            if valor is not None and self._texto in str(valor).lower():
                return True
        return False

    def lessThan(self, izquierda, derecha) -> bool:
        origen = self.sourceModel()
        a = origen.data(izquierda, Qt.ItemDataRole.EditRole)
        b = origen.data(derecha, Qt.ItemDataRole.EditRole)
        if a is None:
            a = origen.data(izquierda, Qt.ItemDataRole.DisplayRole)
        if b is None:
            b = origen.data(derecha, Qt.ItemDataRole.DisplayRole)
        try:
            return (a is None, a) < (b is None, b)
        except TypeError:
            return str(a).lower() < str(b).lower()
