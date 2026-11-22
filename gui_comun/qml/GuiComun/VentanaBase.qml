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
// 4.3: translúcida y desenfocada como Dolphin cuando Kvantum lo pide (`aplicacionStudio.translucidez`, véase
// `gui_comun/translucidez.py`): el fondo de la ventana es su color a la opacidad del tema; la barra de menú y las
// barras de herramientas de `header`/`footer` dejan ver ese fondo (`FondoVentana`), igual que los paneles laterales de
// la base; las zonas de lectura (`colorSet: View`) siguen opacas. La acción `ventana.translucida` la apaga.
//
// Ningún nombre ni logotipo dentro (el título lo pone el gestor de ventanas); sin colores, fuentes, radios ni sombras
// propios: Kirigami.Theme y Kirigami.Units.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import QtQuick.Templates as T
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
    // 4.3: la translucidez de la ventana (null fuera de una `Aplicacion`: opaca)
    readonly property var translucidez: typeof aplicacionStudio !== "undefined" && aplicacionStudio
                                        ? (aplicacionStudio.translucidez ?? null) : null
    readonly property bool translucida: translucidez ? translucidez.activa : false

    // el contenido: lo que el studio declara dentro, bajo los mensajes y a todo lo ancho (con `anchors.fill: parent`)
    default property alias contenido: zonaContenido.data
    readonly property alias zonaContenido: zonaContenido

    width: 1200
    height: 760
    minimumWidth: Kirigami.Units.gridUnit * 20          // 4.2: cabe en un celular o media pantalla (antes 640)
    // 4.2: en una ventana angosta, la barra de menú se pliega en un solo «☰ Menú» con todos los menús dentro
    property bool menuPlegado: width < Kirigami.Units.gridUnit * 34
    onMenuPlegadoChanged: Qt.callLater(ventana.ponerMenuPlegado)
    function ponerMenuPlegado() {
        if (ventana.menuPlegado && barraMenu.menuAt(0) !== menuTodo) barraMenu.insertMenu(0, menuTodo)
        else if (!ventana.menuPlegado && barraMenu.menuAt(0) === menuTodo) barraMenu.removeMenu(menuTodo)
    }
    Component.onCompleted: { Qt.callLater(ventana.ponerMenuPlegado); Qt.callLater(ventana.ponerTranslucidez) }
    QQC2.Menu {
        id: menuTodo
        title: "☰ Menú"
    }
    Instantiator {          // los menús dentro de «☰ Menú» (solo mientras está plegada: así ningún atajo se registra dos veces)
        active: ventana.menuPlegado
        model: ventana.acciones ? ventana.acciones.menus : []
        delegate: MenuAcciones {
            required property var modelData
            acciones: ventana.acciones
            titulo: modelData.titulo
            elementos: modelData.elementos
        }
        onObjectAdded: (indice, objeto) => menuTodo.insertMenu(indice, objeto)
        onObjectRemoved: (indice, objeto) => menuTodo.removeMenu(objeto)
    }
    minimumHeight: 420
    Kirigami.Theme.colorSet: Kirigami.Theme.Window
    // 4.3: con la ventana translúcida, su color a la opacidad de Kvantum (el compositor desenfoca lo de detrás)
    color: translucida ? Qt.alpha(Kirigami.Theme.backgroundColor, translucidez.opacidad) : Kirigami.Theme.backgroundColor

    // 4.3: las barras de herramientas de `header` y `footer` con el fondo del estilo (el de org.kde.desktop) pasan a
    // `FondoVentana`, con su raya y su alto; un fondo que el studio puso a su barra no se toca
    Component { id: componenteFondoBarra; FondoVentana {} }
    function fondoTranslucidoEn(barra) {
        if (!barra || !(barra instanceof T.ToolBar) || !barra.background || barra.background.control !== barra) return
        const viejo = barra.background
        barra.background = componenteFondoBarra.createObject(barra, {
            separador: barra.position === T.ToolBar.Footer ? "arriba" : "abajo",
            implicitHeight: viejo.implicitHeight
        })
        viejo.destroy()
    }
    function ponerTranslucidez() {
        if (ventana.translucida) { fondoTranslucidoEn(ventana.header); fondoTranslucidoEn(ventana.footer) }
        if (acciones && acciones.existe("ventana.translucida")) {
            acciones.habilitar("ventana.translucida", translucidez ? translucidez.posible : false)
            acciones.marcar("ventana.translucida", ventana.translucida)
        }
    }
    onTranslucidaChanged: ponerTranslucidez()
    onHeaderChanged: if (translucida) fondoTranslucidoEn(header)
    onFooterChanged: if (translucida) fondoTranslucidoEn(footer)

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
    onAccionesChanged: { sincronizarPantallaCompleta(); ponerTranslucidez() }

    Connections {
        target: ventana.acciones ?? null
        function onDisparada(nombre, marcada) {
            switch (nombre) {
            case "ventana.pantalla_completa": ventana.visibility = marcada ? Window.FullScreen : Window.Windowed; break
            case "ventana.paleta": paleta.abrir(""); break
            case "ventana.translucida":
                if (ventana.translucidez) ventana.translucidez.preferir(marcada)
                ventana.ponerTranslucidez()
                break
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
        background: FondoVentana {}                // 4.3: deja ver el fondo translúcido de la ventana
        Instantiator {
            active: !ventana.menuPlegado
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
