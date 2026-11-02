// VentanaBase — la ventana de la familia sin plantilla (3.0): aporta solo lo común y deja el contenido libre.
//
// Lo común: la barra de menú generada desde el registro de acciones (la única que registra atajos), la paleta de
// órdenes (Ctrl+K y la acción `ventana.paleta`), los mensajes en línea, el diálogo de errores presentables
// (`errores`), la confirmación de las operaciones de riesgo (`acciones.confirmacionPedida`), «Acerca de», el diálogo
// de ajustes del studio, pantalla completa y la geometría recordada en QSettings. Lo demás es del studio: lo que se
// declara dentro es el contenido (un lienzo, un editor con su visor, una cuadrícula de herramientas, un grafo de
// commits…), y `header`/`footer` quedan libres. Ninguna navegación lateral, tabla, panel de detalles ni consola
// impuestos: `VentanaStudio` es una distribución más, construida sobre esta.
//
// Ningún nombre ni logotipo dentro (el título lo pone el gestor de ventanas); sin colores, fuentes, radios ni sombras
// propios: Kirigami.Theme y Kirigami.Units.
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
    property var errores: typeof aplicacionStudio !== "undefined" && aplicacionStudio ? aplicacionStudio.errores : null
    property var escritorio: typeof aplicacionStudio !== "undefined" && aplicacionStudio ? aplicacionStudio.escritorio : null
    property string descripcion: ""
    property string autor: ""
    property string sitio: ""
    property var dialogoAjustes: null
    property string claveAjustes: "ventana"
    property bool conMenu: true                        // la barra de menú visible
    property bool notificarTareas: true                // éxito y verificación de las tareas que declaran su operación
    property var mensajes: mensajesBase                // VentanaStudio pone los suyos en la columna central
    readonly property alias paleta: paleta
    readonly property alias confirmacion: confirmacion
    readonly property alias dialogoError: dialogoError

    // el contenido: lo que el studio declara dentro, bajo los mensajes y a todo lo ancho (con `anchors.fill: parent`)
    default property alias contenido: zonaContenido.data
    readonly property alias zonaContenido: zonaContenido

    width: 1200
    height: 760
    minimumWidth: 640
    minimumHeight: 420
    Kirigami.Theme.colorSet: Kirigami.Theme.Window

    // ------------------------------------------------------------------ API para el QML del studio
    // confirmar({titulo, consecuencias, operacion, operacionTexto, textoAceptar, icono, destructiva}, alAceptar)
    function confirmar(peticion, alAceptar) { confirmacion.pedir(peticion, alAceptar) }
    // un error presentable desde QML (desde Python: `aplicacion.error(...)`)
    function error(descripcion, causa, recurso, accion, detalle) {
        if (errores) errores.presentarMapa({ descripcion: descripcion, causa: causa || "", recurso: recurso || "", accion: accion || "", detalle: detalle || "" })
    }
    function notificar(texto, tipo, accionesMensaje) { ventana.mensajes.mostrar(texto, tipo || "informacion", accionesMensaje || []) }
    function existe(nombre) { return acciones ? acciones.existe(nombre) : false }

    Settings {
        id: geometria
        category: ventana.claveAjustes
        property alias x: ventana.x
        property alias y: ventana.y
        property alias width: ventana.width
        property alias height: ventana.height
    }

    // ------------------------------------------------------------------ acciones comunes
    function sincronizarPantallaCompleta() {
        if (acciones && acciones.existe("ventana.pantalla_completa"))
            acciones.marcar("ventana.pantalla_completa", visibility === Window.FullScreen)
    }
    onVisibilityChanged: sincronizarPantallaCompleta()
    onAccionesChanged: sincronizarPantallaCompleta()

    Connections {
        target: ventana.acciones ?? null
        function onDisparada(nombre, marcada) {
            switch (nombre) {
            case "ventana.pantalla_completa": ventana.visibility = marcada ? Window.FullScreen : Window.Windowed; break
            case "ventana.paleta": paleta.abrir(""); break
            case "app.ajustes": if (ventana.dialogoAjustes) ventana.dialogoAjustes.open(); break
            case "app.acerca": acerca.open(); break
            case "app.salir": Qt.quit(); break
            }
        }
        function onConfirmacionPedida(peticion) { confirmacion.pedir(peticion, null) }
    }
    Connections {
        target: ventana.tareas ?? null
        ignoreUnknownSignals: true
        // el éxito y la verificación, por separado (solo las tareas que declaran su operación)
        function onResultado(r) {
            if (!ventana.notificarTareas || !r.operacion || r.nivel !== "ok") return
            if (r.operacion === "lectura" || r.operacion === "simulacion") return
            ventana.mensajes.mostrar("Terminó: " + r.nombre + (r.verificacion ? "" : " (sin verificación)"), "informacion")
        }
        function onVerificada(nombre, ok, detalle) {
            if (!ventana.notificarTareas || !ok) return          // la que no pasa llega como error presentable
            ventana.mensajes.mostrar("Verificado: " + nombre + (detalle ? " · " + detalle : ""), "positivo")
        }
    }
    Shortcut { sequence: "Ctrl+K"; enabled: ventana.acciones !== undefined && ventana.acciones !== null; onActivated: paleta.abrir("") }

    // ------------------------------------------------------------------ barra de menú (generada)
    menuBar: QQC2.MenuBar {
        id: barraMenu
        visible: ventana.conMenu
        height: visible ? implicitHeight : 0
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

    // ------------------------------------------------------------------ contenido
    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        Mensajes { id: mensajesBase; Layout.fillWidth: true; visible: ventana.mensajes === mensajesBase && cuantos > 0 }
        Item { id: zonaContenido; Layout.fillWidth: true; Layout.fillHeight: true }
    }

    // ------------------------------------------------------------------ paleta, diálogos y «Acerca de»
    PaletaOrdenes {
        id: paleta
        parent: ventana.contentItem
        acciones: ventana.acciones
    }

    DialogoConfirmacion { id: confirmacion; objectName: "confirmacion"; acciones: ventana.acciones }

    DialogoError {
        id: dialogoError
        objectName: "dialogoError"
        errores: ventana.errores
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
