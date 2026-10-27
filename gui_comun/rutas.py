"""gui_comun/rutas.py — dónde está cada cosa para los studios: la raíz del workspace y las demás rutas salen de core/env.py.

Los backends de cada studio viven en su mismo repo y cada uno los resuelve desde su raíz (`<paquete>/utils/paths.py`
o `quarto_app/services/paths.py`); aquí queda solo lo que es del workspace: `DOCS_ROOT`, `INDEX_DIR`, `CORE_DIR`…
Toda variable respeta un valor previo del entorno (lo hace core/env.py).
"""

from __future__ import annotations

import importlib.util
from functools import lru_cache
from pathlib import Path

CORE_DIR = Path(__file__).resolve().parents[2]     # core/ (py-common/gui_comun/rutas.py)


@lru_cache(maxsize=1)
def core_env():
    """El módulo core/env.py del workspace, cargado por su ruta (no depende de sys.path)."""
    archivo = CORE_DIR / "env.py"
    if not archivo.is_file():
        raise RuntimeError(f"no encuentro {archivo}")
    spec = importlib.util.spec_from_file_location("core_env", archivo)
    env = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(env)
    return env


def variable(nombre: str) -> Path:
    """Una ruta de core/env (DOCS_ROOT, INDEX_DIR, CORE_DIR…)."""
    return Path(getattr(core_env(), nombre))


def docs_root() -> Path:
    return variable("DOCS_ROOT")
