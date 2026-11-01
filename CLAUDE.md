---
tipo: guia_ia
estado: activo
---
# CLAUDE.md — gui-comun (paquete `gui_comun`, repo público `achalmed/gui-comun`)

El marco común de los studios PySide6. Rige el `CLAUDE.md` raíz de `~/Documents`; aquí solo lo propio. Léase antes:
`README.md` y `estado.md`.

## Reglas propias

- **Los nombres son contrato** de seis studios: `aplicar_tema`, `Disenador`, `montar_studio`, `Marco`, `Comando`,
  los widgets de `tarjetas`, las señales de `ConsoleDock` y los workers. Se añade sin quitar; lo que cambia sube la
  mayor en `CHANGELOG.md` con su migración, tras `rg` en los studios.
- **Repo público y sin el espacio de trabajo**: nada de rutas de máquina, nombres del despacho ni dependencias de
  `core/`; `rutas.py` encuentra `core/env.py` subiendo carpetas y sin él degrada a `DOCS_ROOT`.
- **Ningún widget guarda la `QApplication`** ni crea envoltorios de `QLayoutItem` (`layout.itemAt()`): los dos
  dejaban objetos vivos tras `main()` y la salida terminaba en violación de segmento.
- **Español con tildes** en código, comentarios y textos.

## Verificar

```bash
python3 -m py_compile gui_comun/*.py gui_comun/widgets/*.py gui_comun/workers/*.py
for r in filesystem-studio git-studio quarto-studio latex-studio; do (cd ../$r && QT_QPA_PLATFORM=offscreen python3 -m pytest -q tests); done
(cd ../raphi && .venv/bin/python -m pytest -q tests/test_studio.py)
```
