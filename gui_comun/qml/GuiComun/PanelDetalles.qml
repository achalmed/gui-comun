// PanelDetalles — el panel derecho con lo del elemento seleccionado: cabecera discreta (icono, nombre en Heading
// de nivel 4, botones de icono y una línea secundaria), pestañas y una página por pestaña (los hijos, en orden).
// pestanas: [{titulo, contador (opcional), visible (opcional)}]
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

QQC2.Control {
    id: panel

    property string titulo: ""
    property string subtitulo: ""
    property string icono: ""
    property list<QtObject> accionesCabecera
    property var pestanas: []
    property alias pestanaActual: barra.currentIndex
    property string mensajeVacio: "Nada seleccionado"
    property string iconoVacio: "view-list-details"
    property int anchoPreferido: Kirigami.Units.gridUnit * 24
    property int anchoMinimo: Kirigami.Units.gridUnit * 18
    default property alias paginas: pila.data

    implicitWidth: anchoPreferido
    padding: 0
    Kirigami.Theme.colorSet: Kirigami.Theme.Window
    Kirigami.Theme.inherit: false
    Accessible.name: "Detalles" + (titulo ? ": " + titulo : "")

    // si la pestaña actual pasa a oculta (cambió la lista), salta a la primera visible
    function primeraVisible() { return pestanas.findIndex(p => !p || p.visible !== false) }
    onPestanasChanged: {
        const p = pestanas[pestanaActual]
        if (p && p.visible === false) { const i = primeraVisible(); if (i >= 0) pestanaActual = i }
    }

    background: Rectangle { color: Kirigami.Theme.backgroundColor }

    contentItem: ColumnLayout {
        spacing: 0

        ColumnLayout {
            visible: panel.titulo !== ""
            Layout.fillWidth: true
            Layout.margins: Kirigami.Units.largeSpacing
            spacing: 2
            RowLayout {
                Layout.fillWidth: true
                spacing: Kirigami.Units.smallSpacing
                Kirigami.Icon {
                    visible: panel.icono !== ""
                    source: panel.icono
                    implicitWidth: Kirigami.Units.iconSizes.smallMedium
                    implicitHeight: implicitWidth
                }
                Kirigami.Heading {
                    level: 4
                    text: panel.titulo
                    Layout.fillWidth: true
                    elide: Text.ElideRight
                }
                Repeater {
                    model: panel.accionesCabecera
                    delegate: BotonAccion {
                        required property QtObject modelData
                        accion: modelData
                        conTexto: false
                    }
                }
            }
            QQC2.Label {
                visible: panel.subtitulo !== ""
                text: panel.subtitulo
                color: Kirigami.Theme.disabledTextColor
                font: Kirigami.Theme.smallFont
                elide: Text.ElideMiddle
                Layout.fillWidth: true
            }
        }

        QQC2.TabBar {
            id: barra
            visible: panel.titulo !== "" && panel.pestanas.length > 1
            Layout.fillWidth: true
            // el modelo es el NÚMERO de pestañas: así un cambio de contador o de visibilidad no recrea los botones (el TabBar
            // de org.kde.desktop lee la altura del botón actual y fallaba con «Cannot read property 'height' of null»)
            Repeater {
                model: panel.pestanas.length
                delegate: QQC2.TabButton {
                    required property int index
                    readonly property var pestana: panel.pestanas[index] || {}
                    visible: pestana.visible === undefined ? true : pestana.visible
                    width: visible ? implicitWidth : 0
                    text: (pestana.titulo || "") + (pestana.contador > 0 ? " (" + pestana.contador + ")" : "")
                }
            }
        }

        StackLayout {
            id: pila
            visible: panel.titulo !== ""
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: barra.currentIndex
        }

        Kirigami.PlaceholderMessage {
            visible: panel.titulo === ""
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.margins: Kirigami.Units.largeSpacing
            text: panel.mensajeVacio
            icon.name: panel.iconoVacio
        }
    }
}
