---
tipo: doc
estado: activo
forma: referencia
titulo: "Componentes de GuiComun 2.0: qué es cada uno, sus propiedades y señales, y la API Python que los alimenta"
creado: 2026-11-01
---
# Componentes de GuiComun (2.0)

La referencia del módulo QML `GuiComun` (`gui_comun/qml/GuiComun/`) y del núcleo Python que lo alimenta. La anatomía
y la justificación están en `arquitectura-qml-kirigami.md` §4–5 y en `git-studio/docs/rediseno.md` §4–7; la galería
(`python3 -m gui_comun.galeria`) muestra cada pieza con datos de muestra. Regla de todo el módulo: **cero colores,
fuentes, radios o sombras propios** (`Kirigami.Theme`, `Kirigami.Units`), cada control sin texto declara
`Accessible.name`, y **ningún nombre ni logotipo de la aplicación dentro de la ventana**.

## 1. QML

### VentanaStudio

`Kirigami.AbstractApplicationWindow`. Menú generado desde `acciones.menus`; barra de herramientas con `acciones.barra`,
`herramientasExtra` (p. ej. un `Kirigami.SearchField`), los conmutadores de los tres paneles y el menú completo;
`SplitView` vertical (espacio de trabajo · panel inferior) con otro horizontal (navegación · centro · detalles);
barra de estado; paleta de órdenes; «Acerca de». Geometría, visibilidad de paneles y posición de los divisores en
`QSettings` (`claveAjustes`, por omisión `ventana`).

| propiedad | tipo | qué es |
|---|---|---|
| `acciones` · `tareas` · `consola` | objetos Python | el registro (`gui_comun.acciones.Acciones`), las tareas (`Tareas`) y la consola (`Consola`); se pasan como `studio.acciones`… |
| `navegacion` · `centro` · `detalles` · `inferior` | `Item` | lo que va en cada ranura (cualquier `Item`; los componentes de abajo encajan) |
| `resumen` · `contexto` | `string` | la barra de estado: izquierda y derecha |
| `descripcion` · `autor` · `sitio` | `string` | «Acerca de» |
| `dialogoAjustes` | `DialogoAjustes` | lo abre `app.ajustes` |
| `mostrarNavegacion` · `mostrarDetalles` · `mostrarInferior` | `bool` | el estado de los paneles (recordado; F9 · F11 · F4) |
| `abrirInferiorAlEmpezarTarea` | `bool` | abre el panel inferior cuando `tareas` arranca algo (como Kate) |
| `anchoEstrecho` (900) · `anchoMedio` (1200) · `estrecha` · `media` | `int` · `bool` | con menos de `anchoEstrecho`, la navegación se pliega a iconos y los detalles se abren como hoja sobre la tabla |
| `mensajes` | `Mensajes` | `ventana.mensajes.mostrar(texto, tipo, acciones)` |
| `paleta` | `PaletaOrdenes` | `paleta.abrir("texto")` |

La ventana atiende `ventana.navegacion`, `ventana.detalles`, `ventana.inferior`, `ventana.pantalla_completa`,
`ventana.paleta`, `app.ajustes`, `app.acerca` y `app.salir` (las registra `Acciones.estandar()`); el studio puede
escucharlas también.

### PanelNavegacion

`secciones: [{titulo, filas: [{nombre, texto, icono, contador}]}]`, `actual` (nombre), `plegado` (solo iconos),
`anchoPreferido` (13 unidades) · `anchoMinimo` (9). Señal `elegida(nombre)`.

### TablaDatos

`TableView` + `HorizontalHeaderView` sobre un `QAbstractTableModel` (o `ModeloFiltrado`). Roles que entiende:
`display` (texto), `nivel` (`positivo` · `neutro` · `activo` · `negativo` · `inactivo`; color solo en las columnas
`semantica`), `habilitado` (falso atenúa la fila), `icono` (en las columnas `conIcono`).

`columnas: [{ancho (unidades; 0 = estira), minimo, alinear, mono, semantica, conIcono, visible, estrecho, secundaria}]`;
`altoFila` (1,7 unidades); `umbralEstrecho` (50 unidades: bajo él se ocultan las `estrecho`); `columnaOrden` ·
`descendente`; `menuContextual` (un `Menu`, p. ej. `MenuAcciones` sin atajos); `mensajeVacio` · `iconoVacio`;
`seleccion` (`ItemSelectionModel`), `filaActual`, `filas`. Señales: `ordenar(columna, descendente)`,
`activada(fila)` (doble clic o Intro), `suprimir()` (Supr), `filaActualCambiada(fila)`, `seleccionCambiada()`.
Funciones: `filasSeleccionadas()`, `seleccionarTodo()`, `invertirSeleccion()`, `seleccionarFila(fila, limpiar)`,
`mostrarColumna(c, visible)`. Selección múltiple con Ctrl y Mayús; columnas redimensionables arrastrando la cabecera.

### PanelDetalles

`titulo`, `subtitulo`, `icono`, `accionesCabecera` (lista de `Accion`: botones de icono), `pestanas:
[{titulo, contador, visible}]`, `pestanaActual`; los hijos son las páginas, en el orden de las pestañas;
`mensajeVacio` cuando no hay título; `anchoPreferido` (24) · `anchoMinimo` (18).

### PanelInferior

