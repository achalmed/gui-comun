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

    Repeater {
        model: raiz.pasos
        delegate: RowLayout {
            required property string modelData
            required property int index
            spacing: 0
            // en poco ancho, cada paso se encoge (y su texto se corta) en vez de ensanchar a quien lo contiene
            Layout.fillWidth: true
            Layout.minimumWidth: Kirigami.Units.gridUnit * 3
            Layout.maximumWidth: implicitWidth
            Kirigami.Separator { visible: index > 0; Layout.preferredWidth: Kirigami.Units.gridUnit; Layout.alignment: Qt.AlignVCenter }
            QQC2.ToolButton {
                Layout.fillWidth: true
                Layout.minimumWidth: Kirigami.Units.gridUnit * 2
                QQC2.ToolTip.text: Accessible.name
                QQC2.ToolTip.visible: hovered
                readonly property bool hecho: index < raiz.alcanzado
                readonly property bool siguiente: index === raiz.alcanzado
                readonly property bool frenado: raiz.bloqueado && index === 3
                checkable: true
                checked: index === raiz.actual
                enabled: index <= raiz.alcanzado
                icon.name: frenado ? "dialog-cancel" : hecho ? "checkmark" : (siguiente ? "go-next" : "")
                icon.color: frenado ? Kirigami.Theme.negativeTextColor : Kirigami.Theme.textColor
                text: (index + 1) + " " + modelData + (raiz.cuentas[index] ? " · " + raiz.cuentas[index] : "")
                display: QQC2.AbstractButton.TextBesideIcon
                font.bold: checked
                onClicked: raiz.elegido(index)
                Accessible.name: "Paso " + (index + 1) + ": " + modelData + (frenado ? ", bloqueado" : hecho ? ", hecho" : siguiente ? ", siguiente" : ", pendiente")
            }
        }
    }
    Item { Layout.fillWidth: true }
}
