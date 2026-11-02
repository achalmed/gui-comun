// ListaDiagnosticos (2.3) — la lista de errores y avisos de una herramienta: cada uno con su nivel (icono y color
// semántico), su mensaje (en varias líneas si hace falta), su archivo y su línea; Intro o doble clic «va a» (el studio
// abre el editor en esa línea). Lo que la pestaña Problemas de LaTeX Studio pidió y que una tabla no da en un panel
// de detalles: mensajes largos que se leen enteros. Sin colores propios: Kirigami.Theme y Kirigami.Units.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

QQC2.Control {
    id: raiz

    // un modelo de lista con los roles `nivel` (error · aviso · informacion · tipografia · otro), `mensaje`, `archivo`,
    // `linea` (número; 0 o vacío: sin línea) y, opcional, `detalle` (p. ej. gui_comun.modelos.ModeloLista)
    property var modelo
    property string mensajeVacio: ""
    property string iconoVacio: "data-success"
    property string nombreAccesible: "Diagnósticos"
    property QQC2.Menu menuContextual: null
    readonly property alias vista: lista
    readonly property int filaActual: lista.currentIndex
    readonly property int filas: lista.count

    signal activada(int fila)
    signal filaActualCambiada(int fila)

    function seleccionarFila(fila) { lista.currentIndex = fila }
    function iconoDe(nivel) {
        switch (nivel) {
        case "error": return "data-error"
        case "aviso": return "data-warning"
        case "informacion": return "data-information"
        case "tipografia": return "format-justify-fill"
        default: return "dialog-information"
        }
    }
    function colorDe(nivel) {
        switch (nivel) {
        case "error": return Kirigami.Theme.negativeTextColor
        case "aviso": return Kirigami.Theme.neutralTextColor
        case "informacion": return Kirigami.Theme.activeTextColor
        default: return Kirigami.Theme.disabledTextColor
        }
    }
    function textoNivel(nivel) {
        switch (nivel) {
        case "error": return "Error"
        case "aviso": return "Aviso"
        case "informacion": return "Información"
        case "tipografia": return "Tipografía"
        default: return nivel
        }
    }

    implicitWidth: Kirigami.Units.gridUnit * 20
    implicitHeight: Kirigami.Units.gridUnit * 12
    padding: 0
    Kirigami.Theme.colorSet: Kirigami.Theme.View
    Kirigami.Theme.inherit: false
    Accessible.role: Accessible.List
    Accessible.name: nombreAccesible

    background: Rectangle { color: Kirigami.Theme.backgroundColor }

    contentItem: QQC2.ScrollView {
        QQC2.ScrollBar.horizontal.policy: QQC2.ScrollBar.AlwaysOff
        ListView {
            id: lista
            clip: true
            model: raiz.modelo
            currentIndex: -1
            keyNavigationEnabled: true
            activeFocusOnTab: true
            onCurrentIndexChanged: raiz.filaActualCambiada(currentIndex)
            Keys.onReturnPressed: if (currentIndex >= 0) raiz.activada(currentIndex)
            Keys.onEnterPressed: if (currentIndex >= 0) raiz.activada(currentIndex)
            delegate: QQC2.ItemDelegate {
                id: fila
                required property int index
                required property var model
                readonly property string nivel: model.nivel !== undefined ? String(model.nivel) : ""
                readonly property string donde: {
                    const partes = []
                    if (model.archivo) partes.push(model.archivo)
                    if (model.linea && Number(model.linea) > 0) partes.push("línea " + model.linea)
                    return partes.join(" · ")
                }
                width: ListView.view.width
                highlighted: ListView.isCurrentItem
                onClicked: lista.currentIndex = index
                onDoubleClicked: { lista.currentIndex = index; raiz.activada(index) }
                Accessible.name: raiz.textoNivel(nivel) + ": " + (model.mensaje || "") + (donde ? ", " + donde : "")
                TapHandler {
                    acceptedButtons: Qt.RightButton
                    onTapped: { lista.currentIndex = fila.index; if (raiz.menuContextual) raiz.menuContextual.popup() }
                }
                contentItem: RowLayout {
                    spacing: Kirigami.Units.smallSpacing * 2
                    Kirigami.Icon {
                        source: raiz.iconoDe(fila.nivel)
                        color: raiz.colorDe(fila.nivel)
                        implicitWidth: Kirigami.Units.iconSizes.smallMedium
                        implicitHeight: implicitWidth
                        Layout.alignment: Qt.AlignTop
                        Layout.topMargin: Kirigami.Units.smallSpacing / 2
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 0
                        QQC2.Label {
                            Layout.fillWidth: true
                            text: fila.model.mensaje || ""
                            wrapMode: Text.Wrap
                            color: fila.highlighted ? Kirigami.Theme.highlightedTextColor : Kirigami.Theme.textColor
                        }
                        QQC2.Label {
                            Layout.fillWidth: true
                            visible: text !== ""
                            text: (fila.donde ? fila.donde : "") + (fila.model.detalle ? (fila.donde ? " · " : "") + fila.model.detalle : "")
                            elide: Text.ElideMiddle
                            font: Kirigami.Theme.smallFont
                            color: fila.highlighted ? Kirigami.Theme.highlightedTextColor : Kirigami.Theme.disabledTextColor
                        }
                    }
                    QQC2.Label {
                        text: raiz.textoNivel(fila.nivel)
                        font: Kirigami.Theme.smallFont
                        color: fila.highlighted ? Kirigami.Theme.highlightedTextColor : raiz.colorDe(fila.nivel)
                        Layout.alignment: Qt.AlignTop
                    }
                }
            }
        }
    }

    Kirigami.PlaceholderMessage {
        anchors.centerIn: parent
        width: parent.width - Kirigami.Units.gridUnit * 4
        visible: lista.count === 0 && raiz.mensajeVacio !== ""
        text: raiz.mensajeVacio
        icon.name: raiz.iconoVacio
    }
}
