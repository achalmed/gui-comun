"""gui_comun/diferencias.py — una diferencia unificada convertida en filas lado a lado, por trozos (3.1; sin Qt).

Lo pinta `GuiComun.VistaComparacion`. Viene de Git Studio (`services/diferencias.py`), que Dotfiles y Lliphi copiaron
igual; aquí se añade comparar dos textos (lo instalado y lo generado, el repositorio y HOME) y el parche de unas
líneas sueltas de un trozo (preparar líneas, como `git add -p` con «e»).

    d = analizar(texto_de_git_diff)
    d = comparar("antes\\n", "después\\n", ruta="a.conf", izquierda="Repositorio", derecha="HOME")
    parche = parche_de_trozo(d, 0)                       # para `git apply --cached`
    parche = parche_de_lineas(d, {3, 4})                 # solo esas filas (índices de `filas`)

Cada fila: {tipo: trozo · igual · cambio · quitada · anadida · aviso, trozo, izqNum, izq, izqTipo, derNum, der,
derTipo, izqLinea, derLinea}; `izqLinea`/`derLinea` son la posición de esa línea dentro de `lineas` de su trozo (−1 si
el lado está vacío): lo que necesita `parche_de_lineas`.
"""

from __future__ import annotations

import difflib
import re

_TROZO = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$")
MAX_FILAS = 6000
TIPOS_CAMBIO = ("cambio", "quitada", "anadida")


def analizar(texto: str, max_filas: int = MAX_FILAS) -> dict:
    """La diferencia unificada `texto` (la de `git diff` o `diff -u` de un archivo) como cabecera, trozos y filas."""
    cabecera: list[str] = []
    trozos: list[dict] = []
    filas: list[dict] = []
    binario = False
    actual: dict | None = None
    izq = der = 0
    quitadas: list[tuple[int, str, int]] = []
    anadidas: list[tuple[int, str, int]] = []
    recortado = False

    def volcar():
        """Empareja las quitadas y añadidas pendientes en filas lado a lado."""
        nonlocal quitadas, anadidas
        for k in range(max(len(quitadas), len(anadidas))):
            q = quitadas[k] if k < len(quitadas) else None
            a = anadidas[k] if k < len(anadidas) else None
            filas.append({"tipo": "cambio" if q and a else ("quitada" if q else "anadida"), "trozo": len(trozos) - 1,
                          "izqNum": q[0] if q else 0, "izq": q[1] if q else "", "izqTipo": "quitada" if q else "vacia",
                          "derNum": a[0] if a else 0, "der": a[1] if a else "", "derTipo": "anadida" if a else "vacia",
                          "izqLinea": q[2] if q else -1, "derLinea": a[2] if a else -1})
        quitadas, anadidas = [], []

    for linea in (texto or "").splitlines():
        if actual is None and not linea.startswith("@@"):
            if linea.startswith("Binary files") or linea.startswith("GIT binary patch"):
                binario = True
            cabecera.append(linea)
            continue
        m = _TROZO.match(linea)
        if m:
            volcar()
            izq, der = int(m.group(1)), int(m.group(3))
            actual = {"indice": len(trozos), "cabecera": linea, "lineas": [], "titulo": m.group(5).strip(), "izq": izq, "der": der}
            trozos.append(actual)
            filas.append({"tipo": "trozo", "trozo": actual["indice"], "izqNum": 0, "izq": linea, "izqTipo": "trozo",
                          "derNum": 0, "der": m.group(5).strip(), "derTipo": "trozo", "izqLinea": -1, "derLinea": -1})
            continue
        if actual is None:
            continue
        posicion = len(actual["lineas"])
        actual["lineas"].append(linea)
        if len(filas) >= max_filas:
            recortado = True
            continue
        if linea.startswith("-"):
            quitadas.append((izq, linea[1:], posicion))
            izq += 1
        elif linea.startswith("+"):
            anadidas.append((der, linea[1:], posicion))
            der += 1
        elif linea.startswith("\\"):
            volcar()
            filas.append({"tipo": "aviso", "trozo": actual["indice"], "izqNum": 0, "izq": linea[2:], "izqTipo": "aviso",
                          "derNum": 0, "der": "", "derTipo": "aviso", "izqLinea": -1, "derLinea": -1})
        else:
            volcar()
            contenido = linea[1:] if linea.startswith(" ") else linea
            filas.append({"tipo": "igual", "trozo": actual["indice"], "izqNum": izq, "izq": contenido, "izqTipo": "igual",
                          "derNum": der, "der": contenido, "derTipo": "igual", "izqLinea": posicion, "derLinea": posicion})
            izq += 1
            der += 1
    volcar()
    return {"cabecera": cabecera, "trozos": trozos, "filas": filas, "binario": binario, "recortado": recortado,
            "anadidas": sum(1 for f in filas if f["derTipo"] == "anadida"),
            "quitadas": sum(1 for f in filas if f["izqTipo"] == "quitada"),
            "vacia": not trozos and not binario}


