"""gui_comun/galeria/esquema.py — correr una ventana con otro esquema de color de KDE sin tocar el escritorio.

Un archivo `.colors` de KDE tiene los mismos grupos que `kdeglobals` (`[Colors:View]`, `[Colors:Window]`…). Para
ver un studio en claro cuando el escritorio está en oscuro (las capturas de la documentación), se copia el
`kdeglobals` del usuario a una carpeta temporal, se le reemplazan los grupos de color por los del `.colors`
pedido y se arranca el proceso con `XDG_CONFIG_HOME` apuntando ahí: el resto de la configuración (fuentes, iconos)
se conserva y nada del escritorio cambia.

    env = entorno_con_esquema(Path("LliphiClaro.colors"))
    subprocess.run([...], env=env)
"""

from __future__ import annotations

import configparser
import os
import shutil
import tempfile
from pathlib import Path


def _leer(ruta: Path) -> configparser.RawConfigParser:
    cfg = configparser.RawConfigParser(strict=False, delimiters=("=",), interpolation=None)
    cfg.optionxform = str
    if ruta.is_file():
        cfg.read(ruta, encoding="utf-8")
    return cfg


def kdeglobals_con_esquema(colors: Path, destino: Path, kdeglobals: Path | None = None) -> Path:
    """Escribe en `destino` un kdeglobals = el del usuario (o el dado) con los colores de `colors`."""
    origen = kdeglobals or Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "kdeglobals"
    base = _leer(origen)
    esquema = _leer(colors)
    for seccion in list(base.sections()):
        if seccion.startswith("Colors:") or seccion in ("WM",):
            base.remove_section(seccion)
    for seccion in esquema.sections():
        if seccion.startswith("Colors:") or seccion == "WM":
            base.add_section(seccion)
            for clave, valor in esquema.items(seccion):
                base.set(seccion, clave, valor)
    nombre = esquema.get("General", "Name", fallback=colors.stem)
    if not base.has_section("General"):
        base.add_section("General")
    base.set("General", "ColorScheme", nombre)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", encoding="utf-8") as f:
        base.write(f, space_around_delimiters=False)
    return destino


def entorno_con_esquema(colors: Path, carpeta: Path | None = None) -> dict[str, str]:
    """El entorno de un proceso hijo que verá ese esquema: `XDG_CONFIG_HOME` temporal con el kdeglobals derivado."""
    carpeta = carpeta or Path(tempfile.mkdtemp(prefix="gui-comun-esquema-"))
    config_usuario = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    for nombre in ("kdeglobals", "kcminputrc", "kwinrc", "Kvantum"):      # lo que afecta al aspecto, copiado
        origen = config_usuario / nombre
        if origen.is_dir():
            shutil.copytree(origen, carpeta / nombre, dirs_exist_ok=True)
        elif origen.is_file():
            shutil.copy2(origen, carpeta / nombre)
    kdeglobals_con_esquema(colors, carpeta / "kdeglobals")
    env = dict(os.environ)
    env["XDG_CONFIG_HOME"] = str(carpeta)
    return env
