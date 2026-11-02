"""gui_comun/escritorio.py — la integración con el escritorio KDE (3.0): tres operaciones distintas, tres funciones.

No se confunden (instrucción del autor, §4.2):

    abrirConAplicacion(ruta)   abre el archivo (o la dirección web) con la aplicación que el escritorio asocia a su
                               tipo: un PDF en Okular, un .tex en el editor elegido… (`QDesktopServices.openUrl`, que
                               con el tema de plataforma de KDE es KIO y respeta las asociaciones y la activación)
    mostrarEnDolphin(ruta)     abre Dolphin en la carpeta que contiene la ruta y la deja señalada (`dolphin --select`);
                               sin Dolphin, abre la carpeta con `xdg-open`
    abrirCarpeta(ruta)         abre la carpeta (la de un archivo, si es un archivo) en el gestor de archivos del
                               escritorio, que en Kubuntu es Dolphin (`xdg-open`)

Elegir archivos o carpetas no es nada de esto: lo hacen `ElegirArchivos`, `ElegirCarpeta` y `GuardarComo` (QML, sobre
`QtQuick.Dialogs`), que con la `QApplication` de `Aplicacion` son el diálogo nativo de KDE.

    escritorio = Escritorio(errores)               # Aplicacion ya crea uno y lo expone como `escritorio`
    escritorio.mostrarEnDolphin("~/Documentos/informe.pdf")

Si la ruta no existe o el programa no arranca, devuelve False y presenta el error (descripción, causa, recurso,
acción) en `errores`. Las pruebas inyectan `lanzar`, `abrir_url` y `buscar`: nada se abre de verdad.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Callable

from gui_comun.qt import QDesktopServices, QObject, QProcess, QUrl, Property, Slot


def _lanzar_separado(argv: list[str]) -> bool:
    """Arranca un programa que sigue vivo aunque el studio se cierre."""
    resultado = QProcess.startDetached(argv[0], argv[1:])
    return bool(resultado[0] if isinstance(resultado, tuple) else resultado)


def ruta_local(texto: str) -> str:
    """Una ruta o una URL `file://` → la ruta local absoluta, con `~` expandida (sin resolver enlaces)."""
    texto = (texto or "").strip()
    if texto.startswith("file:"):
        texto = QUrl(texto).toLocalFile()
    return os.path.abspath(os.path.expanduser(texto)) if texto else ""


def _es_url_externa(texto: str) -> bool:
    url = QUrl(texto)
    return url.isValid() and url.scheme() not in ("", "file") and len(url.scheme()) > 1     # «C:» no es un esquema


class Escritorio(QObject):
    """Abrir, mostrar y señalar con el escritorio. Expuesto a QML como `escritorio` (y `aplicacionStudio.escritorio`)."""

    def __init__(self, errores=None, *, lanzar: Callable[[list[str]], bool] | None = None,
                 abrir_url: Callable[[QUrl], bool] | None = None, buscar: Callable[[str], str | None] | None = None,
                 parent=None):
        super().__init__(parent)
        self._errores = errores
        self._lanzar = lanzar or _lanzar_separado
        self._abrir_url = abrir_url or QDesktopServices.openUrl
        self._buscar = buscar or shutil.which

    # ------------------------------------------------------------------ consulta
    @Property(bool, constant=True)
    def hayDolphin(self) -> bool:
        return self._buscar("dolphin") is not None

    @Slot(str, result=str)
    def rutaDeUrl(self, url: str) -> str:
        """`file:///home/x/a%20b.pdf` → `/home/x/a b.pdf` (lo que devuelven los diálogos de QML)."""
        return ruta_local(url)

    @Slot(str, result=str)
    def urlDeRuta(self, ruta: str) -> str:
        """`/home/x/a b.pdf` → `file:///home/x/a%20b.pdf` (la carpeta inicial de un diálogo)."""
        local = ruta_local(ruta)
        return bytes(QUrl.fromLocalFile(local).toEncoded()).decode() if local else ""

    @Slot(str, result=bool)
    def existe(self, ruta: str) -> bool:
        local = ruta_local(ruta)
        return bool(local) and os.path.lexists(local)

    # ------------------------------------------------------------- operaciones
    @Slot(str, result=bool)
    def abrirConAplicacion(self, ruta: str) -> bool:
        """Abre el archivo con su aplicación asociada; también una dirección web o de correo."""
        if _es_url_externa(ruta):
            if self._abrir_url(QUrl(ruta)):
                return True
            return self._fallo("No se pudo abrir la dirección", ruta, "Ninguna aplicación del escritorio la aceptó.",
                               "Compruebe que hay un navegador o un programa asociado a ese tipo de dirección.")
        local = ruta_local(ruta)
        if not self._comprobar(local, "No se pudo abrir el archivo"):
            return False
        if self._abrir_url(QUrl.fromLocalFile(local)):
            return True
        return self._fallo("No se pudo abrir el archivo", local, "El escritorio no tiene una aplicación asociada a "
                           "este tipo de archivo, o la aplicación no arrancó.",
                           "Asocie una aplicación desde Dolphin (clic derecho › Abrir con) o use «Mostrar en Dolphin».")

    @Slot(str, result=bool)
    def mostrarEnDolphin(self, ruta: str) -> bool:
        """Abre Dolphin en la carpeta que contiene `ruta` con `ruta` señalada; sin Dolphin, abre esa carpeta."""
        local = ruta_local(ruta)
        if not self._comprobar(local, "No se pudo mostrar en Dolphin"):
            return False
        dolphin = self._buscar("dolphin")
        if dolphin:
            if self._lanzar([dolphin, "--select", local]):
                return True
            return self._fallo("No se pudo abrir Dolphin", local, "Dolphin está instalado pero no arrancó.",
                               "Ábralo a mano; el detalle técnico está en el registro.")
        return self._abrir_carpeta(os.path.dirname(local.rstrip("/")) or "/", "No se pudo mostrar la ubicación")

    @Slot(str, result=bool)
    def abrirCarpeta(self, ruta: str) -> bool:
        """Abre la carpeta (o la que contiene el archivo) en el gestor de archivos del escritorio."""
        local = ruta_local(ruta)
        if not self._comprobar(local, "No se pudo abrir la carpeta"):
            return False
        carpeta = local if os.path.isdir(local) else os.path.dirname(local)
        return self._abrir_carpeta(carpeta, "No se pudo abrir la carpeta")

    # ------------------------------------------------------------------ interno
    def _abrir_carpeta(self, carpeta: str, descripcion: str) -> bool:
        xdg = self._buscar("xdg-open")
        if xdg and self._lanzar([xdg, carpeta]):
            return True
        if self._abrir_url(QUrl.fromLocalFile(carpeta)):            # sin xdg-open: lo que diga el tema de plataforma
            return True
        return self._fallo(descripcion, carpeta, "No hay gestor de archivos asociado (falta xdg-open o no arrancó).",
                           "Instale xdg-utils o abra la carpeta a mano.")

    def _comprobar(self, local: str, descripcion: str) -> bool:
        if local and os.path.lexists(local):
            return True
        padre = Path(local).parent if local else None
        causa = "La ruta está vacía." if not local else (
            "El archivo o la carpeta ya no existe (se movió, se renombró o aún no se ha creado)."
            if padre and padre.is_dir() else "Ni la ruta ni su carpeta existen.")
        return self._fallo(descripcion, local, causa, "Actualice la vista y compruebe la ruta.")

    def _fallo(self, descripcion: str, recurso: str, causa: str, accion: str) -> bool:
        from gui_comun import errores as _errores
        destino = self._errores or _errores.predeterminado()
        if destino is not None:
            destino.presentar(descripcion, causa=causa, recurso=recurso, accion=accion, nivel="aviso")
        return False
