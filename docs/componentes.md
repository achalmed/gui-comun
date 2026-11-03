---
tipo: doc
estado: activo
forma: referencia
titulo: "Componentes de GuiComun 3.x: qué es cada uno, sus propiedades y señales, y la API Python que los alimenta"
creado: 2026-11-01
---
# Componentes de GuiComun (3.1)

La referencia del módulo QML `GuiComun` (`gui_comun/qml/GuiComun/`) y del núcleo Python que lo alimenta. **3.0**: la
ventana deja de imponer distribución (`VentanaBase`, y `VentanaStudio` como una distribución más), la aplicación es una
`QApplication` (el diálogo de archivos de KDE; ver `integracion-kde.md`), y hay errores presentables, estados de
operación con confirmación redactada y la integración con el escritorio (abrir, mostrar en Dolphin, abrir carpeta). **3.1** promueve lo que los studios
repetían tras la reingeniería: el editor (`EditorTexto`, `BarraBuscarReemplazar`), el visor PDF (`VistaPdf`), la lista de
problemas (`ListaErrores`), la diferencia lado a lado (`VistaComparacion`), los pasos de una escritura
(`PasosEscritura`, `LineaPasos`), el gráfico científico (`GraficoXY`, `PaletaCategorica`), `EtiquetaNivel`, el
proveedor de miniaturas y el orden por cabecera de `ArbolDatos`. La anatomía
y la justificación están en `arquitectura-qml-kirigami.md` §4–5 y en `git-studio/docs/rediseno.md` §4–7; la galería
(`python3 -m gui_comun.galeria`) muestra cada pieza con datos de muestra. Regla de todo el módulo: **cero colores,
fuentes, radios o sombras propios** (`Kirigami.Theme`, `Kirigami.Units`), cada control sin texto declara
`Accessible.name`, y **ningún nombre ni logotipo de la aplicación dentro de la ventana**.

## 1. QML

### VentanaBase (3.0)

`Kirigami.AbstractApplicationWindow` que aporta solo lo común y deja el contenido libre: lo que se declara dentro
(con `anchors.fill: parent`) va bajo los mensajes y a todo lo ancho; `header` y `footer` quedan libres. Trae la barra
de menú generada desde `acciones.menus` (la única que registra atajos), la paleta de órdenes (Ctrl+K y la acción
`ventana.paleta`), `Mensajes`, un `DialogoError` sobre `errores` (se abre solo cuando llega un error), un
`DialogoConfirmacion` (se abre cuando una acción emite `confirmacionPedida`), «Acerca de», el `dialogoAjustes` del
studio, pantalla completa y la geometría en `QSettings` (`claveAjustes`, por omisión `ventana`). Atiende
`ventana.pantalla_completa`, `ventana.paleta`, `app.ajustes`, `app.acerca`, `app.salir`. Con las tareas que declaran su
operación, notifica el éxito (escritura, instalación, publicación, eliminación) y, aparte, la verificación correcta (la
fallida llega como error presentable).

| propiedad | tipo | qué es |
|---|---|---|
| `acciones` · `tareas` · `consola` | objetos Python | el registro, las tareas, la consola |
| `errores` · `escritorio` | objetos Python | por omisión los de `Aplicacion` (`aplicacionStudio.errores`, `.escritorio`) |
| `descripcion` · `autor` · `sitio` | `string` | «Acerca de» |
| `dialogoAjustes` | `DialogoAjustes` | lo abre `app.ajustes` |
| `claveAjustes` | `string` | el grupo de `QSettings` de la geometría |
| `conMenu` · `notificarTareas` | `bool` | la barra de menú visible (true) · los avisos de éxito y verificación (true) |
| `mensajes` | `Mensajes` | dónde van los mensajes (el de la base; `VentanaStudio` pone los suyos sobre el centro) |
| `paleta` · `confirmacion` · `dialogoError` | componentes | la paleta, el diálogo de confirmación, el de errores |
| `contenido` (por omisión) · `zonaContenido` | `Item` | lo que el studio declara dentro · su contenedor |

Funciones: `confirmar(peticion, alAceptar)` (una confirmación ad hoc: `{titulo, consecuencias, operacion,
operacionTexto, textoAceptar, icono, destructiva}`), `error(descripcion, causa, recurso, accion, detalle)`,
`notificar(texto, tipo, acciones)`, `existe(nombre)`.

### VentanaStudio

