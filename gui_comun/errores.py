"""gui_comun/errores.py — errores presentables (3.0): qué pasó, por qué, dónde, qué hacer y el detalle técnico.

Un error de un studio no se le enseña al usuario como una traza ni le obliga a leer la consola. Se presenta con cinco
partes (la anatomía de `KMessageBox::detailedError` de KDE, ampliada):

    descripción   «No se pudo sincronizar «yachay»»          — lo que el usuario intentaba y no ocurrió
    causa         «La rama ha divergido de origin»            — la causa probable, en palabras del usuario
    recurso       «~/Documentos/yachay»                       — el archivo, la carpeta, el repositorio o el servicio
    acción        «Traiga los cambios y vuelva a intentarlo»  — qué hacer ahora
    detalle       la salida o la traza, desplegable           — para quien quiera mirar; la consola sigue teniéndolo

    errores = Errores(consola)
    errores.presentar("No se pudo abrir el informe", causa="El archivo no existe", recurso=ruta,
                      accion="Vuelva a generarlo desde Herramientas › Informe")
    try: ...
    except OSError as exc:
        errores.desde_excepcion(exc, "No se pudo guardar la ficha", recurso=ruta)

`Aplicacion` crea uno, lo expone como `errores` (y `aplicacionStudio.errores`) y lo deja como predeterminado: `Tareas`
lo usa cuando una tarea falla y `Escritorio` cuando no puede abrir algo. La ventana (`VentanaBase`) muestra cada error
en un `DialogoError`, uno detrás de otro; `TarjetaError` pinta el mismo error dentro de una página.
"""

from __future__ import annotations

import errno
import time
import traceback

from gui_comun.qt import QObject, Property, Signal, Slot

NIVELES = ("error", "aviso", "informacion")
_MAX_DETALLE = 12000                  # caracteres de detalle que se guardan (la consola guarda lo demás)
_MAX_PENDIENTES = 20                  # una ráfaga de fallos no apila cien diálogos: se cuentan los que se omiten

_predeterminado: "Errores | None" = None


def predeterminado() -> "Errores | None":
    """El registro de errores de la aplicación en marcha (lo fija `Aplicacion`); None fuera de una aplicación."""
    return _predeterminado


def fijar_predeterminado(errores: "Errores | None") -> None:
    global _predeterminado
    _predeterminado = errores


# --------------------------------------------------------------------------------------------- explicar causas
# (causa probable, acción recomendada) por errno de un OSError
_POR_ERRNO = {
    errno.ENOENT: ("El archivo o la carpeta no existe (se movió, se renombró o aún no se ha creado).",
                   "Compruebe la ruta; si el archivo lo genera otra operación, ejecútela antes."),
    errno.EACCES: ("No hay permiso para leer o escribir ahí.", "Revise los permisos del archivo o de su carpeta."),
    errno.EPERM: ("El sistema no permite esta operación sobre ese archivo.", "Revise los permisos o el propietario."),
    errno.ENOSPC: ("El disco está lleno.", "Libere espacio y vuelva a intentarlo; no se escribió nada a medias."),
    errno.EROFS: ("El sistema de archivos es de solo lectura.", "Elija otro destino o monte el disco con escritura."),
    errno.EISDIR: ("Se esperaba un archivo y la ruta es una carpeta.", "Elija un archivo dentro de esa carpeta."),
    errno.ENOTDIR: ("Se esperaba una carpeta y la ruta es un archivo.", "Elija la carpeta que lo contiene."),
    errno.EEXIST: ("Ya existe un archivo o una carpeta con ese nombre.", "Elija otro nombre o retire el existente."),
    errno.ENOTEMPTY: ("La carpeta no está vacía.", "Vacíela antes o elija otra."),
    errno.EBUSY: ("El recurso está en uso por otro programa.", "Cierre el programa que lo usa y vuelva a intentarlo."),
    errno.ETIMEDOUT: ("El servicio tardó demasiado en responder.", "Compruebe la conexión y vuelva a intentarlo."),
    errno.ECONNREFUSED: ("El servicio rechazó la conexión (¿no está en marcha?).", "Arranque el servicio y reintente."),
    errno.ENETUNREACH: ("No hay conexión de red.", "Compruebe la conexión a Internet y vuelva a intentarlo."),
    errno.EHOSTUNREACH: ("No se alcanza el servidor.", "Compruebe la conexión y la dirección del servidor."),
}