def comparar(antes: str, despues: str, ruta: str = "", izquierda: str = "Antes", derecha: str = "Después",
             contexto: int = 3, max_filas: int = MAX_FILAS) -> dict:
    """Dos textos comparados como `analizar` (con `difflib`, sin git), más lo que pinta la cabecera de la vista:
    `ruta`, y qué es cada lado (`izquierda`, `derecha`)."""
    lineas = difflib.unified_diff((antes or "").splitlines(), (despues or "").splitlines(),
                                  fromfile=f"a/{ruta}", tofile=f"b/{ruta}", n=contexto, lineterm="")
    d = analizar("\n".join(lineas), max_filas)
    d.update(ruta=ruta, izquierda=izquierda, derecha=derecha)
    return d


def _cabecera_parche(diferencia: dict) -> list[str]:
    return [l for l in diferencia["cabecera"] if l.startswith(("diff --git", "--- ", "+++ ", "new file", "deleted file",
                                                                "old mode", "new mode", "index "))]


def parche_de_trozo(diferencia: dict, indice: int) -> str:
    """El parche de un solo trozo (cabecera del archivo + el trozo), listo para `git apply` por la entrada estándar."""
    trozos = diferencia["trozos"]
    if not 0 <= indice < len(trozos):
        return ""
    t = trozos[indice]
    return "\n".join(_cabecera_parche(diferencia) + [t["cabecera"]] + t["lineas"]) + "\n"


def parche_de_lineas(diferencia: dict, filas: set[int] | list[int], inverso: bool = False) -> str:
    """El parche de unas filas sueltas (índices de `diferencia["filas"]`): solo sus líneas quitadas o añadidas; lo
    demás del trozo queda como estaba. Así lo hace `git add -p` al editar un trozo:

    - hacia delante (preparar, `git apply --cached`): una `+` no elegida desaparece y una `-` no elegida pasa a contexto;
    - `inverso` (quitar del índice, `git apply --cached -R`): una `-` no elegida desaparece y una `+` no elegida pasa a
      contexto (el parche se aplica al revés).

    Las cabeceras `@@` se recalculan. Devuelve "" si ninguna fila elegida es un cambio."""
    elegidas: dict[int, set[int]] = {}
    for i in filas:
        if 0 <= i < len(diferencia["filas"]):
            f = diferencia["filas"][i]
            if f["tipo"] in TIPOS_CAMBIO:
                lado = elegidas.setdefault(f["trozo"], set())
                if f["izqTipo"] == "quitada":
                    lado.add(f["izqLinea"])
                if f["derTipo"] == "anadida":
                    lado.add(f["derLinea"])
    salida: list[str] = []
    for indice in sorted(elegidas):
        t = diferencia["trozos"][indice]
        cuerpo, n_izq, n_der = [], 0, 0
        for pos, linea in enumerate(t["lineas"]):
            marca, resto = linea[:1], linea[1:]
            if marca in ("-", "+"):
                if pos in elegidas[indice]:
                    cuerpo.append(linea)
                    n_izq += marca == "-"
                    n_der += marca == "+"
                    continue
                pasa_a_contexto = (marca == "-") != inverso
                if pasa_a_contexto:
                    cuerpo.append(" " + resto)
                    n_izq += 1
                    n_der += 1
                continue
            cuerpo.append(linea)
            if marca != "\\":
                n_izq += 1
                n_der += 1
        if cuerpo:
            salida.append(f"@@ -{t['izq']},{n_izq} +{t['der']},{n_der} @@")   # con varios trozos, `git apply --recount`
            salida.extend(cuerpo)
    if not salida:
        return ""
    return "\n".join(_cabecera_parche(diferencia) + salida) + "\n"
