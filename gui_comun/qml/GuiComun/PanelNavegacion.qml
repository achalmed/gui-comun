// PanelNavegacion — el panel izquierdo compacto (como «Lugares» de Dolphin): secciones con cabecera, filas con icono,
// texto y contador tenue; un clic elige; plegado, solo iconos con su ayuda emergente.
// secciones: [{titulo, filas: [{nombre, texto, icono, contador}]}]
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

QQC2.Control {
    id: panel

    property var secciones: []
    property string actual: ""
    property bool plegado: false
    property int anchoPreferido: Kirigami.Units.gridUnit * 13
    property int anchoMinimo: Kirigami.Units.gridUnit * 9
    signal elegida(string nombre)

    implicitWidth: plegado ? Kirigami.Units.iconSizes.smallMedium + Kirigami.Units.largeSpacing * 3 : anchoPreferido
    padding: Kirigami.Units.smallSpacing
    Kirigami.Theme.colorSet: Kirigami.Theme.Window
    Kirigami.Theme.inherit: false
    Accessible.role: Accessible.List
    Accessible.name: "Navegación"

    background: Rectangle { color: Kirigami.Theme.backgroundColor }

    contentItem: QQC2.ScrollView {
        QQC2.ScrollBar.horizontal.policy: QQC2.ScrollBar.AlwaysOff
        ColumnLayout {
            width: panel.availableWidth
            spacing: 0
            Repeater {
                model: panel.secciones
                delegate: ColumnLayout {
                    id: seccion
                    required property var modelData
                    required property int index
                    Layout.fillWidth: true
                    spacing: 0
                    Kirigami.ListSectionHeader {
                        visible: !panel.plegado
                        text: seccion.modelData.titulo
                        Layout.fillWidth: true
                    }
                    Kirigami.Separator { visible: panel.plegado && seccion.index > 0; Layout.fillWidth: true; Layout.margins: Kirigami.Units.smallSpacing }
                    Repeater {
                        model: seccion.modelData.filas
                        delegate: QQC2.ItemDelegate {
                            id: fila
                            required property var modelData
                            Layout.fillWidth: true
                            highlighted: panel.actual === modelData.nombre
                            text: modelData.texto
                            icon.name: modelData.icono || ""
                            onClicked: { panel.actual = modelData.nombre; panel.elegida(modelData.nombre) }
                            Accessible.name: modelData.texto + (modelData.contador !== undefined ? ", " + modelData.contador : "")
                            QQC2.ToolTip.visible: panel.plegado && hovered
                            QQC2.ToolTip.text: modelData.texto + (modelData.contador !== undefined && modelData.contador !== "" ? " · " + modelData.contador : "")
                            contentItem: RowLayout {
                                spacing: Kirigami.Units.smallSpacing
                                Kirigami.Icon {
                                    source: fila.modelData.icono || "folder"
                                    implicitWidth: Kirigami.Units.iconSizes.small
                                    implicitHeight: implicitWidth
                                    Layout.alignment: Qt.AlignVCenter
                                }
                                QQC2.Label {
                                    visible: !panel.plegado
                                    text: fila.modelData.texto
                                    Layout.fillWidth: true
                                    elide: Text.ElideRight
                                    color: fila.highlighted ? Kirigami.Theme.highlightedTextColor : Kirigami.Theme.textColor
                                }
                                QQC2.Label {
                                    visible: !panel.plegado && fila.modelData.contador !== undefined && fila.modelData.contador !== ""
                                    text: fila.modelData.contador !== undefined ? fila.modelData.contador : ""
                                    font: Kirigami.Theme.smallFont
                                    color: fila.highlighted ? Kirigami.Theme.highlightedTextColor : Kirigami.Theme.disabledTextColor
                                }
                            }
                        }
                    }
                }
            }
            Item { Layout.fillHeight: true }
        }
    }
}
