"""gui_comun/rutas.py — dónde está cada cosa para los studios: la raíz del espacio de trabajo y sus rutas.

Dentro del espacio de trabajo las rutas salen de `core/env.py`, que se encuentra subiendo carpetas desde este paquete
(el repo `gui-comun` vive junto a `core/`) o desde la carpeta actual. Fuera de él (gui-comun instalado con pip, sin
`core/`), `docs_root()` usa `DOCS_ROOT` o `~/Documents`, y pedir otra variable es un error claro.
Toda variable respeta un valor previo del entorno (lo hace core/env.py).
"""

from __future__ import annotations

import importlib.util
import os
from functools import lru_cache
from pathlib import Path


def _buscar_core() -> Path | None:
    for base in (Path(__file__).resolve(), Path.cwd().resolve()):
        for carpeta in (base, *base.parents):
            if (carpeta / "core" / "env.py").is_file():
                return carpeta / "core"
    raiz = os.environ.get("DOCS_ROOT")
    if raiz and (Path(raiz) / "core" / "env.py").is_file():
        return Path(raiz) / "core"
    return None


CORE_DIR = _buscar_core()      # None fuera del espacio de trabajo


@lru_cache(maxsize=1)
def core_env():
    """El módulo core/env.py del espacio de trabajo, cargado por su ruta (no depende de sys.path)."""
    if CORE_DIR is None:
        raise RuntimeError("gui_comun.rutas: no hay core/env.py (fuera del espacio de trabajo); exporta DOCS_ROOT")
    spec = importlib.util.spec_from_file_location("core_env", CORE_DIR / "env.py")
    env = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(env)
    return env


def variable(nombre: str) -> Path:
    """Una ruta de core/env (DOCS_ROOT, INDEX_DIR, CORE_DIR…)."""
    return Path(getattr(core_env(), nombre))


def docs_root() -> Path:
    try:
        return variable("DOCS_ROOT")
    except RuntimeError:
        return Path(os.environ.get("DOCS_ROOT") or Path.home() / "Documents").expanduser()
