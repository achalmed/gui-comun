// BotonPrincipal (4.2) — la acción principal de un diálogo, una tarjeta o un panel («Guardar la ficha», «Confirmar»,
// «Aplicar»): relleno del acento del tema y texto en su color de contraste, para que se distinga a simple vista de los
// botones secundarios. Hace falta porque con el estilo Kvantum el `highlighted` de un Button de QQC2 no pinta nada.
// Se aviva al pasar el ratón, se oscurece al pulsar, lleva un anillo con el foco del teclado y se apaga si está
// deshabilitado. Con `accion` (una Accion de Python) sigue su texto, icono y habilitado y la dispara, como BotonAccion.
//     BotonPrincipal { text: "Guardar la ficha"; icon.name: "document-save"; onClicked: … }
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

QQC2.Button {
    id: raiz
    property QtObject accion: null

    text: accion ? accion.textoPlano : ""
    icon.name: accion ? accion.icono : ""
    enabled: accion ? accion.habilitada : true
    onClicked: if (accion) accion.disparar()
    Accessible.name: text

    hoverEnabled: true
    leftPadding: Kirigami.Units.largeSpacing + Kirigami.Units.smallSpacing
    rightPadding: Kirigami.Units.largeSpacing + Kirigami.Units.smallSpacing
    topPadding: Kirigami.Units.smallSpacing + Kirigami.Units.smallSpacing / 2
    bottomPadding: Kirigami.Units.smallSpacing + Kirigami.Units.smallSpacing / 2

    background: Rectangle {
        implicitHeight: Kirigami.Units.gridUnit * 1.75
        radius: Kirigami.Units.cornerRadius
        color: !raiz.enabled ? Kirigami.ColorUtils.tintWithAlpha(Kirigami.Theme.backgroundColor, Kirigami.Theme.highlightColor, 0.35)
             : raiz.down ? Qt.darker(Kirigami.Theme.highlightColor, 1.18)
             : raiz.hovered ? Qt.lighter(Kirigami.Theme.highlightColor, 1.10)
             : Kirigami.Theme.highlightColor
        border.width: raiz.visualFocus ? 2 : 0
        border.color: Kirigami.ColorUtils.linearInterpolation(Kirigami.Theme.highlightColor, Kirigami.Theme.highlightedTextColor, 0.6)
        Behavior on color { ColorAnimation { duration: Kirigami.Units.shortDuration } }
    }
    contentItem: RowLayout {
        spacing: Kirigami.Units.smallSpacing
        Item { Layout.fillWidth: true }
        Kirigami.Icon {
            visible: raiz.icon.name !== ""
            source: raiz.icon.name
            color: Kirigami.Theme.highlightedTextColor
            isMask: true
            implicitWidth: Kirigami.Units.iconSizes.small
            implicitHeight: implicitWidth
        }
        QQC2.Label {
            text: raiz.text
            color: Kirigami.Theme.highlightedTextColor
            font.weight: Font.DemiBold
            opacity: raiz.enabled ? 1 : 0.7
        }
        Item { Layout.fillWidth: true }
    }
}
