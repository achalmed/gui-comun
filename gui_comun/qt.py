"""gui_comun/qt.py — el binding de Qt con el que corre el studio: PySide6 si existe y, si no, PyQt6.

Los studios corren con el Python del sistema y el Qt del sistema (el único que carga Kirigami); ahí puede haber
PySide6 (`python3-pyside6.*`) o PyQt6 (`python3-pyqt6`). Este adaptador importa de uno u otro los nombres que usa el
código nuevo de la familia (núcleo, acciones, tareas, consola, modelos de cada studio), con los nombres de PySide6:

    from gui_comun.qt import QObject, Signal, Slot, Property, QAbstractTableModel, QQmlApplicationEngine, cast

Reglas para que un módulo corra con los dos: enumeraciones siempre con su ámbito (`Qt.ItemDataRole.DisplayRole`,
nunca `Qt.DisplayRole`), los roles como `QByteArray`, los tipos de `Property` y `Slot` como tipos de Python o cadenas
de Qt (`"QVariant"`, `"QVariantList"`, `"QVariantMap"`), y los enteros de los roles con `int(...)`.
Sin `qtpy` ni ninguna dependencia nueva: solo lo que hay instalado.
"""

from __future__ import annotations

import importlib.util

BINDING = "PySide6" if importlib.util.find_spec("PySide6") else "PyQt6"

if BINDING == "PySide6":
    from PySide6.QtCore import (  # noqa: F401
        QAbstractItemModel, QAbstractListModel, QAbstractTableModel, QByteArray, QCoreApplication, QDir, QEvent,
        QFileInfo, QLocale, QMimeDatabase, QModelIndex, QObject, QPoint, QProcess, QSettings, QSize,
        QSortFilterProxyModel, QStandardPaths, Qt, QThread, QTimer, QTranslator, QUrl, Signal, Slot, Property,
        QItemSelectionModel,
    )
    from PySide6.QtGui import QGuiApplication, QIcon, QKeySequence, QFontDatabase  # noqa: F401
    try:   # QML: no hace falta para los studios de Widgets (1.x), que solo usan QtCore de aquí
        from PySide6.QtQml import QQmlApplicationEngine, QQmlPropertyMap, qmlRegisterType  # noqa: F401
        from PySide6.QtQuick import QQuickItem, QQuickWindow  # noqa: F401
    except ImportError:   # pragma: no cover
        pass
    import shiboken6 as _shiboken

    def cast(objeto, tipo):
        """El mismo objeto de C++ visto como `tipo` (lo que `sip.cast` hace en PyQt)."""
        return _shiboken.wrapInstance(_shiboken.getCppPointer(objeto)[0], tipo)

    def es_valido(objeto) -> bool:
        return _shiboken.isValid(objeto)

else:
    from PyQt6.QtCore import (  # noqa: F401
        QAbstractItemModel, QAbstractListModel, QAbstractTableModel, QByteArray, QCoreApplication, QDir, QEvent,
        QFileInfo, QLocale, QMimeDatabase, QModelIndex, QObject, QPoint, QProcess, QSettings, QSize,
        QSortFilterProxyModel, QStandardPaths, Qt, QThread, QTimer, QTranslator, QUrl, QItemSelectionModel,
    )
    from PyQt6.QtCore import pyqtProperty as Property, pyqtSignal as Signal, pyqtSlot as Slot  # noqa: F401
    from PyQt6.QtGui import QGuiApplication, QIcon, QKeySequence, QFontDatabase  # noqa: F401
    try:
        from PyQt6.QtQml import QQmlApplicationEngine, QQmlPropertyMap, qmlRegisterType  # noqa: F401
        from PyQt6.QtQuick import QQuickItem, QQuickWindow  # noqa: F401
    except ImportError:   # pragma: no cover
        pass
    from PyQt6 import sip as _sip

    def cast(objeto, tipo):
        return _sip.cast(objeto, tipo)

    def es_valido(objeto) -> bool:
        return not _sip.isdeleted(objeto)


def rol(desplazamiento: int) -> int:
    """Un rol de modelo propio: `Qt.UserRole + desplazamiento`, como entero en los dos bindings."""
    return int(Qt.ItemDataRole.UserRole) + desplazamiento


def roles(*nombres: str, base: int = 1) -> dict[int, QByteArray]:
    """`roleNames()` a partir de nombres: {UserRole+1: b"nombre1", …}; el primero recibe `base`."""
    return {rol(base + i): QByteArray(n.encode()) for i, n in enumerate(nombres)}


def version_qt() -> str:
    from importlib import import_module
    core = import_module(f"{BINDING}.QtCore")
    return getattr(core, "qVersion", lambda: getattr(core, "QT_VERSION_STR", "?"))()
