"""gui_comun/miniaturas.py — un proveedor de miniaturas para `Image { source: "image://<nombre>/<clave>" }` (3.1).

Viene de Biblioteca Studio (`controladores/portadas.py`, las portadas de Calibre en la cuadrícula); sirve a cualquier
catálogo visual (Raphi: las imágenes de una carpeta; Quarto: las miniaturas de los sitios). Un proveedor asíncrono
lee la imagen de origen en SOLO LECTURA con `QImageReader`, escalada al leer (no se decodifica la imagen entera), la
guarda como JPEG en una carpeta de caché (la clave lleva el elemento, el ancho y la fecha del archivo: una imagen nueva
invalida la vieja) y la devuelve. La caché se poda a un tope quitando lo menos usado. Un elemento sin imagen devuelve
una imagen vacía: QML pinta su sustituto. Nunca se escribe junto al origen.

    proveedor = ProveedorMiniaturas(Path(cache) / "portadas", anchos={"": 220, "grande": 520})
    proveedor.fijar_rutas({"42": "/biblioteca/Autor/Libro (42)/cover.jpg"})
    app.motor.addImageProvider("portadas", proveedor)
    # QML: Image { source: "image://portadas/42" }  ·  "image://portadas/42/grande"
"""

from __future__ import annotations

import os
import threading
from pathlib import Path

from gui_comun.qt import QImage, QImageReader, QQmlImageProviderBase, QQuickImageProvider, QSize

TOPE_MB = 200
CALIDAD = 85
ANCHOS = {"": 220, "grande": 520}


def podar(carpeta: Path, tope_bytes: int) -> int:
    """Borra las miniaturas menos usadas (la fecha se renueva al usarlas) hasta quedar bajo el tope; devuelve cuántas
    borró. Solo toca su propia carpeta de caché."""
    try:
        archivos = [(p, p.stat()) for p in carpeta.glob("*.jpg")]
    except OSError:
        return 0
    total = sum(s.st_size for _p, s in archivos)
    borradas = 0
    for p, s in sorted(archivos, key=lambda x: x[1].st_mtime):
        if total <= tope_bytes:
            break
        try:
            p.unlink()
            total -= s.st_size
            borradas += 1
        except OSError:
            pass
    return borradas


def _segura(clave: str) -> str:
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in clave)[:120] or "_"


def miniatura(origen: Path, carpeta: Path, clave: str, ancho: int) -> QImage:
    """La miniatura de `origen` a `ancho` px (de la caché si ya está); una imagen vacía si no hay imagen legible."""
    try:
        st = origen.stat()
    except OSError:
        return QImage()
    clave = _segura(clave)
    archivo = carpeta / f"{clave}-{ancho}-{st.st_mtime_ns}.jpg"
    if archivo.is_file():
        try:
            os.utime(archivo)                      # usada ahora: la poda quita primero lo que nadie mira
        except OSError:
            pass
        img = QImage(str(archivo))
        if not img.isNull():
            return img
    lector = QImageReader(str(origen))
    lector.setAutoTransform(True)
    tam = lector.size()
    if tam.isValid() and tam.width() > ancho:
        lector.setScaledSize(QSize(ancho, max(1, round(tam.height() * ancho / tam.width()))))
    img = lector.read()
    if img.isNull():
        return QImage()
    try:
        carpeta.mkdir(parents=True, exist_ok=True)
        for viejo in carpeta.glob(f"{clave}-{ancho}-*.jpg"):          # la de una imagen anterior del mismo elemento
            viejo.unlink(missing_ok=True)
        img.save(str(archivo), "JPG", CALIDAD)
    except OSError:
        pass
    return img


class ProveedorMiniaturas(QQuickImageProvider):
    """`image://<nombre>/<clave>[/<tamaño>]`: la imagen de `clave` (de `fijar_rutas`, o la propia clave si
    `claves_son_rutas`) al ancho de `anchos[tamaño]`, o al que pida `sourceSize` (64–1200 px)."""

    def __init__(self, carpeta: Path, anchos: dict[str, int] | None = None, tope_mb: int = TOPE_MB,
                 claves_son_rutas: bool = False):
        super().__init__(QQuickImageProvider.ImageType.Image, QQmlImageProviderBase.Flag.ForceAsynchronousImageLoading)
        self.carpeta = Path(carpeta)
        self.anchos = dict(anchos or ANCHOS)
        self.tope = tope_mb * 1024 * 1024
        self.claves_son_rutas = claves_son_rutas
        self._rutas: dict[str, str] = {}
        self._cerrojo = threading.Lock()
        self._nuevas = 0

    def fijar_rutas(self, rutas: dict[str, str]) -> None:
        with self._cerrojo:
            self._rutas = dict(rutas)

    def ruta(self, clave: str) -> str:
        if self.claves_son_rutas:
            return clave if clave.startswith("/") else "/" + clave
        with self._cerrojo:
            return self._rutas.get(clave, "")

    def requestImage(self, ident, size=None, requested=None):   # noqa: N802  (la firma de Qt)
        texto = str(ident).split("?", 1)[0]
        if self.claves_son_rutas:
            clave, _sep, tamano = texto.rpartition("@")
            clave, tamano = (clave, tamano) if _sep else (texto, "")
        else:
            clave, _sep, tamano = texto.partition("/")
        ancho = self.anchos.get(tamano, self.anchos.get("", 220))
        if requested is not None and requested.isValid() and requested.width() > 0:
            ancho = min(max(requested.width(), 64), 1200)
        ruta = self.ruta(clave)
        img = miniatura(Path(ruta), self.carpeta, clave, ancho) if ruta else QImage()
        if not img.isNull():
            self._nuevas += 1
            if self._nuevas % 200 == 0:
                podar(self.carpeta, self.tope)
        if size is not None and hasattr(size, "setWidth"):
            size.setWidth(img.width())
            size.setHeight(img.height())
        return img
