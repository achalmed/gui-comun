"""gui_comun/visor_pdf.py — el controlador de `GuiComun.VistaPdf` (3.1): un PDF integrado en la ventana.

Viene de LaTeX Studio (`latex_app/visor.py` y `controladores/visor.py`); Raphi (vista previa) y Quarto (el PDF de un
documento) lo necesitaban igual. Dos motores de página (`motor`):

- **qtpdf**: con el módulo QML `QtQuick.Pdf` instalado (`qml6-module-qtquick-pdf`), cada página la pinta Qt
  (`PdfPageImage`) y aquí no se renderiza nada;
- **pdftoppm** (respaldo): las páginas se renderizan con `pdftoppm` (poppler) a PNG, por demanda y a la resolución del
  zoom, en hilos aparte, en una caché bajo `<cache>/paginas/<clave>/`, donde la clave lleva la ruta, la fecha y el
  tamaño del PDF: recompilar invalida solo ese documento. La caché tiene un tope (200 MB) y se poda por antigüedad.

`GUI_COMUN_VISOR=pdftoppm` (o la variable propia del studio, `variable_motor`) fuerza el segundo. El tamaño de las
páginas (`pdfinfo`), el zoom, la marca y la recarga conservando la página son los mismos con los dos.

Lo propio de una disciplina no vive aquí: SyncTeX es de LaTeX (su studio hereda de `VisorPdf`, añade sus `Slot` y
conecta `dobleClic` de la vista); la base solo ofrece `marcarRecuadro` (ir a la página y marcar un recuadro).

    visor = VisorPdf(cache=Path(xdg_cache) / "mi-studio")
    app.exponer("visor", visor)          # VistaPdf { visor: studio.visor }
    visor.abrir("/ruta/documento.pdf")
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from gui_comun.modelos import ModeloLista
from gui_comun.qt import QObject, Property, Signal, Slot

LIMITE_CACHE = 200 * 1024 * 1024
ROLES = ("pagina", "ancho", "alto", "imagen", "miniatura")
PPP_MINIATURA = 18
ZOOM_MIN, ZOOM_MAX = 0.25, 4.0
_TAMANO = re.compile(r"^Page\s+(\d+)\s+size:\s+([\d.]+)\s+x\s+([\d.]+)", re.M)
_PAGINAS = re.compile(r"^Pages:\s+(\d+)", re.M)


# ======================================================================================================================
# sin Qt: tamaños, renderizado y caché

def cache_paginas(base: Path) -> Path:
    return Path(base) / "paginas"


def clave(pdf: Path) -> str:
    try:
        st = pdf.stat()
        firma = f"{pdf.resolve()}|{st.st_mtime_ns}|{st.st_size}"
    except OSError:
        firma = str(pdf)
    return hashlib.sha1(firma.encode("utf-8")).hexdigest()[:16]


def paginas(pdf: Path) -> list[tuple[float, float]]:
    """El tamaño en puntos de cada página (ancho, alto) según `pdfinfo`; [] si no hay PDF o poppler."""
    if not pdf.is_file() or not shutil.which("pdfinfo"):
        return []
    try:
        r = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, timeout=20)
        m = _PAGINAS.search(r.stdout)
        total = int(m.group(1)) if m else 0
        if total == 0:
            return []
        r = subprocess.run(["pdfinfo", "-f", "1", "-l", str(total), str(pdf)], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError, ValueError):
        return []
    tamanos = {int(n): (float(a), float(b)) for n, a, b in _TAMANO.findall(r.stdout)}
    defecto = next(iter(tamanos.values()), (595.0, 842.0))
    return [tamanos.get(i, defecto) for i in range(1, total + 1)]


def renderizar(pdf: Path, pagina: int, ppp: int, cache: Path) -> Path | None:
    """La página `pagina` (1-based) a `ppp` puntos por pulgada como PNG en la caché; la ruta, o None si falla. Si ya
    está, no se vuelve a renderizar (y se le actualiza la fecha para la poda)."""
    ppp = max(20, min(400, int(ppp)))
    carpeta = cache_paginas(cache) / clave(pdf)
    destino = carpeta / f"p{pagina}-{ppp}.png"
    if destino.is_file():
        try:
            os.utime(destino)
        except OSError:
            pass
        return destino
    if not shutil.which("pdftoppm") or not pdf.is_file():
        return None
    carpeta.mkdir(parents=True, exist_ok=True)
    tmp = carpeta / f".p{pagina}-{ppp}-{os.getpid()}-{time.monotonic_ns()}"
    try:
        r = subprocess.run(["pdftoppm", "-f", str(pagina), "-l", str(pagina), "-r", str(ppp), "-png", "-singlefile",
                            "-aa", "yes", "-aaVector", "yes", str(pdf), str(tmp)], capture_output=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    hecho = Path(str(tmp) + ".png")            # pdftoppm -singlefile añade la extensión
    if r.returncode != 0 or not hecho.is_file():
        return None
    os.replace(hecho, destino)
    return destino


def tamano_cache(cache: Path) -> int:
    total = 0
    for raiz, _d, archivos in os.walk(cache_paginas(cache)):
        for a in archivos:
            try:
                total += os.stat(os.path.join(raiz, a)).st_size
            except OSError:
                pass
    return total


def podar(cache: Path, limite: int = LIMITE_CACHE, conservar: str = "") -> int:
    """Borra las carpetas de PDF más antiguas (por último acceso) hasta quedar bajo `limite`; nunca la de `conservar`
    (la clave del PDF abierto). Devuelve los bytes liberados. Solo toca la caché del visor."""
    raiz = cache_paginas(cache)
    if not raiz.is_dir():
        return 0
    carpetas = []
    for d in raiz.iterdir():
        if not d.is_dir():
            continue
        archivos = [f for f in d.iterdir() if f.is_file()]
        carpetas.append((max((f.stat().st_mtime for f in archivos), default=0.0), sum(f.stat().st_size for f in archivos), d))
    total = sum(b for _u, b, _d in carpetas)
    liberado = 0
    for _ultimo, bytes_, d in sorted(carpetas):
        if total <= limite:
            break
        if d.name == conservar:
            continue
        shutil.rmtree(d, ignore_errors=True)
        total -= bytes_
        liberado += bytes_
    return liberado


def hay_qtpdf(variable_motor: str = "") -> bool:
    """¿Está el módulo QML `QtQuick.Pdf`? Si no, o con `GUI_COMUN_VISOR=pdftoppm` (o la variable del studio), no."""
    for nombre in ("GUI_COMUN_VISOR", variable_motor):
        if nombre and os.environ.get(nombre, "").strip().lower() == "pdftoppm":
            return False
    try:
        from PySide6.QtCore import QLibraryInfo
    except ImportError:
        try:
            from PyQt6.QtCore import QLibraryInfo
        except ImportError:
            return False
    base = QLibraryInfo.path(QLibraryInfo.LibraryPath.QmlImportsPath)
    return (Path(base) / "QtQuick" / "Pdf" / "qmldir").is_file()


# ======================================================================================================================
# el controlador

class VisorPdf(QObject):
    """Las páginas del PDF abierto como modelo (`paginas`: tamaño en puntos y, con pdftoppm, la imagen renderizada a la
    resolución del zoom), el zoom, las miniaturas, la recarga conservando la página y la marca de un recuadro.

    Los hilos solo corren `pdftoppm`; el modelo se toca siempre en el hilo de la interfaz (la señal `_hecho` cruza)."""

    cambiado = Signal()
    zoomCambiado = Signal()
    irAPagina = Signal(int, float)           # página (1-based), y en puntos desde arriba (−1: el principio)
    marcar = Signal(int, float, float, float, float)   # página, x, y, ancho, alto (puntos)
    aviso = Signal(str, str)
    _hecho = Signal(str, int, int, str)      # clave del PDF, página, ppp, ruta del PNG (desde el hilo)

    def __init__(self, cache: Path, variable_motor: str = "", parent=None):
        super().__init__(parent)
        self._cache = Path(cache)            # la carpeta de caché del studio (la de las páginas cuelga de ella)
        self._paginas = ModeloLista(ROLES, parent=self)
        self._pdf = ""
        self._clave = ""
        self._zoom = 1.0
        self._ajustar = True
        self._escala = 1.0                   # devicePixelRatio de la pantalla (lo fija QML)
        self._pedidas: set = set()
        self._motor = "qtpdf" if hay_qtpdf(variable_motor) else "pdftoppm"
        self._revision = 0                   # sube con cada PDF nuevo o recompilado: QML vuelve a abrir el documento
        self._hilos = ThreadPoolExecutor(max_workers=2, thread_name_prefix="pdftoppm")
        self._hecho.connect(self._poner_imagen)

    paginas = Property(QObject, lambda self: self._paginas, constant=True)
    motor = Property(str, lambda self: self._motor, constant=True)

    # ---------------------------------------------------------------------------------------------------- el PDF
    @Slot(str)
    def abrir(self, pdf: str) -> None:
        """Muestra `pdf`; si es el mismo con otra fecha (recompilado), la vista conserva la página."""
        ruta = Path(pdf) if pdf else None
        if ruta is None or not ruta.is_file():
            if self._pdf or self._paginas.filas:
                self._pdf, self._clave = "", ""
                self._paginas.poner([])
                self.cambiado.emit()
            return
        nueva = clave(ruta)
        if pdf == self._pdf and nueva == self._clave:
            return
        self._pdf, self._clave = pdf, nueva
        self._revision += 1
        self._pedidas.clear()
        self._paginas.poner([{"pagina": i, "ancho": a, "alto": b, "imagen": "", "miniatura": ""}
                             for i, (a, b) in enumerate(paginas(ruta), start=1)])
        podar(self._cache, conservar=nueva)
        self.cambiado.emit()

    @Slot()
    def recargar(self) -> None:
        pdf, self._pdf, self._clave = self._pdf, "", ""
        self.abrir(pdf)

    @Slot()
    def cerrar(self) -> None:
        self.abrir("")

    @Property(str, notify=cambiado)
    def pdf(self) -> str:
        return self._pdf

    @Property(str, notify=cambiado)
    def pdfUrl(self) -> str:
        return Path(self._pdf).as_uri() if self._pdf else ""

    @Property(int, notify=cambiado)
    def revision(self) -> int:
        return self._revision

    @Property(int, notify=cambiado)
    def total(self) -> int:
        return self._paginas.filas

    @Property(float, notify=cambiado)
    def anchoMaximo(self) -> float:
        """El ancho en puntos de la página más ancha (el ancho del contenido del visor)."""
        return max((f["ancho"] for f in self._paginas.todas()), default=0.0)

    # ---------------------------------------------------------------------------------------------------- zoom
    def _zoom_set(self, z: float) -> None:
        z = max(ZOOM_MIN, min(ZOOM_MAX, float(z)))
        if abs(z - self._zoom) > 1e-3:
            self._zoom = z
            self.zoomCambiado.emit()

    def _ajustar_set(self, v: bool) -> None:
        self._ajustar = bool(v)
        self.zoomCambiado.emit()

    def _escala_set(self, v: float) -> None:
        self._escala = max(1.0, float(v))

    zoom = Property(float, lambda self: self._zoom, _zoom_set, notify=zoomCambiado)
    ajustarAncho = Property(bool, lambda self: self._ajustar, _ajustar_set, notify=zoomCambiado)
    escala = Property(float, lambda self: self._escala, _escala_set, notify=zoomCambiado)

    @Slot()
    def acercar(self) -> None:
        self.ajustarAncho = False
        self.zoom = self._zoom * 1.2

    @Slot()
    def alejar(self) -> None:
        self.ajustarAncho = False
        self.zoom = self._zoom / 1.2

    @Slot(float)
    def ajustarA(self, ancho_disponible: float) -> None:
        """Con «ajustar al ancho», el zoom que hace caber la página más ancha en `ancho_disponible` (píxeles lógicos)."""
        if self._ajustar and self._paginas.filas:
            ancho = max(f["ancho"] for f in self._paginas.todas())
            self.zoom = max(ZOOM_MIN, min(ZOOM_MAX, ancho_disponible / ancho))

    def ppp(self) -> int:
        """Los puntos por pulgada del zoom actual, redondeados a pasos de 12 para que la caché se reutilice."""
        valor = 72.0 * self._zoom * self._escala
        return max(24, min(400, int(round(valor / 12.0)) * 12))

    # ---------------------------------------------------------------------------------------------------- marca
    @Slot(int, float, float, float, float)
    def marcarRecuadro(self, pagina: int, x: float, y: float, ancho: float, alto: float) -> None:
        """Va a la página y marca un recuadro (puntos, origen arriba a la izquierda): SyncTeX, un resultado de búsqueda."""
        if 1 <= pagina <= self._paginas.filas:
            self.irAPagina.emit(pagina, y)
            self.marcar.emit(pagina, x, y, ancho, alto)

    # ---------------------------------------------------------------------------------------------------- renderizado
    @Slot(int)
    def pedir(self, pagina: int) -> None:
        """QML pide una página visible: si no está a la resolución del zoom, se renderiza en un hilo."""
        self._pedir(pagina, self.ppp())

    @Slot(int)
    def pedirMiniatura(self, pagina: int) -> None:
        self._pedir(pagina, PPP_MINIATURA)

    def _pedir(self, pagina: int, ppp: int) -> None:
        if self._motor == "qtpdf":           # Qt pinta la página: nada que renderizar aquí
            return
        if not self._pdf or not (1 <= pagina <= self._paginas.filas):
            return
        llave = (self._clave, pagina, ppp)
        if llave in self._pedidas:
            return
        self._pedidas.add(llave)
        pdf, base, clave_pdf = Path(self._pdf), self._cache, self._clave

        def trabajo():
            ruta = renderizar(pdf, pagina, ppp, base)
            self._hecho.emit(clave_pdf, pagina, ppp, str(ruta) if ruta else "")

        self._hilos.submit(trabajo)

    def renderizar_ya(self, pagina: int, ppp: int | None = None) -> str:
        """En el hilo actual (pruebas y capturas)."""
        ppp = ppp or self.ppp()
        ruta = renderizar(Path(self._pdf), pagina, ppp, self._cache)
        self._poner_imagen(self._clave, pagina, ppp, str(ruta) if ruta else "")
        return str(ruta) if ruta else ""

    def _poner_imagen(self, clave_pdf: str, pagina: int, ppp: int, ruta: str) -> None:
        if clave_pdf != self._clave or not ruta or not (1 <= pagina <= self._paginas.filas):
            if not ruta:
                self._pedidas.discard((clave_pdf, pagina, ppp))
            return
        url = Path(ruta).as_uri()
        if ppp == PPP_MINIATURA:
            self._paginas.actualizar(pagina - 1, miniatura=url)
        else:
            self._paginas.actualizar(pagina - 1, imagen=url)

    def apagar(self) -> None:
        """Al cerrar la ventana: no espera a los `pdftoppm` en curso."""
        self._hilos.shutdown(wait=False, cancel_futures=True)
