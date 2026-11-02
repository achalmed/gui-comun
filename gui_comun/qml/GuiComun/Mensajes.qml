// Mensajes — mensajes en línea (Kirigami.InlineMessage) solo para lo que exige atención: conflicto, remoto caído,
// error de una operación. Se apilan arriba del centro y se cierran. Un resumen no va aquí (va a la barra de estado).
// mostrar(texto, tipo, acciones): tipo = "informacion" | "positivo" | "aviso" | "error"; acciones = [{texto, icono, ejecutar}]
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

ColumnLayout {
    id: raiz
    spacing: Kirigami.Units.smallSpacing
    visible: modelo.count > 0

    readonly property alias cuantos: modelo.count

    function mostrar(texto, tipo, acciones) {
        modelo.append({ texto: texto, tipo: tipo || "informacion", acciones: acciones || [] })
    }
    function limpiar() { modelo.clear() }

    ListModel { id: modelo }

    Repeater {
        model: modelo
        delegate: Kirigami.InlineMessage {
            id: mensaje
            required property int index
            required property string texto
            required property string tipo
            required property var acciones
            Layout.fillWidth: true
            Layout.margins: Kirigami.Units.smallSpacing
            visible: true
            showCloseButton: true
            text: texto
            type: tipo === "error" ? Kirigami.MessageType.Error
                : tipo === "aviso" ? Kirigami.MessageType.Warning
                : tipo === "positivo" ? Kirigami.MessageType.Positive
                : Kirigami.MessageType.Information
            onVisibleChanged: if (!visible) Qt.callLater(() => { if (mensaje.index < modelo.count) modelo.remove(mensaje.index) })
            Component.onCompleted: {
                const lista = []
                for (let i = 0; i < acciones.count; i++) {
                    const a = acciones.get(i)
                    const accion = componenteAccion.createObject(mensaje, { text: a.texto, ejecutar: a.ejecutar })
                    accion.icon.name = a.icono || ""
                    lista.push(accion)
                }
                actions = lista
            }
            Component {
                id: componenteAccion
                Kirigami.Action {
                    property var ejecutar
                    onTriggered: { if (ejecutar) ejecutar(); mensaje.visible = false }
                }
            }
        }
    }
}
