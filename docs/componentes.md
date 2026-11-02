---
tipo: doc
estado: activo
forma: referencia
titulo: "Componentes de GuiComun 2.x: qué es cada uno, sus propiedades y señales, y la API Python que los alimenta"
creado: 2026-11-01
---
# Componentes de GuiComun (2.5)

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
`seleccion` (`ItemSelectionModel`), `filaActual`, `filas`; `claveAjustes` (2.1: con ella, los anchos de columna que
el usuario arrastró se recuerdan en QSettings, grupo `tablas/<clave>`). Señales: `ordenar(columna, descendente)`,
`activada(fila)` (doble clic o Intro), `suprimir()` (Supr), `filaActualCambiada(fila)`, `seleccionCambiada()`.
Funciones: `filasSeleccionadas()`, `seleccionarTodo()`, `invertirSeleccion()`, `seleccionarFila(fila, limpiar)`,
`mostrarColumna(c, visible)`. Selección múltiple con Ctrl y Mayús; columnas redimensionables arrastrando la cabecera.

### ArbolDatos (2.1)

`TreeView` de Qt Quick + `HorizontalHeaderView` sobre cualquier `QAbstractItemModel` jerárquico con los roles de
`TablaDatos` (`display`, `nivel`, `icono`, `habilitado`), p. ej. `modelos.ModeloArbol`. Mismas `columnas`
(`ancho`, `minimo`, `alinear`, `mono`, `semantica`, `conIcono`, `visible`, `estrecho`, `secundaria`), `altoFila`,
`umbralEstrecho`, `menuContextual`, `mensajeVacio` · `iconoVacio`, `seleccion`, `filaActual`, `filas`; además `raiz`
(un `QModelIndex` que acota la vista: el explorador de carpetas) y `expandirAlCargar` (niveles que se expanden solos
al poner el modelo; −1 todos). Señales: `activada(indice)` (doble clic o Intro; el `QModelIndex`), `suprimir()`,
`filaActualCambiada(fila)`, `seleccionCambiada()`. Funciones: `indiceDe(fila)`, `indiceActual()`, `expandirTodo(niveles)`,
`contraerTodo()`, `expandir(fila)` · `contraer(fila)` · `alternar(fila)`, `filasSeleccionadas()`,
`indicesSeleccionados()`, `seleccionarTodo()`, `seleccionarFila(fila, limpiar)`, `mostrarColumna(c, visible)`. La
flecha de la primera columna expande con el ratón; ← y → con el teclado (← en una fila contraída sube al padre).

### PanelDetalles

`titulo`, `subtitulo`, `icono`, `accionesCabecera` (lista de `Accion`: botones de icono), `pestanas:
[{titulo, contador, visible}]`, `pestanaActual`; los hijos son las páginas, en el orden de las pestañas (una pestaña
con `visible: false` conserva su índice: su página sigue siendo el hijo de esa posición); `mensajeVacio` cuando no hay
título; `anchoPreferido` (24) · `anchoMinimo` (18). 2.4: cambiar un contador o la visibilidad no recrea los botones ni
mueve `pestanaActual`; si la actual pasa a oculta, salta a la primera visible.

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

### CampoRuta (2.1)

Un `TextField` con su botón de elegir: `texto`, `carpeta` (verdadero: `FolderDialog`; falso: `FileDialog` con
`filtros`), `titulo`, `marcador`, `nombreAccesible`; señal `aceptada(texto)` (Intro o el diálogo); funciones
`abrir()`, `enfocar()`; `campoTexto` es el campo.

### VistaTexto (2.2)

Texto de solo lectura con mensaje de vacío: `texto`; `markdown` (verdadero: `MarkdownText`, fuente del sistema, líneas
ajustadas, los enlaces abren fuera; falso: monoespaciado, sin partir líneas) y `definicion` (la de KSyntaxHighlighting
que resalta el texto plano: «Bash», «Diff», «JSON», «Markdown»…; vacía, sin resaltar; si el módulo
`org.kde.syntaxhighlighting` falta, texto plano); `ajustarLineas`; `mensajeVacio` · `iconoVacio`; `nombreAccesible`;
`area` es el `TextArea`. El centro de una vista de documento o la pestaña de lectura de un panel de detalles.

### ListaDiagnosticos (2.3)

La lista de errores y avisos de una herramienta sobre un modelo de lista con los roles `nivel` (`error` · `aviso` ·
`informacion` · `tipografia` · otro), `mensaje`, `archivo`, `linea` (número; 0 o vacío, sin línea) y, opcional,
`detalle` (p. ej. `modelos.ModeloLista`): `modelo`; cada fila con el icono y el color semántico de su nivel, el
mensaje en varias líneas y «archivo · línea n» debajo; `mensajeVacio` · `iconoVacio`; `nombreAccesible`;
`menuContextual`; `filaActual`, `filas`, `vista`. Señales: `activada(fila)` (Intro o doble clic: «ir a»),
`filaActualCambiada(fila)`. Funciones: `seleccionarFila(fila)`, `iconoDe(nivel)`, `colorDe(nivel)`,
`textoNivel(nivel)`. La pestaña Problemas de LaTeX Studio.

### Grafico (2.6)