# (fragmento en minúsculas de la salida de un proceso, causa probable, acción recomendada); el primero que aparece
_POR_SALIDA = (
    ("no space left on device", "El disco está lleno.", "Libere espacio y vuelva a intentarlo."),
    ("permission denied (publickey)", "El servidor rechazó la clave SSH.",
     "Compruebe que su clave SSH está cargada (ssh-add -l) y registrada en el servidor."),
    ("authentication failed", "El servidor rechazó las credenciales.", "Revise el usuario y el token o la clave."),
    ("could not resolve host", "No se pudo resolver el nombre del servidor (sin conexión o nombre mal escrito).",
     "Compruebe la conexión a Internet y la dirección."),
    ("connection timed out", "El servidor no respondió a tiempo.", "Compruebe la conexión y vuelva a intentarlo."),
    ("connection refused", "El servicio rechazó la conexión (¿no está en marcha?).", "Arranque el servicio y reintente."),
    ("not a git repository", "La carpeta no es un repositorio de Git.", "Elija la carpeta raíz del repositorio."),
    ("conflict (", "Hay conflictos entre versiones.", "Resuelva los conflictos y vuelva a intentarlo."),
    ("non-fast-forward", "El remoto tiene cambios que aún no ha traído.", "Traiga los cambios (pull) y vuelva a enviar."),
    ("database is locked", "La base de datos está bloqueada por otro programa.",
     "Cierre el programa que la usa (p. ej. Calibre) y vuelva a intentarlo."),
    ("permission denied", "No hay permiso para leer, escribir o ejecutar algo que la orden necesita.",
     "Revise los permisos de los archivos indicados en el detalle."),
    ("no such file or directory", "Falta un archivo o una carpeta que la orden necesita.",
     "Compruebe las rutas indicadas en el detalle."),
    ("command not found", "Falta un programa que la orden necesita.", "Instálelo o revise el PATH."),
    ("out of memory", "El proceso se quedó sin memoria.", "Cierre otros programas o procese menos elementos a la vez."),
)


def explicar(excepcion: BaseException) -> tuple[str, str]:
    """La causa probable y la acción recomendada de una excepción, en palabras del usuario ("", "" si no se sabe)."""
    import subprocess
    if isinstance(excepcion, subprocess.CalledProcessError):
        salida = "\n".join(str(x) for x in (excepcion.stdout, excepcion.stderr) if x)
        return explicar_codigo(excepcion.returncode, salida)
    if isinstance(excepcion, subprocess.TimeoutExpired):
        return ("La orden tardó más de lo permitido y se detuvo.", "Vuelva a intentarlo con menos elementos.")
    if isinstance(excepcion, OSError) and excepcion.errno in _POR_ERRNO:
        return _POR_ERRNO[excepcion.errno]
    if isinstance(excepcion, UnicodeError):
        return ("El archivo no está en la codificación esperada (UTF-8).", "Conviértalo a UTF-8 y vuelva a intentarlo.")
    nombre = type(excepcion).__name__
    if nombre == "JSONDecodeError":
        return ("El archivo JSON está mal formado.", "Corrija el archivo en la línea indicada en el detalle.")
    if nombre in ("YAMLError", "ScannerError", "ParserError"):
        return ("El archivo YAML está mal formado.", "Corrija el archivo en la línea indicada en el detalle.")
    if nombre == "OperationalError" and "locked" in str(excepcion).lower():
        return ("La base de datos está bloqueada por otro programa.",
                "Cierre el programa que la usa (p. ej. Calibre) y vuelva a intentarlo.")
    if isinstance(excepcion, MemoryError):
        return ("El proceso se quedó sin memoria.", "Cierre otros programas o procese menos elementos a la vez.")
    if isinstance(excepcion, (ConnectionError, TimeoutError)):
        return ("Falló la conexión con un servicio.", "Compruebe la conexión y vuelva a intentarlo.")
    return ("", "")


def explicar_codigo(codigo: int, salida: str = "") -> tuple[str, str]:
    """La causa probable y la acción de un proceso que terminó con `codigo`, mirando también su salida."""
    texto = (salida or "").lower()
    for fragmento, causa, accion in _POR_SALIDA:
        if fragmento in texto:
            return causa, accion
    if codigo == 127:
        return ("No se encontró el programa (no está instalado o no está en el PATH).", "Instálelo o revise el PATH.")
    if codigo == 126:
        return ("El programa no tiene permiso de ejecución.", "Dele permiso de ejecución (chmod +x) o revise la ruta.")
    if codigo in (137, -9):
        return ("El proceso fue terminado a la fuerza (a menudo, por falta de memoria).",
                "Cierre otros programas o procese menos elementos a la vez.")
    if codigo in (143, -15, 130, -2):
        return ("El proceso fue interrumpido.", "Vuelva a lanzarlo si no lo detuvo usted.")
    return (f"La orden terminó con el código de salida {codigo}.", "Lea el detalle técnico: la orden explica allí qué falló.")


