"""gui_comun/markdown_html.py (4.2) — un documento Markdown como HTML de texto enriquecido de Qt con el aspecto del tema:
títulos con aire, tablas de filas tenues con la cabecera tenue y las cifras a la derecha, código sobre un fondo
alterno. Los colores no son de aquí: llegan de QML (`Kirigami.Theme`) en `tema`; sin ellos, el texto va sin color.
Lo usa `VistaTexto` en Markdown por `aplicacionStudio.markdownHtml` (el MarkdownText de Qt pinta tablas con rejilla
negra, títulos pegados y se traga los «<nombre>»). Nació en Filesystem Studio (`fs_app/services/informe_html.py`).

Cubre títulos `#`…`######`, párrafos, listas `-`/`*`/`1.`, tablas con su fila de alineación, bloques ``` y en línea
`código`, **negrita**, *cursiva*, enlaces `[texto](url)` y `---`; lo demás pasa como texto. Todo el texto se escapa:
un `<nombre>` no se toma por etiqueta.
"""

from __future__ import annotations

import html
import re

_TITULO = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_LISTA = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")
_SEPARADOR_TABLA = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
_TAMANOS = {1: "x-large", 2: "large", 3: "medium", 4: "medium", 5: "small", 6: "small"}


def _color(tema: dict, clave: str) -> str:
    valor = str((tema or {}).get(clave) or "")
    return valor if re.fullmatch(r"#[0-9a-fA-F]{6}([0-9a-fA-F]{2})?|[a-z]+", valor) else ""


def _en_linea(texto: str, tema: dict) -> str:
    """Lo de dentro de una línea: código, negrita, cursiva y enlaces, con el resto escapado."""
    fondo_codigo = _color(tema, "fondoCodigo")
    partes = re.split(r"(`[^`]+`)", texto)
    salida = []
    for parte in partes:
        if len(parte) > 1 and parte.startswith("`") and parte.endswith("`"):
            estilo = "font-family: monospace;" + (f" background-color: {fondo_codigo};" if fondo_codigo else "")
            salida.append(f'<span style="{estilo}">{html.escape(parte[1:-1])}</span>')
            continue
        t = html.escape(parte, quote=False)
        enlace = _color(tema, "enlace")
        # 4.2: lo citado entre comillas, en cursiva (antes de insertar etiquetas, que llevan comillas en sus atributos)
        t = re.sub(r"«([^«»]{1,400})»", r"«<i>\1</i>»", t)
        t = re.sub(r'"([^"]{2,400})"', r"“<i>\1</i>”", t)
        # los rótulos en mayúsculas («PROPÓSITO:», «ORDEN DE LECTURA:»): pequeños, en negrita y del color de los enlaces
        t = re.sub(r"(?<![\w])([A-ZÁÉÍÓÚÑ]{3,}(?: [A-ZÁÉÍÓÚÑ]{2,}){0,4}):",
                   lambda m: f'<span style="{("color: " + enlace + "; ") if enlace else ""}font-size: small; font-weight: 600;">{m.group(1)}</span>', t)
        # las referencias a un lugar del texto («[hoja 1 ¶1]», «[p. 45]»): marcas pequeñas del color de los enlaces
        t = re.sub(r"\[((?:hoja|hojas|p\.|pp\.|pág\.|párr\.|¶)[^\[\]]{0,40})\](?!\()",
                   lambda m: f'<span style="{("color: " + enlace + "; ") if enlace else ""}font-size: small;">[{m.group(1)}]</span>', t)
        enlace = _color(tema, "enlace")
        t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)",
                   lambda m: f'<a href="{html.escape(m.group(2))}"' + (f' style="color: {enlace};"' if enlace else "") + f">{m.group(1)}</a>", t)
        t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
        t = re.sub(r"(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?![*\w])", r"<i>\1</i>", t)
        salida.append(t)
    return "".join(salida)


def _celdas(linea: str) -> list[str]:
    linea = linea.strip()
    if linea.startswith("|"):
        linea = linea[1:]
    if linea.endswith("|"):
        linea = linea[:-1]
    return [c.strip() for c in linea.split("|")]


def _tabla(filas: list[str], tema: dict) -> str:
    """4.2: una tabla moderna: sin rejilla ni bloques de fondo; la cabecera en letra pequeña, tenue y en negrita con una
    raya fina debajo, cada fila separada por una raya más tenue y aire en cada celda; la alineación de la fila de guiones
    (las cifras a la derecha)."""
    cabecera, alineacion, cuerpo = _celdas(filas[0]), _celdas(filas[1]), [_celdas(f) for f in filas[2:]]
    lados = ["right" if a.endswith(":") and not a.startswith(":") else "center" if a.startswith(":") and a.endswith(":") else "left"
             for a in alineacion]
    borde, tenue = _color(tema, "borde"), _color(tema, "tenue")
    fondo_cabecera = _color(tema, "fondoCabecera") or borde
    n = max(len(cabecera), 1)
    raya = lambda color: (f'<tr><td colspan="{n}" style="padding: 0px;"><hr style="margin: 0px;'
                          + (f' background-color: {color};' if color else "") + '" /></td></tr>')
    partes = ['<table border="0" cellspacing="0" cellpadding="7" width="100%" style="margin-top: 8px; margin-bottom: 14px;">']
    color_cabecera = f"color: {tenue}; " if tenue else ""
    partes.append("<tr>" + "".join(f'<td align="{lados[i] if i < len(lados) else "left"}"><span style="{color_cabecera}font-size: small; '
                                   f'font-weight: 600;">{_en_linea(c, tema)}</span></td>' for i, c in enumerate(cabecera)) + "</tr>")
    partes.append(raya(borde))
    for k, fila in enumerate(cuerpo):
        partes.append("<tr>" + "".join(f'<td valign="top" align="{lados[i] if i < len(lados) else "left"}">{_en_linea(c, tema)}</td>'
                                       for i, c in enumerate(fila)) + "</tr>")
        if k < len(cuerpo) - 1:
            partes.append(raya(fondo_cabecera))
    partes.append("</table>")
    return "".join(partes)


