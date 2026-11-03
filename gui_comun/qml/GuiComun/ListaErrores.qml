// ListaErrores (3.1) — errores y avisos como errores presentables, en lista: título comprensible, archivo y línea,
// causa probable, qué hacer y el detalle técnico desplegable por fila (la versión «lista» de TarjetaError). Un clic o
// Intro elige el problema (`elegido(indice)`: ir a la línea en el editor). Viene de LaTeX Studio. El modelo es
// cualquiera con los roles `nivel` (error · aviso · tipografia · informacion), `titulo`, `mensaje`, `causa`, `accion`,
// `detalle`, `ubicacion` y `linea` (los que falten, vacíos); arriba, lo que el studio ponga (`cabecera`: sus filtros).
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

ColumnLayout {
    id: raiz

    property var modelo: null
    property alias actual: lista.currentIndex
    property alias cabecera: barra.data              // cabecera: [ QQC2.ToolButton { … } ]
    property string mensajeVacio: "Sin errores ni avisos"
    property string explicacionVacia: ""
    property string iconoVacio: "data-success"
    property string nombreAccesible: "Problemas"
    signal elegido(int indice)
    spacing: 0
    Accessible.name: nombreAccesible

    function icono(nivel) { return nivel === "error" ? "data-error" : nivel === "aviso" ? "data-warning" : nivel === "tipografia" ? "format-justify-fill" : "data-information" }
    function color(nivel) { return nivel === "error" ? Kirigami.Theme.negativeTextColor : nivel === "aviso" ? Kirigami.Theme.neutralTextColor : Kirigami.Theme.disabledTextColor }
    // en la fila elegida, el texto de la selección (el rojo o el gris sobre el color de selección no se leen)
    function tinta(fila, normal) { return fila.highlighted ? Kirigami.Theme.highlightedTextColor : normal }
    function texto(v) { return v === undefined || v === null ? "" : String(v) }

    RowLayout {
        id: barra
        Layout.fillWidth: true
        Layout.margins: Kirigami.Units.smallSpacing
        visible: children.length > 0
        spacing: Kirigami.Units.smallSpacing
    }
    Kirigami.Separator { Layout.fillWidth: true; visible: barra.visible }

    ListView {
        id: lista
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        model: raiz.modelo
        keyNavigationEnabled: true
        Accessible.name: raiz.nombreAccesible
        QQC2.ScrollBar.vertical: QQC2.ScrollBar {}
        Keys.onReturnPressed: raiz.elegido(currentIndex)

        delegate: QQC2.ItemDelegate {
            id: fila
            required property var model
            required property int index
            readonly property string titulo: raiz.texto(model.titulo) || raiz.texto(model.mensaje)
            readonly property string ubicacion: raiz.texto(model.ubicacion) + (model.linea ? ":" + model.linea : "")
            property bool abierto: false
            width: lista.width
            highlighted: ListView.isCurrentItem
            onClicked: { lista.currentIndex = index; raiz.elegido(index) }
            Accessible.name: titulo + (model.linea ? ", línea " + model.linea : "")
            contentItem: RowLayout {
                spacing: Kirigami.Units.largeSpacing
                Kirigami.Icon { Layout.alignment: Qt.AlignTop; source: raiz.icono(fila.model.nivel); implicitWidth: Kirigami.Units.iconSizes.smallMedium; implicitHeight: implicitWidth }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: Kirigami.Units.smallSpacing / 2
                    RowLayout {
                        Layout.fillWidth: true
                        QQC2.Label { text: fila.titulo; font.weight: Font.DemiBold; color: raiz.tinta(fila, raiz.color(fila.model.nivel)); elide: Text.ElideRight; Layout.fillWidth: true }
                        QQC2.Label { text: fila.ubicacion; visible: text !== ""; font: Kirigami.Theme.fixedWidthFont; color: raiz.tinta(fila, Kirigami.Theme.disabledTextColor) }
                    }
                    QQC2.Label { visible: raiz.texto(fila.model.causa) !== ""; Layout.fillWidth: true; wrapMode: Text.WordWrap; text: "Causa probable: " + raiz.texto(fila.model.causa); color: raiz.tinta(fila, Kirigami.Theme.textColor) }
                    QQC2.Label { visible: raiz.texto(fila.model.accion) !== ""; Layout.fillWidth: true; wrapMode: Text.WordWrap; text: "Qué hacer: " + raiz.texto(fila.model.accion); font.italic: true; color: raiz.tinta(fila, Kirigami.Theme.textColor) }
                    QQC2.Label {
                        visible: raiz.texto(fila.model.mensaje) !== "" && fila.titulo !== raiz.texto(fila.model.mensaje)
                        Layout.fillWidth: true; wrapMode: Text.WrapAnywhere; text: raiz.texto(fila.model.mensaje)
                        font: Kirigami.Theme.fixedWidthFont; color: raiz.tinta(fila, Kirigami.Theme.disabledTextColor)
                    }
                    QQC2.Button {
                        visible: raiz.texto(fila.model.detalle) !== ""
                        flat: true
                        text: fila.abierto ? "Ocultar el detalle técnico" : "Detalle técnico"
                        icon.name: fila.abierto ? "arrow-up" : "arrow-down"
                        onClicked: fila.abierto = !fila.abierto
                    }
                    QQC2.Label {
                        visible: fila.abierto
                        Layout.fillWidth: true
                        text: raiz.texto(fila.model.detalle)
                        wrapMode: Text.WrapAnywhere
                        font: Kirigami.Theme.fixedWidthFont
                        color: raiz.tinta(fila, Kirigami.Theme.textColor)
                        textFormat: Text.PlainText
                    }
                }
            }
        }

        Kirigami.PlaceholderMessage {
            anchors.centerIn: parent
            width: parent.width - Kirigami.Units.gridUnit * 4
            visible: lista.count === 0
            icon.name: raiz.iconoVacio
            text: raiz.mensajeVacio
            explanation: raiz.explicacionVacia
        }
    }
}
