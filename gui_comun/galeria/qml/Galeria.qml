// Galeria.qml — la galería de GuiComun: la VentanaStudio real con cada componente en una página, datos de muestra.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.formcard as FormCard
import GuiComun

VentanaStudio {
    id: ventana
    title: "Galería de GuiComun"
    acciones: studio.acciones
    tareas: studio.tareas
    consola: studio.consola
    descripcion: "La galería de componentes del marco común de la familia de studios: cada componente con datos de muestra, en claro y oscuro según el esquema del escritorio."
    autor: "Edison Achalma"
    sitio: "https://github.com/achalmed/gui-comun"
    resumen: repos.filas + " repositorios · 6 sincronizados · 2 con cambios · 1 por traer · 1 desactivado"
    contexto: tabla.filaActual >= 0 ? repos.data(repos.index(tabla.filaActual, 0)) + " · " + repos.data(repos.index(tabla.filaActual, 1)) : ""
    mostrarInferior: true

    readonly property var paginas: [
        { nombre: "espacio", texto: "Espacio de trabajo", icono: "window" },
        { nombre: "tabla", texto: "TablaDatos", icono: "view-list-details" },
        { nombre: "arbol", texto: "ArbolDatos", icono: "view-list-tree" },
        { nombre: "navegacion", texto: "PanelNavegacion", icono: "view-sidetree" },
        { nombre: "detalles", texto: "PanelDetalles", icono: "view-right-new" },
        { nombre: "inferior", texto: "PanelInferior", icono: "utilities-terminal" },
        { nombre: "mensajes", texto: "Mensajes", icono: "dialog-information" },
        { nombre: "acciones", texto: "Acciones y menús", icono: "configure-shortcuts" },
        { nombre: "formulario", texto: "Formularios (Addons)", icono: "document-edit" },
        { nombre: "texto", texto: "VistaTexto", icono: "text-x-generic" },
        { nombre: "diagnosticos", texto: "ListaDiagnosticos", icono: "data-warning" },
        { nombre: "grafico", texto: "Grafico", icono: "office-chart-line" },
        { nombre: "tema", texto: "Tema y unidades", icono: "preferences-desktop-color" }
    ]
    property string paginaActual: paginaInicial || "espacio"
    readonly property int indicePagina: paginas.findIndex(p => p.nombre === paginaActual)

    Connections {
        target: studio.acciones
        function onDisparada(nombre, marcada) {
            if (nombre === "mensajes.aviso") ventana.mensajes.mostrar("yachay: la rama ha divergido de origin; hay que traer y enviar.", "aviso", [{ texto: "Resolver…", icono: "dialog-warning" }])
            else if (nombre === "mensajes.error") ventana.mensajes.mostrar("No se pudo contactar con github.com (¿sin conexión?).", "error")
            else if (nombre === "editar.buscar") filtro.forceActiveFocus()
            else if (nombre === "editar.todo") tabla.seleccionarTodo()
            else if (nombre === "ver.rama") tabla.mostrarColumna(1, marcada)
            else if (nombre === "ver.ultimo") tabla.mostrarColumna(6, marcada)
        }
    }

    herramientasExtra: [
        Kirigami.SearchField {
            id: filtro
            Layout.preferredWidth: Kirigami.Units.gridUnit * 14
            placeholderText: "Filtrar (Ctrl+F)"
            onTextChanged: repos.filtrar(text)
        }
    ]

    dialogoAjustes: DialogoAjustes {
        title: "Configurar la galería"
        modulos: [
            { titulo: "General", icono: "configure", pagina: paginaGeneral },
            { titulo: "Apariencia", icono: "preferences-desktop-theme", pagina: paginaApariencia }
        ]
    }
    Component {
        id: paginaGeneral
        ColumnLayout {
            FormCard.FormHeader { title: "Repositorios" }
            FormCard.FormCard {
                FormCard.FormTextFieldDelegate { label: "Directorio base"; text: "~/Documentos" }
                FormCard.FormCheckDelegate { text: "Traer antes de analizar (git fetch)"; checked: true }
                FormCard.FormSpinBoxDelegate { label: "Días de actividad reciente"; from: 1; to: 90; value: 7 }
            }
        }
    }
    Component {
        id: paginaApariencia
        ColumnLayout {
            FormCard.FormHeader { title: "Tabla" }
            FormCard.FormCard {
                FormCard.FormCheckDelegate { text: "Filas alternas"; checked: true }
                FormCard.FormComboBoxDelegate { text: "Agrupar por"; model: ["Nada", "Grupo", "Estado"]; currentIndex: 1 }
            }
        }
    }

    navegacion: PanelNavegacion {
        actual: ventana.paginaActual
        secciones: [
            { titulo: "Galería", filas: ventana.paginas.map(p => ({ nombre: p.nombre, texto: p.texto, icono: p.icono })) },
            { titulo: "Estado (muestra)", filas: [
                { nombre: "f.todos", texto: "Todos", icono: "folder-git", contador: 10 },
                { nombre: "f.cambios", texto: "Con cambios", icono: "document-edit", contador: 2 },
                { nombre: "f.enviar", texto: "Sin enviar", icono: "upload-media", contador: 2 },
                { nombre: "f.traer", texto: "Por traer", icono: "download", contador: 2 } ] }
        ]
        onElegida: nombre => { if (!nombre.startsWith("f.")) ventana.paginaActual = nombre; else actual = nombre }
    }

    centro: StackLayout {
        currentIndex: Math.max(0, ventana.indicePagina)

        // 1. espacio de trabajo: la tabla real
        TablaDatos {
            id: tabla
            modelo: repos
            mensajeVacio: "Ningún repositorio coincide con el filtro"
            columnas: [
                { ancho: 0, minimo: 12, conIcono: true },
                { ancho: 9, secundaria: true },
                { ancho: 12, semantica: true, conIcono: true },
                { ancho: 8 },
                { ancho: 2.5, alinear: "centro", mono: true },
                { ancho: 2.5, alinear: "centro", mono: true },
                { ancho: 0, minimo: 10, secundaria: true, estrecho: true },
                { ancho: 6, secundaria: true, estrecho: true }
            ]
            onOrdenar: (columna, descendente) => repos.ordenar(columna, descendente)
            onActivada: fila => ventana.mostrarDetalles = true
            menuContextual: MenuAcciones {
                acciones: acciones
                conAtajos: false
                elementos: [{ tipo: "accion", nombre: "repo.obtener" }, { tipo: "accion", nombre: "repo.enviar" }, { tipo: "accion", nombre: "repo.sincronizar" }, { tipo: "separador" }, { tipo: "accion", nombre: "repo.confirmar" }]
            }
        }

        // 2. TablaDatos: la misma, explicada
        Pagina {
            titulo: "TablaDatos"
            texto: "TableView + HorizontalHeaderView sobre un QAbstractTableModel (o un ModeloFiltrado). Clic en la cabecera ordena; arrastre entre cabeceras redimensiona; columnas opcionales (`visible`) y que se ocultan al estrechar (`estrecho`); filas alternas; selección múltiple con Ctrl y Mayús; menú contextual; doble clic e Intro activan; Supr avisa. Color semántico solo en la columna `semantica` (rol `nivel`)."
            TablaDatos {
                Layout.fillWidth: true
                Layout.preferredHeight: Kirigami.Units.gridUnit * 14
                modelo: repos
                columnas: tabla.columnas
                onOrdenar: (columna, descendente) => repos.ordenar(columna, descendente)
            }
        }

        // 3. ArbolDatos
        Pagina {
            titulo: "ArbolDatos"
            texto: "TreeView de Qt Quick con la misma anatomía y roles que TablaDatos (display, nivel, icono, habilitado): flecha de expandir en la primera columna, ← → por teclado, selección por filas, menú contextual, doble clic e Intro. El modelo es un ModeloArbol (nodos de diccionario; los hijos pueden cargarse al expandir: el tercer conjunto) o cualquier QAbstractItemModel; `raiz` acota la vista a un índice."
            ArbolDatos {
                Layout.fillWidth: true
                Layout.preferredHeight: Kirigami.Units.gridUnit * 14
                modelo: arbol
                expandirAlCargar: 1
                columnas: [
                    { ancho: 0, minimo: 14, conIcono: true, semantica: true },
                    { ancho: 5, mono: true, alinear: "derecha", secundaria: true },
                    { ancho: 5, alinear: "derecha" },
                    { ancho: 5, alinear: "derecha" },
                    { ancho: 5, alinear: "derecha", estrecho: true }
                ]
                menuContextual: MenuAcciones {
                    acciones: acciones
                    conAtajos: false
                    elementos: [{ tipo: "accion", nombre: "editar.todo" }]
                }
            }
        }

        // 4. PanelNavegacion
        Pagina {
            titulo: "PanelNavegacion"
            texto: "Secciones con Kirigami.ListSectionHeader, filas con icono, texto y contador tenue; plegado, solo iconos con su ayuda emergente (como «Lugares» de Dolphin). Abajo: la misma navegación plegada y sin plegar."
            RowLayout {
                spacing: Kirigami.Units.largeSpacing
                PanelNavegacion { Layout.preferredHeight: Kirigami.Units.gridUnit * 14; secciones: ventana.navegacion.secciones; actual: "f.cambios" }
                PanelNavegacion { Layout.preferredHeight: Kirigami.Units.gridUnit * 14; secciones: ventana.navegacion.secciones; actual: "f.cambios"; plegado: true }
            }
        }

        // 4. PanelDetalles
        Pagina {
            titulo: "PanelDetalles"
            texto: "Cabecera discreta (icono, Heading de nivel 4, botones de icono, ruta en smallFont) y pestañas; cada hijo es una página. Resumen en Kirigami.FormLayout; Cambios con el campo de confirmación al pie."
            PanelDetalles {
                Layout.fillWidth: true
                Layout.preferredHeight: Kirigami.Units.gridUnit * 16
                titulo: "git-studio"
                subtitulo: "~/Documentos/git-studio"
                icono: "folder-git"
                accionesCabecera: [acciones.accion("repo.obtener"), acciones.accion("repo.enviar")]
                pestanas: [{ titulo: "Resumen" }, { titulo: "Cambios", contador: cambios.filas }, { titulo: "Historial" }]
                pestanaActual: 1
                Kirigami.FormLayout {
                    QQC2.Label { Kirigami.FormData.label: "Rama:"; text: "wip/2026-11-01-qml" }
                    QQC2.Label { Kirigami.FormData.label: "Estado:"; text: "Cambios sin confirmar"; color: Kirigami.Theme.neutralTextColor }
                    QQC2.Label { Kirigami.FormData.label: "Último commit:"; text: "c9ec7fe · hace 10 min" }
                }
                ListaCambios {}
                ListaHistorial {}
            }
        }

        // 5. PanelInferior
        Pagina {
            titulo: "PanelInferior"
            texto: "Pestañas Salida y Registro sobre gui_comun.consola.Consola; fuente monoespaciada del sistema y resaltado de KSyntaxHighlighting; botones de limpiar y cerrar. En la ventana vive abajo (F4) y se abre solo cuando empieza una tarea."
            PanelInferior { Layout.fillWidth: true; Layout.preferredHeight: Kirigami.Units.gridUnit * 10; consola: studio.consola }
        }

        // 6. Mensajes
        Pagina {
            titulo: "Mensajes"
            texto: "Kirigami.InlineMessage solo para lo que exige atención; se cierran. Un resumen va a la barra de estado, nunca aquí."
            Mensajes {
                id: muestraMensajes
                Layout.fillWidth: true
                Component.onCompleted: {
                    mostrar("Información: el análisis usa la caché de la última vez; F5 lo refresca.", "informacion")
                    mostrar("Sincronización terminada sin errores.", "positivo")
                    mostrar("yachay: la rama ha divergido de origin.", "aviso", [{ texto: "Resolver conflictos…", icono: "dialog-warning" }])
                    mostrar("No se pudo contactar con github.com.", "error")
                }
            }
        }

        // 7. Acciones
        Pagina {
            titulo: "Acciones y menús"
            texto: "Cada operación existe una sola vez en gui_comun.acciones y aparece en el menú, la barra, el menú contextual y la paleta (Ctrl+Alt+I · Ctrl+K) desde el mismo objeto; el atajo se registra una vez. Abajo, el registro entero."
            ListView {
                Layout.fillWidth: true
                Layout.preferredHeight: Kirigami.Units.gridUnit * 14
                clip: true
                model: acciones
                delegate: QQC2.ItemDelegate {
                    required property var model
                    width: ListView.view.width
                    text: model.texto
                    icon.name: model.icono
                    enabled: model.habilitada
                    onClicked: acciones.ejecutar(model.nombre)
                    contentItem: RowLayout {
                        Kirigami.Icon { source: model.icono || "system-run"; implicitWidth: Kirigami.Units.iconSizes.small; implicitHeight: implicitWidth }
                        QQC2.Label { text: model.texto; Layout.fillWidth: true }
                        QQC2.Label { text: model.grupo; font: Kirigami.Theme.smallFont; color: Kirigami.Theme.disabledTextColor }
                        QQC2.Label { text: model.atajo; font: Kirigami.Theme.smallFont; color: Kirigami.Theme.disabledTextColor }
                        QQC2.Label { text: model.nombre; font: Kirigami.Theme.fixedWidthFont; color: Kirigami.Theme.disabledTextColor }
                    }
                }
            }
        }

        // 8. Formularios
        Pagina {
            titulo: "Formularios (Kirigami Addons FormCard)"
            texto: "Los diálogos y ajustes de los studios usan FormCard: campos, casillas, selectores y botones con la anatomía de las Preferencias del sistema."
            FormCard.FormCard {
                Layout.fillWidth: true
                FormCard.FormTextFieldDelegate { label: "Usuario de GitHub"; text: "achalmed" }
                FormCard.FormComboBoxDelegate { text: "Protocolo"; model: ["ssh", "https"] }
                FormCard.FormCheckDelegate { text: "Registrar los clonados en repos-config.yml"; checked: true }
                FormCard.FormButtonDelegate { text: "Carpeta destino"; description: "~/Documentos"; icon.name: "folder" }
            }
            QQC2.Label { text: "CampoRuta: un campo de ruta con su botón de elegir (FolderDialog o FileDialog); Intro o el diálogo emiten `aceptada`."; wrapMode: Text.WordWrap; Layout.fillWidth: true }
            CampoRuta { Layout.fillWidth: true; texto: "~/Documentos"; nombreAccesible: "Carpeta de trabajo" }
            CampoRuta { Layout.fillWidth: true; carpeta: false; texto: "~/Documentos/web/_metadata.yml"; filtros: ["YAML (*.yml)"]; nombreAccesible: "Archivo de referencia" }
        }

        // 9. VistaTexto
        Pagina {
            titulo: "VistaTexto"
            texto: "Texto de solo lectura con mensaje de vacío: un documento en Markdown (fuente del sistema, líneas ajustadas, los enlaces abren fuera) o texto monoespaciado con el resaltado de KSyntaxHighlighting que se pida (`definicion`). El centro de una vista de documento o la pestaña de lectura de un panel de detalles."
            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: Kirigami.Units.gridUnit * 14
                spacing: Kirigami.Units.largeSpacing
                VistaTexto {
                    Layout.fillWidth: true; Layout.fillHeight: true
                    markdown: true
                    texto: "# HALLAZGOS\n\nCada `[+]` es una **hipótesis** hasta verificarla (manual §26).\n\n| hallazgo | severidad | estado |\n|---|---|---|\n| perfil antiguo en un foro | 🟡 media | verificado |\n| correo en una brecha de 2019 | 🔴 alta | contraseña rotada |\n\n- <https://haveibeenpwned.com/>"
                    nombreAccesible: "Documento de muestra"
                }
                VistaTexto {
                    Layout.fillWidth: true; Layout.fillHeight: true
                    definicion: "Bash"
                    texto: "#!/usr/bin/env bash\n# fase12-usuario-correo.sh — dónde existen los usuarios\nset -euo pipefail\nfor u in \"${USUARIOS[@]}\"; do\n    sherlock \"$u\" --timeout 10\ndone\necho \"Listo → $SALIDA\""
                    nombreAccesible: "Texto de muestra"
                }
                VistaTexto {
                    Layout.fillWidth: true; Layout.fillHeight: true
                    mensajeVacio: "Selecciona un archivo para leerlo"
                    iconoVacio: "document-preview"
                }
            }
        }

        // 10. ListaDiagnosticos
        Pagina {
            titulo: "ListaDiagnosticos"
            texto: "La lista de errores y avisos de una herramienta: nivel (icono y color semántico: error, aviso, información, tipografía), mensaje en varias líneas, archivo y línea; Intro o doble clic «va a» (`activada(fila)`); menú contextual; mensaje de vacío. Para la pestaña Problemas de un panel de detalles, donde una tabla no deja leer el mensaje entero."
            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: Kirigami.Units.gridUnit * 14
                spacing: Kirigami.Units.largeSpacing
                ListaDiagnosticos {
                    Layout.fillWidth: true; Layout.fillHeight: true
                    modelo: diagnosticos
                    nombreAccesible: "Problemas de muestra"
                    onActivada: fila => ventana.mensajes.mostrar("Ir a " + diagnosticos.fila(fila).archivo + ", línea " + diagnosticos.fila(fila).linea, "informacion")
                }
                ListaDiagnosticos {
                    Layout.preferredWidth: Kirigami.Units.gridUnit * 16; Layout.fillHeight: true
                    mensajeVacio: "Sin errores ni avisos"
                }
            }
        }

        // 11. Grafico
        Pagina {
            titulo: "Grafico"
            texto: "Un gráfico de líneas o de barras sobre org.kde.quickcharts: las series sobre una rejilla común de x, las etiquetas de los ejes, la rejilla, la leyenda, los puntos marcados, el equilibrio, las marcas y una anotación. Los colores de las series salen de la paleta de QuickCharts sobre el acento de Kirigami.Theme. Sin el módulo, muestra la imagen alternativa (un PNG) o el mensaje de vacío. La pestaña Resultados de Simuladores Studio."
            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: Kirigami.Units.gridUnit * 16
                spacing: Kirigami.Units.largeSpacing
                Grafico {
                    Layout.fillWidth: true; Layout.fillHeight: true
                    series: [{ nombre: "IS", y: [10, 7.5, 5, 2.5, 0] }, { nombre: "LM", y: [0, 2.5, 5, 7.5, 10] }]
                    etiquetasX: ["0", "250", "500", "750", "1 000"]
                    xMinimo: 0; xMaximo: 1000; yMinimo: 0; yMaximo: 10
                    equilibrio: ({ x: 500, y: 5, etiqueta: "E" })
                    marcas: [{ x: 500, etiqueta: "Y*" }]
                    etiquetaX: "Producto (Y)"; etiquetaY: "Tasa de interés (r)"; anotacion: "Y* = 500 · r* = 5,00"
                    nombreAccesible: "IS-LM de muestra"
                }
                Grafico {
                    Layout.preferredWidth: Kirigami.Units.gridUnit * 18; Layout.fillHeight: true
                    barras: ({ categorias: ["S", "T", "M", "I", "G", "X"], valores: [120, 90, 60, 200, 150, 250] })
                    yMinimo: 0; yMaximo: 275
                    etiquetaY: "Flujo (u. m.)"; anotacion: "filtraciones = inyecciones"
                    nombreAccesible: "Flujo circular de muestra"
                }
                Grafico {
                    Layout.preferredWidth: Kirigami.Units.gridUnit * 12; Layout.fillHeight: true
                    mensajeVacio: "Corre un escenario (F5) para ver sus curvas"
                }
            }
        }

        // 12. Tema
        Pagina {
            titulo: "Tema y unidades"
            texto: "Cero colores propios: todo sale de Kirigami.Theme (el esquema del usuario) y Kirigami.Units."
            Flow {
                Layout.fillWidth: true
                spacing: Kirigami.Units.largeSpacing
                Repeater {
                    model: [
                        { n: "textColor", c: Kirigami.Theme.textColor }, { n: "disabledTextColor", c: Kirigami.Theme.disabledTextColor },
                        { n: "highlightColor", c: Kirigami.Theme.highlightColor }, { n: "positiveTextColor", c: Kirigami.Theme.positiveTextColor },
                        { n: "neutralTextColor", c: Kirigami.Theme.neutralTextColor }, { n: "negativeTextColor", c: Kirigami.Theme.negativeTextColor },
                        { n: "activeTextColor", c: Kirigami.Theme.activeTextColor }, { n: "linkColor", c: Kirigami.Theme.linkColor },
                        { n: "backgroundColor", c: Kirigami.Theme.backgroundColor }, { n: "alternateBackgroundColor", c: Kirigami.Theme.alternateBackgroundColor }
                    ]
                    delegate: ColumnLayout {
                        required property var modelData
                        Rectangle { width: Kirigami.Units.gridUnit * 4; height: Kirigami.Units.gridUnit * 2; color: modelData.c; border.color: Kirigami.Theme.disabledTextColor; radius: Kirigami.Units.cornerRadius }
                        QQC2.Label { text: modelData.n; font: Kirigami.Theme.smallFont }
                    }
                }
            }
            Kirigami.FormLayout {
                QQC2.Label { Kirigami.FormData.label: "defaultFont:"; text: Kirigami.Theme.defaultFont.family + " " + Kirigami.Theme.defaultFont.pointSize }
                QQC2.Label { Kirigami.FormData.label: "smallFont:"; text: Kirigami.Theme.smallFont.family + " " + Kirigami.Theme.smallFont.pointSize; font: Kirigami.Theme.smallFont }
                QQC2.Label { Kirigami.FormData.label: "fixedWidthFont:"; text: Kirigami.Theme.fixedWidthFont.family; font: Kirigami.Theme.fixedWidthFont }
                QQC2.Label { Kirigami.FormData.label: "gridUnit:"; text: Kirigami.Units.gridUnit + " px · smallSpacing " + Kirigami.Units.smallSpacing + " · largeSpacing " + Kirigami.Units.largeSpacing }
                QQC2.Label { Kirigami.FormData.label: "iconSizes:"; text: Kirigami.Units.iconSizes.small + " · " + Kirigami.Units.iconSizes.smallMedium + " · " + Kirigami.Units.iconSizes.medium + " · " + Kirigami.Units.iconSizes.large }
            }
        }
    }

    detalles: PanelDetalles {
        titulo: tabla.filaActual >= 0 ? repos.data(repos.index(tabla.filaActual, 0)) : ""
        subtitulo: titulo ? "~/Documentos/" + titulo : ""
        icono: "folder-git"
        accionesCabecera: [acciones.accion("repo.obtener"), acciones.accion("repo.enviar")]
        pestanas: [{ titulo: "Resumen" }, { titulo: "Cambios", contador: cambios.filas }, { titulo: "Historial" }, { titulo: "Ramas" }]
        pestanaActual: 1
        mensajeVacio: "Selecciona un repositorio para ver sus detalles"
        Kirigami.FormLayout {
            Layout.margins: Kirigami.Units.largeSpacing
            QQC2.Label { Kirigami.FormData.label: "Rama:"; text: tabla.filaActual >= 0 ? repos.data(repos.index(tabla.filaActual, 1)) : "" }
            QQC2.Label { Kirigami.FormData.label: "Estado:"; text: tabla.filaActual >= 0 ? repos.data(repos.index(tabla.filaActual, 2)) : "" }
            QQC2.Label { Kirigami.FormData.label: "Último commit:"; text: tabla.filaActual >= 0 ? repos.data(repos.index(tabla.filaActual, 6)) : "" }
        }
        ListaCambios {}
        ListaHistorial {}
        Kirigami.PlaceholderMessage { text: "Ramas y etiquetas"; explanation: "main · wip/2026-11-01-qml · 2 etiquetas"; icon.name: "vcs-branch" }
    }

    inferior: PanelInferior { consola: studio.consola }

    // ---- piezas de la galería ----
    component Pagina: QQC2.ScrollView {
        id: pagina
        property string titulo
        property string texto
        default property alias contenido: cuerpo.data
        contentWidth: availableWidth
        ColumnLayout {
            id: cuerpo
            width: pagina.availableWidth - Kirigami.Units.largeSpacing * 2
            x: Kirigami.Units.largeSpacing
            y: Kirigami.Units.largeSpacing
            spacing: Kirigami.Units.largeSpacing
            Kirigami.Heading { level: 2; text: pagina.titulo }
            QQC2.Label { text: pagina.texto; wrapMode: Text.WordWrap; Layout.fillWidth: true }
        }
    }
    component ListaCambios: ColumnLayout {
        spacing: 0
        ListView {
            Layout.fillWidth: true; Layout.fillHeight: true
            clip: true
            model: cambios
            delegate: QQC2.ItemDelegate {
                required property string tipo
                required property string ruta
                required property string detalle
                width: ListView.view.width
                contentItem: RowLayout {
                    spacing: Kirigami.Units.smallSpacing
                    QQC2.Label { text: tipo; font.family: Kirigami.Theme.fixedWidthFont.family; font.bold: true; Layout.preferredWidth: Kirigami.Units.gridUnit
                                 color: tipo === "M" ? Kirigami.Theme.neutralTextColor : tipo === "?" ? Kirigami.Theme.disabledTextColor : Kirigami.Theme.positiveTextColor }
                    QQC2.Label { text: ruta; Layout.fillWidth: true; elide: Text.ElideMiddle }
                    QQC2.Label { text: detalle; color: Kirigami.Theme.disabledTextColor; font: Kirigami.Theme.smallFont }
                }
            }
        }
        Kirigami.Separator { Layout.fillWidth: true }
        RowLayout {
            Layout.fillWidth: true
            Layout.margins: Kirigami.Units.smallSpacing
            QQC2.TextField { Layout.fillWidth: true; placeholderText: "Mensaje del commit (Ctrl+Intro)" }
            QQC2.Button { text: "Confirmar"; icon.name: "vcs-commit" }
        }
    }
    component ListaHistorial: ListView {
        clip: true
        model: historial
        delegate: QQC2.ItemDelegate {
            required property string hash
            required property string mensaje
            required property string hace
            width: ListView.view.width
            contentItem: RowLayout {
                spacing: Kirigami.Units.smallSpacing
                QQC2.Label { text: hash; font.family: Kirigami.Theme.fixedWidthFont.family; color: Kirigami.Theme.disabledTextColor }
                QQC2.Label { text: mensaje; Layout.fillWidth: true; elide: Text.ElideRight }
                QQC2.Label { text: hace; color: Kirigami.Theme.disabledTextColor; font: Kirigami.Theme.smallFont }
            }
        }
    }
}
