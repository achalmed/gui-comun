"""gui_comun/lanzador.py — el acceso directo de un studio en el menú de aplicaciones (freedesktop: KDE, GNOME…).

Escribe `~/.local/share/applications/<id>.desktop` y el icono `~/.local/share/icons/hicolor/scalable/apps/<id>.svg`
(la losa del logo con el acento del studio), y avisa al escritorio para que lo muestre sin cerrar sesión. Simula si se
pide: dice qué escribiría y no toca nada. Cada studio lo llama desde su `main.py --instalar-lanzador`, y su
`install.sh` lo hace al instalar.

    from gui_comun import lanzador
    lanzador.instalar("filesystem-studio", "Filesystem Studio", "Árboles, extensiones y hardlinks",
                      [sys.executable, str(MAIN)], logo_svg=SVG, acento="verde", categorias="Utility;FileTools;")
"""

from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess
from pathlib import Path

from gui_comun.acentos import ACENTOS


def _datos() -> Path:
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")


def rutas(app_id: str) -> tuple[Path, Path]:
    """(el .desktop, el icono) de un studio."""
    return (_datos() / "applications" / f"{app_id}.desktop",
            _datos() / "icons" / "hicolor" / "scalable" / "apps" / f"{app_id}.svg")


def icono_svg(logo_svg: str, acento: str) -> str:
    """La losa del logo con el acento (el tono claro, que se lee en paneles claros y oscuros) y el trazo en blanco.

    Sin `<svg>` anidados: el motor SVG de Qt (el de KDE) es SVG Tiny 1.2 y los ignora; el dibujo del logo entra como un
    grupo escalado que hereda los atributos de trazo de su `<svg>` raíz."""
    color = ACENTOS.get(acento, ACENTOS["azul"])["claro"]
    m = re.search(r"<svg\b([^>]*)>(.*)</svg>", logo_svg, re.S)
    atributos, dibujo = (m.group(1), m.group(2)) if m else ("", logo_svg)
    attr = dict(re.findall(r'([\w:-]+)="([^"]*)"', atributos))
    vb = [float(x) for x in attr.get("viewBox", "0 0 24 24").replace(",", " ").split()]
    escala = 36 / max(vb[2], vb[3])
    heredados = " ".join(f'{k}="{v}"' for k, v in attr.items()
                         if k in ("fill", "stroke", "stroke-width", "stroke-linecap", "stroke-linejoin"))
    blanco = lambda t: re.sub(r'(stroke|fill)="(#[0-9a-fA-F]{3,8}|currentColor|black|white)"', r'\1="#ffffff"', t)
    grupo = (f'<g transform="translate({14 - vb[0] * escala:g} {14 - vb[1] * escala:g}) scale({escala:g})" '
             f'{blanco(heredados)}>{blanco(dibujo)}</g>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
            f'<rect x="2" y="2" width="60" height="60" rx="15" fill="{color}"/>{grupo}</svg>')


def entrada(app_id: str, nombre: str, comentario: str, orden: list[str], *, categorias: str = "Utility;",
            palabras: str = "", archivos: bool = False, mimetypes: str = "", esquema: str = "") -> str:
    """`esquema`: un esquema de enlaces propio (`biblioteca-studio://…`) que el escritorio abre con este studio."""
    if esquema:
        mimetypes = f"{mimetypes}x-scheme-handler/{esquema};"
    exec_ = shlex.join(orden) + (" %u" if esquema else " %F" if archivos else "")
    lineas = ["[Desktop Entry]", "Type=Application", f"Name={nombre}", f"Comment={comentario}", f"Exec={exec_}",
              f"Icon={app_id}", "Terminal=false", f"Categories={categorias}", f"StartupWMClass={app_id}",
              f"X-GNOME-WMClass={app_id}"]
    if palabras:
        lineas.append(f"Keywords={palabras}")
    if mimetypes:
        lineas.append(f"MimeType={mimetypes}")
    return "\n".join(lineas) + "\n"


def instalar(app_id: str, nombre: str, comentario: str, orden: list[str], *, logo_svg: str, acento: str,
             categorias: str = "Utility;", palabras: str = "", archivos: bool = False, mimetypes: str = "",
             esquema: str = "", simular: bool = False) -> list[Path]:
    """Escribe el acceso directo y su icono (o, al simular, solo dice cuáles). Devuelve las rutas."""
    desktop, icono = rutas(app_id)
    if simular:
        return [desktop, icono]
    desktop.parent.mkdir(parents=True, exist_ok=True)
    icono.parent.mkdir(parents=True, exist_ok=True)
    icono.write_text(icono_svg(logo_svg, acento), encoding="utf-8")
    desktop.write_text(entrada(app_id, nombre, comentario, orden, categorias=categorias, palabras=palabras,
                               archivos=archivos, mimetypes=mimetypes, esquema=esquema), encoding="utf-8")
    desktop.chmod(0o755)
    if esquema and shutil.which("xdg-mime"):           # que el escritorio abra esos enlaces con este studio
        subprocess.run(["xdg-mime", "default", desktop.name, f"x-scheme-handler/{esquema}"], check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    _avisar_al_escritorio()
    return [desktop, icono]


def quitar(app_id: str, simular: bool = False) -> list[Path]:
    existentes = [p for p in rutas(app_id) if p.exists()]
    if not simular:
        for p in existentes:
            p.unlink()
        _avisar_al_escritorio()
    return existentes


def _avisar_al_escritorio() -> None:
    """Que el menú lo muestre ya (KDE: kbuildsycoca; los demás: la base de .desktop y la caché de iconos)."""
    for orden in (["update-desktop-database", str(_datos() / "applications")],
                  ["gtk-update-icon-cache", "-q", "-t", str(_datos() / "icons" / "hicolor")],
                  ["kbuildsycoca6", "--noincremental"], ["kbuildsycoca5"]):
        if shutil.which(orden[0]):
            subprocess.run(orden, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            if orden[0].startswith("kbuildsycoca"):
                break


def desde_main(argv: list[str], **datos) -> int | None:
    """Para el `main.py` de un studio: atiende `--instalar-lanzador` y `--quitar-lanzador` (con `-n`, simula).

    Devuelve el código de salida si atendió una de ellas, o None si no había ninguna (y el studio abre su ventana)."""
    simular = "-n" in argv or "--simular" in argv
    if "--instalar-lanzador" in argv:
        hechas = instalar(simular=simular, **datos)
        print(("Escribiría" if simular else "Instalado") + ":\n  " + "\n  ".join(str(p) for p in hechas))
        return 0
    if "--quitar-lanzador" in argv:
        hechas = quitar(datos["app_id"], simular=simular)
        print(("Quitaría" if simular else "Quitado") + ":\n  " + ("\n  ".join(str(p) for p in hechas) or "(nada)"))
        return 0
    return None
