"""gui_comun/modelos.py — modelos de datos que los studios QML repiten: lista de diccionarios y tabla filtrada.

- `ModeloLista`: un `QAbstractListModel` sobre una lista de dict con roles por nombre (cambios de un repo, historial,
  informes, entradas de la paleta…). `poner(filas)` lo reemplaza entero; `fila(i)` devuelve el dict.
- `ModeloFiltrado`: un `QSortFilterProxyModel` que QML maneja: `ordenar(columna, descendente)`, `filtrar(texto)`
  sobre todas las columnas o `filtrarPor(rol, valor)`; conserva los `roleNames` del origen y expone `filas`.
  Es el que la `TablaDatos` espera para ordenar al pulsar una cabecera y filtrar desde la barra.
- `ModeloTabla` (2.1): una tabla desde filas de dict con columnas (título, clave), roles `nivel`, `icono`,
  `habilitado` y el valor crudo para ordenar.
- `ModeloArbol` (2.1): un árbol desde nodos de dict (`valores` por columna, `hijos` como lista o función perezosa),
  para `ArbolDatos`; `ordenar(columna, descendente)` (3.1) ordena cada nivel por la cabecera.
"""

from __future__ import annotations

from typing import Callable

from gui_comun.qt import (QAbstractItemModel, QAbstractListModel, QAbstractTableModel, QByteArray, QModelIndex,
                          QSortFilterProxyModel, Qt, Property, Signal, Slot, rol)


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

    @Slot(result="QVariantList")
    def todas(self) -> list[dict]:
        """Todas las filas (3.1: también desde QML, para leer la lista entera sin exponer otra propiedad)."""
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


class ModeloTabla(QAbstractTableModel):
    """Una tabla genérica desde filas de diccionario (2.1): `columnas` son pares (título, clave) y cada fila un dict con
    esas claves y, opcionalmente, `nivel`, `icono` (texto para la primera columna o {clave: icono}), `habilitado` y
    `crudo` ({clave: valor} con el que se ordena: `EditRole`; sin él, el propio valor). Lo que cada studio repetía:
    extensiones, plan de carpetas, reportes, resultados.

        m = ModeloTabla([("Extensión", "ext"), ("Cantidad", "n")], [{"ext": ".pdf", "n": "12", "crudo": {"n": 12}}])
        tabla = ModeloFiltrado(m)     # orden por cabecera y filtro desde QML
    """

    filasCambiadas = Signal()
    R_NIVEL, R_ICONO, R_HABILITADO = rol(1), rol(2), rol(3)

    def __init__(self, columnas, filas: list[dict] | None = None, parent=None):
        super().__init__(parent)
        self._columnas = [(c, c) if isinstance(c, str) else tuple(c) for c in columnas]
        self._filas: list[dict] = list(filas or [])

    # ----------------------------------------------------------- escritura
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
            self.dataChanged.emit(self.index(indice, 0), self.index(indice, self.columnCount() - 1))

    def todas(self) -> list[dict]:
        return list(self._filas)

    # ---------------------------------------------------------------- QML
    @Slot(int, result="QVariantMap")
    def fila(self, indice: int) -> dict:
        return dict(self._filas[indice]) if 0 <= indice < len(self._filas) else {}

    @Property(int, notify=filasCambiadas)
    def filas(self) -> int:
        return len(self._filas)

    @Property(int, constant=True)
    def columnas(self) -> int:
        return len(self._columnas)

    @Slot(int, result=str)
    def clave(self, columna: int) -> str:
        return self._columnas[columna][1] if 0 <= columna < len(self._columnas) else ""

    # ---------------------------------------------------------- overrides
    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._filas)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._columnas)

    def headerData(self, seccion, orientacion, role=Qt.ItemDataRole.DisplayRole):
        if orientacion == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole and 0 <= seccion < len(self._columnas):
            return self._columnas[seccion][0]
        return None

    def roleNames(self):
        return {Qt.ItemDataRole.DisplayRole: QByteArray(b"display"), self.R_NIVEL: QByteArray(b"nivel"),
                self.R_ICONO: QByteArray(b"icono"), self.R_HABILITADO: QByteArray(b"habilitado")}

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._filas):
            return None
        f = self._filas[index.row()]
        clave = self._columnas[index.column()][1]
        if role == Qt.ItemDataRole.DisplayRole:
            v = f.get(clave)
            return "" if v is None else str(v)
        if role == Qt.ItemDataRole.EditRole:
            return f.get("crudo", {}).get(clave, f.get(clave))
        if role == self.R_NIVEL:
            return f.get("nivel", "")
        if role == self.R_HABILITADO:
            return f.get("habilitado", True)
        if role == self.R_ICONO:
            icono = f.get("icono", "")
            if isinstance(icono, dict):
                return icono.get(clave, "")
            return icono if index.column() == 0 else ""
        return None