3.0: una distribución sobre `VentanaBase` (la de Dolphin y Kate), con la misma API que en 2.x. Barra de herramientas
con `acciones.barra`, `herramientasExtra` (p. ej. un `Kirigami.SearchField`), los conmutadores de los tres paneles y el
menú completo; `SplitView` vertical (espacio de trabajo · panel inferior) con otro horizontal (navegación · centro ·
detalles); barra de estado. Visibilidad de paneles y posición de los divisores en `QSettings`. Lo demás (menú, paleta,
«Acerca de», ajustes, errores, confirmaciones, geometría) lo pone la base. Un studio cuya disciplina pide otra cosa
(un editor con su visor, un lienzo, un catálogo) usa `VentanaBase`.

| propiedad | tipo | qué es |
|---|---|---|
| (las de `VentanaBase`) | | `acciones`, `tareas`, `consola`, `descripcion`, `autor`, `sitio`, `dialogoAjustes`, `claveAjustes`… |
| `navegacion` · `centro` · `detalles` · `inferior` | `Item` | lo que va en cada ranura (cualquier `Item`; los componentes de abajo encajan) |
| `resumen` · `contexto` | `string` | la barra de estado: izquierda y derecha |
| `descripcion` · `autor` · `sitio` | `string` | «Acerca de» |
| `dialogoAjustes` | `DialogoAjustes` | lo abre `app.ajustes` |
| `mostrarNavegacion` · `mostrarDetalles` · `mostrarInferior` | `bool` | el estado de los paneles (recordado; F9 · F11 · F4) |
| `abrirInferiorAlEmpezarTarea` | `bool` | abre el panel inferior cuando `tareas` arranca algo (como Kate) |
| `anchoEstrecho` (900) · `anchoMedio` (1200) · `estrecha` · `media` | `int` · `bool` | con menos de `anchoEstrecho`, la navegación se pliega a iconos y los detalles se abren como hoja sobre la tabla |
| `mensajes` | `Mensajes` | `ventana.mensajes.mostrar(texto, tipo, acciones)` (sobre el centro) |
| `paleta` | `PaletaOrdenes` | `paleta.abrir("texto")` |

La ventana atiende `ventana.navegacion`, `ventana.detalles` y `ventana.inferior` (y la base, el resto; las registra
`Acciones.estandar()`); el studio puede escucharlas también.

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
flecha de la primera columna expande con el ratón; ← y → con el teclado (← en una fila contraída sube al padre). 3.1:
`ordenable` (un clic en la cabecera ordena cada nivel por esa columna; el segundo, al revés), `columnaOrden`,
`descendente`, `ordenarPor(columna, descendente)` (llama a `modelo.ordenar` si el modelo lo tiene) y señal
`ordenar(columna, descendente)`.

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

### CampoRuta (2.1; 3.0)

Un `TextField` con su botón de elegir: `texto`, `carpeta` (verdadero: `ElegirCarpeta`; falso: `ElegirArchivos` con
`filtros`, o `GuardarComo` con `guardar: true`), `carpetaInicial` (3.0: donde abre el diálogo si el campo está vacío),
`titulo`, `marcador`, `nombreAccesible`; señal `aceptada(texto)` (Intro o el diálogo); funciones `abrir()`,
`enfocar()`, `poner(ruta)`; `campoTexto` es el campo. 3.0: las rutas con espacios o «#» vuelven bien (antes «%20»).

### ElegirArchivos · ElegirCarpeta · GuardarComo (3.0)

El diálogo de archivos del escritorio (el de KDE con la `QApplication` de `Aplicacion`; `integracion-kde.md`), nunca un
explorador propio. Hablan en **rutas locales**, no en URL.

| componente | propiedades | funciones y señales |
|---|---|---|
| `ElegirArchivos` (`FileDialog`) | `titulo`, `filtros` (`["Documentos PDF (*.pdf)"]` o `[{nombre, patrones: ["*.pdf"]}]`), `conTodos` (añade «Todos los archivos (*)»; true), `carpetaInicial`, `multiple` | `abrir(carpeta)`; `elegidos(rutas)`, `elegido(ruta)` (la primera), `cancelado()` |
| `ElegirCarpeta` (`FolderDialog`) | `titulo`, `carpetaInicial` | `abrir(carpeta)`; `elegida(ruta)`, `cancelado()` |
| `GuardarComo` (`FileDialog` en modo guardar) | `titulo`, `filtros`, `conTodos` (false), `carpetaInicial`, `nombreSugerido`, `sufijo` (la extensión si el usuario no escribe ninguna) | `abrir(carpeta, nombre)`; `elegido(ruta)`, `cancelado()` |

