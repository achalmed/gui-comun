// BarraFlotante (4.2) — un contenedor que flota sobre el contenido (una barra de selección, de herramientas de un
// lienzo, de acciones de lo elegido): fondo de la vista, radio, borde tenue y sombra, todo derivado del tema, legible
// en claro y en oscuro. Lo de dentro se declara como `contentItem` (un RowLayout, un GridLayout…). Nació de la barra
// de la selección de Ñawinchay.
//     BarraFlotante { anchors.horizontalCenter: parent.horizontalCenter; anchors.bottom: parent.bottom
//                     contentItem: RowLayout { … } }
import QtQuick
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

QQC2.Pane {
    id: raiz
    // ¿el fondo es oscuro? (para dosificar la sombra y el borde)
    readonly property bool oscuro: Kirigami.ColorUtils.brightnessForColor(Kirigami.Theme.backgroundColor) === Kirigami.ColorUtils.Dark
    // la sombra; sin ella (`elevada: false`) queda solo el borde, para una barra que va dentro de un panel
    property bool elevada: true

    padding: Kirigami.Units.smallSpacing + Kirigami.Units.smallSpacing / 2
    Kirigami.Theme.colorSet: Kirigami.Theme.View
    Kirigami.Theme.inherit: false

    background: Kirigami.ShadowedRectangle {
        color: Kirigami.Theme.backgroundColor
        radius: Kirigami.Units.cornerRadius * 2
        border.width: 1
        border.color: Kirigami.ColorUtils.linearInterpolation(Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor, raiz.oscuro ? 0.22 : 0.16)
        shadow.size: raiz.elevada ? Kirigami.Units.gridUnit : 0
        shadow.yOffset: raiz.elevada ? Kirigami.Units.smallSpacing / 2 : 0
        shadow.color: Qt.alpha(Qt.darker(Kirigami.Theme.backgroundColor, raiz.oscuro ? 4 : 2.5), raiz.oscuro ? 0.6 : 0.3)
    }
}