Un gráfico de líneas o de barras sobre `org.kde.quickcharts`: `series` (`[{nombre, y}]`, todas con el mismo número de
valores: QuickCharts posiciona cada valor por su índice, así que quien lo usa remuestrea sus curvas sobre una rejilla
común de x), `etiquetasX` (repartidas de izquierda a derecha), `xMinimo` · `xMaximo` (sitúan puntos, equilibrio y
marcas), `yMinimo` · `yMaximo` (el rango que se dibuja), `barras` (`{categorias, valores}`, en vez de líneas),
`puntos` (`[{x, y, etiqueta}]`), `equilibrio` (`{x, y, etiqueta}`), `marcas` (`[{x, etiqueta}]` o `[{y, etiqueta}]`:
líneas verticales u horizontales), `etiquetaX` · `etiquetaY`, `anotacion`, `conLeyenda`; `imagen` (un PNG: se muestra
si falta el módulo o con `preferirImagen`), `mensajeVacio` · `iconoVacio`, `nombreAccesible`; `hayModulo`, `hayDatos`,
`conImagen`. Los colores de las series salen de `ColorGradientSource` sobre `Kirigami.Theme.highlightColor` (la paleta
de QuickCharts), las barras del acento y el resto de `Kirigami.Theme`. Sin pantalla, la plataforma `offscreen` elige el
renderizador por software, que no dibuja los materiales de QuickCharts: una captura necesita `QT_QUICK_BACKEND=rhi`.
La pestaña Resultados de Simuladores Studio.

### PaginaFormulario (2.7)

Un `Kirigami.FormLayout` generado desde `campos` (`[{clave, etiqueta, tipo, defecto, opciones, minimo, maximo, ayuda,
obligatorio, marcador}]`, la ficha de una herramienta) con un control por `tipo`: `texto` (y cualquier tipo
desconocido), `multilinea`, `entero` (`SpinBox` con `minimo` y `maximo`), `decimal`, `opcion` (`ComboBox` sobre
`opciones`: `[valor, etiqueta]` o valores sueltos), `casilla`, `clave` (contraseña), `color` (muestra, campo y
`ColorDialog`), `ruta` y `carpeta` (`CampoRuta`); la ayuda debajo de cada campo y el asterisco de lo obligatorio.
`valores` es lo escrito, sin los vacíos (quien lo usa pone el valor por omisión: `Parametro.convertir` del motor de
Raphi); `valor(clave)` (lo escrito o el `defecto`), `fijar(clave, valor)`, `poner(mapa)`, `restablecer()`; señal
`cambiado(clave, valor)`; `nombreAccesible`, `mensajeVacio`, `nCampos`. Cambiar `campos` vacía los valores. La pestaña
Opciones de Raphi Studio.

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
| `tareas.Tareas(consola)` | `.funcion(nombre, fn, *args, al_terminar=, al_fallar=, **kw)`, `.proceso(nombre, argv, cwd=, al_terminar=, progreso_de=, entrada=, entorno=)` (el proceso en su propio grupo; 2.3: `progreso_de(texto)` → `(porcentaje, elemento)` o `None` por cada línea de la salida; 2.5: `entrada`, el texto que se escribe en su entrada estándar y se cierra, sin ella cerrada; `entorno`, variables añadidas), `.cancelar()` (a la función, su `cancel_cb`; al proceso, `SIGTERM` al grupo entero); `activa`, `nombre`, `progreso`, `elemento`, `cuantas`; señales `iniciada`, `cambiada`, `linea`, `terminada(nivel, nombre, detalle)` |
| `consola.Consola` | `.salida`, `.registro` (`ModeloConsola`: `escribir`, `limpiar`, `texto`, `textoConHora`, `lineas`), `.escribir(texto, nivel)`, `.registrar(nivel, texto)`, `.log(nivel, texto)`; señal `escrita` |
| `modelos.ModeloLista(roles, filas)` | `.poner`, `.anadir`, `.quitar`, `.actualizar`, `.fila(i)`, `.todas()`, `filas` |
| `modelos.ModeloFiltrado(origen)` | `.ordenar(columna, descendente)`, `.filtrar(texto)`, `.aceptar_con(criterio)`, `.filaOrigen`, `.filaVisible`, `filas`, `columnaOrden`, `descendente` |
| `modelos.ModeloTabla(columnas, filas)` (2.1) | `columnas` = [(título, clave)]; filas de dict con esas claves y, opcionales, `nivel`, `icono` (texto o {clave: icono}), `habilitado`, `crudo` ({clave: valor} para ordenar); `.poner`, `.anadir`, `.quitar`, `.actualizar`, `.fila(i)`, `.todas()`, `.clave(c)`, `filas`, `columnas` |
| `modelos.ModeloArbol(columnas, raices)` (2.1) | nodos de dict: `valores` (uno por columna), `nivel`, `icono` (texto o {columna: icono}), `habilitado`, `hijos` (lista o función `f(nodo)` que se consulta al expandir) y lo propio; `.poner`, `.recargar(indice)`, `.datos(indice)`, `.ruta(indice)`, `.todas(indice)`, `filas` |
| `i18n.instalar(motor, idioma)` | el objeto de contexto con `i18n`, `i18nc`, `i18nd`, `i18ndc`, `i18np`, `i18ncp`, `i18ndp`, `i18ndcp` y las `xi18n*` (gettext sobre `/usr/share/locale`) |
| `qt` | `BINDING`, los nombres de QtCore/QtGui/QtQml con la API de PySide6, `cast`, `rol`, `roles`, `version_qt` |
| `galeria.esquema.entorno_con_esquema(colors)` | el entorno de un proceso con otro esquema de color de KDE (kdeglobals temporal) |

## 3. Lo que falta (2.x)

- `org.kde.kirigamiaddons.settings` cuando Kubuntu lo empaquete (hoy `DialogoAjustes` reproduce su anatomía).
- Orden por cabecera en `ArbolDatos` (un `KSortFilterProxyModel` de `org.kde.kitemmodels` sobre el árbol) cuando un
  studio lo pida.