def _recortar(texto: str) -> str:
    texto = texto or ""
    return texto if len(texto) <= _MAX_DETALLE else "…\n" + texto[-_MAX_DETALLE:]


# ---------------------------------------------------------------------------------------------------- registro
class Errores(QObject):
    """La cola de errores por presentar. QML lee `actual` (el que se muestra), `cuantos` y `omitidos`; `descartar()`
    pasa al siguiente. Cada error también queda en el registro de la consola (si la hay)."""

    presentado = Signal("QVariantMap")     # el error recién añadido
    cambiado = Signal()                    # cambió la cola (actual, cuantos u omitidos)

    def __init__(self, consola=None, parent=None):
        super().__init__(parent)
        self._consola = consola
        self._cola: list[dict] = []
        self._omitidos = 0

    # ------------------------------------------------------------ presentar
    def presentar(self, descripcion: str, causa: str = "", recurso: str = "", accion: str = "", detalle: str = "",
                  nivel: str = "error") -> dict:
        """Añade un error a la cola y lo devuelve como dict ({descripcion, causa, recurso, accion, detalle, nivel, hora})."""
        error = {"descripcion": descripcion or "Ocurrió un error", "causa": causa or "", "recurso": str(recurso or ""),
                 "accion": accion or "", "detalle": _recortar(detalle), "nivel": nivel if nivel in NIVELES else "error",
                 "hora": time.strftime("%H:%M:%S")}
        if self._consola is not None:
            self._consola.registrar(error["nivel"] if error["nivel"] != "informacion" else "info",
                                    " · ".join(p for p in (error["descripcion"], error["causa"], error["recurso"]) if p))
        if len(self._cola) >= _MAX_PENDIENTES:
            self._omitidos += 1
        else:
            self._cola.append(error)
        self.presentado.emit(error)
        self.cambiado.emit()
        return error

    @Slot(str, str, str, str, str)
    def presentarTexto(self, descripcion: str, causa: str, recurso: str, accion: str, detalle: str) -> None:
        """Desde QML: `errores.presentarTexto(descripcion, causa, recurso, accion, detalle)`."""
        self.presentar(descripcion, causa, recurso, accion, detalle)

    @Slot("QVariantMap")
    def presentarMapa(self, mapa: dict) -> None:
        """Desde QML: `errores.presentarMapa({descripcion, causa, recurso, accion, detalle, nivel})`."""
        mapa = dict(mapa or {})
        self.presentar(str(mapa.get("descripcion", "")), str(mapa.get("causa", "")), str(mapa.get("recurso", "")),
                       str(mapa.get("accion", "")), str(mapa.get("detalle", "")), str(mapa.get("nivel", "error")))

    def desde_excepcion(self, excepcion: BaseException, descripcion: str, recurso: str = "", accion: str = "",
                        causa: str = "") -> dict:
        """Presenta una excepción: la causa y la acción salen de `explicar` si no se dan; el detalle es la traza."""
        causa_p, accion_p = explicar(excepcion)
        if not recurso and isinstance(excepcion, OSError) and excepcion.filename:
            recurso = str(excepcion.filename)
        detalle = "".join(traceback.format_exception(type(excepcion), excepcion, excepcion.__traceback__))
        return self.presentar(descripcion, causa or causa_p or str(excepcion), recurso, accion or accion_p, detalle)

    def desde_proceso(self, descripcion: str, argv: list[str], codigo: int, salida: str = "", recurso: str = "",
                      accion: str = "") -> dict:
        """Presenta un proceso fallido: causa por su código y su salida; el detalle, la orden y sus últimas líneas."""
        causa, accion_p = explicar_codigo(codigo, salida)
        detalle = "$ " + " ".join(argv) + f"\n(código de salida {codigo})\n\n" + (salida or "")
        return self.presentar(descripcion, causa, recurso, accion or accion_p, detalle)

    # ----------------------------------------------------------------- cola
    @Slot()
    def descartar(self) -> None:
        """Quita el error que se muestra (el diálogo pasa al siguiente)."""
        if self._cola:
            self._cola.pop(0)
            if not self._cola:
                self._omitidos = 0
            self.cambiado.emit()

    @Slot()
    def limpiar(self) -> None:
        self._cola.clear()
        self._omitidos = 0
        self.cambiado.emit()

    @Property("QVariantMap", notify=cambiado)
    def actual(self) -> dict:
        return dict(self._cola[0]) if self._cola else {}

    @Property(int, notify=cambiado)
    def cuantos(self) -> int:
        return len(self._cola)

    @Property(int, notify=cambiado)
    def omitidos(self) -> int:
        return self._omitidos

    def pendientes(self) -> list[dict]:
        return [dict(e) for e in self._cola]