El diálogo de KDE pregunta antes de sobrescribir. `rutas.js` (en el módulo, `import "rutas.js" as Rutas` desde dentro)
convierte: `deUrl`, `aUrl`, `carpetaDe`, `nombreDe`, `filtros(lista, conTodos)`, `lista(urls)`.

### TarjetaError · DialogoError (3.0)

`TarjetaError`: un error presentable — `error` (`{descripcion, causa, recurso, accion, detalle, nivel}`, el mapa de
`Errores`; cada parte también suelta), el icono del nivel (`error` · `aviso` · `informacion`), la descripción como
título, «Causa probable», «Afecta a» (el recurso, con «Mostrar en Dolphin» si es una ruta que existe y «Copiar la
ruta»), «Qué hacer», el detalle técnico desplegable (`detalleAbierto`) y «Copiar todo»; `escritorio`, `conIcono`. Cabe
dentro de una página (el trabajo fallido de una cola).

`DialogoError` (`Kirigami.Dialog`): la cola de `errores` (por omisión `aplicacionStudio.errores`), uno detrás de otro
(«Error (1 de 3)», «Siguiente», «Descartar todos»); se abre solo al llegar un error (`abrirSolo`); al cerrarlo descarta
el que se veía. `VentanaBase` ya trae uno.

### DialogoConfirmacion (3.0)

`Kirigami.Dialog` para las operaciones de riesgo: el icono, el estado («Publicación · no se puede deshacer desde aquí»
en las eliminaciones), las consecuencias redactadas y el botón que dice qué hace («Publicar el sitio»); el foco empieza
en Cancelar. `acciones`, `peticion`; `pedir(peticion, alAceptar)`: sin `alAceptar`, al aceptar llama a
`acciones.confirmar(peticion.nombre)`; señal `aceptada(nombre)`. `VentanaBase` ya trae uno y lo abre con
`acciones.confirmacionPedida`.

### VistaTexto (2.2)

Texto de solo lectura con mensaje de vacío: `texto`; `markdown` (verdadero: `MarkdownText`, fuente del sistema, líneas
ajustadas, los enlaces abren fuera; falso: monoespaciado, sin partir líneas) y `definicion` (la de KSyntaxHighlighting
que resalta el texto plano: «Bash», «Diff», «JSON», «Markdown»…; vacía, sin resaltar; 3.1: con el tema de
KSyntaxHighlighting claro u oscuro según el fondo; si el módulo `org.kde.syntaxhighlighting` falta, texto plano); `ajustarLineas`; `mensajeVacio` · `iconoVacio`; `nombreAccesible`;
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
`cambiado(clave, valor)`; `nombreAccesible`, `mensajeVacio`, `nCampos`, `formulario` (el `Kirigami.FormLayout` de dentro; la raíz es un `ColumnLayout`). Cambiar `campos` vacía los valores. La pestaña
Opciones de Raphi Studio.

### VistaComparacion (3.1)

La diferencia de un archivo lado a lado, como Meld o Sublime Merge (une las copias de Git, Dotfiles y Lliphi):
`diferencia` (lo que da `gui_comun.diferencias.analizar` o `comparar`, como diccionario o como objeto con las mismas
claves: `ruta`, `filas`, `trozos` (lista o número), `anadidas`, `quitadas`, `binario`, `vacia`, `recortado` y, si las
hay, `nuevo`, `izquierda` · `derecha` (qué es cada lado) y `notas`); `accionesTrozo` (`[{clave, texto, icono,
accesible, noEnNuevo}]`: los botones de la cabecera de cada trozo) → señal `trozoPedido(clave, trozo)`;
`seleccionable` (un clic elige una línea cambiada; Ctrl suma, Mayús un rango) con `filasElegidas` (índices de
`filas`), `limpiarSeleccion()` y señal `seleccionCambiada()`; `mensajeVacio`, `nombreAccesible`. Lo quitado y lo
añadido con los fondos semánticos del tema. Git la usa para preparar trozos y líneas sueltas
(`diferencias.parche_de_lineas`), Dotfiles y Lliphi para comparar.

### EditorTexto · BarraBuscarReemplazar (3.1)

