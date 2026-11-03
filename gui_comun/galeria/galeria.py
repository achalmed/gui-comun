"""gui_comun/galeria/galeria.py — la galería: un VentanaStudio con un registro de acciones de muestra, una tabla de
«repositorios» ficticios, listas, consola y tareas simuladas; cada componente de GuiComun tiene su página."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from gui_comun import __version__

AQUI = Path(__file__).resolve().parent
QML = AQUI / "qml" / "Galeria.qml"

# nombre, grupo, rama, nivel, estado, cambios, ↑, ↓, último commit, actividad, habilitado
FILAS = [
    ("gui-comun", "Studios", "main", "positivo", "Sincronizado", "", 0, 0, "2.0.0: módulo QML GuiComun", "hace 1 h", True),
    ("git-studio", "Studios", "wip/2026-11-01-qml", "neutro", "Cambios sin confirmar", "4 mod. · 2 sin seg.", 0, 0, "Piloto QML + Kirigami", "hace 10 min", True),
    ("filesystem-studio", "Studios", "main", "positivo", "Sincronizado", "", 0, 0, "Explorador: «Usar en…» como submenú", "ayer", True),
    ("raphi", "Studios", "main", "activo", "Commits por traer", "", 0, 1, "Dolphin: menús de servicio por familia", "hace 2 d", True),
    ("lliphi", "Studios", "main", "positivo", "Sincronizado", "", 0, 0, "0.3.0: Lliphi Studio y sesión anidada", "hace 5 h", True),
    ("qillqa", "Plataforma", "main", "neutro", "Commits sin enviar", "", 1, 0, "OpenProject: respaldo nocturno", "hace 1 h", True),
    ("yachay", "Plataforma", "main", "negativo", "Divergido: traer y enviar", "1 mod.", 2, 3, "Acervo: unidades citables", "hace 9 d", True),
    ("web", "Sitios", "main", "positivo", "Sincronizado", "", 0, 0, "Tema: hardlinks con los 12 sitios", "hace 2 d", True),
    ("datafw", "Investigación", "main", "positivo", "Sincronizado", "", 0, 0, "Acervo BCRP: series mensuales", "hace 1 sem", True),
    ("prompts", "Gobierno", "—", "inactivo", "Desactivado", "", 0, 0, "", "", False),
]
COLUMNAS = ("Repositorio", "Rama", "Estado", "Cambios", "↑", "↓", "Último commit", "Actividad")
EMBLEMAS = {"positivo": "vcs-normal", "neutro": "vcs-locally-modified", "activo": "vcs-update-required",
            "negativo": "vcs-conflicting", "inactivo": "emblem-pause"}


def construir(app):
    """Registra acciones, modelos y datos de muestra en la aplicación de la galería."""
    from gui_comun.acciones import Acciones, StandardKey
    from gui_comun.consola import Consola
    from gui_comun.modelos import ModeloFiltrado, ModeloLista
    from gui_comun.qt import QAbstractTableModel, QByteArray, QModelIndex, Qt, rol
    from gui_comun.tareas import Tareas

    class Tabla(QAbstractTableModel):
        R_NIVEL, R_HABILITADO, R_ICONO, R_GRUPO = rol(1), rol(2), rol(3), rol(4)

        def rowCount(self, parent=QModelIndex()):
            return 0 if parent.isValid() else len(FILAS)

        def columnCount(self, parent=QModelIndex()):
            return 0 if parent.isValid() else len(COLUMNAS)

        def roleNames(self):
            return {Qt.ItemDataRole.DisplayRole: QByteArray(b"display"), self.R_NIVEL: QByteArray(b"nivel"),
                    self.R_HABILITADO: QByteArray(b"habilitado"), self.R_ICONO: QByteArray(b"icono"),
                    self.R_GRUPO: QByteArray(b"grupo")}

        def headerData(self, seccion, orientacion, role=Qt.ItemDataRole.DisplayRole):
            if orientacion == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
                return COLUMNAS[seccion]
            return None

        def data(self, index, role=Qt.ItemDataRole.DisplayRole):
            f = FILAS[index.row()]
            c = index.column()
            if role == self.R_NIVEL:
                return f[3]
            if role == self.R_HABILITADO:
                return f[10]
            if role == self.R_GRUPO:
                return f[1]
            if role == self.R_ICONO:
                return "folder-git" if c == 0 else EMBLEMAS[f[3]] if c == 2 else ""
            if role == Qt.ItemDataRole.EditRole and c in (4, 5):
                return f[6] if c == 4 else f[7]
            if role != Qt.ItemDataRole.DisplayRole:
                return None
            valores = (f[0], f[2], f[4], f[5] or ("—" if f[10] else ""), str(f[6]) if f[6] else "", str(f[7]) if f[7] else "", f[8], f[9])
            return valores[c]

    consola = Consola()
    tareas = Tareas(consola)
    acciones = Acciones()
    acciones.estandar("Galería")

    def tarea_de_muestra():
        import time

        def trabajo(progress_cb=None, cancel_cb=None, message_cb=None):
            for i, (nombre, *_r) in enumerate(FILAS, 1):
                if cancel_cb():
                    from gui_comun.workers.function_worker import OperationCancelled
                    raise OperationCancelled()
                progress_cb(int(i * 100 / len(FILAS)), nombre)
                message_cb("cmd", f"$ git -C ~/Documentos/{nombre} status --porcelain=v1 -b")
                message_cb("out", f"## main...origin/main")
                time.sleep(0.25)
            message_cb("ok", f"{len(FILAS)} repositorios analizados")
            return len(FILAS)
        tareas.funcion("Analizando repositorios…", trabajo, al_terminar=lambda n: consola.registrar("ok", f"Analizados: {n}"))

    acciones.registrar("repo.analizar", "&Analizar estado", "view-refresh", StandardKey.Refresh, "Repositorio",
                       descripcion="Vuelve a leer el estado de todos los repositorios", al_disparar=tarea_de_muestra)
    acciones.registrar("repo.obtener", "&Obtener cambios (pull)", "download", None, "Repositorio")
    acciones.registrar("repo.enviar", "&Enviar cambios (push)", "upload-media", None, "Repositorio")
    acciones.registrar("repo.sincronizar", "&Sincronizar", "folder-sync", "Ctrl+Shift+S", "Repositorio")
    acciones.registrar("repo.confirmar", "&Confirmar cambios…", "vcs-commit", "Ctrl+Return", "Repositorio", habilitada=False)
    acciones.registrar("archivo.anadir", "&Añadir repositorio…", "list-add", StandardKey.New, "Archivo")
    acciones.registrar("archivo.clonar", "&Clonar desde GitHub…", "download", "Ctrl+Shift+N", "Archivo")
    acciones.registrar("editar.buscar", "&Buscar", "edit-find", StandardKey.Find, "Editar")
    acciones.registrar("editar.todo", "Seleccionar &todo", "edit-select-all", StandardKey.SelectAll, "Editar")
    acciones.registrar("ver.rama", "Rama", "", None, "Ver › Columnas", marcable=True, marcada=True)
    acciones.registrar("ver.ultimo", "Último commit", "", None, "Ver › Columnas", marcable=True, marcada=True)
    acciones.registrar("herr.informe", "&Informe de sincronización…", "view-list-details", None, "Herramientas")
    # 3.0: una operación de cada estado de riesgo, con trabajo de muestra que no toca nada
    def trabajo_de_muestra(segundos: float, resultado=3):
        def trabajo(progress_cb=None, cancel_cb=None, message_cb=None):
            import time
            for i in range(5):
                progress_cb(int((i + 1) * 20), f"paso {i + 1} de 5")
                time.sleep(segundos / 5)
            return resultado
        return trabajo
    acciones.registrar("galeria.escribir", "&Escribir el informe…", "document-save", None, "Galería", operacion="escritura",
                       confirmar=True, consecuencias="Sobrescribe «informe.md» de muestra (no se escribe nada de verdad).",
                       al_disparar=lambda: tareas.funcion("Escribiendo el informe", trabajo_de_muestra(1.0), operacion="escritura",
                                                          verificar=lambda n: (n == 3, "3 archivos comprobados en disco")))
    acciones.registrar("galeria.instalar", "&Instalar el tema…", "run-install", None, "Galería", operacion="instalacion",
                       consecuencias="Instalaría el tema de muestra en ~/.local/share (aquí no se instala nada). Se puede revertir con «Desinstalar».",
                       al_disparar=lambda: tareas.funcion("Instalando el tema", trabajo_de_muestra(1.0), operacion="instalacion",
                                                          verificar=lambda _n: (False, "el esquema instalado no coincide con el generado")))
    acciones.registrar("galeria.publicar", "&Publicar el sitio…", "document-send", None, "Galería", operacion="publicacion",
                       consecuencias="Subiría 14 archivos a ejemplo.netlify.app y sustituiría la versión publicada (es una muestra: falla a propósito).",
                       al_disparar=lambda: tareas.proceso("Publicar el sitio", ["sh", "-c", "echo 'Subiendo 14 archivos…'; echo 'fatal: Could not resolve host: ejemplo.netlify.app' >&2; exit 128"],
                                                          operacion="publicacion"))
    acciones.registrar("galeria.eliminar", "&Eliminar los auxiliares…", "edit-delete", None, "Galería", operacion="eliminacion",
                       consecuencias="Borraría 23 archivos auxiliares (.aux, .log, .bbl…) de la muestra; las fuentes no se tocan. Aquí no se borra nada.",
                       al_disparar=lambda: tareas.funcion("Eliminando los auxiliares", trabajo_de_muestra(0.6, 23), operacion="eliminacion",
                                                          verificar=lambda n: (True, f"{n} auxiliares menos; fuentes intactas")))
    acciones.registrar("galeria.fallar", "Una tarea que &falla", "system-run", None, "Galería",
                       al_disparar=lambda: tareas.proceso("Compilar «articulo.tex»", ["sh", "-c", "echo 'This is LuaHBTeX'; echo '! Undefined control sequence.' >&2; echo 'l.41 \\comandoquenoexiste' >&2; exit 1"]))
    acciones.registrar("mensajes.aviso", "Mostrar un &mensaje de aviso", "dialog-warning", None, "Galería")
    acciones.registrar("mensajes.error", "Mostrar un mensaje de &error", "dialog-error", None, "Galería")
    acciones.definir_menus([
        ("&Archivo", ["archivo.anadir", "archivo.clonar", "|", "app.salir"]),
        ("&Editar", ["editar.buscar", "editar.todo"]),
        ("&Ver", ["ventana.navegacion", "ventana.detalles", "ventana.inferior", "|", ("C&olumnas", ["ver.rama", "ver.ultimo"]), "|", "ventana.pantalla_completa"]),
        ("&Repositorio", ["repo.analizar", "repo.obtener", "repo.enviar", "repo.sincronizar", "|", "repo.confirmar"]),
        ("&Herramientas", ["ventana.paleta", "herr.informe", "|", "mensajes.aviso", "mensajes.error"]),
        ("&Operaciones", ["galeria.escribir", "galeria.instalar", "galeria.publicar", "galeria.eliminar", "|", "galeria.fallar"]),
        ("A&justes", ["app.ajustes"]),
        ("Ay&uda", ["app.acerca"]),
    ])
    acciones.definir_barra(["repo.analizar", "repo.obtener", "repo.enviar", "repo.sincronizar", "|", "repo.confirmar"])

    tabla = Tabla()
    filtrado = ModeloFiltrado(tabla)
    cambios = ModeloLista(("tipo", "ruta", "detalle"), [
        {"tipo": "M", "ruta": "studio/git_app/aplicacion.py", "detalle": "+41 −12"},
        {"tipo": "M", "ruta": "studio/qml/Main.qml", "detalle": "+120 −3"},
        {"tipo": "?", "ruta": "docs/figuras/", "detalle": "nuevo"}])
    historial = ModeloLista(("hash", "mensaje", "hace", "autor"), [
        {"hash": "c9ec7fe", "mensaje": "Piloto QML + Kirigami", "hace": "hace 10 min", "autor": "Edison Achalma"},
        {"hash": "f493538", "mensaje": "Servicios intactos; controladores nuevos", "hace": "ayer", "autor": "Edison Achalma"},
        {"hash": "2858abf", "mensaje": "Pruebas en offscreen", "hace": "hace 3 d", "autor": "Edison Achalma"}])
    diagnosticos = ModeloLista(("nivel", "mensaje", "archivo", "linea", "detalle"), [
        {"nivel": "error", "mensaje": "Undefined control sequence.", "archivo": "./articulo.tex", "linea": 41, "detalle": "\\comandoquenoexiste"},
        {"nivel": "aviso", "mensaje": "Reference `fig:modelo' on page 3 undefined", "archivo": "./articulo.tex", "linea": 23, "detalle": ""},
        {"nivel": "aviso", "mensaje": "hyperref: Token not allowed in a PDF string (Unicode): removing `\\label'", "archivo": "./articulo.tex", "linea": 7, "detalle": ""},
        {"nivel": "tipografia", "mensaje": "Overfull \\hbox (12.0pt too wide)", "archivo": "./articulo.tex", "linea": 31, "detalle": ""},
        {"nivel": "informacion", "mensaje": "Biber: 14 entradas leídas, 9 citadas", "archivo": "", "linea": 0, "detalle": ""}])
    from gui_comun.modelos import ModeloArbol
    arbol = ModeloArbol(("Conjunto / ruta", "Inodo", "Enlaces", "Tamaño", "Ahorro"), [
        {"valores": ["Conjunto 1 — _partials/pie.qmd", "1203", "3", "1,2 KB", "2,4 KB"], "icono": "folder", "nivel": "positivo",
         "hijos": [{"valores": ["web/_partials/pie.qmd", "", "", "", ""], "icono": "text-markdown"},
                   {"valores": ["web/_pubs/axiomata/_partials/pie.qmd", "", "", "", ""], "icono": "text-markdown"},
                   {"valores": ["web/_pubs/chaska/_partials/pie.qmd", "", "", "", ""], "icono": "text-markdown"}]},
        {"valores": ["Conjunto 2 — _metadata.yml", "1310", "12", "640 B", "6,9 KB"], "icono": "folder", "nivel": "positivo",
         "hijos": [{"valores": [f"web/_pubs/{n}/_metadata.yml", "", "", "", ""], "icono": "text-x-generic"} for n in ("actus-mercator", "aequilibria", "axiomata")]
                  + [{"valores": ["⚠ 9 enlaces fuera del directorio analizado", "", "", "", ""], "nivel": "neutro", "icono": "dialog-warning"}]},
        {"valores": ["Conjunto 3 — theme.scss", "1377", "13", "28 KB", "336 KB"], "icono": "folder", "nivel": "positivo",
         "hijos": lambda nodo: [{"valores": [f"web/_pubs/{n}/theme.scss", "", "", "", ""], "icono": "text-css"} for n in ("chaska", "dialectica-y-mercado")]},
    ])
    consola.escribir("$ git -C ~/Documentos/git-studio status --porcelain=v1 -b", "cmd")
    consola.escribir("## wip/2026-11-01-qml\n M studio/git_app/aplicacion.py\n?? docs/figuras/", "out")
    consola.registrar("info", "Galería de GuiComun " + __version__)

    # 3.0: el registro de la ventana libre (VentanaBase): sin paneles, con su atajo de disciplina
    acciones_libre = Acciones()
    acciones_libre.estandar("Ventana libre", paneles=False)
    acciones_libre.registrar("lienzo.procesar", "&Procesar", "media-playback-start", "Ctrl+Return", "Herramienta",
                             descripcion="Procesa con la herramienta elegida (Ctrl+Intro, como en Raphi)",
                             al_disparar=lambda: tareas.funcion("Procesando", trabajo_de_muestra(0.8), operacion="escritura"))
    acciones_libre.definir_menus([("&Archivo", ["lienzo.procesar", "|", "app.salir"]), ("&Ver", ["ventana.pantalla_completa", "ventana.paleta"]),
                                  ("Ay&uda", ["app.acerca"])])
    app.exponer("accionesLibre", acciones_libre)

    # 3.1: las piezas promovidas de los studios, sobre muestras en una carpeta temporal que se borra al salir
    import atexit
    import shutil
    import tempfile
    from gui_comun import diferencias, pasos
    from gui_comun.editor import ControladorEditor
    from gui_comun.galeria import muestras
    from gui_comun.visor_pdf import VisorPdf
    temporal = Path(tempfile.mkdtemp(prefix="gui-comun-galeria-"))
    atexit.register(shutil.rmtree, temporal, True)
    articulo = temporal / "articulo.tex"
    articulo.write_text(muestras.TEX, encoding="utf-8")
    editor = ControladorEditor(consola)
    editor.abrir(str(articulo))
    visor = VisorPdf(cache=temporal / "cache")
    visor.abrir(str(muestras.pdf(temporal / "articulo.pdf", 3)))
    diferencia = diferencias.comparar("[General]\nColorScheme=LliphiClaro\nfont=Inter,10\nwidgetStyle=kvantum\n",
                                      "[General]\nColorScheme=LliphiOscuro\nfont=Inter,10\nwidgetStyle=kvantum\nAccentColor=196,63,72\n",
                                      ruta="~/.config/kdeglobals", izquierda="Instalado", derecha="Generado")
    diferencia["notas"] = ["Muestra: el archivo instalado y el que generaría el tema."]
    problemas = ModeloLista(("nivel", "titulo", "mensaje", "causa", "accion", "detalle", "ubicacion", "linea"), [
        {"nivel": "error", "titulo": "Orden desconocida: \\comandoquenoexiste", "mensaje": "Undefined control sequence.",
         "causa": "Una errata en el nombre de la orden o un paquete sin cargar.", "accion": "Corrija el nombre o añada el \\usepackage que la define.",
         "detalle": "! Undefined control sequence.\nl.41 \\comandoquenoexiste", "ubicacion": "articulo.tex", "linea": 41},
        {"nivel": "aviso", "titulo": "Referencia sin definir: eq:islm", "mensaje": "Reference `eq:islm' on page 1 undefined",
         "causa": "Falta la \\label o hace falta otra pasada.", "accion": "Compile otra vez; si sigue, añada \\label{eq:islm}.",
         "detalle": "", "ubicacion": "articulo.tex", "linea": 9},
        {"nivel": "tipografia", "titulo": "Línea demasiado larga (12 pt)", "mensaje": "Overfull \\hbox (12.0pt too wide)", "causa": "",
         "accion": "", "detalle": "", "ubicacion": "articulo.tex", "linea": 31}])
    plan = pasos.Plan("muestra", "Crear carpetas en lote", "~/muestra", "Crear 3 carpetas; las que ya existen se omiten.",
                      afectados=[{"ruta": f"~/muestra/{n}", "accion": "crear", "detalle": ""} for n in ("2026", "2027", "2028")],
                      conflictos=[{"ruta": "~/muestra/2025", "motivo": "ya existe: se omite"}])
    app.exponer("diferenciaMuestra", diferencia)
    app.exponer("planMuestra", plan.como_dict())
    app.exponer("cuentasMuestra", pasos.cuentas(plan, {"hechos": 3}, None))
    app.exponer("lineaMuestra", pasos.fijar(pasos.fijar(pasos.linea([
        ("cerrada", "Calibre cerrado", "no puede estar abierto mientras se escribe"),
        ("respaldo", "Respaldo verificado", "copia de la base con quick_check = ok"),
        ("aplicar", "Aplicar los cambios", "la suite escribe por calibredb"),
        ("integridad", "Integridad verificada", "PRAGMA integrity_check")]), "cerrada", "hecho", "cerrado ahora"),
        "respaldo", "en_curso", "copiando metadata.db…"))
    app.exponer("articuloMuestra", str(articulo))
    app.app.aboutToQuit.connect(lambda: (editor.soltar(), visor.apagar()))   # el vigía de inotify, dentro del bucle

    for nombre, objeto in (("acciones", acciones), ("tareas", tareas), ("consola", consola), ("repos", filtrado),
                           ("cambios", cambios), ("historial", historial), ("arbol", arbol), ("diagnosticos", diagnosticos),
                           ("editor", editor), ("visor", visor), ("problemas", problemas)):
        app.exponer(nombre, objeto)
    app._vivos = (acciones, acciones_libre, tareas, consola, tabla, filtrado, cambios, historial, arbol, diagnosticos,
                  editor, visor, problemas)    # que no los recoja el GC
    return acciones


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="gui_comun.galeria", description="Galería de componentes de GuiComun")
    parser.add_argument("--captura", metavar="PNG", help="guarda una captura de la ventana y sale")
    parser.add_argument("--esquema", metavar="COLORS", help="archivo .colors de KDE con el que verla (relanza el proceso)")
    parser.add_argument("--pagina", default="", help="página inicial de la galería (nombre de la navegación)")
    parser.add_argument("--ventana-libre", action="store_true", help="abre también la ventana libre (VentanaBase, 3.0)")
    parser.add_argument("--smoke", action="store_true", help="abre y cierra")
    args = parser.parse_args(argv)

    if args.esquema:
        from gui_comun.galeria.esquema import entorno_con_esquema
        env = entorno_con_esquema(Path(args.esquema).expanduser())
        orden = [sys.executable, "-m", "gui_comun.galeria"] + [a for a in argv if not a.startswith("--esquema") and a != args.esquema]
        return subprocess.run(orden, env=env).returncode

    from gui_comun.nucleo import Aplicacion
    app = Aplicacion("gui-comun-galeria", "Galería de GuiComun", version=__version__)
    construir(app)
    app.exponer("paginaInicial", args.pagina)
    app.exponer("abrirVentanaLibre", args.ventana_libre)
    if args.captura:
        app.capturar(args.captura, espera_ms=1800)
    return app.ejecutar(QML, humo=args.smoke)
