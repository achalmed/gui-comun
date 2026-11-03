"""gui_comun/galeria/muestras.py — datos de muestra de la galería que también usan las pruebas (sin Qt): un PDF
mínimo escrito a mano y un archivo de LaTeX para el editor. Nada de la máquina: todo inventado."""

from __future__ import annotations

from pathlib import Path

TEX = r"""\documentclass{article}
% Un artículo de muestra para el editor de la galería
\usepackage{amsmath}
\begin{document}
\section{Introducción}
El modelo IS-LM resume el equilibrio del mercado de bienes y del de dinero.
\begin{equation}
  Y = C(Y - T) + I(r) + G
\end{equation}
Véase la ecuación~\ref{eq:islm} y \cite{hicks1937}.
\end{document}
"""


def pdf(ruta: Path, paginas: int = 2, enlaces: bool = True) -> Path:
    """Un PDF mínimo válido (páginas A4 con texto), escrito a mano con su tabla xref. Con `enlaces`, la primera página
    lleva un enlace interno a la segunda y uno externo (para la selección, los enlaces y la búsqueda de VistaPdf)."""
    pagina_obj = lambda i: 3 + 3 * i                     # cada página: objeto de página, contenido y anotaciones
    fuente = 3 + 3 * paginas
    objetos = ["<< /Type /Catalog /Pages 2 0 R >>",
               "<< /Type /Pages /Kids [" + " ".join(f"{pagina_obj(i)} 0 R" for i in range(paginas)) + f"] /Count {paginas} >>"]
    for i in range(paginas):
        lineas = [f"BT /F1 24 Tf 72 720 Td (Pagina {i + 1} de {paginas}) Tj ET",
                  "BT /F1 12 Tf 72 690 Td (Una muestra con la palabra cometa para buscar.) Tj ET"]
        anotaciones = []
        if enlaces and i == 0 and paginas > 1:
            lineas += ["BT /F1 12 Tf 72 660 Td (Ir a la pagina 2) Tj ET", "BT /F1 12 Tf 72 640 Td (https://example.org) Tj ET"]
            anotaciones = [f"<< /Type /Annot /Subtype /Link /Rect [70 655 175 672] /Border [0 0 0] /Dest [{pagina_obj(1)} 0 R /XYZ 0 842 0] >>",
                           "<< /Type /Annot /Subtype /Link /Rect [70 635 190 652] /Border [0 0 0] /A << /S /URI /URI (https://example.org) >> >>"]
        flujo = "\n".join(lineas)
        objetos.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents {pagina_obj(i) + 1} 0 R "
                       f"/Annots {pagina_obj(i) + 2} 0 R /Resources << /Font << /F1 {fuente} 0 R >> >> >>")
        objetos.append(f"<< /Length {len(flujo)} >>\nstream\n{flujo}\nendstream")
        objetos.append("[" + " ".join(anotaciones) + "]")
    objetos.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    salida = b"%PDF-1.4\n"
    desplazamientos = []
    for n, cuerpo in enumerate(objetos, 1):
        desplazamientos.append(len(salida))
        salida += f"{n} 0 obj\n{cuerpo}\nendobj\n".encode("latin-1")
    xref = len(salida)
    salida += f"xref\n0 {len(objetos) + 1}\n0000000000 65535 f \n".encode()
    salida += "".join(f"{d:010d} 00000 n \n" for d in desplazamientos).encode()
    salida += f"trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    ruta.write_bytes(salida)
    return ruta
