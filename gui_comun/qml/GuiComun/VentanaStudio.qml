// VentanaStudio — la ventana de trabajo de la familia (al estilo Dolphin/Kate): barra de menú generada desde el
// registro de acciones, barra de herramientas corta con conmutadores de paneles, SplitView con cuatro ranuras
// (navegación · centro · detalles · panel inferior), barra de estado con resumen, tarea en curso y contexto, paleta
// de órdenes (Ctrl+Alt+I y Ctrl+K), «Acerca de» y el diálogo de ajustes del studio. Geometría y paneles se recuerdan
// en QSettings. Ningún nombre ni logotipo dentro: el título lo pone el gestor de ventanas y el icono, el lanzador.
// Sin colores, fuentes, radios ni sombras propios: Kirigami.Theme y Kirigami.Units.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import QtCore
import org.kde.kirigami as Kirigami

Kirigami.AbstractApplicationWindow {
    id: ventana

    // --- lo que el studio da ---
    property var acciones
    property var tareas
    property var consola
    property Item navegacion
    property Item centro
    property Item detalles
    property Item inferior
    property string resumen: ""
    property string contexto: ""
    property string descripcion: ""
    property string autor: ""
    property string sitio: ""
    property var dialogoAjustes: null
    property alias herramientasExtra: zonaExtra.data
    property alias mensajes: mensajes
    readonly property alias paleta: paleta

    // --- estado de los paneles (recordado) ---
    property bool mostrarNavegacion: true
    property bool mostrarDetalles: true
    property bool mostrarInferior: false
    property bool abrirInferiorAlEmpezarTarea: true
    property int anchoEstrecho: 900
    property int anchoMedio: 1200
    readonly property bool estrecha: width < anchoEstrecho
    readonly property bool media: width < anchoMedio
    property string claveAjustes: "ventana"

    signal navegacionPulsada()

    width: 1280
    height: 800
    minimumWidth: 800
    minimumHeight: 520
    Kirigami.Theme.colorSet: Kirigami.Theme.Window

    Settings {
        id: ajustes
        category: ventana.claveAjustes
        property alias x: ventana.x
        property alias y: ventana.y
        property alias width: ventana.width
        property alias height: ventana.height
        property alias navegacion: ventana.mostrarNavegacion
        property alias detalles: ventana.mostrarDetalles
        property alias inferior: ventana.mostrarInferior
        property var divisionHorizontal
        property var divisionVertical
    }

    // ------------------------------------------------------------------ colocación de las ranuras
    function colocar(item, ranura) {
        if (!item) return
        item.parent = ranura
        item.anchors.fill = ranura
    }
    function colocarDetalles() {
        if (!detalles) return
        colocar(detalles, estrecha ? ranuraDetallesCajon : ranuraDetalles)
    }
    onNavegacionChanged: { colocar(navegacion, ranuraNavegacion); if (navegacion && navegacion.hasOwnProperty("plegado")) navegacion.plegado = Qt.binding(() => ventana.estrecha) }
    onCentroChanged: colocar(centro, ranuraCentro)
    onDetallesChanged: colocarDetalles()
    onEstrechaChanged: colocarDetalles()
    onInferiorChanged: {
        colocar(inferior, ranuraInferior)
        if (inferior && inferior.cerrar !== undefined) inferior.cerrar.connect(() => { ventana.mostrarInferior = false })
    }

    // ------------------------------------------------------------------ acciones de la ventana
    function existe(nombre) { return acciones ? acciones.existe(nombre) : false }
    function sincronizarMarcas() {
        if (!acciones) return
        acciones.marcar("ventana.navegacion", mostrarNavegacion)
        acciones.marcar("ventana.detalles", mostrarDetalles)
        acciones.marcar("ventana.inferior", mostrarInferior)
        acciones.marcar("ventana.pantalla_completa", visibility === Window.FullScreen)
    }
    onMostrarNavegacionChanged: sincronizarMarcas()
    onMostrarDetallesChanged: sincronizarMarcas()
    onMostrarInferiorChanged: sincronizarMarcas()
    onVisibilityChanged: sincronizarMarcas()
    onAccionesChanged: sincronizarMarcas()

    Connections {
        target: ventana.acciones
        function onDisparada(nombre, marcada) {
            switch (nombre) {
            case "ventana.navegacion": ventana.mostrarNavegacion = marcada; break
            case "ventana.detalles": ventana.mostrarDetalles = marcada; break
            case "ventana.inferior": ventana.mostrarInferior = marcada; break
            case "ventana.pantalla_completa": ventana.visibility = marcada ? Window.FullScreen : Window.Windowed; break
            case "ventana.paleta": paleta.abrir(""); break
            case "app.ajustes": if (ventana.dialogoAjustes) ventana.dialogoAjustes.open(); break
            case "app.acerca": acerca.open(); break
            case "app.salir": Qt.quit(); break
            }
        }
    }
    Connections {
        target: ventana.tareas
        function onIniciada(nombre) { if (ventana.abrirInferiorAlEmpezarTarea) ventana.mostrarInferior = true }
    }
    Shortcut { sequence: "Ctrl+K"; onActivated: paleta.abrir("") }

    Component.onCompleted: {
        colocar(navegacion, ranuraNavegacion)
        colocar(centro, ranuraCentro)
        colocarDetalles()
        colocar(inferior, ranuraInferior)
        if (ajustes.divisionHorizontal) horizontal.restoreState(ajustes.divisionHorizontal)
        if (ajustes.divisionVertical) vertical.restoreState(ajustes.divisionVertical)
        sincronizarMarcas()
    }
    Component.onDestruction: {
        ajustes.divisionHorizontal = horizontal.saveState()
        ajustes.divisionVertical = vertical.saveState()
    }

    // ------------------------------------------------------------------ barra de menú (generada)
    menuBar: QQC2.MenuBar {
        id: barraMenu
        Instantiator {
            model: ventana.acciones ? ventana.acciones.menus : []
            delegate: MenuAcciones {
                required property var modelData
                acciones: ventana.acciones
                titulo: modelData.titulo
                elementos: modelData.elementos
            }
            onObjectAdded: (indice, objeto) => barraMenu.insertMenu(indice, objeto)
            onObjectRemoved: (indice, objeto) => barraMenu.removeMenu(objeto)
        }
    }

    // ------------------------------------------------------------------ barra de herramientas (corta)
    header: QQC2.ToolBar {
        position: QQC2.ToolBar.Header
        Accessible.name: "Barra de herramientas"
        RowLayout {
            anchors.fill: parent
            spacing: Kirigami.Units.smallSpacing
            Component { id: cSeparador; QQC2.ToolSeparator {} }
            Component { id: cBoton; BotonAccion {} }
            Repeater {
                model: ventana.acciones ? ventana.acciones.barra : []
                delegate: Loader {
                    required property var modelData
                    sourceComponent: modelData === "|" ? cSeparador : cBoton
                    onLoaded: if (modelData !== "|") item.accion = ventana.acciones.accion(modelData)
                }
            }
            Item { Layout.fillWidth: true }
            RowLayout { id: zonaExtra; spacing: Kirigami.Units.smallSpacing }
            QQC2.ToolSeparator { visible: zonaExtra.children.length > 0 }
            BotonAccion { visible: ventana.existe("ventana.navegacion") && ventana.navegacion !== null; accion: ventana.existe("ventana.navegacion") ? ventana.acciones.accion("ventana.navegacion") : null; conTexto: false }
            BotonAccion { visible: ventana.existe("ventana.detalles") && ventana.detalles !== null; accion: ventana.existe("ventana.detalles") ? ventana.acciones.accion("ventana.detalles") : null; conTexto: false }
            BotonAccion { visible: ventana.existe("ventana.inferior") && ventana.inferior !== null; accion: ventana.existe("ventana.inferior") ? ventana.acciones.accion("ventana.inferior") : null; conTexto: false }
            QQC2.ToolButton {
                icon.name: "overflow-menu"
                text: "Menú"
                display: QQC2.AbstractButton.IconOnly
                QQC2.ToolTip.text: "Todas las órdenes"
                QQC2.ToolTip.visible: hovered
                Accessible.name: text
                onClicked: menuCompleto.popup()
                MenuAcciones {
                    id: menuCompleto
                    acciones: ventana.acciones
                    conAtajos: false
                    elementos: ventana.acciones ? ventana.acciones.menus : []
                }
            }
        }
    }

    // ------------------------------------------------------------------ espacio de trabajo
    QQC2.SplitView {
        id: vertical
        anchors.fill: parent
        orientation: Qt.Vertical

        QQC2.SplitView {
            id: horizontal
            orientation: Qt.Horizontal
            QQC2.SplitView.fillHeight: true

            Item {
                id: ranuraNavegacion
                visible: ventana.mostrarNavegacion && ventana.navegacion !== null
                QQC2.SplitView.preferredWidth: ventana.navegacion ? ventana.navegacion.implicitWidth : 0
                QQC2.SplitView.minimumWidth: ventana.estrecha ? (ventana.navegacion ? ventana.navegacion.implicitWidth : 0)
                                           : (ventana.navegacion && ventana.navegacion.anchoMinimo !== undefined ? ventana.navegacion.anchoMinimo : Kirigami.Units.gridUnit * 9)
                QQC2.SplitView.maximumWidth: ventana.estrecha ? (ventana.navegacion ? ventana.navegacion.implicitWidth : 0) : Kirigami.Units.gridUnit * 24
            }

            ColumnLayout {
                QQC2.SplitView.fillWidth: true
                QQC2.SplitView.minimumWidth: Kirigami.Units.gridUnit * 28
                spacing: 0
                Mensajes { id: mensajes; Layout.fillWidth: true }
                Item { id: ranuraCentro; Layout.fillWidth: true; Layout.fillHeight: true }
            }

            Item {
                id: ranuraDetalles
                visible: ventana.mostrarDetalles && ventana.detalles !== null && !ventana.estrecha
                QQC2.SplitView.preferredWidth: ventana.detalles && ventana.detalles.anchoPreferido !== undefined ? ventana.detalles.anchoPreferido : Kirigami.Units.gridUnit * 24
                QQC2.SplitView.minimumWidth: ventana.detalles && ventana.detalles.anchoMinimo !== undefined ? ventana.detalles.anchoMinimo : Kirigami.Units.gridUnit * 18
            }
        }

        Item {
            id: ranuraInferior
            visible: ventana.mostrarInferior && ventana.inferior !== null
            QQC2.SplitView.preferredHeight: ventana.inferior && ventana.inferior.altoPreferido !== undefined ? ventana.inferior.altoPreferido : Kirigami.Units.gridUnit * 9
            QQC2.SplitView.minimumHeight: ventana.inferior && ventana.inferior.altoMinimo !== undefined ? ventana.inferior.altoMinimo : Kirigami.Units.gridUnit * 5
        }
    }

    // en ventanas estrechas los detalles se abren sobre la tabla, como hoja deslizante
    Kirigami.OverlayDrawer {
        id: cajonDetalles
        edge: Qt.RightEdge
        modal: true
        handleVisible: false
        width: Math.min(ventana.width * 0.8, Kirigami.Units.gridUnit * 28)
        drawerOpen: ventana.estrecha && ventana.mostrarDetalles && ventana.detalles !== null
        onDrawerOpenChanged: if (!drawerOpen && ventana.estrecha && ventana.mostrarDetalles) ventana.mostrarDetalles = false
        contentItem: Item { id: ranuraDetallesCajon; implicitWidth: cajonDetalles.width }
    }

    // ------------------------------------------------------------------ barra de estado
    footer: BarraEstado {
        resumen: ventana.resumen
        contexto: ventana.contexto
        tareas: ventana.tareas
        onProgresoPulsado: ventana.mostrarInferior = true
    }

    // ------------------------------------------------------------------ paleta y «Acerca de»
    PaletaOrdenes {
        id: paleta
        parent: ventana.contentItem
        acciones: ventana.acciones
    }

    Kirigami.Dialog {
        id: acerca
        readonly property var datos: typeof aplicacionStudio !== "undefined" ? aplicacionStudio : null
        title: "Acerca de " + (datos ? datos.nombre : "")
        standardButtons: QQC2.Dialog.Close
        // ancho fijo y texto que se ajusta: sin esto el diálogo crecía hasta el largo de la descripción
        readonly property real anchoTexto: Kirigami.Units.gridUnit * 24
        preferredWidth: anchoTexto + Kirigami.Units.largeSpacing * 4
        maximumWidth: Kirigami.Units.gridUnit * 32
        padding: Kirigami.Units.largeSpacing * 2
        ColumnLayout {
            spacing: Kirigami.Units.largeSpacing
            RowLayout {
                spacing: Kirigami.Units.largeSpacing
                Kirigami.Icon {
                    source: acerca.datos ? acerca.datos.appId : ""
                    fallback: "applications-development"
                    implicitWidth: Kirigami.Units.iconSizes.large
                    implicitHeight: implicitWidth
                }
                ColumnLayout {
                    spacing: 0
                    Kirigami.Heading { level: 2; text: acerca.datos ? acerca.datos.nombre : "" }
                    QQC2.Label { visible: acerca.datos && acerca.datos.version !== ""; text: "Versión " + (acerca.datos ? acerca.datos.version : ""); color: Kirigami.Theme.disabledTextColor }
                }
            }
            QQC2.Label {
                visible: ventana.descripcion !== ""
                text: ventana.descripcion
                wrapMode: Text.WordWrap
                Layout.preferredWidth: acerca.anchoTexto
                Layout.maximumWidth: acerca.anchoTexto
            }
            Kirigami.FormLayout {
                Layout.maximumWidth: acerca.anchoTexto
                QQC2.Label { Kirigami.FormData.label: "Autor:"; visible: ventana.autor !== ""; text: ventana.autor; wrapMode: Text.WordWrap; Layout.maximumWidth: acerca.anchoTexto * 0.7 }
                QQC2.Label { Kirigami.FormData.label: "Sitio:"; visible: ventana.sitio !== ""; text: "<a href=\"" + ventana.sitio + "\">" + ventana.sitio + "</a>"; onLinkActivated: link => Qt.openUrlExternally(link); elide: Text.ElideMiddle; Layout.maximumWidth: acerca.anchoTexto * 0.7 }
                QQC2.Label { Kirigami.FormData.label: "Marco:"; text: "gui-comun " + (acerca.datos ? acerca.datos.versionGuiComun : "") + " · Kirigami · " + (acerca.datos ? acerca.datos.binding : "") + " · Qt " + (acerca.datos ? acerca.datos.versionQt : ""); color: Kirigami.Theme.disabledTextColor; wrapMode: Text.WordWrap; Layout.maximumWidth: acerca.anchoTexto * 0.7 }
            }
        }
    }
}