`EditorTexto` es un archivo abierto (de LaTeX Studio, que Quarto copió): `controlador` (`gui_comun.editor.
ControladorEditor`), `ruta`, `definicion` (KSyntaxHighlighting, con su tema claro u oscuro según el fondo),
`soloLectura`, `ajustarLineas`, `tamanoLetra` (0: la monoespaciada del tema), `conNumeros`; `completar` (función
`(textoAntes, forzado) → {tipo, prefijo, elementos: [{texto, detalle, insertar, cierre}]}`) y `disparaCompletado`
(`(textoAntes, tecla) → bool`) para un autocompletado propio; `modificado` (compara con el texto leído: abrir no
marca nada), `original`, `lineaActual`, `columnaActual`, `area`. Funciones: `cargar()`, `recargarDesdeDisco()`,
`guardar(forzar)` (→ "" · «externo» · error; solo lo llama la acción del studio), `irALinea(n, columna)`,
`seleccionar(a, b)`, `comentar()` (el comentario del lenguaje), `abrirSugerencias(forzado)`. Señales: `ctrlClic(linea,
columna)` (SyncTeX en LaTeX), `guardado()`. `BarraBuscarReemplazar { editor }` busca y reemplaza en el editor con expresiones
regulares de Python (`controlador.buscar`, `controlador.reemplazar`, posiciones UTF-16): `abrir(reemplazar)`,
`cerrar()`, `siguiente()`, `anterior()`; señal `reemplazados(n)`. Cada reemplazo se deshace con Ctrl+Z.

### VistaPdf (3.1)

Un PDF integrado (de LaTeX Studio; Raphi y Quarto lo necesitaban): `visor` (`gui_comun.visor_pdf.VisorPdf`, obligatorio),
`miniaturas`, `mensajeVacio` · `explicacionVacia`, `barraExtra` (botones propios: `barraExtra: [QQC2.ToolButton {…}]`);
`paginaActual`; `irA(pagina, yPuntos)`; señal `dobleClic(pagina, x, y)` en puntos. Con el módulo `QtQuick.Pdf`
(`qml6-module-qtquick-pdf`), cada página la pinta Qt; sin él (o con `GUI_COMUN_VISOR=pdftoppm`), `pdftoppm` la
renderiza por demanda. Zoom con Ctrl+rueda, ajustar al ancho, recargar conservando la página, abrir con su aplicación
(`studio.escritorio`). El blanco del papel es del documento, no de la interfaz. SyncTeX es de LaTeX: su controlador
hereda de `VisorPdf` (Python) y conecta `dobleClic`; la marca, `visor.marcarRecuadro(pagina, x, y, ancho, alto)`.

### ListaErrores (3.1)

Errores y avisos como errores presentables, en lista (de LaTeX Studio): `modelo` con los roles `nivel` (`error` ·
`aviso` · `tipografia` · `informacion`), `titulo`, `mensaje`, `causa`, `accion`, `detalle`, `ubicacion`, `linea` (los
que falten, vacíos); cada fila con su título, «archivo:línea», «Causa probable», «Qué hacer», el mensaje original y el
detalle técnico desplegable; `cabecera` (lo que el studio ponga arriba: sus filtros), `actual`, `mensajeVacio` ·
`explicacionVacia` · `iconoVacio`, `nombreAccesible`; señal `elegido(indice)` (clic o Intro: ir a la línea). Hermana de
`ListaDiagnosticos` (2.3), que solo tiene mensaje, archivo y línea.

### PasosEscritura · LineaPasos (3.1)

`PasosEscritura`: la barra de los seis pasos de una escritura (Plan · Afectados · Conflictos · Ejecutar · Verificar ·
Informe; Filesystem y Lliphi la tenían igual): `pasos` (los seis por omisión), `alcanzado` (1…6, el último hecho),
`actual` (0…5, el que se muestra), `cuentas` (`gui_comun.pasos.cuentas`), `bloqueado` (un conflicto que bloquea marca
«Ejecutar»); señal `elegido(paso)`; en poco ancho cada paso se encoge y su texto se corta. `LineaPasos`: los pasos de
un proceso que ocurre fuera, como línea de tiempo vertical (la puerta de escritura de Biblioteca, de donde viene; las
fases de Huella): `pasos` (`[{titulo, explicacion, estado, detalle}]`, estado ∈ `gui_comun.pasos.ESTADOS`), `titulo`,
`resumen`, `elegible` y `actual`; señal `elegido(indice)`.