def html_de_markdown(texto: str, tema: dict | None = None) -> str:
    """El Markdown de un informe como HTML de texto enriquecido de Qt, con los colores de `tema`:
    {texto, tenue, borde, fondoCabecera, fondoCodigo, enlace} (colores «#rrggbb»; los que falten no se ponen)."""
    tema = tema or {}
    lineas = (texto or "").replace("\r\n", "\n").split("\n")
    color_texto, tenue, fondo_codigo, borde = (_color(tema, c) for c in ("texto", "tenue", "fondoCodigo", "borde"))
    bloques: list[str] = []
    parrafo: list[str] = []
    lista: list[tuple[str, str]] = []          # (tipo ul|ol, html del elemento)
    primero = True

    def cerrar_parrafo():
        # 4.2: un párrafo que es solo negrita («**Su versión**») es un título de hecho: se pinta como tal
        solo = re.fullmatch(r"\*\*([^*]{1,120})\*\*\s*(\([^)]{0,80}\))?:?", " ".join(parrafo).strip()) if parrafo else None
        if solo:
            color = f" color: {color_texto};" if color_texto else ""
            nota = f' <span style="font-weight: normal; font-size: small;">{html.escape(solo.group(2))}</span>' if solo.group(2) else ""
            bloques.append(f'<h4 style="margin-top: 16px; margin-bottom: 4px; font-size: medium; font-weight: 600;{color}">'
                           f'{html.escape(solo.group(1))}{nota}</h4>')
            parrafo.clear()
            return
        if parrafo:
            bloques.append(f'<p style="margin-top: 4px; margin-bottom: 8px; line-height: 135%;">{_en_linea(" ".join(parrafo), tema)}</p>')
            parrafo.clear()

    def cerrar_lista():
        if lista:
            tipo = lista[0][0]
            elementos = "".join(f'<li style="margin-bottom: 3px; line-height: 130%;">{e}</li>' for _, e in lista)
            bloques.append(f'<{tipo} style="margin-top: 2px; margin-bottom: 10px;">{elementos}</{tipo}>')
            lista.clear()

    i = 0
    while i < len(lineas):
        linea = lineas[i]
        if linea.strip().startswith("```"):
            cerrar_parrafo(); cerrar_lista()
            codigo = []
            i += 1
            while i < len(lineas) and not lineas[i].strip().startswith("```"):
                codigo.append(lineas[i])
                i += 1
            fondo = f' bgcolor="{fondo_codigo}"' if fondo_codigo else ""
            bloques.append(f'<table width="100%" cellspacing="0" cellpadding="8" style="margin-top: 4px; margin-bottom: 10px;"><tr><td{fondo}>'
                           f'<pre style="margin: 0px; font-family: monospace;">{html.escape(chr(10).join(codigo))}</pre></td></tr></table>')
            i += 1
            continue
        if "|" in linea and i + 1 < len(lineas) and _SEPARADOR_TABLA.match(lineas[i + 1]):
            cerrar_parrafo(); cerrar_lista()
            filas = [linea, lineas[i + 1]]
            i += 2
            while i < len(lineas) and "|" in lineas[i] and lineas[i].strip():
                filas.append(lineas[i])
                i += 1
            bloques.append(_tabla(filas, tema))
            bloques.append('<p style="margin: 0px; font-size: 4px;">&nbsp;</p>')
            continue
        m = _TITULO.match(linea)
        if m:
            cerrar_parrafo(); cerrar_lista()
            nivel = len(m.group(1))
            arriba = 0 if primero else (22 if nivel <= 2 else 14)
            color = f" color: {color_texto};" if color_texto else ""
            bloques.append(f'<h{nivel} style="margin-top: {arriba}px; margin-bottom: {10 if nivel == 1 else 6}px; '
                           f'font-size: {_TAMANOS[nivel]}; font-weight: 600;{color}">{_en_linea(m.group(2), tema)}</h{nivel}>')
            if nivel == 1 and borde:
                bloques.append(f'<hr style="background-color: {borde}; margin-bottom: 8px;" />')
            primero = False
            i += 1
            continue
        if re.fullmatch(r"\s*(-{3,}|\*{3,}|_{3,})\s*", linea):
            cerrar_parrafo(); cerrar_lista()
            bloques.append(f'<hr{f" style={chr(34)}background-color: {borde};{chr(34)}" if borde else ""} />')
            i += 1
            continue
        m = _LISTA.match(linea)
        if m:
            cerrar_parrafo()
            tipo = "ol" if m.group(2)[0].isdigit() else "ul"
            if lista and lista[0][0] != tipo:
                cerrar_lista()
            lista.append((tipo, _en_linea(m.group(3), tema)))
            primero = False
            i += 1
            continue
        if not linea.strip():
            cerrar_parrafo(); cerrar_lista()
            i += 1
            continue
        if lista and linea.startswith(("  ", "\t")):
            tipo, elemento = lista[-1]
            lista[-1] = (tipo, elemento + " " + _en_linea(linea.strip(), tema))
            i += 1
            continue
        cerrar_lista()
        parrafo.append(linea.strip())
        primero = False
        i += 1
    cerrar_parrafo(); cerrar_lista()
    cuerpo = "".join(bloques)
    color = f' style="color: {color_texto};"' if color_texto else ""
    return f"<html><body{color}>{cuerpo}</body></html>"
