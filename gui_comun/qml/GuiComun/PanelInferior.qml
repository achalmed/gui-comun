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
    property int pestanaActual: 0
    property int altoPreferido: Kirigami.Units.gridUnit * 9
    property int altoMinimo: Kirigami.Units.gridUnit * 5
    signal cerrar()

    implicitHeight: altoPreferido
    padding: 0
    readonly property bool oscuro: Kirigami.Theme.backgroundColor.hslLightness < 0.5
    Kirigami.Theme.colorSet: Kirigami.Theme.View
    Kirigami.Theme.inherit: false
    Accessible.name: "Panel inferior"

    function mostrarSalida() { panel.pestanaActual = 0 }
    function mostrarRegistro() { panel.pestanaActual = 1 }
    function mostrarExtra(i) { panel.pestanaActual = 2 + i }

    background: Rectangle { color: Kirigami.Theme.backgroundColor }

    contentItem: ColumnLayout {
        spacing: 0
        QQC2.ToolBar {
            Layout.fillWidth: true
            position: QQC2.ToolBar.Header
            RowLayout {
                anchors.fill: parent
                spacing: Kirigami.Units.smallSpacing
                SelectorSegmentado {          // 4.2: en lugar del TabBar
                    id: pestanas
                    objectName: "pestanasInferior"
                    compacto: true
                    opciones: [{ clave: "0", texto: "Salida", icono: "utilities-terminal" }, { clave: "1", texto: "Registro", icono: "view-history" }]
                              .concat((panel.extras || []).map((e, i) => ({ clave: String(2 + i), texto: e.titulo })))
                    actual: String(panel.pestanaActual)
                    onElegida: clave => panel.pestanaActual = parseInt(clave)
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
                        if (panel.pestanaActual === 0) panel.consola.salida.limpiar()
                        else if (panel.pestanaActual === 1) panel.consola.registro.limpiar()
                    }
                }
                BotonCierre {          // 4.2: la X neutra (el window-close de algunos temas es un círculo rojo)
                    text: "Cerrar el panel (F4)"
                    onClicked: panel.cerrar()
                }
            }
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: panel.pestanaActual

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
                    onTextChanged: cursorPosition = text.lastIndexOf("\n") + 1     // la última línea, sin desplazar a la derecha
                    Loader {          // 4.2: con el tema de KSyntaxHighlighting claro u oscuro (en oscuro se leía apenas)
                        source: "ResaltadoEditor.qml"
                        onLoaded: { item.nombreDefinicion = panel.definicion; item.oscuro = Qt.binding(() => panel.oscuro); item.textEdit = salida }
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
                    onTextChanged: cursorPosition = text.lastIndexOf("\n") + 1
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
