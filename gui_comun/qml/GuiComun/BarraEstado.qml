// BarraEstado — el pie de la ventana: el resumen de la colección a la izquierda, la tarea en curso con su progreso y
// «n de m» en medio (solo mientras hay tarea; un clic abre el panel inferior; cancelar al lado), el contexto de la
// selección a la derecha. Es donde van las cifras que antes eran tarjetas.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

QQC2.ToolBar {
    id: barra

    property string resumen: ""
    property string contexto: ""
    property var tareas
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
                elide: Text.ElideMiddle
                Layout.maximumWidth: Kirigami.Units.gridUnit * 22
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
        QQC2.ToolSeparator { visible: barra.contexto !== "" }
        QQC2.Label {
            visible: barra.contexto !== ""
            text: barra.contexto
            elide: Text.ElideMiddle
            Layout.maximumWidth: Kirigami.Units.gridUnit * 24
            Accessible.name: "Selección: " + text
        }
    }
}
