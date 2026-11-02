---
tipo: guia_ia
estado: activo
---
# CLAUDE.md — gui-comun (paquete `gui_comun` y módulo QML `GuiComun`, repo público `achalmed/gui-comun`)

El marco común de los studios. Rige el `CLAUDE.md` raíz de `~/Documents`; aquí solo lo propio. Léase antes:
`README.md`, `estado.md` y, para tocar el QML, `docs/componentes.md` y `docs/arquitectura-qml-kirigami.md`.

## Reglas propias

- **Dos capas que no se mezclan.** 2.x–3.x es QML (`gui_comun/qml/GuiComun/`) con `nucleo`, `acciones`, `tareas`,
  `consola`, `modelos`, `errores`, `escritorio`, `i18n` y `qt`; 1.x (`widgets/`, `diseno`, `theming`, `marco`,
  `ui_loader`, `icons`) está **congelada**: solo correcciones, ninguna mejora; 4.0 la retira. Un studio migrado no
  importa nada de `widgets`.
- **La base no impone distribución (3.0).** `VentanaBase` solo aporta lo común; `VentanaStudio` es una distribución más.
  Nada de navegación lateral, tabla, detalles, consola ni atajos de disciplina (F5) por defecto en la base: lo nuevo
  común entra como componente que un studio elige, no como ranura que todos heredan.
- **`QApplication` y nada más de `QtWidgets`** (3.0): la clase de la aplicación, para el diálogo de archivos de KDE y el
  `QStyle` de `org.kde.desktop` (`docs/integracion-kde.md`). Elegir archivos es `ElegirArchivos`/`ElegirCarpeta`/
  `GuardarComo`; abrir, mostrar en Dolphin y abrir carpeta son tres funciones de `escritorio`, nunca un explorador propio.
- **Los nombres son contrato** de diez studios: en 1.x `aplicar_tema`, `Disenador`, `montar_studio`, `Marco`,
  `Comando`, los widgets de `tarjetas`, las señales de `ConsoleDock` y los workers; en 2.x las propiedades y señales
  de cada componente de `docs/componentes.md` y la API de `Acciones`, `Tareas`, `Consola`, `Aplicacion`. Se añade sin
  quitar; lo que cambia sube la mayor en `CHANGELOG.md` con su migración, tras `rg` en los studios.
- **Cero colores, fuentes, radios o sombras propios en QML**: `Kirigami.Theme` y `Kirigami.Units`; ningún nombre ni
  logotipo de la aplicación dentro de la ventana; cada control sin texto declara `Accessible.name`
  (`tests/test_qml.py` lo vigila).
- **Python no construye interfaz y QML no ejecuta procesos**: Python expone modelos, acciones y estado; QML pinta y
  pide (`@Slot`). Una operación existe una sola vez, en `Acciones`, con su estado (lectura … eliminación), y la barra de
  menú es la única que registra atajos. Instalación, publicación y eliminación confirman siempre, con sus consecuencias
  redactadas; un éxito no es una verificación; un fallo se presenta con causa, recurso y acción (`errores`).
- **El binding es el del sistema** (`/usr/bin/python3`, PySide6 o PyQt6 de apt): solo él carga Kirigami. Todo el
  código nuevo importa de `gui_comun.qt`, con enumeraciones con ámbito y roles como `QByteArray`.
- **Repo público y sin el espacio de trabajo**: nada de rutas de máquina, nombres del despacho ni dependencias de
  `core/`; `rutas.py` encuentra `core/env.py` subiendo carpetas y sin él degrada a `DOCS_ROOT`.
- **Ningún widget guarda la `QApplication`** ni crea envoltorios de `QLayoutItem`; en 2.x `Aplicacion.cerrar()`
  destruye la ventana y el motor antes de que Python libere lo expuesto (si no, ligaduras nulas al salir).
- **Español con tildes** en código, comentarios, textos y QML.

## Verificar

```bash
python3 -m py_compile gui_comun/*.py gui_comun/widgets/*.py gui_comun/workers/*.py gui_comun/galeria/*.py
tests/run.sh                                            # en proceso + cada .qml y la galería con /usr/bin/python3
GUI_COMUN_DIR=$PWD PYTHONPATH=$PWD QT_QPA_PLATFORM=offscreen <Exec del .desktop> --smoke   # cada studio arranca con esta base
/usr/bin/python3 -m gui_comun.galeria                   # la galería en la sesión real (claro/oscuro: --esquema)
for r in filesystem-studio git-studio; do (cd ../$r && tests/run.sh); done                      # los studios no se rompen
for r in quarto-studio latex-studio; do (cd ../$r && QT_QPA_PLATFORM=offscreen python3 -m pytest -q tests); done
(cd ../raphi && .venv/bin/python -m pytest -q tests/test_studio.py)
```
