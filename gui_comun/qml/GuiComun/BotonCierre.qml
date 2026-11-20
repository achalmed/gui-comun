// BotonCierre (4.2) — cerrar o soltar algo (un panel, una barra, una búsqueda, una pestaña): una X monocroma y
// discreta, que se aviva al pasar el ratón. Los iconos `window-close`, `dialog-close` y `tab-close` de varios temas
// de iconos (Colloid, Papirus) son círculos rojos que gritan más que el contenido: la X se dibuja. `text` es lo que hace (la ayuda emergente y el nombre accesible).
//     BotonCierre { text: "Cerrar el panel (Esc)"; onClicked: … }
import QtQuick
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

QQC2.ToolButton {
    id: raiz
    text: "Cerrar"
    display: QQC2.AbstractButton.IconOnly
    Accessible.name: text
    QQC2.ToolTip.text: text
    QQC2.ToolTip.visible: hovered
    QQC2.ToolTip.delay: Kirigami.Units.toolTipDelay
    // 4.2: la X dibujada con dos trazos del color del texto, no un icono: el del tema puede venir con un color fijo
    // (Colloid oscuro la trae casi blanca, invisible en un esquema claro) o ser un círculo rojo
    contentItem: Item {
        implicitWidth: Kirigami.Units.iconSizes.small
        implicitHeight: Kirigami.Units.iconSizes.small
        opacity: !raiz.enabled ? 0.35 : raiz.hovered || raiz.visualFocus || raiz.pressed ? 1 : 0.7
        Repeater {
            model: [45, -45]
            delegate: Rectangle {
                required property int modelData
                anchors.centerIn: parent
                width: parent.width * 0.78
                height: 1.5
                radius: height / 2
                rotation: modelData
                antialiasing: true
                color: Kirigami.Theme.textColor
            }
        }
    }
}
