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
    height: Math.min(campo.implicitHeight + Kirigami.Units.smallSpacing * 4 + 1
                     + Math.max(Kirigami.Units.gridUnit * 6, lista.contentHeight),
                     Kirigami.Units.gridUnit * 22, parent.height - Kirigami.Units.gridUnit * 4)
    modal: true
    dim: true
    focus: true
    padding: Kirigami.Units.smallSpacing
    readonly property bool oscuro: Kirigami.ColorUtils.brightnessForColor(Kirigami.Theme.backgroundColor) === Kirigami.ColorUtils.Dark
    Kirigami.Theme.colorSet: Kirigami.Theme.View
    Kirigami.Theme.inherit: false
    // 4.2: una superficie flotante (opaca, radio, borde y sombra del tema), como BarraFlotante; el alto se ciñe a los
    // resultados
    background: Kirigami.ShadowedRectangle {
        color: Kirigami.Theme.backgroundColor
        radius: Kirigami.Units.cornerRadius * 2
        border.width: 1
        border.color: Kirigami.ColorUtils.linearInterpolation(Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor, paleta.oscuro ? 0.22 : 0.16)
        shadow.size: Kirigami.Units.gridUnit * 1.5
        shadow.yOffset: Kirigami.Units.smallSpacing
        shadow.color: Qt.alpha(Qt.darker(Kirigami.Theme.backgroundColor, paleta.oscuro ? 4 : 2.5), paleta.oscuro ? 0.65 : 0.35)
    }
    QQC2.Overlay.modal: Rectangle { color: Qt.alpha(Qt.darker(Kirigami.Theme.backgroundColor, 3), 0.35) }
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
                hoverEnabled: true
                leftInset: Kirigami.Units.smallSpacing / 2
                rightInset: Kirigami.Units.smallSpacing / 2
                topInset: 1
                bottomInset: 1
                leftPadding: Kirigami.Units.largeSpacing
                rightPadding: Kirigami.Units.largeSpacing
                // 4.2: la actual, teñida del acento (no el bloque lleno), con su marca a la izquierda
                background: Rectangle {
                    radius: Kirigami.Units.cornerRadius
                    color: fila.highlighted ? EstiloSeleccion.fondo(Kirigami.Theme.backgroundColor, Kirigami.Theme.highlightColor, 0.24)
                         : fila.hovered ? Kirigami.ColorUtils.tintWithAlpha(Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor, 0.07)
                         : "transparent"
                    Rectangle {
                        visible: fila.highlighted && EstiloSeleccion.conMarca
                        anchors { left: parent.left; verticalCenter: parent.verticalCenter; leftMargin: Kirigami.Units.smallSpacing / 2 }
                        width: Kirigami.Units.smallSpacing * 0.75
                        height: parent.height - Kirigami.Units.smallSpacing * 2.5
                        radius: width / 2
                        color: Kirigami.Theme.highlightColor
                    }
                }
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
                        color: Kirigami.Theme.textColor
                        font.weight: fila.highlighted ? Font.DemiBold : Font.Normal
                    }
                    QQC2.Label {
                        text: fila.modelData.grupo || ""
                        font: Kirigami.Theme.smallFont
                        color: Kirigami.Theme.disabledTextColor
                    }
                    QQC2.Label {
                        text: fila.modelData.atajo || ""
                        font: Kirigami.Theme.smallFont
                        color: Kirigami.Theme.disabledTextColor
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
