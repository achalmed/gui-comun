"""test_comunes_31.py — lo que 3.1 promovió de los studios a la base: diferencias, editor, visor PDF, miniaturas,
pasos, paleta, el orden del árbol y el tema de Kvantum a juego en `entorno_con_esquema`.

Todo sobre datos de muestra en carpetas temporales: un repositorio de git propio, un PDF escrito aquí, imágenes
generadas. Ninguna ruta de la máquina.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from conftest import requiere_binding

from gui_comun import diferencias, pasos, paleta


# ------------------------------------------------------------------------------------------------ utilidades
def _pdf(ruta: Path, paginas: int = 2) -> Path:
    """Un PDF mínimo válido (el de la galería)."""
    from gui_comun.galeria.muestras import pdf
    return pdf(ruta, paginas)


def _git(cwd: Path, *args: str, entrada: str | None = None) -> str:
    env = dict(os.environ, GIT_AUTHOR_NAME="Prueba", GIT_AUTHOR_EMAIL="p@ejemplo.invalid", GIT_COMMITTER_NAME="Prueba",
               GIT_COMMITTER_EMAIL="p@ejemplo.invalid", GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_SYSTEM="/dev/null")
    r = subprocess.run(["git", *args], cwd=cwd, input=entrada, capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stderr
    return r.stdout


# ------------------------------------------------------------------------------------------------ diferencias
TEXTO_A = "uno\ndos\ntres\ncuatro\ncinco\nseis\nsiete\nocho\nnueve\ndiez\n"
TEXTO_B = "uno\nDOS\ntres\ncuatro\ncinco\nseis\nsiete\nocho\nnueve\ndiez\nonce\n"


def test_comparar_dos_textos_lado_a_lado():
    d = diferencias.comparar(TEXTO_A, TEXTO_B, ruta="a.txt", izquierda="Instalado", derecha="Generado")
    assert d["izquierda"] == "Instalado" and d["derecha"] == "Generado" and d["ruta"] == "a.txt"
    assert d["anadidas"] == 2 and d["quitadas"] == 1 and not d["vacia"]
    cambio = next(f for f in d["filas"] if f["tipo"] == "cambio")
    assert (cambio["izq"], cambio["der"], cambio["izqNum"], cambio["derNum"]) == ("dos", "DOS", 2, 2)
    assert diferencias.comparar("igual\n", "igual\n")["vacia"]


def test_parche_de_lineas_prepara_solo_lo_elegido(tmp_path):
    """Con git de verdad: de dos cambios en un trozo se prepara uno; el índice queda con ese y nada más."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    (repo / "a.txt").write_text("uno\ndos\ntres\n", encoding="utf-8")
    _git(repo, "add", "a.txt")
    _git(repo, "commit", "-qm", "inicio")
    (repo / "a.txt").write_text("uno\nDOS\ntres\ncuatro\n", encoding="utf-8")
    d = diferencias.analizar(_git(repo, "diff", "--", "a.txt"))
    fila_cuatro = next(i for i, f in enumerate(d["filas"]) if f["der"] == "cuatro")
    parche = diferencias.parche_de_lineas(d, {fila_cuatro})
    _git(repo, "apply", "--cached", "--recount", "-", entrada=parche)
    assert _git(repo, "show", ":a.txt") == "uno\ndos\ntres\ncuatro\n"
    # y al revés: quitar del índice la línea preparada
    d2 = diferencias.analizar(_git(repo, "diff", "--cached", "--", "a.txt"))
    fila = next(i for i, f in enumerate(d2["filas"]) if f["der"] == "cuatro")
    _git(repo, "apply", "--cached", "--recount", "-R", "-", entrada=diferencias.parche_de_lineas(d2, {fila}, inverso=True))
    assert _git(repo, "show", ":a.txt") == "uno\ndos\ntres\n"
    assert diferencias.parche_de_lineas(d, set()) == ""