### GraficoXY · PaletaCategorica (3.1)

`GraficoXY` (de Simuladores Studio) dibuja con Canvas: `datos` (`{lineas: [{nombre, rol, x, y}], barras:
{categorias, valores, roles}, puntos, equilibrio, verticales, horizontales, limites, etiquetaX, etiquetaY, anotacion}`:
cada línea con su propio x, sin remuestrear como `Grafico`), `base` (otro igual, punteado y atenuado debajo),
`limites`, `marcaX`, `invalido` · `nivelInvalido` · `motivoInvalido` (la marca de un resultado que no se presenta como
bueno), `nombreDatos` · `nombreBase`, `mensajeVacio`, `nombreAccesible`; el valor bajo el cursor y la leyenda.
`PaletaCategorica` (un `QtObject`): `rol(nombre)` pinta un rol con significado (`azul`, `rojo`, `verde`, `dorado`,
`morado`, `cian`, `gris`, `texto`; de `gui_comun.paleta.rol`) con los colores semánticos del tema (azul, morado y cian
derivados si el tema no los trae), e `indice(i)` da categorías sin significado (el acento girado en séptimos).

### EtiquetaNivel (3.1)

Una etiqueta redondeada con el color semántico de `nivel` (`positivo`, `neutro`, `negativo`, `activo`, `inactivo`) y un
`icono` opcional: «instalado», «conflicto», «local».

### MenuAcciones · BotonAccion

`MenuAcciones { acciones; elementos; titulo; conAtajos }`: un `Menu` construido desde `[{tipo: "accion", nombre} |
{tipo: "separador"} | {tipo: "menu", titulo, elementos}]` (lo que produce `Acciones.definir_menus`); con
`conAtajos: false` para los contextuales. `BotonAccion { accion; conTexto }`: un `ToolButton` ligado a una `Accion`.

## 2. Python

