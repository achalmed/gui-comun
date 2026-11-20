// PasosEscritura (3.1) — los seis pasos de una escritura, visibles (encargo del autor del 2026-11-02, §3.2): Plan ·
// Afectados · Conflictos · Ejecutar · Verificar · Informe. Cada paso con su número, su estado (hecho, el siguiente,
// pendiente) y una cuenta corta («12», «✓»); al elegirlo, el studio muestra su contenido debajo. Un paso no alcanzado
// no se abre. Filesystem y Lliphi lo tenían igual (y Biblioteca, en vertical: LineaPasos); el plan, la verificación
// y el informe comunes están en gui_comun.pasos.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

RowLayout {
    id: raiz
    property var pasos: ["Plan", "Afectados", "Conflictos", "Ejecutar", "Verificar", "Informe"]
    property int alcanzado: 0          // 1…6: el último hecho
    property int actual: 0             // 0…5: el que se muestra
    property var cuentas: []           // un texto corto por paso (gui_comun.pasos.cuentas)
    property bool bloqueado: false     // un conflicto que bloquea: «Ejecutar» se marca en negativo
    signal elegido(int paso)
    spacing: 0
    Accessible.name: "Pasos de la operación"

    // 4.2: cada paso, una píldora con su insignia redonda (✓ hecho, su número el siguiente y los pendientes, ✕ si un
    // conflicto lo frena); la elegida, teñida del acento con borde; la línea entre pasos, del acento hasta el alcanzado
    readonly property bool oscuro: Kirigami.ColorUtils.brightnessForColor(Kirigami.Theme.backgroundColor) === Kirigami.ColorUtils.Dark
    Repeater {
        model: raiz.pasos
        delegate: RowLayout {
            id: tramo
            required property string modelData
            required property int index
            spacing: 0
            // en poco ancho, cada paso se encoge (y su texto se corta) en vez de ensanchar a quien lo contiene
            Layout.fillWidth: true
            // el paso elegido no se encoge; los demás ceden su texto
            Layout.minimumWidth: tramo.index === raiz.actual ? implicitWidth : Kirigami.Units.gridUnit * 3.5
            Layout.maximumWidth: implicitWidth
            Rectangle {          // la línea que viene del paso anterior
                visible: tramo.index > 0
                Layout.preferredWidth: Kirigami.Units.gridUnit * 0.6
                Layout.preferredHeight: 2
                Layout.alignment: Qt.AlignVCenter
                radius: 1
                color: tramo.index <= raiz.alcanzado ? Kirigami.ColorUtils.tintWithAlpha(Kirigami.Theme.backgroundColor, Kirigami.Theme.highlightColor, 0.6)
                     : Kirigami.ColorUtils.linearInterpolation(Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor, 0.18)
            }
            QQC2.AbstractButton {
                id: paso
                Layout.fillWidth: true
                Layout.minimumWidth: Kirigami.Units.gridUnit * 2.5
                readonly property bool hecho: tramo.index < raiz.alcanzado
                readonly property bool siguiente: tramo.index === raiz.alcanzado
                readonly property bool frenado: raiz.bloqueado && tramo.index === 3
                readonly property color tono: frenado ? Kirigami.Theme.negativeTextColor : hecho ? Kirigami.Theme.positiveTextColor : Kirigami.Theme.highlightColor
                checkable: true
                checked: tramo.index === raiz.actual
                enabled: tramo.index <= raiz.alcanzado
                hoverEnabled: true
                text: tramo.modelData
                onClicked: raiz.elegido(tramo.index)
                Accessible.name: "Paso " + (tramo.index + 1) + ": " + tramo.modelData + (frenado ? ", bloqueado" : hecho ? ", hecho" : siguiente ? ", siguiente" : ", pendiente")
                QQC2.ToolTip.text: Accessible.name + (raiz.cuentas[tramo.index] ? " · " + raiz.cuentas[tramo.index] : "")
                QQC2.ToolTip.visible: hovered
                QQC2.ToolTip.delay: Kirigami.Units.toolTipDelay
                leftPadding: Kirigami.Units.smallSpacing
                rightPadding: Kirigami.Units.smallSpacing * 2
                topPadding: Kirigami.Units.smallSpacing
                bottomPadding: Kirigami.Units.smallSpacing
                implicitWidth: implicitContentWidth + leftPadding + rightPadding
                implicitHeight: implicitContentHeight + topPadding + bottomPadding
                background: Rectangle {
                    radius: height / 2
                    color: paso.checked ? Kirigami.ColorUtils.tintWithAlpha(Kirigami.Theme.backgroundColor, Kirigami.Theme.highlightColor, paso.hovered ? 0.30 : 0.22)
                         : paso.hovered && paso.enabled ? Kirigami.ColorUtils.tintWithAlpha(Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor, 0.07)
                         : "transparent"
                    border.width: paso.visualFocus ? 2 : paso.checked ? 1 : 0
                    border.color: Kirigami.ColorUtils.tintWithAlpha(Kirigami.Theme.backgroundColor, Kirigami.Theme.highlightColor, 0.6)
                    Behavior on color { ColorAnimation { duration: Kirigami.Units.shortDuration } }
                }
                contentItem: RowLayout {
                    spacing: Kirigami.Units.smallSpacing
                    Rectangle {          // la insignia
                        Layout.alignment: Qt.AlignVCenter
                        implicitWidth: Kirigami.Units.gridUnit * 1.1
                        implicitHeight: implicitWidth
                        radius: width / 2
                        color: paso.hecho || paso.frenado ? Kirigami.ColorUtils.tintWithAlpha(Kirigami.Theme.backgroundColor, paso.tono, raiz.oscuro ? 0.35 : 0.22)
                             : paso.siguiente ? Kirigami.ColorUtils.tintWithAlpha(Kirigami.Theme.backgroundColor, Kirigami.Theme.highlightColor, 0.18)
                             : "transparent"
                        border.width: 1
                        border.color: paso.enabled ? Kirigami.ColorUtils.tintWithAlpha(Kirigami.Theme.backgroundColor, paso.tono, 0.7)
                                    : Kirigami.ColorUtils.linearInterpolation(Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor, 0.3)
                        Kirigami.Icon {
                            anchors.centerIn: parent
                            visible: paso.hecho || paso.frenado
                            width: Kirigami.Units.iconSizes.small * 0.75
                            height: width
                            source: paso.frenado ? "close-symbolic" : "checkmark"
                            fallback: paso.frenado ? "window-close-symbolic" : "dialog-ok-apply"
                            isMask: true
                            color: paso.tono
                        }
                        QQC2.Label {
                            anchors.centerIn: parent
                            visible: !paso.hecho && !paso.frenado
                            text: tramo.index + 1
                            font: Kirigami.Theme.smallFont
                            color: paso.enabled ? Kirigami.Theme.textColor : Kirigami.Theme.disabledTextColor
                        }
                    }
                    QQC2.Label {
                        Layout.fillWidth: true
                        text: tramo.modelData
                        elide: Text.ElideRight
                        font.weight: paso.checked ? Font.DemiBold : Font.Normal
                        color: paso.enabled ? Kirigami.Theme.textColor : Kirigami.Theme.disabledTextColor
                    }
                    QQC2.Label {
                        visible: text !== ""
                        text: raiz.cuentas[tramo.index] || ""
                        font: Kirigami.Theme.smallFont
                        color: paso.frenado ? Kirigami.Theme.negativeTextColor : Kirigami.Theme.disabledTextColor
                    }
                }
            }
        }
    }
    Item { Layout.fillWidth: true }
}
