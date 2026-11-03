"""gui_comun/editor.py — el controlador de `GuiComun.EditorTexto` y `GuiComun.BarraBuscarReemplazar` (3.1).

Los archivos abiertos en un editor y lo que el editor pide a Python: leer, guardar (solo cuando el usuario lo pide, y
sin pisar un cambio hecho fuera sin preguntar), guardar como, buscar y reemplazar con expresiones regulares y el aviso
de que un archivo cambió en disco (`QFileSystemWatcher`, creado al abrir el primer archivo). Viene de LaTeX Studio
(`controladores/editor.py`), que Quarto Studio copió cambiando solo las definiciones de resaltado: aquí esas
definiciones son un parámetro.

El texto vive en QML (un `TextArea` por archivo abierto, cada uno con su historial de deshacer); Python no lo guarda.
Las posiciones que devuelve la búsqueda son de UTF-16 (las de QML), no de Python.

    editor = ControladorEditor(consola, definiciones={".tex": "LaTeX", ".bib": "BibTeX"})
    app.exponer("editor", editor)        # EditorTexto { controlador: studio.editor; ruta: … }
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Callable

from gui_comun.modelos import ModeloLista
from gui_comun.qt import QFileSystemWatcher, QObject, Property, Signal, Slot

ROLES = ("ruta", "nombre", "carpeta", "modificado", "definicion", "solo_lectura")
_ASTRAL = re.compile("[\U00010000-\U0010FFFF]")

# extensión → definición de KSyntaxHighlighting (los nombres de `Repository.definitionForName`)
DEFINICIONES = {
    ".tex": "LaTeX", ".sty": "LaTeX", ".cls": "LaTeX", ".ltx": "LaTeX", ".dtx": "LaTeX", ".bbx": "LaTeX", ".cbx": "LaTeX",
    ".lbx": "LaTeX", ".def": "LaTeX", ".cfg": "LaTeX", ".bib": "BibTeX", ".md": "Markdown", ".qmd": "Markdown",
    ".rmd": "Markdown", ".yml": "YAML", ".yaml": "YAML", ".json": "JSON", ".ipynb": "JSON", ".toml": "TOML",
    ".ini": "INI Files", ".conf": "INI Files", ".py": "Python", ".sh": "Bash", ".bash": "Bash", ".zsh": "Zsh",
    ".lua": "Lua", ".js": "JavaScript", ".ts": "TypeScript", ".qml": "QML", ".css": "CSS", ".scss": "SCSS",
    ".html": "HTML", ".xml": "XML", ".svg": "XML", ".r": "R Script", ".sql": "SQL", ".csv": "", ".txt": "",
}
# nombres de archivo sin extensión que se reconocen por el nombre
NOMBRES = {"latexmkrc": "Perl", ".latexmkrc": "Perl", "makefile": "Makefile", "dockerfile": "Dockerfile",
           ".gitignore": "Git Ignore", ".bashrc": "Bash", ".zshrc": "Zsh"}

# definición → (abre, cierra) del comentario de línea; lo usa EditorTexto para Ctrl+T (aquí, para las pruebas)
COMENTARIOS = {"LaTeX": ("% ", ""), "BibTeX": ("% ", ""), "Markdown": ("<!-- ", " -->"), "HTML": ("<!-- ", " -->"),
               "XML": ("<!-- ", " -->"), "YAML": ("# ", ""), "Python": ("# ", ""), "Bash": ("# ", ""), "Zsh": ("# ", ""),
               "TOML": ("# ", ""), "INI Files": ("; ", ""), "Perl": ("# ", ""), "R Script": ("# ", ""), "Lua": ("-- ", ""),
               "SQL": ("-- ", ""), "JavaScript": ("// ", ""), "TypeScript": ("// ", ""), "QML": ("// ", ""),
               "SCSS": ("// ", ""), "CSS": ("/* ", " */"), "JSON": ("", "")}


def definicion_de(ruta: str, definiciones: dict[str, str] | None = None) -> str:
    """La definición de KSyntaxHighlighting de `ruta` según su extensión (o su nombre); "" sin resaltado."""
    p = Path(ruta)
    nombre = p.name.lower()
    if nombre in NOMBRES:
        return NOMBRES[nombre]
    mapa = DEFINICIONES if definiciones is None else definiciones
    return mapa.get(p.suffix.lower(), "")


def _utf16(texto: str, indices: list[int]) -> list[int]:
    """Índices de Python → índices de UTF-16 (los de QML); iguales si no hay caracteres fuera del plano básico."""
    if not _ASTRAL.search(texto):
        return indices
    mapa, acumulado, ultimo = {}, 0, 0
    for i in sorted(set(indices)):
        acumulado += len(texto[ultimo:i].encode("utf-16-le")) // 2
        ultimo = i
        mapa[i] = acumulado
    return [mapa[i] for i in indices]


def compilar_patron(patron: str, regex: bool, mayusculas: bool, palabra: bool):
    if not regex:
        patron = re.escape(patron)
    if palabra:
        patron = rf"\b(?:{patron})\b"
    return re.compile(patron, 0 if mayusculas else re.IGNORECASE)


def buscar(texto: str, patron: str, regex: bool = False, mayusculas: bool = False, palabra: bool = False) -> list[list[int]]:
    """Las coincidencias como [inicio, fin] en UTF-16; las vacías (p. ej. `^`) se omiten."""
    if not patron:
        return []
    r = compilar_patron(patron, regex, mayusculas, palabra)
    pares = [(m.start(), m.end()) for m in r.finditer(texto) if m.end() > m.start()]
    planos = _utf16(texto, [x for par in pares for x in par])
    return [[planos[2 * i], planos[2 * i + 1]] for i in range(len(pares))]


def reemplazos(texto: str, patron: str, reemplazo: str, regex: bool = False, mayusculas: bool = False,
               palabra: bool = False, solo_desde: int = -1) -> list[list]:
    """Los reemplazos como [inicio, fin, texto nuevo] (UTF-16), del último al primero para aplicarlos sin desplazar;
    con `regex`, `reemplazo` admite \\1 y \\g<nombre>. `solo_desde` ≥ 0: solo la primera coincidencia desde ahí."""
    if not patron:
        return []
    r = compilar_patron(patron, regex, mayusculas, palabra)
    coincidencias = [m for m in r.finditer(texto) if m.end() > m.start()]
    if solo_desde >= 0:
        pos = _utf16(texto, [m.start() for m in coincidencias])
        coincidencias = [m for m, p in zip(coincidencias, pos) if p >= solo_desde][:1] or coincidencias[:1]
    nuevos = [(m.start(), m.end(), m.expand(reemplazo) if regex else reemplazo) for m in coincidencias]
    planos = _utf16(texto, [x for a, b, _n in nuevos for x in (a, b)])
    return [[planos[2 * i], planos[2 * i + 1], nuevos[i][2]] for i in range(len(nuevos))][::-1]


class ControladorEditor(QObject):
    """Los archivos abiertos (`abiertos`, un `ModeloLista` con ROLES) y las operaciones del editor.

    `definiciones`: extensión → definición de resaltado (por omisión, `DEFINICIONES`); o `definicion`, una función
    `ruta -> definición` que manda sobre las dos (Quarto: un `.qmd` es Markdown). `consola`: la del studio, o None."""

    cambiado = Signal()                      # la lista de abiertos
    actualCambiado = Signal()
    cambioExterno = Signal(str)              # ruta: el archivo cambió en disco desde que se abrió o se guardó
    guardadoArchivo = Signal(str)
    aviso = Signal(str, str)

    def __init__(self, consola=None, definiciones: dict[str, str] | None = None,
                 definicion: Callable[[str], str] | None = None, parent=None):
        super().__init__(parent)
        self.consola = consola
        self._definiciones = definiciones
        self._definicion = definicion
        self._abiertos = ModeloLista(ROLES, parent=self)
        self._firmas: dict[str, tuple] = {}
        self._crlf: dict[str, bool] = {}
        self._actual = ""
        self._vigia: QFileSystemWatcher | None = None

    abiertos = Property(QObject, lambda self: self._abiertos, constant=True)

    @Slot(str, result=str)
    def definicionDe(self, ruta: str) -> str:
        return self._definicion(ruta) if self._definicion else definicion_de(ruta, self._definiciones)

    def _registrar(self, nivel: str, texto: str) -> None:
        if self.consola is not None:
            self.consola.registrar(nivel, texto)

    # ------------------------------------------------------------- abrir y cerrar
    @staticmethod
    def _firma(ruta: str) -> tuple:
        try:
            st = os.stat(ruta)
            return (st.st_mtime_ns, st.st_size)
        except OSError:
            return (0, 0)

    def _indice(self, ruta: str) -> int:
        return next((i for i, f in enumerate(self._abiertos.todas()) if f["ruta"] == ruta), -1)

    @Slot(str, result=int)
    def abrir(self, ruta: str) -> int:
        """Añade el archivo a los abiertos (si no lo estaba) y lo hace actual; devuelve su índice o −1."""
        ruta = str(Path(ruta).expanduser()) if ruta else ""
        if not ruta or not os.path.isfile(ruta):
            self.aviso.emit(f"No existe: {ruta}", "aviso")
            return -1
        i = self._indice(ruta)
        if i < 0:
            self._abiertos.anadir({"ruta": ruta, "nombre": Path(ruta).name, "carpeta": str(Path(ruta).parent), "modificado": False,
                                   "definicion": self.definicionDe(ruta), "solo_lectura": not os.access(ruta, os.W_OK)})
            i = self._abiertos.filas - 1
            self._vigilar(ruta)
            self.cambiado.emit()
        self.fijarActual(ruta)
        return i

    @Slot(str)
    def cerrar(self, ruta: str) -> None:
        i = self._indice(ruta)
        if i < 0:
            return
        self._abiertos.quitar(i)
        self._firmas.pop(ruta, None)
        if self._vigia is not None and ruta in self._vigia.files():
            self._vigia.removePath(ruta)
        if self._actual == ruta:
            resto = self._abiertos.todas()
            self.fijarActual(resto[min(i, len(resto) - 1)]["ruta"] if resto else "")
        self.cambiado.emit()

    @Slot()
    def cerrarTodos(self) -> None:
        for f in list(self._abiertos.todas()):
            self.cerrar(f["ruta"])

    @Slot(str)
    def fijarActual(self, ruta: str) -> None:
        if ruta != self._actual:
            self._actual = ruta
            self.actualCambiado.emit()

    @Property(str, notify=actualCambiado)
    def actual(self) -> str:
        return self._actual

    @Property(int, notify=actualCambiado)
    def indiceActual(self) -> int:
        return self._indice(self._actual)

    @Slot(str, bool)
    def marcarModificado(self, ruta: str, modificado: bool) -> None:
        i = self._indice(ruta)
        if i >= 0 and self._abiertos.fila(i).get("modificado") != modificado:
            self._abiertos.actualizar(i, modificado=modificado)
            self.cambiado.emit()

    @Property(bool, notify=cambiado)
    def hayModificados(self) -> bool:
        return any(f.get("modificado") for f in self._abiertos.todas())

    @Property("QVariantList", notify=cambiado)
    def modificados(self) -> list:
        return [f["ruta"] for f in self._abiertos.todas() if f.get("modificado")]

    # ------------------------------------------------------------- leer y guardar
    @Slot(str, result=str)
    def leer(self, ruta: str) -> str:
        """El texto del archivo (UTF-8; los finales de línea de Windows se recuerdan para guardarlos igual)."""
        try:
            with open(ruta, encoding="utf-8", errors="replace", newline="") as f:
                texto = f.read()
        except OSError as e:
            self.aviso.emit(f"No se pudo leer {ruta}: {e.strerror}", "error")
            return ""
        self._crlf[ruta] = "\r\n" in texto
        self._firmas[ruta] = self._firma(ruta)
        return texto.replace("\r\n", "\n")

    @Slot(str, str, bool, result=str)
    def guardar(self, ruta: str, texto: str, forzar: bool = False) -> str:
        """Escribe el archivo (en su sitio: conserva permisos y enlaces duros). Devuelve "" si guardó, «externo» si el
        archivo cambió en disco desde que se leyó (y no se forzó), o el error. Solo lo llama una orden del usuario."""
        if not forzar and ruta in self._firmas and self._firma(ruta) != self._firmas[ruta]:
            return "externo"
        if self._crlf.get(ruta):
            texto = texto.replace("\n", "\r\n")
        try:
            with open(ruta, "w", encoding="utf-8", newline="") as f:
                f.write(texto)
        except OSError as e:
            return f"No se pudo guardar {Path(ruta).name}: {e.strerror}"
        self._firmas[ruta] = self._firma(ruta)
        self.marcarModificado(ruta, False)
        self._registrar("info", f"Guardado: {ruta}")
        self.guardadoArchivo.emit(ruta)
        return ""

    @Slot(str, str, str, result=str)
    def guardarComo(self, ruta: str, nueva: str, texto: str) -> str:
        """Guardar como: escribe `texto` en `nueva` (el diálogo de KDE ya preguntó si sobrescribir) y la pestaña pasa a
        ser la de `nueva`; el archivo original no se toca. Devuelve "" o el error."""
        nueva = str(Path(nueva).expanduser()) if nueva else ""
        if not nueva:
            return "Sin nombre de archivo."
        try:
            with open(nueva, "w", encoding="utf-8", newline="") as f:
                f.write(texto.replace("\n", "\r\n") if self._crlf.get(ruta) else texto)
        except OSError as e:
            return f"No se pudo guardar {Path(nueva).name}: {e.strerror}"
        i = self._indice(ruta)
        if i >= 0 and nueva != ruta:
            otra = self._indice(nueva)
            if otra >= 0:                                    # ya estaba abierta: se cierra la vieja pestaña de ese archivo
                self._abiertos.quitar(otra)
                i = self._indice(ruta)
            self._abiertos.actualizar(i, ruta=nueva, nombre=Path(nueva).name, carpeta=str(Path(nueva).parent), modificado=False,
                                      definicion=self.definicionDe(nueva), solo_lectura=False)
            self._firmas.pop(ruta, None)
            self._crlf[nueva] = self._crlf.pop(ruta, False)
            if self._vigia is not None and ruta in self._vigia.files():
                self._vigia.removePath(ruta)
        self._firmas[nueva] = self._firma(nueva)
        self._vigilar(nueva)
        if self._actual == ruta:
            self._actual = nueva
            self.actualCambiado.emit()
        self.cambiado.emit()
        self._registrar("info", f"Guardado como: {nueva}")
        self.guardadoArchivo.emit(nueva)
        return ""

    @Slot(str)
    def aceptarDisco(self, ruta: str) -> None:
        """El usuario recargó el archivo desde el disco: la firma nueva es la buena."""
        self._firmas[ruta] = self._firma(ruta)

    # ------------------------------------------------------------- vigilar cambios externos
    def _vigilar(self, ruta: str) -> None:
        if self._vigia is None:
            self._vigia = QFileSystemWatcher(self)
            self._vigia.fileChanged.connect(self._cambio_en_disco)
        if ruta not in self._vigia.files():
            self._vigia.addPath(ruta)

    def _cambio_en_disco(self, ruta: str) -> None:
        if self._vigia is not None and os.path.exists(ruta) and ruta not in self._vigia.files():
            self._vigia.addPath(ruta)                 # los editores guardan reemplazando: se vuelve a vigilar
        if ruta in self._firmas and self._firma(ruta) != self._firmas[ruta] and self._indice(ruta) >= 0:
            self.cambioExterno.emit(ruta)

    @Slot(str, result=bool)
    def cambioEnDisco(self, ruta: str) -> bool:
        return ruta in self._firmas and self._firma(ruta) != self._firmas[ruta]

    def soltar(self) -> None:
        """Retira el vigía dentro del bucle de eventos (su notificador de inotify no sobrevive a que lo recoja Python).
        Llámese al cerrar la ventana, antes de `Aplicacion.cerrar()`."""
        if self._vigia is not None:
            self._vigia.fileChanged.disconnect(self._cambio_en_disco)
            self._vigia.deleteLater()
            self._vigia = None

    # ------------------------------------------------------------- buscar y reemplazar
    @Slot(str, str, bool, bool, bool, result="QVariantMap")
    def buscar(self, texto: str, patron: str, regex: bool, mayusculas: bool, palabra: bool) -> dict:
        try:
            return {"error": "", "coincidencias": buscar(texto, patron, regex, mayusculas, palabra)}
        except re.error as e:
            return {"error": f"Expresión regular no válida: {e}", "coincidencias": []}

    @Slot(str, str, str, bool, bool, bool, int, result="QVariantMap")
    def reemplazar(self, texto: str, patron: str, reemplazo: str, regex: bool, mayusculas: bool, palabra: bool, desde: int) -> dict:
        """`desde` ≥ 0: solo la siguiente coincidencia; −1: todas."""
        try:
            return {"error": "", "cambios": reemplazos(texto, patron, reemplazo, regex, mayusculas, palabra, desde)}
        except (re.error, IndexError) as e:
            return {"error": f"No se pudo reemplazar: {e}", "cambios": []}
