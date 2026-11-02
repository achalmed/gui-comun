// VentanaStudio — una distribución de trabajo sobre VentanaBase (al estilo Dolphin/Kate): barra de herramientas
// corta con conmutadores de paneles, SplitView con cuatro ranuras (navegación · centro · detalles · panel inferior) y
// barra de estado con resumen, tarea en curso y contexto. Lo común (menú desde el registro de acciones, paleta Ctrl+K,
// mensajes, errores presentables, confirmaciones, «Acerca de», ajustes, geometría recordada) lo pone VentanaBase.
// 3.0: es una distribución más, no la de todos; un studio cuya disciplina pide otra cosa usa VentanaBase directamente.
// Paneles y divisores se recuerdan en QSettings. Ningún nombre ni logotipo dentro. Sin colores, fuentes, radios ni
// sombras propios: Kirigami.Theme y Kirigami.Units.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import QtCore
import org.kde.kirigami as Kirigami

VentanaBase {
    id: ventana

    // --- lo que el studio da (además de lo de VentanaBase: acciones, tareas, consola, descripcion, autor, sitio,
    //     dialogoAjustes, claveAjustes) ---
    property Item navegacion
    property Item centro
    property Item detalles
    property Item inferior
    property string resumen: ""
    property string contexto: ""
    property alias herramientasExtra: zonaExtra.data

    // --- estado de los paneles (recordado) ---
    property bool mostrarNavegacion: true
    property bool mostrarDetalles: true
    property bool mostrarInferior: false
    property bool abrirInferiorAlEmpezarTarea: true
    property int anchoEstrecho: 900
    property int anchoMedio: 1200
    readonly property bool estrecha: width < anchoEstrecho
    readonly property bool media: width < anchoMedio

    signal navegacionPulsada()

    width: 1280
    height: 800
    minimumWidth: 800
    minimumHeight: 520
    mensajes: mensajesCentro                     // sobre el centro, no sobre toda la ventana

    Settings {
        id: ajustes
        category: ventana.claveAjustes
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

    // ------------------------------------------------------------------ conmutadores de los paneles
    function marcar(nombre, valor) { if (existe(nombre)) acciones.marcar(nombre, valor) }
    function sincronizarMarcas() {
        if (!acciones) return
        marcar("ventana.navegacion", mostrarNavegacion)
        marcar("ventana.detalles", mostrarDetalles)
        marcar("ventana.inferior", mostrarInferior)
    }
    onMostrarNavegacionChanged: sincronizarMarcas()
    onMostrarDetallesChanged: sincronizarMarcas()
    onMostrarInferiorChanged: sincronizarMarcas()
    onAccionesChanged: sincronizarMarcas()

    Connections {
        target: ventana.acciones ?? null
        function onDisparada(nombre, marcada) {
            switch (nombre) {
            case "ventana.navegacion": ventana.mostrarNavegacion = marcada; break
            case "ventana.detalles": ventana.mostrarDetalles = marcada; break
            case "ventana.inferior": ventana.mostrarInferior = marcada; break
            }
        }
    }
    Connections {
        target: ventana.tareas ?? null
        function onIniciada(nombre) { if (ventana.abrirInferiorAlEmpezarTarea) ventana.mostrarInferior = true }
    }

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
                Mensajes { id: mensajesCentro; Layout.fillWidth: true }
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
        parent: ventana.contentItem              // 3.0: el contenido va a VentanaBase; el cajón, a la ventana entera
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
}