`consola` (`Consola`): pestañas Salida (`consola.salida.texto`, con `ResaltadoSalida` de `org.kde.syntaxhighlighting`,
`definicion` «Bash») y Registro (`consola.registro.textoConHora`); `extras: [{titulo, componente}]` añade pestañas
(la tabla de resultados por repo de Git Studio); `altoPreferido` (9) · `altoMinimo` (5); señal `cerrar()`;
funciones `mostrarSalida()`, `mostrarRegistro()`, `mostrarExtra(i)`.

### BarraEstado

`resumen`, `contexto`, `tareas` (muestra nombre · elemento, barra de progreso y cancelar mientras hay tarea);
señal `progresoPulsado()` (la ventana abre el panel inferior).

### Mensajes

`mostrar(texto, tipo, acciones)` con `tipo` ∈ `informacion` · `positivo` · `aviso` · `error` y `acciones:
[{texto, icono, ejecutar}]`; `limpiar()`; `cuantos`. Solo para lo que exige atención.

### PaletaOrdenes

`acciones`; `abrir(texto)`. Pide `acciones.buscar(texto)` (difusa) y ejecuta `acciones.ejecutar(nombre)`. Las fuentes
dinámicas (`Acciones.anadir_fuente`) entran en la misma lista (ir a un repositorio, abrir un informe).

### DialogoAjustes

`Kirigami.Dialog` con `modulos: [{titulo, icono, pagina (Component)}]`; cada página puede declarar `function guardar()`,
que se llama al aceptar o aplicar; señal `guardado()`. Páginas con `FormCard`.

### MenuAcciones · BotonAccion

`MenuAcciones { acciones; elementos; titulo; conAtajos }`: un `Menu` construido desde `[{tipo: "accion", nombre} |
{tipo: "separador"} | {tipo: "menu", titulo, elementos}]` (lo que produce `Acciones.definir_menus`); con
`conAtajos: false` para los contextuales. `BotonAccion { accion; conTexto }`: un `ToolButton` ligado a una `Accion`.

## 2. Python

| módulo | API |
|---|---|
| `nucleo.Aplicacion(app_id, nombre, version=, organizacion=, idioma="es", nombre_ajustes=)` | `.exponer(nombre, objeto)` (también `studio.<nombre>`), `.cargar(qml)`, `.ejecutar(qml, humo=False)`, `.ventana()`, `.capturar(png, espera_ms)`, `.cerrar()`, `.traducciones`, `.mensaje_de_fallo()`; `aplicacionStudio` en QML (appId, nombre, version, binding, versionGuiComun, versionQt) |
| `acciones.Acciones` | `.registrar(nombre, texto, icono, atajo, grupo, habilitada=, marcable=, marcada=, descripcion=, al_disparar=)` → `Accion`; `.estandar(nombre_app)`; `.definir_menus([...])`; `.definir_barra([...])`; `.anadir_fuente(fn)`; `.accion(nombre)`, `.existe`, `.ejecutar`, `.habilitar`, `.marcar`, `.buscar(texto)`; señal `disparada(nombre, marcada)`; es modelo de lista |
| `acciones.Accion` | propiedades `nombre`, `texto`, `textoPlano`, `icono`, `atajo`, `atajoTexto`, `grupo`, `habilitada`, `marcable`, `marcada`, `visible`, `descripcion`; `.conectar(fn)`, `.disparar()`; señal `disparada(marcada)` |
| `tareas.Tareas(consola)` | `.funcion(nombre, fn, *args, al_terminar=, al_fallar=, **kw)`, `.proceso(nombre, argv, cwd=, al_terminar=)`, `.cancelar()`; `activa`, `nombre`, `progreso`, `elemento`, `cuantas`; señales `iniciada`, `cambiada`, `linea`, `terminada(nivel, nombre, detalle)` |
| `consola.Consola` | `.salida`, `.registro` (`ModeloConsola`: `escribir`, `limpiar`, `texto`, `textoConHora`, `lineas`), `.escribir(texto, nivel)`, `.registrar(nivel, texto)`, `.log(nivel, texto)`; señal `escrita` |
| `modelos.ModeloLista(roles, filas)` | `.poner`, `.anadir`, `.quitar`, `.actualizar`, `.fila(i)`, `.todas()`, `filas` |
| `modelos.ModeloFiltrado(origen)` | `.ordenar(columna, descendente)`, `.filtrar(texto)`, `.aceptar_con(criterio)`, `.filaOrigen`, `.filaVisible`, `filas`, `columnaOrden`, `descendente` |
| `i18n.instalar(motor, idioma)` | el objeto de contexto con `i18n`, `i18nc`, `i18nd`, `i18ndc`, `i18np`, `i18ncp`, `i18ndp`, `i18ndcp` y las `xi18n*` (gettext sobre `/usr/share/locale`) |
| `qt` | `BINDING`, los nombres de QtCore/QtGui/QtQml con la API de PySide6, `cast`, `rol`, `roles`, `version_qt` |
| `galeria.esquema.entorno_con_esquema(colors)` | el entorno de un proceso con otro esquema de color de KDE (kdeglobals temporal) |

## 3. Lo que falta (2.x)

- `org.kde.kirigamiaddons.settings` cuando Kubuntu lo empaquete (hoy `DialogoAjustes` reproduce su anatomía).
- Anchos de columna de `TablaDatos` recordados entre sesiones (hoy se recuerdan los paneles y la geometría).
- `Grafico` (`org.kde.quickcharts`) para Simuladores; `PaginaFormulario` generada desde fichas para Raphi (F5).
