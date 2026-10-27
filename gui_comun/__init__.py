"""gui_comun — lo que comparten los studios PySide6: rutas por core/env, tema, carga de .ui e iconos, ajustes, workers, consola e historial.

Lo importan Filesystem Studio, Git Studio y, para las rutas, Quarto Studio, cada uno desde su propio repo. Cada studio
pone `core/py-common` en `sys.path` desde el `__init__.py` de su paquete (subiendo carpetas hasta hallar `core/`, como
los envoltorios del logger) antes de importar nada de aquí. Llegó con su historia del repo que reunía las tres GUI,
retirado el 2026-10-27 (docs/decisiones.md §2.9).
"""
