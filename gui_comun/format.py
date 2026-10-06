"""
utils/format.py — Formateo compartido de tamaños, duraciones y fechas.

Reemplaza a las TRES implementaciones divergentes de format_size que
existían en los scripts originales (awk, bash entero y Python).
"""

from datetime import datetime

_UNITS = ["B", "KB", "MB", "GB", "TB"]


def format_size(size_bytes: int | float | None) -> str:
    """Convierte bytes a una unidad legible con un decimal (1.5 MB)."""
    if size_bytes is None:
        return "?"
    size = float(size_bytes)
    unit = 0
    while size >= 1024 and unit < len(_UNITS) - 1:
        size /= 1024
        unit += 1
    if unit == 0:
        return f"{int(size)} B"
    return f"{size:.1f} {_UNITS[unit]}"


def format_duration(seconds: float) -> str:
    """Duración legible: 0.8 s, 1 min 05 s, 1 h 02 min."""
    if seconds < 60:
        return f"{seconds:.1f} s"
    minutes, secs = divmod(int(seconds), 60)
    if minutes < 60:
        return f"{minutes} min {secs:02d} s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours} h {minutes:02d} min"


def timestamp() -> str:
    """Marca de tiempo estándar para logs y reportes."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def stamp_for_filename() -> str:
    """Marca de tiempo apta para nombres de archivo."""
    return datetime.now().strftime("%Y%m%d-%H%M%S")
