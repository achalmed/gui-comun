"""gui_comun — lo que comparten los studios PySide6: rutas por core/env, tema, carga de .ui e iconos, ajustes, workers, consola e historial.

Lo importan Filesystem Studio (repo `filesystem-studio`), Git Studio (repo `git-studio`) y, para las rutas, Quarto
Studio (`scripts-quarto/studio`). Cada studio pone `core/py-common` en `sys.path` desde el `__init__.py` de su
paquete (subiendo carpetas hasta hallar `core/`, como los envoltorios del logger) antes de importar nada de aquí.
Llegó de `gui-suites/comun/` con su historia el 2026-10-27 (sesión 9 de la cola de la auditoría posterior).
"""
