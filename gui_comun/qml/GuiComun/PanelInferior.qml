// PanelInferior — el panel acoplable de abajo (como el terminal de Dolphin o la salida de Kate): pestañas Salida y
// Registro sobre `gui_comun.consola.Consola`, con fuente monoespaciada y resaltado de KSyntaxHighlighting, más las
// pestañas que el studio añada (`extras`: [{titulo, componente}]). Botones de limpiar y cerrar.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

QQC2.Control {
    id: panel

    property var consola
    property string definicion: "Bash"
    property var extras: []
    property alias pestanaActual: pestanas.currentIndex
    property int altoPreferido: Kirigami.Units.gridUnit * 9
    property int altoMinimo: Kirigami.Units.gridUnit * 5
    signal cerrar()

    implicitHeight: altoPreferido
    padding: 0
    Kirigami.Theme.colorSet: Kirigami.Theme.View
    Kirigami.Theme.inherit: false
    Accessible.name: "Panel inferior"

    function mostrarSalida() { pestanas.currentIndex = 0 }
    function mostrarRegistro() { pestanas.currentIndex = 1 }
    function mostrarExtra(i) { pestanas.currentIndex = 2 + i }

    background: Rectangle { color: Kirigami.Theme.backgroundColor }

    contentItem: ColumnLayout {
        spacing: 0
        QQC2.ToolBar {
            Layout.fillWidth: true
            position: QQC2.ToolBar.Header
            RowLayout {
                anchors.fill: parent
                spacing: Kirigami.Units.smallSpacing
                QQC2.TabBar {
                    id: pestanas
                    QQC2.TabButton { text: "Salida"; width: implicitWidth }
                    QQC2.TabButton { text: "Registro"; width: implicitWidth }
                    Repeater {
                        model: panel.extras
                        delegate: QQC2.TabButton {
                            required property var modelData
                            text: modelData.titulo
                            width: implicitWidth
                        }
                    }
                }
                Item { Layout.fillWidth: true }
                QQC2.ToolButton {
                    icon.name: "edit-clear-history"
                    text: "Limpiar"
                    display: QQC2.AbstractButton.IconOnly
                    QQC2.ToolTip.text: "Limpiar"
                    QQC2.ToolTip.visible: hovered
                    Accessible.name: text
                    onClicked: {
                        if (!panel.consola) return
                        if (pestanas.currentIndex === 0) panel.consola.salida.limpiar()
                        else if (pestanas.currentIndex === 1) panel.consola.registro.limpiar()
                    }
                }
                QQC2.ToolButton {
                    icon.name: "window-close"
                    text: "Cerrar"
                    display: QQC2.AbstractButton.IconOnly
                    QQC2.ToolTip.text: "Cerrar el panel (F4)"
                    QQC2.ToolTip.visible: hovered
                    Accessible.name: text
                    onClicked: panel.cerrar()
                }
            }
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: pestanas.currentIndex

            QQC2.ScrollView {
                id: vistaSalida
                QQC2.TextArea {
                    id: salida
                    readOnly: true
                    font: Kirigami.Theme.fixedWidthFont
                    wrapMode: TextEdit.NoWrap
                    background: null
                    text: panel.consola ? panel.consola.salida.texto : ""
                    selectByMouse: true
                    Accessible.name: "Salida"
                    onTextChanged: cursorPosition = length
                    Loader {
                        source: "ResaltadoSalida.qml"
                        onLoaded: { item.nombreDefinicion = panel.definicion; item.textEdit = salida }
                    }
                }
            }
            QQC2.ScrollView {
                QQC2.TextArea {
                    id: registro
                    readOnly: true
                    font: Kirigami.Theme.fixedWidthFont
                    wrapMode: TextEdit.NoWrap
                    background: null
                    text: panel.consola ? panel.consola.registro.textoConHora : ""
                    selectByMouse: true
                    Accessible.name: "Registro"
                    onTextChanged: cursorPosition = length
                }
            }
            Repeater {
                model: panel.extras
                delegate: Loader {
                    required property var modelData
                    sourceComponent: modelData.componente
                }
            }
        }
    }
}