class _Nodo:
    __slots__ = ("padre", "fila", "datos", "_hijos")

    def __init__(self, padre, fila: int, datos: dict):
        self.padre, self.fila, self.datos = padre, fila, datos
        self._hijos = None

    def hijos(self, orden=None) -> list:
        if self._hijos is None:
            fuente = self.datos.get("hijos") or []
            if callable(fuente):                       # perezoso: se consulta una vez, al expandir
                fuente = fuente(self.datos)
            self._hijos = [_Nodo(self, i, d) for i, d in enumerate(fuente)]
            if orden is not None:
                self.ordenar(*orden, recursivo=False)
        return self._hijos

    def ordenar(self, columna: int, descendente: bool, recursivo: bool = True) -> None:
        """Ordena los hijos ya cargados (los perezosos se ordenan al cargarse): por `grupo` (las carpetas antes que
        los archivos, siempre arriba) y por el valor de la columna; `orden` (lista por columna) da el valor crudo
        (un tamaño en bytes en vez de «1,2 KB»). Los números van antes que los textos y los vacíos al final."""
        if self._hijos is None:
            return

        def clave(n):
            d = n.datos
            crudos = d.get("orden") or d.get("valores") or []
            v = crudos[columna] if columna < len(crudos) else None
            vacio = v is None or v == ""
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                valor = (0, float(v), "")
            else:
                valor = (1, 0.0, str(v if v is not None else "").casefold())
            return vacio, valor

        grupos = sorted({n.datos.get("grupo", 0) for n in self._hijos})
        ordenados = []
        for g in grupos:
            del_grupo = [n for n in self._hijos if n.datos.get("grupo", 0) == g]
            llenos = sorted((n for n in del_grupo if not clave(n)[0]), key=lambda n: clave(n)[1], reverse=descendente)
            ordenados += llenos + [n for n in del_grupo if clave(n)[0]]
        self._hijos = ordenados
        for i, n in enumerate(self._hijos):
            n.fila = i
            if recursivo:
                n.ordenar(columna, descendente)

    def cargado(self) -> bool:
        return self._hijos is not None

    def puede_tener_hijos(self) -> bool:
        h = self.datos.get("hijos")
        return bool(h) or callable(h)