def test_parche_de_lineas_quitada_suelta(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    (repo / "a.txt").write_text("a\nb\nc\nd\n", encoding="utf-8")
    _git(repo, "add", "a.txt")
    _git(repo, "commit", "-qm", "inicio")
    (repo / "a.txt").write_text("a\nd\n", encoding="utf-8")            # quitadas b y c
    d = diferencias.analizar(_git(repo, "diff"))
    fila_c = next(i for i, f in enumerate(d["filas"]) if f["izq"] == "c")
    _git(repo, "apply", "--cached", "--recount", "-", entrada=diferencias.parche_de_lineas(d, [fila_c]))
    assert _git(repo, "show", ":a.txt") == "a\nb\nd\n"


# ------------------------------------------------------------------------------------------------ editor
def test_editor_buscar_y_reemplazar_en_utf16():
    from gui_comun import editor
    texto = "α 😀 beta beta"
    # el emoji ocupa dos unidades UTF-16: «beta» empieza en 5 para QML (en 4 para Python)
    assert editor.buscar(texto, "beta") == [[5, 9], [10, 14]]
    assert editor.reemplazos(texto, r"b(e)ta", r"\1", regex=True) == [[10, 14, "e"], [5, 9, "e"]]
    assert editor.reemplazos(texto, "beta", "B", solo_desde=6) == [[10, 14, "B"]]
    assert editor.definicion_de("x/tesis.tex") == "LaTeX" and editor.definicion_de("latexmkrc") == "Perl"
    assert editor.definicion_de("a.qmd", {".qmd": "Markdown"}) == "Markdown" and editor.definicion_de("a.tex", {}) == ""


@requiere_binding
def test_controlador_editor_guarda_sin_pisar_un_cambio_externo(app, tmp_path):
    from gui_comun.editor import ControladorEditor
    ruta = tmp_path / "a.md"
    ruta.write_bytes(b"uno\r\ndos\r\n")
    ed = ControladorEditor(definicion=lambda r: "Markdown")
    assert ed.abrir(str(ruta)) == 0 and ed.actual == str(ruta)
    assert ed.abiertos.fila(0)["definicion"] == "Markdown"
    assert ed.leer(str(ruta)) == "uno\ndos\n"                    # los CRLF se recuerdan…
    assert ed.guardar(str(ruta), "uno\ntres\n", False) == ""
    assert ruta.read_bytes() == b"uno\r\ntres\r\n"               # …y se conservan al guardar
    os.utime(ruta, ns=(1, 1))                                    # alguien lo cambió fuera
    assert ed.cambioEnDisco(str(ruta)) and ed.guardar(str(ruta), "x\n", False) == "externo"
    assert ed.guardar(str(ruta), "x\n", True) == ""
    nueva = tmp_path / "b.md"
    assert ed.guardarComo(str(ruta), str(nueva), "copia\n") == "" and ed.actual == str(nueva)
    assert ruta.read_bytes() == b"x\r\n" and nueva.read_bytes() == b"copia\r\n"
    assert ed.buscar("abc", "(", True, False, False)["error"].startswith("Expresión regular no válida")
    ed.soltar()


# ------------------------------------------------------------------------------------------------ visor PDF
@pytest.mark.skipif(not shutil.which("pdftoppm"), reason="sin poppler")
def test_visor_pdf_tamanos_render_y_poda(tmp_path):
    from gui_comun import visor_pdf as vp
    pdf = _pdf(tmp_path / "doc.pdf", 3)
    assert vp.paginas(pdf) == [(595.0, 842.0)] * 3
    cache = tmp_path / "cache"
    png = vp.renderizar(pdf, 2, 36, cache)
    assert png and png.is_file() and png.read_bytes()[:4] == b"\x89PNG"
    assert vp.renderizar(pdf, 2, 36, cache) == png                       # de la caché
    otro = _pdf(tmp_path / "otro.pdf", 1)
    vp.renderizar(otro, 1, 36, cache)
    os.utime(png, (1, 1))                                                # el de doc.pdf, el más viejo
    liberado = vp.podar(cache, limite=1, conservar=vp.clave(otro))
    assert liberado > 0 and not png.exists() and vp.tamano_cache(cache) > 0


@requiere_binding
@pytest.mark.skipif(not shutil.which("pdftoppm"), reason="sin poppler")
def test_controlador_visor_abre_marca_y_recarga(app, tmp_path, monkeypatch):
    from gui_comun.visor_pdf import VisorPdf
    monkeypatch.setenv("GUI_COMUN_VISOR", "pdftoppm")
    pdf = _pdf(tmp_path / "doc.pdf", 2)
    v = VisorPdf(cache=tmp_path / "cache")
    assert v.motor == "pdftoppm"
    v.abrir(str(pdf))
    assert v.total == 2 and v.anchoMaximo == 595.0 and v.pdfUrl.startswith("file://")
    marcas = []
    v.marcar.connect(lambda *a: marcas.append(a))
    v.marcarRecuadro(2, 10, 20, 30, 40)
    v.marcarRecuadro(9, 0, 0, 0, 0)                                      # fuera del PDF: nada
    assert marcas == [(2, 10.0, 20.0, 30.0, 40.0)]
    assert v.renderizar_ya(1, 36).endswith(".png") and v.paginas.fila(0)["imagen"].startswith("file://")
    revision = v.revision
    v.recargar()
    assert v.revision == revision + 1
    v.ajustarA(595.0 * 1.5)
    assert abs(v.zoom - 1.5) < 1e-6
    v.cerrar()
    assert v.total == 0
    v.apagar()


# ------------------------------------------------------------------------------------------------ miniaturas
@requiere_binding
def test_miniaturas_escalan_al_leer_cachean_y_podan(app, tmp_path):
    from gui_comun.miniaturas import ProveedorMiniaturas, miniatura, podar
    from gui_comun.qt import QImage, QSize
    origen = tmp_path / "cover.png"
    img = QImage(800, 1200, QImage.Format.Format_RGB32)
    img.fill(0x336699)
    assert img.save(str(origen))
    antes = origen.read_bytes()
    cache = tmp_path / "cache"
    m = miniatura(origen, cache, "42", 200)
    assert (m.width(), m.height()) == (200, 300)
    assert len(list(cache.glob("42-200-*.jpg"))) == 1 and origen.read_bytes() == antes     # el origen, intacto
    p = ProveedorMiniaturas(cache, anchos={"": 100, "grande": 400})
    p.fijar_rutas({"42": str(origen)})
    tam = QSize()
    assert p.requestImage("42/grande", tam, QSize()).width() == 400 and tam.width() == 400
    assert p.requestImage("sin-ruta", None, QSize()).isNull()
    assert podar(cache, 0) == 2 and not list(cache.glob("*.jpg"))
    por_ruta = ProveedorMiniaturas(cache, claves_son_rutas=True)
    assert por_ruta.requestImage(str(origen).lstrip("/") + "@grande", None, QSize()).width() == 520


# ------------------------------------------------------------------------------------------------ pasos y paleta
def test_plan_en_seis_pasos_verificacion_e_informe():
    plan = pasos.Plan("carpetas", "Crear carpetas", "/tmp/x", "Crear 2 carpetas.",
                      afectados=[{"ruta": "/tmp/x/a", "accion": "crear", "detalle": ""}],
                      conflictos=[{"ruta": "/tmp/x/b", "motivo": "ya existe: se omite"}])
    assert not plan.bloqueado and plan.como_dict()["nAfectados"] == 1
    plan.conflictos.append({"ruta": "/tmp/x/c", "motivo": "ajeno", "bloquea": True})
    assert plan.bloqueado
    v = pasos.verificacion([{"ruta": "/tmp/x/a", "ok": True, "detalle": "existe"}, {"ruta": "/tmp/x/z", "ok": False, "detalle": "no existe"}])
    assert v[0] is False and v[1] == "1 de 2 no quedaron como se esperaba"
    texto = pasos.informe(plan, {"hechos": 1, "errores": 0, "detalle": "1 creada"}, v, herramienta="Prueba", fecha="2026-11-03 10:00:00")
    for trozo in ("# Crear carpetas", "## 3. Conflictos", "(bloquea)", "**NO superada**", "✗ `/tmp/x/z`", "## 6. Informe"):
        assert trozo in texto
    assert pasos.cuentas(plan, {"hechos": 1}, v) == ["", "1", "2", "1 hechos", "✗", ""]
    linea = pasos.linea([("a", "Uno", "el primero"), ("b", "Dos", "el segundo")])
    pasos.fijar(linea, "b", "fallo", "se cayó")
    assert linea[1]["nivel"] == "negativo" and linea[1]["detalle"] == "se cayó" and linea[0]["estado"] == "pendiente"
    with pytest.raises(ValueError):
        pasos.fijar(linea, "a", "raro")


def test_paleta_lleva_cada_color_a_su_rol():
    assert paleta.roles(["red", "C0", "#2ca02c", "tab:orange", "k", "lightgray", "purple", "tab:cyan"]) == \
        ["rojo", "azul", "verde", "dorado", "texto", "gris", "morado", "cian"]
    assert paleta.rol("no-es-un-color", 1) == "rojo"                 # sin color: uno por orden


# ------------------------------------------------------------------------------------------------ modelos y esquema
@requiere_binding
def test_arbol_ordenable_por_cabecera_con_grupos_y_perezosos(app):
    from gui_comun.modelos import ModeloArbol
    m = ModeloArbol(("Nombre", "Tamaño"), [
        {"valores": ["b.txt", "2 KB"], "orden": ["b.txt", 2048], "grupo": 1},
        {"valores": ["a.txt", "10 B"], "orden": ["a.txt", 10], "grupo": 1},
        {"valores": ["sub", ""], "orden": ["sub", None], "grupo": 0,
         "hijos": lambda _d: [{"valores": ["z", "1 B"], "orden": ["z", 1]}, {"valores": ["y", "9 B"], "orden": ["y", 9]}]},
    ])
    nombres = lambda padre=None: [m.data(m.index(i, 0, padre) if padre else m.index(i, 0)) for i in range(m.rowCount(padre) if padre else m.rowCount())]
    m.ordenar(1, True)
    assert nombres() == ["sub", "b.txt", "a.txt"] and m.columnaOrden == 1 and m.descendente
    assert nombres(m.index(0, 0)) == ["y", "z"]                        # el perezoso, ordenado al cargarse
    m.ordenar(0, False)
    assert nombres() == ["sub", "a.txt", "b.txt"] and nombres(m.index(0, 0)) == ["y", "z"]
    m.ordenar(0, True)
    assert nombres(m.index(0, 0)) == ["z", "y"]


@requiere_binding
def test_modelo_lista_todas_es_un_slot(app):
    from gui_comun.modelos import ModeloLista
    m = ModeloLista(("a",), [{"a": 1}, {"a": 2}])
    meta = m.metaObject()
    assert any(meta.method(i).name().data() == b"todas" for i in range(meta.methodCount()))
    assert m.todas() == [{"a": 1}, {"a": 2}]


def test_esquema_pone_kvantum_a_juego(tmp_path, monkeypatch):
    from gui_comun.galeria.esquema import entorno_con_esquema
    config = tmp_path / "config"
    (config / "Kvantum" / "LliphiOscuro").mkdir(parents=True)
    (config / "Kvantum" / "kvantum.kvconfig").write_text("[General]\ntheme=LliphiClaro\n", encoding="utf-8")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config))
    colors = tmp_path / "LliphiOscuro.colors"
    colors.write_text("[General]\nName=Lliphi Oscuro\n[Colors:View]\nBackgroundNormal=10,10,10\n", encoding="utf-8")
    env = entorno_con_esquema(colors, tmp_path / "salida")
    assert env["XDG_CONFIG_HOME"] == str(tmp_path / "salida")
    assert "theme=LliphiOscuro" in (tmp_path / "salida" / "Kvantum" / "kvantum.kvconfig").read_text(encoding="utf-8")
    assert "theme=LliphiClaro" in (config / "Kvantum" / "kvantum.kvconfig").read_text(encoding="utf-8")   # el del usuario, intacto
    claro = tmp_path / "Otro.colors"
    claro.write_text("[General]\nName=Otro\n", encoding="utf-8")
    entorno_con_esquema(claro, tmp_path / "salida2")                   # sin tema de Kvantum con ese nombre: el del usuario
    assert "theme=LliphiClaro" in (tmp_path / "salida2" / "Kvantum" / "kvantum.kvconfig").read_text(encoding="utf-8")
