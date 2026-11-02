// DialogoError — el diálogo de los errores presentables (3.0): muestra el primero de la cola de `errores`
// (`gui_comun.errores.Errores`) en una `TarjetaError` y pasa al siguiente al cerrarlo. Se abre solo cuando llega un
// error. `VentanaBase` ya trae uno; un studio no lo instancia salvo que no use la ventana base.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

Kirigami.Dialog {
    id: dialogo

    property var errores: typeof aplicacionStudio !== "undefined" && aplicacionStudio ? aplicacionStudio.errores : null
    property bool abrirSolo: true
    readonly property int cuantos: errores ? errores.cuantos : 0
    readonly property int omitidos: errores ? errores.omitidos : 0
    signal verRegistro()

    title: !errores || !errores.actual.nivel || errores.actual.nivel === "error" ? (cuantos > 1 ? "Error (1 de " + cuantos + ")" : "Error")
         : errores.actual.nivel === "aviso" ? (cuantos > 1 ? "Aviso (1 de " + cuantos + ")" : "Aviso") : "Información"
    preferredWidth: Kirigami.Units.gridUnit * 34
    maximumHeight: Kirigami.Units.gridUnit * 34
    padding: Kirigami.Units.largeSpacing * 2
    standardButtons: QQC2.Dialog.NoButton
    showCloseButton: true

    customFooterActions: [
        Kirigami.Action {
            text: "Descartar todos"
            icon.name: "edit-clear-all"
            visible: dialogo.cuantos > 1
            onTriggered: { dialogo.errores.limpiar(); dialogo.close() }
        },
        Kirigami.Action {
            text: dialogo.cuantos > 1 ? "Siguiente" : "Cerrar"
            icon.name: dialogo.cuantos > 1 ? "go-next" : "dialog-close"
            onTriggered: { if (dialogo.cuantos > 1) dialogo.errores.descartar(); else dialogo.close() }
        }
    ]

    // al cerrar (Cerrar, Esc, la ×) se descarta el que se veía; si quedan, vuelve a abrirse con el siguiente
    onClosed: {
        if (!errores || errores.cuantos === 0) return
        errores.descartar()
        if (errores.cuantos > 0) Qt.callLater(dialogo.open)
    }

    Connections {
        target: dialogo.errores ?? null
        function onCambiado() {
            if (!dialogo.abrirSolo || !dialogo.errores) return
            if (dialogo.errores.cuantos > 0 && !dialogo.opened && !dialogo.visible) dialogo.open()
        }
    }

    ColumnLayout {
        spacing: Kirigami.Units.largeSpacing
        TarjetaError {
            id: tarjeta
            Layout.fillWidth: true
            Layout.preferredWidth: Kirigami.Units.gridUnit * 30
            error: dialogo.errores ? dialogo.errores.actual : ({})
        }
        QQC2.Label {
            visible: dialogo.omitidos > 0
            text: dialogo.omitidos + " errores más no se muestran; están en el registro."
            color: Kirigami.Theme.disabledTextColor
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }
    }
}