class ModeloArbol(QAbstractItemModel):
    """Un árbol genérico desde nodos de diccionario (2.1), para `ArbolDatos`: cada nodo trae `valores` (lista, uno por
    columna), opcionalmente `nivel`, `icono`, `habilitado`, cualquier dato propio, e `hijos` (lista de nodos, o una
    función `f(nodo) -> lista` que se llama una vez, al expandir: el explorador de carpetas).

        m = ModeloArbol(("Conjunto / ruta", "Inodo"), [{"valores": ["Conjunto 1", "1203"], "hijos": [{"valores": ["a.txt", ""]}]}])
    """

    filasCambiadas = Signal()
    ordenCambiado = Signal()
    R_NIVEL, R_ICONO, R_HABILITADO = rol(1), rol(2), rol(3)

    def __init__(self, columnas: tuple[str, ...], raices: list[dict] | None = None, parent=None):
        super().__init__(parent)
        self._columnas = tuple(columnas)
        self._raiz = _Nodo(None, -1, {"hijos": list(raices or [])})
        self._orden: tuple[int, bool] | None = None

    # ----------------------------------------------------------- escritura
    def poner(self, raices: list[dict]) -> None:
        self.beginResetModel()
        self._raiz = _Nodo(None, -1, {"hijos": list(raices)})
        if self._orden is not None:
            self._raiz.hijos(self._orden)
        self.endResetModel()
        self.filasCambiadas.emit()

    @Slot(int, bool)
    def ordenar(self, columna: int, descendente: bool = False) -> None:
        """Ordena cada nivel por `columna` (3.1, la cabecera de `ArbolDatos`); lo expandido sigue expandido."""
        if not 0 <= columna < len(self._columnas):
            return
        self.layoutAboutToBeChanged.emit()
        viejos = self.persistentIndexList()
        nodos = [(i.internalPointer(), i.column()) for i in viejos]
        self._orden = (columna, bool(descendente))
        self._raiz.hijos()
        self._raiz.ordenar(columna, bool(descendente))
        self.changePersistentIndexList(viejos, [self.createIndex(n.fila, c, n) for n, c in nodos])
        self.layoutChanged.emit()
        self.ordenCambiado.emit()

    @Property(int, notify=ordenCambiado)
    def columnaOrden(self) -> int:
        return self._orden[0] if self._orden else -1

    @Property(bool, notify=ordenCambiado)
    def descendente(self) -> bool:
        return bool(self._orden and self._orden[1])

    def recargar(self, index=QModelIndex()) -> None:
        """Olvida los hijos cargados de ese nodo (o de la raíz) para volver a consultarlos."""
        nodo = self._nodo(index)
        self.beginResetModel() if not index.isValid() else self.layoutAboutToBeChanged.emit()
        nodo._hijos = None
        self.endResetModel() if not index.isValid() else self.layoutChanged.emit()
        self.filasCambiadas.emit()

    # ---------------------------------------------------------------- QML
    @Slot(QModelIndex, result="QVariantMap")
    def datos(self, index) -> dict:
        """El nodo como diccionario (sin `hijos`)."""
        if not index.isValid():
            return {}
        return {k: v for k, v in self._nodo(index).datos.items() if k != "hijos"}

    @Slot(QModelIndex, result="QVariantList")
    def ruta(self, index) -> list:
        """Las filas desde la raíz hasta el nodo (para reencontrarlo tras un reset)."""
        filas = []
        nodo = self._nodo(index)
        while nodo is not None and nodo.fila >= 0:
            filas.insert(0, nodo.fila)
            nodo = nodo.padre
        return filas

    @Property(int, notify=filasCambiadas)
    def filas(self) -> int:
        return len(self._raiz.hijos(self._orden))

    def todas(self, index=QModelIndex()) -> list[dict]:
        return [n.datos for n in self._nodo(index).hijos(self._orden)]

    # ---------------------------------------------------------- overrides
    def _nodo(self, index) -> _Nodo:
        return index.internalPointer() if index.isValid() else self._raiz

    def index(self, fila, columna, parent=QModelIndex()):
        padre = self._nodo(parent)
        hijos = padre.hijos(self._orden)
        if 0 <= fila < len(hijos) and 0 <= columna < len(self._columnas):
            return self.createIndex(fila, columna, hijos[fila])
        return QModelIndex()

    def parent(self, index=QModelIndex()):
        if not index.isValid():
            return QModelIndex()
        padre = self._nodo(index).padre
        if padre is None or padre is self._raiz:
            return QModelIndex()
        return self.createIndex(padre.fila, 0, padre)

    def rowCount(self, parent=QModelIndex()) -> int:
        if parent.isValid() and parent.column() != 0:
            return 0
        return len(self._nodo(parent).hijos(self._orden))

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._columnas)

    def hasChildren(self, parent=QModelIndex()) -> bool:
        if parent.isValid() and parent.column() != 0:
            return False
        nodo = self._nodo(parent)
        return len(nodo.hijos()) > 0 if nodo.cargado() else nodo.puede_tener_hijos()

    def headerData(self, seccion, orientacion, role=Qt.ItemDataRole.DisplayRole):
        if orientacion == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole and 0 <= seccion < len(self._columnas):
            return self._columnas[seccion]
        return None

    def roleNames(self):
        return {Qt.ItemDataRole.DisplayRole: QByteArray(b"display"), self.R_NIVEL: QByteArray(b"nivel"),
                self.R_ICONO: QByteArray(b"icono"), self.R_HABILITADO: QByteArray(b"habilitado")}

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        d = self._nodo(index).datos
        c = index.column()
        if role == Qt.ItemDataRole.DisplayRole:
            valores = d.get("valores") or []
            return str(valores[c]) if c < len(valores) and valores[c] is not None else ""
        if role == self.R_NIVEL:
            return d.get("nivel", "")
        if role == self.R_HABILITADO:
            return d.get("habilitado", True)
        if role == self.R_ICONO:
            icono = d.get("icono", "")
            if isinstance(icono, dict):
                return icono.get(c, "")
            return icono if c == 0 else ""
        return None
