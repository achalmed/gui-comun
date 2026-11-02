// PaletaOrdenes — Ctrl+Alt+I (KDE) y Ctrl+K: cualquier orden o destino por su nombre, con coincidencia difusa
// (la hace `acciones.buscar` en Python), grupo y atajo a la derecha; ↑ ↓ Intro Esc.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

QQC2.Popup {
    id: paleta

    property var acciones
    property string textoInicial: ""
    property var resultados: []

    x: Math.round((parent.width - width) / 2)
    y: Kirigami.Units.gridUnit * 2
    width: Math.min(Kirigami.Units.gridUnit * 36, parent.width - Kirigami.Units.gridUnit * 4)
    height: Math.min(Kirigami.Units.gridUnit * 22, parent.height - Kirigami.Units.gridUnit * 4)
    modal: true
    focus: true
    padding: 0
    closePolicy: QQC2.Popup.CloseOnEscape | QQC2.Popup.CloseOnPressOutside

    function abrir(texto) {
        campo.text = texto || ""
        buscar()
        open()
        campo.forceActiveFocus()
        campo.selectAll()
    }

    function buscar() {
        resultados = acciones ? acciones.buscar(campo.text) : []
        lista.currentIndex = resultados.length > 0 ? 0 : -1
    }

    function ejecutarActual() {
        if (lista.currentIndex < 0 || lista.currentIndex >= resultados.length) return
        const nombre = resultados[lista.currentIndex].nombre
        paleta.close()
        acciones.ejecutar(nombre)
    }

    onOpened: { buscar(); campo.forceActiveFocus() }

    contentItem: ColumnLayout {
        spacing: 0
        Accessible.name: "Paleta de órdenes"
        Kirigami.SearchField {
            id: campo
            Layout.fillWidth: true
            Layout.margins: Kirigami.Units.smallSpacing
            placeholderText: "Escribe una orden…"
            autoAccept: false
            onTextChanged: paleta.buscar()
            onAccepted: paleta.ejecutarActual()
            Keys.onDownPressed: lista.incrementCurrentIndex()
            Keys.onUpPressed: lista.decrementCurrentIndex()
            Keys.onPressed: event => {
                if (event.key === Qt.Key_PageDown) { lista.currentIndex = Math.min(lista.count - 1, lista.currentIndex + 8); event.accepted = true }
                else if (event.key === Qt.Key_PageUp) { lista.currentIndex = Math.max(0, lista.currentIndex - 8); event.accepted = true }
            }
        }
        Kirigami.Separator { Layout.fillWidth: true }
        ListView {
            id: lista
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: paleta.resultados
            keyNavigationEnabled: true
            highlightMoveDuration: Kirigami.Units.shortDuration
            QQC2.ScrollBar.vertical: QQC2.ScrollBar {}
            delegate: QQC2.ItemDelegate {
                id: fila
                required property int index
                required property var modelData
                width: ListView.view.width
                highlighted: ListView.isCurrentItem
                text: modelData.texto
                onClicked: { lista.currentIndex = index; paleta.ejecutarActual() }
                Accessible.name: modelData.texto + (modelData.grupo ? ", " + modelData.grupo : "")
                contentItem: RowLayout {
                    spacing: Kirigami.Units.largeSpacing
                    Kirigami.Icon {
                        source: fila.modelData.icono || "system-run"
                        implicitWidth: Kirigami.Units.iconSizes.small
                        implicitHeight: implicitWidth
                    }
                    QQC2.Label {
                        text: fila.modelData.texto
                        Layout.fillWidth: true
                        elide: Text.ElideRight
                        color: fila.highlighted ? Kirigami.Theme.highlightedTextColor : Kirigami.Theme.textColor
                    }
                    QQC2.Label {
                        text: fila.modelData.grupo || ""
                        font: Kirigami.Theme.smallFont
                        color: fila.highlighted ? Kirigami.Theme.highlightedTextColor : Kirigami.Theme.disabledTextColor
                    }
                    QQC2.Label {
                        text: fila.modelData.atajo || ""
                        font: Kirigami.Theme.smallFont
                        color: fila.highlighted ? Kirigami.Theme.highlightedTextColor : Kirigami.Theme.disabledTextColor
                    }
                }
            }
            Kirigami.PlaceholderMessage {
                anchors.centerIn: parent
                width: parent.width - Kirigami.Units.gridUnit * 4
                visible: lista.count === 0
                text: "Ninguna orden coincide"
                icon.name: "edit-none"
            }
        }
    }
}
