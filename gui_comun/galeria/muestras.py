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


def pdf(ruta: Path, paginas: int = 2) -> Path:
    """Un PDF mínimo válido (páginas A4 con una línea de texto), escrito a mano con su tabla xref."""
    objetos = ["<< /Type /Catalog /Pages 2 0 R >>",
               "<< /Type /Pages /Kids [" + " ".join(f"{3 + 2 * i} 0 R" for i in range(paginas)) + f"] /Count {paginas} >>"]
    fuente = 3 + 2 * paginas
    for i in range(paginas):
        flujo = f"BT /F1 24 Tf 72 720 Td (Pagina {i + 1} de {paginas}) Tj ET"
        objetos.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents {4 + 2 * i} 0 R "
                       f"/Resources << /Font << /F1 {fuente} 0 R >> >> >>")
        objetos.append(f"<< /Length {len(flujo)} >>\nstream\n{flujo}\nendstream")
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
