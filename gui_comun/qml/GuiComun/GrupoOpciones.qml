// GrupoOpciones (4.2) — un «pozo» tenue que agrupa opciones hermanas en fila (OpcionColor, ToolButton, casillas): un
// contenedor en forma de píldora, apenas más oscuro (o más claro) que su fondo, que separa el grupo de lo de al lado
// mejor que una raya. Lo de dentro se declara como hijo. `titulo` es su nombre para lectores de pantalla.
//     GrupoOpciones { titulo: "Anotar como"; Repeater { model: …; delegate: OpcionColor { … } } }
import QtQuick
import org.kde.kirigami as Kirigami

Rectangle {
    id: raiz
    property string titulo: ""
    default property alias contenido: fila.data
    readonly property bool oscuro: Kirigami.ColorUtils.brightnessForColor(Kirigami.Theme.backgroundColor) === Kirigami.ColorUtils.Dark
    readonly property real holgura: Kirigami.Units.smallSpacing / 2

    implicitWidth: fila.implicitWidth + (holgura + border.width) * 2
    implicitHeight: fila.implicitHeight + (holgura + border.width) * 2
    radius: height / 2
    color: Kirigami.ColorUtils.linearInterpolation(Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor, oscuro ? 0.07 : 0.05)
    border.width: 1
    border.color: Kirigami.ColorUtils.linearInterpolation(Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor, oscuro ? 0.12 : 0.10)
    Accessible.role: Accessible.Grouping
    Accessible.name: titulo

    Row {
        id: fila
        anchors.centerIn: parent
        spacing: Kirigami.Units.smallSpacing / 2
    }
}
