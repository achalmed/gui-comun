"""comun/rutas.py — dónde está cada cosa para los studios: la raíz y los backends salen de core/env.py.

Ningún studio encuentra su backend por ruta relativa: los de Filesystem Studio y Git Studio son suites de
primer nivel de `SCRIPTS_LINUX` y los de Quarto Studio viven en `SCRIPTS_QUARTO/backend/`. Si un backend se
mueve, se toca `BACKENDS` y nada más. Toda variable respeta un valor previo del entorno (lo hace core/env.py).
"""

from __future__ import annotations

import importlib.util
from functools import lru_cache
from pathlib import Path

STUDIOS_ROOT = Path(__file__).resolve().parents[1]

# Backends por studio: (variable de core/env, partes de la ruta bajo ella).
BACKENDS: dict[str, dict[str, tuple[str, ...]]] = {
    "filesystem": {
        "tree": ("SCRIPTS_LINUX", "script_proyect_tree"),
        "count": ("SCRIPTS_LINUX", "script_count_files_by_extension"),
        "folders": ("SCRIPTS_LINUX", "script_create_folders_batch"),
        "hl_creator": ("SCRIPTS_LINUX", "script_hardlinks-creator"),
        "hl_detector": ("SCRIPTS_LINUX", "script_hardlinks-detector"),
    },
    "git": {
        "download": ("SCRIPTS_LINUX", "script_git_download_respos"),
        "sync": ("SCRIPTS_LINUX", "script_git_sync_respos"),
    },
    "quarto": {
        "blogs_manager": ("SCRIPTS_QUARTO", "backend", "script_blogs_manager"),
        "metadata_manager": ("SCRIPTS_QUARTO", "backend", "script_metadata_manager"),
        "format_yaml": ("SCRIPTS_QUARTO", "backend", "script_format_yaml"),
        "pub_index_symlink": ("SCRIPTS_QUARTO", "backend", "script_pub_index_symlink"),
        "generador_similar": ("SCRIPTS_QUARTO", "backend", "script_generador_publicacion_similar"),
    },
}


@lru_cache(maxsize=1)
def core_env():
    """El módulo core/env.py del workspace: se sube desde studios/ hasta hallarlo."""
    d = STUDIOS_ROOT
    while d != d.parent and not (d / "core" / "env.py").is_file():
        d = d.parent
    archivo = d / "core" / "env.py"
    if not archivo.is_file():
        raise RuntimeError(f"no encuentro core/env.py por encima de {STUDIOS_ROOT}")
    spec = importlib.util.spec_from_file_location("core_env", archivo)
    env = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(env)
    return env


def variable(nombre: str) -> Path:
    """Una ruta de core/env (DOCS_ROOT, SCRIPTS_LINUX, SCRIPTS_QUARTO, INDEX_DIR…)."""
    return Path(getattr(core_env(), nombre))


def docs_root() -> Path:
    return variable("DOCS_ROOT")


def backend(studio: str, clave: str) -> Path:
    """Carpeta de un backend: `backend("git", "sync")` → `$SCRIPTS_LINUX/script_git_sync_respos`."""
    var, *partes = BACKENDS[studio][clave]
    return variable(var).joinpath(*partes)


def backends(studio: str) -> dict[str, Path]:
    return {clave: backend(studio, clave) for clave in BACKENDS[studio]}
