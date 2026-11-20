"""test_markdown_html.py (4.2) — el Markdown de VistaTexto como HTML con los colores del tema: títulos, listas, tablas
con su alineación, código y enlaces; todo el texto escapado; sin tema, sin colores (nació en Filesystem Studio)."""

from __future__ import annotations

from gui_comun.markdown_html import html_de_markdown

INFORME = """# Informe de auditoría

- **Fecha:** 2026-11-19
- **Carpeta:** `/tmp/<proyecto>`

## Resumen

| Indicador | Valor |
|---|---:|
| Archivos | 31 |

```
árbol <raíz>
```

Ver [la guía](https://example.org).
"""

TEMA = {"texto": "#111111", "tenue": "#777777", "borde": "#cccccc", "fondoCabecera": "#eeeeee", "fondoCodigo": "#f2f2f2",
        "enlace": "#2255cc"}


def test_estructura_y_colores():
    h = html_de_markdown(INFORME, TEMA)
    assert "<h1" in h and "<h2" in h and "<ul" in h and "<table" in h and "<pre" in h
    assert "<b>Fecha:</b>" in h
    assert 'align="right">31</td>' in h                 # la columna con «---:» va a la derecha
    assert "#cccccc" in h and "#f2f2f2" in h and "#2255cc" in h
    assert '<a href="https://example.org"' in h


def test_todo_se_escapa():
    h = html_de_markdown(INFORME, TEMA)
    assert "<proyecto>" not in h and "&lt;proyecto&gt;" in h
    assert "<raíz>" not in h and "&lt;raíz&gt;" in h


def test_sin_tema_sin_colores_y_un_color_raro_no_entra():
    assert "#" not in html_de_markdown("# Título\n\ntexto", {}).replace("&#", "")
    h = html_de_markdown("# Título", {"texto": "red; background: url(x)"})
    assert "url(" not in h