| módulo | API |
|---|---|
| `nucleo.Aplicacion(app_id, nombre, version=, organizacion=, idioma="es", nombre_ajustes=)` | 3.0: una `QApplication` (el diálogo de archivos de KDE). `.exponer(nombre, objeto)` (también `studio.<nombre>`), `.cargar(qml)`, `.ejecutar(qml, humo=False)`, `.ventana()`, `.capturar(png, espera_ms)`, `.cerrar()`, `.traducciones`, `.mensaje_de_fallo()`; 3.0: `.errores`, `.escritorio` (expuestos con esos nombres), `.error(descripcion, causa, recurso, accion, detalle, nivel)`; `aplicacionStudio` en QML (appId, nombre, version, binding, versionGuiComun, versionQt; 3.0: errores, escritorio) |
| `escritorio.Escritorio(errores, lanzar=, abrir_url=, buscar=)` (3.0) | `abrirConAplicacion(ruta)` (también una dirección web), `mostrarEnDolphin(ruta)`, `abrirCarpeta(ruta)` → `bool` (falso y error presentado si no existe o no arranca); `rutaDeUrl(url)`, `urlDeRuta(ruta)`, `existe(ruta)`, `hayDolphin`; `ruta_local(texto)` |
| `errores.Errores(consola)` (3.0) | `.presentar(descripcion, causa=, recurso=, accion=, detalle=, nivel=)` → dict; `presentarTexto(5 textos)` y `presentarMapa({...})` desde QML; `.desde_excepcion(exc, descripcion, recurso=, accion=)`; `.desde_proceso(descripcion, argv, codigo, salida)`; la cola: `actual`, `cuantos`, `omitidos` (más de 20 seguidos), `descartar()`, `limpiar()`, `pendientes()`; señales `presentado(mapa)`, `cambiado`. `explicar(exc)` y `explicar_codigo(codigo, salida)` → (causa, acción); `predeterminado()` (el de la aplicación) |
| `acciones.Acciones` | `.registrar(nombre, texto, icono, atajo, grupo, habilitada=, marcable=, marcada=, descripcion=, al_disparar=, operacion=, consecuencias=, confirmar=)` → `Accion` (3.0: `operacion` ∈ `OPERACIONES`; instalación, publicación y eliminación exigen `consecuencias` y siempre confirman); `.estandar(nombre_app, paneles=True, atajos=None)`; 3.0: `.fijar_atajo(nombre, atajo)`, `.conflictos()`, `.peticion(nombre)`, `.confirmar(nombre)`, señal `confirmacionPedida(mapa)`; `.definir_menus([...])`; `.definir_barra([...])`; `.anadir_fuente(fn)`; `.accion(nombre)`, `.existe`, `.ejecutar`, `.habilitar`, `.marcar`, `.buscar(texto)`; señal `disparada(nombre, marcada)`; es modelo de lista |
| `acciones.Accion` | propiedades `nombre`, `texto`, `textoPlano`, `icono`, `atajo`, `atajoTexto`, `grupo`, `habilitada`, `marcable`, `marcada`, `visible`, `descripcion`; 3.0: `operacion`, `operacionTexto`, `requiereConfirmacion`, `consecuencias`; `.conectar(fn)`, `.disparar()` (si confirma, solo pide), `.confirmar()`, `.fijar_atajo(a)`; señales `disparada(marcada)`, `confirmacionPedida`, `atajoCambiado` |
| `tareas.Tareas(consola, errores=)` | 3.0 en `.funcion` y `.proceso`: `operacion=`, `verificar=` (`f(valor)` → `bool` o `(bool, texto)`, tras el éxito), `error=` (`False` o un dict que redacta); al fallar presenta un error; propiedades `operacion`, `operacionTexto`; señales `verificada(nombre, ok, detalle)`, `resultado(mapa)`; cancelar termina en `("warn", "cancelada")`. `.funcion(nombre, fn, *args, al_terminar=, al_fallar=, **kw)`, `.proceso(nombre, argv, cwd=, al_terminar=, progreso_de=, entrada=, entorno=)` (el proceso en su propio grupo; 2.3: `progreso_de(texto)` → `(porcentaje, elemento)` o `None` por cada línea de la salida; 2.5: `entrada`, el texto que se escribe en su entrada estándar y se cierra, sin ella cerrada; `entorno`, variables añadidas), `.cancelar()` (a la función, su `cancel_cb`; al proceso, `SIGTERM` al grupo entero); `activa`, `nombre`, `progreso`, `elemento`, `cuantas`; señales `iniciada`, `cambiada`, `linea`, `terminada(nivel, nombre, detalle)` |
| `consola.Consola` | `.salida`, `.registro` (`ModeloConsola`: `escribir`, `limpiar`, `texto`, `textoConHora`, `lineas`), `.escribir(texto, nivel)`, `.registrar(nivel, texto)`, `.log(nivel, texto)`; señal `escrita` |
| `modelos.ModeloLista(roles, filas)` | `.poner`, `.anadir`, `.quitar`, `.actualizar`, `.fila(i)`, `.todas()` (3.1: también desde QML), `filas` |
| `modelos.ModeloFiltrado(origen)` | `.ordenar(columna, descendente)`, `.filtrar(texto)`, `.aceptar_con(criterio)`, `.filaOrigen`, `.filaVisible`, `filas`, `columnaOrden`, `descendente` |
| `modelos.ModeloTabla(columnas, filas)` (2.1) | `columnas` = [(título, clave)]; filas de dict con esas claves y, opcionales, `nivel`, `icono` (texto o {clave: icono}), `habilitado`, `crudo` ({clave: valor} para ordenar); `.poner`, `.anadir`, `.quitar`, `.actualizar`, `.fila(i)`, `.todas()`, `.clave(c)`, `filas`, `columnas` |
| `modelos.ModeloArbol(columnas, raices)` (2.1) | nodos de dict: `valores` (uno por columna), `nivel`, `icono` (texto o {columna: icono}), `habilitado`, `hijos` (lista o función `f(nodo)` que se consulta al expandir) y lo propio; `.poner`, `.recargar(indice)`, `.datos(indice)`, `.ruta(indice)`, `.todas(indice)`, `filas`; 3.1: `.ordenar(columna, descendente)` (cada nivel; `grupo` va primero, p. ej. carpetas antes que archivos; `orden`, una lista por columna, da el valor crudo), `columnaOrden`, `descendente` |
| `i18n.instalar(motor, idioma)` | el objeto de contexto con `i18n`, `i18nc`, `i18nd`, `i18ndc`, `i18np`, `i18ncp`, `i18ndp`, `i18ndcp` y las `xi18n*` (gettext sobre `/usr/share/locale`) |
| `qt` | `BINDING`, los nombres de QtCore/QtGui/QtQml con la API de PySide6, `cast`, `rol`, `roles`, `version_qt` |
| `galeria.esquema.entorno_con_esquema(colors)` | el entorno de un proceso con otro esquema de color de KDE (kdeglobals temporal); 3.1: y el tema de Kvantum del mismo nombre si existe (con `QApplication` los controles los pinta Kvantum) |
| `diferencias` (3.1) | `analizar(texto_diff)` y `comparar(antes, despues, ruta=, izquierda=, derecha=)` → `{cabecera, trozos, filas, anadidas, quitadas, binario, vacia, recortado}` para `VistaComparacion`; `parche_de_trozo(d, i)` y `parche_de_lineas(d, filas, inverso=False)` para `git apply --cached [--recount] [-R]` |
| `editor.ControladorEditor(consola=None, definiciones=, definicion=)` (3.1) | el de `EditorTexto`: `abiertos` (modelo: ruta, nombre, carpeta, modificado, definicion, solo_lectura), `abrir`, `cerrar`, `cerrarTodos`, `fijarActual`, `actual`, `indiceActual`, `leer`, `guardar(ruta, texto, forzar)`, `guardarComo`, `aceptarDisco`, `cambioEnDisco`, `marcarModificado`, `hayModificados`, `modificados`, `buscar`, `reemplazar`, `definicionDe`, `soltar()` (al cerrar); señales `cambioExterno(ruta)`, `guardadoArchivo`, `aviso`. Sueltas: `definicion_de(ruta, mapa)`, `buscar`, `reemplazos`, `DEFINICIONES`, `COMENTARIOS` |
| `visor_pdf.VisorPdf(cache, variable_motor=)` (3.1) | el de `VistaPdf`: `abrir(pdf)`, `recargar()`, `cerrar()`, `paginas` (modelo), `motor` (`qtpdf` · `pdftoppm`), `pdf`, `pdfUrl`, `revision`, `total`, `anchoMaximo`, `zoom`, `ajustarAncho`, `escala`, `acercar`, `alejar`, `ajustarA(ancho)`, `pedir`, `pedirMiniatura`, `marcarRecuadro(pagina, x, y, ancho, alto)`, `apagar()`; señales `irAPagina`, `marcar`, `aviso`. Sueltas: `paginas(pdf)`, `renderizar(pdf, pagina, ppp, cache)`, `podar(cache, limite, conservar)`, `hay_qtpdf()` |
| `miniaturas.ProveedorMiniaturas(carpeta, anchos=, tope_mb=, claves_son_rutas=)` (3.1) | un `QQuickImageProvider` asíncrono para `image://<nombre>/<clave>[/<tamaño>]` (con `claves_son_rutas`, `image://<nombre>/<ruta>[@<tamaño>]`): lee el origen en solo lectura escalado al leer y cachea en JPEG con poda por tope; `.fijar_rutas({clave: ruta})`; sueltas `miniatura(origen, carpeta, clave, ancho)` y `podar(carpeta, tope)` (de las portadas de Biblioteca) |
| `pasos` (3.1) | `Plan(tipo, titulo, carpeta, descripcion, afectados, conflictos, interno)` con `bloqueado` y `como_dict()`; `cuentas(plan, resultado, verificado)`, `verificacion(filas)`, `informe(plan, resultado, verificado, herramienta=)` (Markdown), `nombre_informe(plan)`; para `LineaPasos`: `linea([(clave, titulo, explicacion)])`, `fijar(pasos, clave, estado, detalle)`, `ESTADOS`, `NIVEL` |
| `paleta` (3.1) | `rol(color, orden)` y `roles(colores)`: un color de matplotlib (hex, nombre, `C0`, `tab:*`) → `azul` · `rojo` · `verde` · `dorado` · `morado` · `cian` · `gris` · `texto` |
| `qt` (3.1) | además, `QImage`, `QImageReader`, `QQuickImageProvider`, `QQmlImageProviderBase` |

## 3. Lo que falta (3.x)

- `org.kde.kirigamiaddons.settings` cuando Kubuntu lo empaquete (hoy `DialogoAjustes` reproduce su anatomía).
- (Hecho en 3.1: el orden por cabecera de `ArbolDatos`, en el propio `ModeloArbol`, sin `org.kde.kitemmodels`.)
- La vista previa con QtWebEngine de Quarto (`VistaWeb`) y la de imágenes, audio y vídeo de Raphi (`VistaPrevia`,
  `ReproductorMedios`): candidatas para cuando un segundo studio las pida.
