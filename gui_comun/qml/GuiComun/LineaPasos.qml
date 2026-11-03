// LineaPasos (3.1) — los pasos de un proceso como línea de tiempo vertical, cada uno con su estado (pendiente,
// en_curso, hecho, fallo, omitido: gui_comun.pasos.ESTADOS) y su detalle (o su explicación mientras no lo tiene): la
// puerta de escritura de Biblioteca (de donde viene: PasosPuerta), las fases de una auditoría (Huella). Con
// `elegible`, un clic en un paso emite `elegido(indice)`. Pasos: [{titulo, explicacion, estado, detalle}].
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

ColumnLayout {
    id: raiz
    property var pasos: []
    property string titulo: ""
    property string resumen: ""
    property bool elegible: false
    property int actual: -1
    signal elegido(int indice)
    visible: pasos.length > 0
    spacing: Kirigami.Units.smallSpacing
    Accessible.name: titulo !== "" ? titulo : "Pasos"

    function icono(estado) {
        switch (estado) {
        case "hecho": return "data-success"
        case "fallo": return "data-error"
        case "omitido": return "dialog-cancel"
        case "en_curso": return "view-refresh"
        default: return ""
        }
    }
    function color(estado) {
        switch (estado) {
        case "hecho": return Kirigami.Theme.positiveTextColor
        case "fallo": return Kirigami.Theme.negativeTextColor
        case "en_curso": return Kirigami.Theme.highlightColor
        default: return Kirigami.Theme.disabledTextColor
        }
    }

    RowLayout {
        Layout.fillWidth: true
        visible: raiz.titulo !== "" || raiz.resumen !== ""
        Kirigami.Heading { level: 4; text: raiz.titulo }
        Item { Layout.fillWidth: true }
        QQC2.Label {
            text: raiz.resumen
            color: Kirigami.Theme.disabledTextColor
            font: Kirigami.Theme.smallFont
            elide: Text.ElideRight
            Layout.maximumWidth: raiz.width * 0.6
        }
    }
    Repeater {
        model: raiz.pasos
        delegate: RowLayout {
            id: paso
            required property var modelData
            required property int index
            Layout.fillWidth: true
            spacing: Kirigami.Units.largeSpacing
            Accessible.role: raiz.elegible ? Accessible.Button : Accessible.StaticText
            Accessible.name: (index + 1) + ". " + modelData.titulo + ": " + modelData.estado + (modelData.detalle ? ", " + modelData.detalle : "")
            // el número sobre la línea que une los pasos
            Item {
                Layout.preferredWidth: Kirigami.Units.iconSizes.medium
                Layout.fillHeight: true
                Layout.minimumHeight: Kirigami.Units.gridUnit * 2.2
                Rectangle {
                    anchors.horizontalCenter: parent.horizontalCenter
                    y: parent.height / 2
                    width: 2
                    height: parent.height / 2 + Kirigami.Units.smallSpacing
                    visible: paso.index < raiz.pasos.length - 1
                    color: Kirigami.Theme.disabledTextColor
                    opacity: 0.4
                }
                Rectangle {                            // en espera: un círculo vacío
                    anchors.centerIn: parent
                    visible: paso.modelData.estado === "pendiente"
                    width: Kirigami.Units.iconSizes.small
                    height: width
                    radius: width / 2
                    color: Kirigami.Theme.backgroundColor
                    border.color: Kirigami.Theme.disabledTextColor
                    border.width: 2
                }
                Kirigami.Icon {
                    anchors.centerIn: parent
                    visible: paso.modelData.estado !== "pendiente"
                    width: Kirigami.Units.iconSizes.smallMedium
                    height: width
                    source: raiz.icono(paso.modelData.estado)
                    color: raiz.color(paso.modelData.estado)
                }
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 0
                TapHandler { enabled: raiz.elegible; onTapped: raiz.elegido(paso.index) }
                QQC2.Label {
                    Layout.fillWidth: true
                    text: (paso.index + 1) + ". " + paso.modelData.titulo
                    font.underline: raiz.elegible && paso.index === raiz.actual
                    font.weight: paso.modelData.estado === "en_curso" || paso.modelData.estado === "fallo" ? Font.DemiBold : Font.Normal
                    color: paso.modelData.estado === "fallo" ? Kirigami.Theme.negativeTextColor : Kirigami.Theme.textColor
                    elide: Text.ElideRight
                }
                QQC2.Label {
                    Layout.fillWidth: true
                    text: paso.modelData.detalle || paso.modelData.explicacion
                    color: Kirigami.Theme.disabledTextColor
                    font: Kirigami.Theme.smallFont
                    wrapMode: Text.WordWrap
                }
            }
        }
    }
}
