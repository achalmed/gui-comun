---
tipo: changelog
estado: activo
---
# CHANGELOG — gui-comun

Formato: [Keep a Changelog 1.1.0](https://keepachangelog.com/es-ES/1.1.0/); versiones: [SemVer 2.0.0](https://semver.org/lang/es/).
La versión vive en `gui_comun/__init__.py` y en `pyproject.toml`.

## [1.3.0] - 2026-11-01

### Añadido

- Acento `indigo` (Dotfiles Studio) y los iconos de trazo `paquete`, `enlace` y `subir`.

## [1.2.0] - 2026-11-01

### Añadido

- Acento `grafito` (Huella Studio) y los iconos de trazo `huella`, `usuario`, `correo`, `codigo` y `globo`.

## [1.1.0] - 2026-10-31

### Añadido

- Acento `sepia` (Biblioteca Studio) y los iconos de trazo `libro`, `sincronizar`, `candado`, `bandeja` y `verificar`.
- `lanzador.entrada(..., esquema=)` e `instalar(..., esquema=)`: el acceso directo declara `x-scheme-handler/<esquema>`,
  recibe el enlace por `%u` y queda como aplicación por omisión de ese esquema (`xdg-mime default`).

## [1.0.0] - 2026-10-31

### Añadido

- Paquete propio (`pip install gui-comun`), separado de `core/py-common/gui_comun` con su historia.
- `lanzador.py`: el acceso directo de cada studio en el menú de aplicaciones.
- Acento `lima` (Simuladores Studio).

### Cambiado

- `rutas.py` busca `core/env.py` subiendo carpetas (desde el paquete o la carpeta actual) y, sin él, `docs_root()`
  usa `DOCS_ROOT` o `~/Documents`.
