"""gui_comun/acentos.py — los acentos de la familia (un color por studio), solo datos.

Los usa `lanzador.py` (la losa del icono del menú de aplicaciones); vive aparte para que el lanzador no arrastre QtSvg,
que el Python del sistema puede no tener. El acento solo existe en ese icono (la interfaz usa el del tema).
"""

# --- Acentos: uno por studio, con su variante clara para el modo oscuro ---
ACENTOS = {
    "verde": {"claro": "#0d9488", "oscuro": "#2dd4bf"},    # Filesystem Studio
    "naranja": {"claro": "#ea580c", "oscuro": "#fb923c"},  # Git Studio
    "azul": {"claro": "#2563eb", "oscuro": "#60a5fa"},     # Quarto Studio
    "violeta": {"claro": "#7c3aed", "oscuro": "#a78bfa"},  # Raphi Studio
    "rosa": {"claro": "#db2777", "oscuro": "#f472b6"},     # LaTeX Studio
    "lima": {"claro": "#65a30d", "oscuro": "#a3e635"},     # Simuladores Studio
    "sepia": {"claro": "#9a6b3f", "oscuro": "#d6a874"},    # Biblioteca Studio
    "grafito": {"claro": "#475569", "oscuro": "#94a3b8"},  # Huella Studio
    "indigo": {"claro": "#4f46e5", "oscuro": "#818cf8"},   # Dotfiles Studio
    "carmesi": {"claro": "#c53133", "oscuro": "#ef6661"},  # Lliphi Studio (el rojo OKLCH 25° de Lliphi)
}
