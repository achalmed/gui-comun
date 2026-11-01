---
tipo: estado
estado: activo
actualizado: 2026-10-31
---
# estado.md — gui-comun

## Hecho

| fecha | qué | dónde se ve |
|---|---|---|
| 2026-10-31 | Nace como repo y paquete propio (1.0.0), separado de `core/py-common/gui_comun` con su historia, para que Raphi Studio corra fuera del espacio de trabajo; `rutas` ya no exige `core/` | `CHANGELOG.md`; `core/docs/decisiones.md` §2.12 |

## En curso

nada en curso

## Por hacer

- 2026-10-31 · dueño: autor · **Crear el remoto público `achalmed/gui-comun`** y empujar con la etiqueta `v1.0.0` (Raphi lo pide desde GitHub cuando no está el repo de al lado): `gh repo create achalmed/gui-comun --public --source . --remote origin && git push -u origin main --tags`. Después, `remoto:` en `meta/workspace.yml`.

## Futuro

- Publicarlo en PyPI si un studio se distribuye fuera de GitHub.
