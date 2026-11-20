// BarraEstado — el pie de la ventana: el resumen de la colección a la izquierda, la tarea en curso con su progreso y
// «n de m» en medio (solo mientras hay tarea; un clic abre el panel inferior; cancelar al lado), el contexto de la
// selección a la derecha. Es donde van las cifras que antes eran tarjetas.
// 4.1: la pista de `mensajes` (por omisión, los de su ventana: `mostrar(texto, "pista")`) ocupa el lugar del contexto
// mientras dura; el studio no arma su propio `Timer`.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

QQC2.ToolBar {
    id: barra

    property string resumen: ""
    property string contexto: ""
    property var tareas
    property var mensajes: QQC2.ApplicationWindow.window && QQC2.ApplicationWindow.window.mensajes !== undefined
                           ? QQC2.ApplicationWindow.window.mensajes : null
    readonly property string pista: mensajes && mensajes.pista !== undefined ? mensajes.pista : ""
    readonly property string textoDerecha: pista !== "" ? pista : contexto
    signal progresoPulsado()

    position: QQC2.ToolBar.Footer
    Accessible.name: "Barra de estado"

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: Kirigami.Units.smallSpacing
        anchors.rightMargin: Kirigami.Units.smallSpacing
        spacing: Kirigami.Units.largeSpacing
        QQC2.Label {
            text: barra.resumen
            elide: Text.ElideRight
            font: Kirigami.Theme.smallFont        // 4.2: en letra pequeña, como la de Dolphin
            Layout.fillWidth: true
            Accessible.name: "Resumen: " + text
        }
        RowLayout {
            visible: barra.tareas ? barra.tareas.activa : false
            spacing: Kirigami.Units.smallSpacing
            QQC2.Label {
                text: {
                    if (!barra.tareas) return ""
                    const e = barra.tareas.elemento
                    const o = barra.tareas.operacionTexto !== undefined ? barra.tareas.operacionTexto : ""   // 3.0
                    return (o ? o + ": " : "") + barra.tareas.nombre + (e ? " · " + e : "")
                }
                elide: Text.ElideRight
                Layout.maximumWidth: Kirigami.Units.gridUnit * 22
                font: Kirigami.Theme.smallFont
                color: Kirigami.Theme.disabledTextColor
            }
            Loader {                      // la barra de progreso existe solo mientras hay tarea
                Layout.preferredWidth: Kirigami.Units.gridUnit * 9
                Layout.preferredHeight: item ? item.implicitHeight : 0
                active: barra.tareas ? barra.tareas.activa : false
                sourceComponent: QQC2.ProgressBar {
                    from: 0; to: 100
                    indeterminate: barra.tareas ? barra.tareas.progreso < 0 : false
                    value: barra.tareas && barra.tareas.progreso >= 0 ? barra.tareas.progreso : 0
                    Accessible.name: "Progreso de " + (barra.tareas ? barra.tareas.nombre : "")
                    TapHandler { onTapped: barra.progresoPulsado() }
                }
            }
            QQC2.ToolButton {
                icon.name: "process-stop"
                text: "Cancelar"
                display: QQC2.AbstractButton.IconOnly
                QQC2.ToolTip.text: "Cancelar la operación"
                QQC2.ToolTip.visible: hovered
                Accessible.name: text
                onClicked: if (barra.tareas) barra.tareas.cancelar()
            }
        }
        QQC2.ToolSeparator { visible: barra.textoDerecha !== "" }
        QQC2.Label {
            objectName: "contextoBarra"
            visible: barra.textoDerecha !== ""
            text: barra.textoDerecha
            elide: Text.ElideRight
            font: Kirigami.Theme.smallFont
            // la pista se lee con el color del texto (es lo nuevo); el contexto, tenue como el resumen
            color: barra.pista !== "" ? Kirigami.Theme.textColor : Kirigami.Theme.disabledTextColor
            Layout.maximumWidth: Kirigami.Units.gridUnit * 24
            Accessible.name: (barra.pista !== "" ? "Pista: " : "Selección: ") + text
        }
    }
}
