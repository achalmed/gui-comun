---
tipo: doc
estado: activo
forma: explicacion
titulo: "Integración con KDE en gui-comun 3.0: la QApplication, los diálogos de archivos nativos, abrir, mostrar en Dolphin y abrir carpeta"
creado: 2026-11-02
---
# Integración con KDE (3.0)

El autor vio en los studios «un explorador de archivos extraño» al abrir o guardar, y pidió que cada studio se
comportara como una aplicación de KDE: el diálogo de archivos del escritorio, Dolphin para mostrar una ubicación y las
asociaciones del escritorio para abrir un archivo (encargo del 2026-11-02, §4). Este documento explica la causa, la
solución en `gui-comun` 3.0 y lo que se comprobó en la sesión real. La referencia de cada pieza está en
`componentes.md`.

## 1. La causa: `QGuiApplication`

Hasta 2.7, `nucleo.Aplicacion` creaba una `QGuiApplication` (sin `QtWidgets`, para que la interfaz fuera solo QML).
Con ella, `FileDialog` y `FolderDialog` de `QtQuick.Dialogs` no encuentran un diálogo nativo y caen a su versión escrita
en QML: una ventana gris con «Home · Desktop · Downloads…» en inglés, sin los lugares de Dolphin, sin vista previa, sin
la barra de rutas de KDE. Es el «selector extraño».

El tema de plataforma de Plasma (`KDEPlasmaPlatformTheme6`) sí ofrece el diálogo de KDE (`KFileWidget`, el mismo de
Dolphin, Kate u Okular), pero es un widget: solo lo da cuando la aplicación es una `QApplication`. Lo mismo el estilo
`org.kde.desktop` de los controles de Qt Quick, que pinta con el `QStyle` del sistema (Breeze, Kvantum) solo si hay
`QApplication`. Así arrancan las aplicaciones de Kirigami de KDE.

**Comprobado el 2026-11-02** en Kubuntu 26.04 (Plasma 6.6, Wayland, Qt 6.10.2, PySide6 del sistema), con una sonda
mínima que abre un `FileDialog` al arrancar y una captura de la ventana activa (`spectacle -b -n -a`):

| clase de la aplicación | diálogo que aparece |
|---|---|
| `QGuiApplication` | el de QML: lista plana, filtros en un `ComboBox` propio, textos en inglés, sin lugares de KDE |
| `QApplication` | el de KDE: «Lugares» con los marcadores de Dolphin, dispositivos, recientes, vistas, vista previa, barra de rutas, «Tipo de archivo» con los filtros, todo en español (con el `LANGUAGE` que fija `Aplicacion`) |

Las capturas de esa prueba no están en el repo (muestran los lugares y las rutas de la máquina del autor); se guardaron
con las notas de la jornada de reingeniería.

## 2. La solución

- `Aplicacion` crea una **`QApplication`**. De `QtWidgets` solo se usa esa clase: ningún widget, ninguna ventana de
  widgets; la interfaz sigue siendo QML sobre Kirigami. Sin `QtWidgets` en el binding (un entorno raro), vuelve a
  `QGuiApplication` y el diálogo será el de QML. Paquete: `python3-pyside6.qtwidgets` (o `python3-pyqt6`).
- **Elegir** archivos o carpetas: `ElegirArchivos`, `ElegirCarpeta` y `GuardarComo` (QML), sobre `QtQuick.Dialogs`, que
  con la `QApplication` son el diálogo de KDE. Nunca un explorador propio. Hablan en rutas locales (las conversiones de
  `rutas.js`: una carpeta con espacio vuelve con su espacio, no con `%20`). `GuardarComo` deja que el diálogo de KDE
  pregunte antes de sobrescribir y añade el sufijo si el usuario no escribe extensión. `CampoRuta` los usa.
- **Abrir, mostrar, abrir carpeta**: `gui_comun.escritorio.Escritorio`, expuesto como `escritorio`. Son tres
  operaciones distintas y tienen tres funciones:

| función | qué hace | cómo |
|---|---|---|
| `abrirConAplicacion(ruta)` | abre el archivo con la aplicación que el escritorio asocia a su tipo (un PDF en Okular) | `QDesktopServices.openUrl`: con el tema de plataforma de KDE es KIO, que respeta las asociaciones y pasa la activación de Wayland |
| `mostrarEnDolphin(ruta)` | abre Dolphin en la carpeta que contiene la ruta, con la ruta señalada | `dolphin --select <ruta>`; sin Dolphin, la carpeta con `xdg-open` |
| `abrirCarpeta(ruta)` | abre la carpeta (la del archivo, si es un archivo) en el gestor de archivos del escritorio | `xdg-open <carpeta>` (en Kubuntu, Dolphin) |

  Si la ruta no existe, nada se lanza: la función devuelve `false` y presenta un error (descripción, causa, recurso,
  acción) en `errores`; igual si el programa no arranca o el tipo no tiene aplicación asociada.

## 3. Lo comprobado en la sesión real (2026-11-02)

- `ElegirArchivos` (múltiple, con filtros «Documentos PDF» y «Fuentes LaTeX»), `GuardarComo` (con «informe con
  espacio.md» sugerido y el sufijo `md`) y `ElegirCarpeta`: el diálogo de KDE, en español, abierto en la carpeta inicial
  pedida aunque su nombre lleve espacios; el título del diálogo es el del studio («Guardar el informe — Sonda»).
- `mostrarEnDolphin` sobre «un archivo con espacio.txt»: Dolphin quedó como **ventana activa** (Wayland no le negó el
  foco) en la carpeta, con el archivo señalado. Para la prueba se añadió `--new-window` y se cerró esa ventana por su
  PID, sin tocar el Dolphin que el autor tenía abierto. En uso normal, `dolphin --select` respeta la preferencia de
  Dolphin («abrir carpetas nuevas en pestañas»): puede abrir una pestaña en la ventana que ya está abierta.
- El diálogo de errores y el de confirmación sobre `VentanaBase`, con el tema Lliphi.
- Aviso inocuo en la salida de error: `qt.qpa.services: Failed to register with host portal … App info not found` cuando
  el `app_id` no tiene un `.desktop` instalado (la sonda); los studios con su lanzador instalado no lo dan por esa causa.

## 4. Lo que queda fuera

- **XDG Desktop Portal** para elegir archivos: dentro de Plasma, el diálogo en proceso (`KFileWidget`) es el nativo y
  no hace falta el portal; fuera de un sandbox (Flatpak, Snap) Qt no lo usa. Si un studio se empaquetara en Flatpak,
  Qt pasaría solo al portal (`org.freedesktop.portal.FileChooser`), que en Plasma muestra el mismo diálogo.
- **`org.freedesktop.FileManager1.ShowItems`** (la interfaz D-Bus con que Firefox «muestra en la carpeta»): sería la vía
  independiente de Dolphin para señalar un archivo; hoy se usa `dolphin --select`, que es lo decidido para Kubuntu.
- Abrir una terminal en una carpeta (Konsole `--workdir`): ningún studio lo pidió todavía.
