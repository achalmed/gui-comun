// OpcionColor (4.2) — una opción con forma de píldora y, si se le da, su punto de color (una intención de lectura, una
// etiqueta, un estado): reconocible como botón, se tiñe de su color al pasar el ratón, va rellena y con borde cuando es
// la `elegida`, y con el foco del teclado lleva un borde doble de su color. El color es un DATO (llega de Python o del
// modelo), no un color propio de la ventana; sin color, usa el acento del tema. La ayuda emergente dice `descripcion`
// y su `atajo`. Va bien dentro de un GrupoOpciones. Nació de las intenciones de la barra de Ñawinchay.
//     OpcionColor { text: "Cita"; color: modelo.color; atajo: "Alt+1"; elegida: actual === "cita"; onClicked: … }
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

QQC2.AbstractButton {
    id: raiz
    // el color de la opción (un dato); vacío: el acento del tema y sin punto
    property color color: "transparent"
    readonly property bool conColor: color.a > 0
    readonly property color tono: conColor ? color : Kirigami.Theme.highlightColor
    property bool elegida: false
    property string atajo: ""
    property string descripcion: ""
    // más ceñida (el celular, una barra estrecha)
    property bool compacta: false
    // el icono con el color del texto (como los simbólicos): en un selector, iconos a todo color de temas distintos
    // desentonan; false, el icono tal cual
    property bool iconoMonocromo: true

    hoverEnabled: true
    focusPolicy: Qt.TabFocus
    Accessible.name: text + (elegida ? ", elegida" : "")
    QQC2.ToolTip.text: (descripcion || text) + (atajo ? " · " + atajo : "")
    QQC2.ToolTip.visible: (hovered || visualFocus) && QQC2.ToolTip.text !== ""
    QQC2.ToolTip.delay: Kirigami.Units.toolTipDelay

    readonly property real holgura: compacta ? Kirigami.Units.smallSpacing : Kirigami.Units.smallSpacing * 2
    leftPadding: holgura
    rightPadding: holgura + (conColor ? Kirigami.Units.smallSpacing / 2 : 0)
    topPadding: Kirigami.Units.smallSpacing
    bottomPadding: Kirigami.Units.smallSpacing
    implicitWidth: implicitContentWidth + leftPadding + rightPadding
    implicitHeight: Math.max(Kirigami.Units.gridUnit * 1.5, implicitContentHeight + topPadding + bottomPadding)

    background: Rectangle {
        radius: height / 2
        color: raiz.pressed ? Kirigami.ColorUtils.tintWithAlpha(Kirigami.Theme.backgroundColor, raiz.tono, 0.42)
             : raiz.elegida ? Kirigami.ColorUtils.tintWithAlpha(Kirigami.Theme.backgroundColor, raiz.tono, raiz.hovered ? 0.36 : 0.28)
             : raiz.hovered ? Kirigami.ColorUtils.tintWithAlpha(Kirigami.Theme.backgroundColor, raiz.tono, 0.16)
             : "transparent"
        // el foco por teclado, un borde doble del color de la opción: el color de foco del tema podría confundirse
        // con otra opción (en Lliphi es rojo)
        border.width: raiz.visualFocus ? 2 : 1
        border.color: raiz.visualFocus || raiz.elegida ? raiz.tono
                    : raiz.hovered ? Kirigami.ColorUtils.tintWithAlpha(Kirigami.Theme.backgroundColor, raiz.tono, 0.55)
                    : "transparent"
        Behavior on color { ColorAnimation { duration: Kirigami.Units.shortDuration } }
    }
    contentItem: RowLayout {
        spacing: Kirigami.Units.smallSpacing + Kirigami.Units.smallSpacing / 2
        Rectangle {
            visible: raiz.conColor
            Layout.alignment: Qt.AlignVCenter
            implicitWidth: Kirigami.Units.smallSpacing * 2.5
            implicitHeight: implicitWidth
            radius: width / 2
            color: raiz.tono
            border.width: 1
            border.color: Kirigami.ColorUtils.linearInterpolation(raiz.tono, Kirigami.Theme.textColor, 0.3)
        }
        Kirigami.Icon {
            visible: raiz.icon.name !== ""
            source: raiz.icon.name
            isMask: raiz.iconoMonocromo
            color: Kirigami.Theme.textColor
            Layout.alignment: Qt.AlignVCenter
            implicitWidth: Kirigami.Units.iconSizes.small
            implicitHeight: implicitWidth
        }
        QQC2.Label {
            visible: raiz.text !== "" && raiz.display !== QQC2.AbstractButton.IconOnly
            text: raiz.text
            font.weight: raiz.elegida ? Font.DemiBold : Font.Normal
        }
    }
}
