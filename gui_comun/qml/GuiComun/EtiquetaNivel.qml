// EtiquetaNivel (3.1) — una etiqueta redondeada con el color semántico de un nivel (positivo, neutro, negativo,
// activo, inactivo): «instalado», «conflicto», «local»… Dotfiles y Lliphi la tenían igual; Filesystem y Biblioteca la
// dibujaban a mano. Sin colores propios: el texto y el fondo semánticos de Kirigami.Theme.
import QtQuick
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

QQC2.Label {
    id: raiz
    property string nivel: ""
    property string icono: ""
    function colorTexto(n) {
        switch (n) {
        case "positivo": return Kirigami.Theme.positiveTextColor
        case "neutro": return Kirigami.Theme.neutralTextColor
        case "negativo": return Kirigami.Theme.negativeTextColor
        case "activo": return Kirigami.Theme.activeTextColor
        default: return Kirigami.Theme.disabledTextColor
        }
    }
    function colorFondo(n) {
        switch (n) {
        case "positivo": return Kirigami.Theme.positiveBackgroundColor
        case "neutro": return Kirigami.Theme.neutralBackgroundColor
        case "negativo": return Kirigami.Theme.negativeBackgroundColor
        case "activo": return Qt.alpha(Kirigami.Theme.activeTextColor, 0.15)
        default: return Qt.alpha(Kirigami.Theme.textColor, 0.08)
        }
    }
    color: colorTexto(nivel)
    font: Kirigami.Theme.smallFont
    leftPadding: Kirigami.Units.smallSpacing * 2 + (icono !== "" ? Kirigami.Units.iconSizes.small + Kirigami.Units.smallSpacing : 0)
    rightPadding: Kirigami.Units.smallSpacing * 2
    topPadding: Kirigami.Units.smallSpacing / 2
    bottomPadding: Kirigami.Units.smallSpacing / 2
    background: Rectangle { radius: height / 2; color: raiz.colorFondo(raiz.nivel) }
    Accessible.name: text
    Kirigami.Icon {
        visible: raiz.icono !== ""
        source: raiz.icono
        color: raiz.color
        x: Kirigami.Units.smallSpacing * 2
        anchors.verticalCenter: parent.verticalCenter
        implicitWidth: Kirigami.Units.iconSizes.small
        implicitHeight: implicitWidth
    }
}
