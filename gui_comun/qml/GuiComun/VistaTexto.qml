// VistaTexto (2.2) — texto de solo lectura con mensaje de vacío: un documento en Markdown (los enlaces abren fuera) o
// texto monoespaciado con resaltado de KSyntaxHighlighting (`definicion`: «Bash», «Diff», «Markdown», «JSON»…; vacía,
// sin resaltar). Lo que tres studios repetían: el árbol de `tree`, la diferencia de un cambio, la guía del repo.
// Sin colores ni fuentes propios: Kirigami.Theme y Kirigami.Units.
import QtQuick
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

QQC2.Control {
    id: raiz

    property string texto: ""
    property bool markdown: false
    property string definicion: ""                       // la definición de resaltado (solo sin markdown)
    property string mensajeVacio: ""
    property string iconoVacio: "text-x-generic"
    property string nombreAccesible: markdown ? "Documento" : "Texto"
    property bool ajustarLineas: markdown                // sin markdown, por omisión no se parten las líneas
    readonly property alias area: area

    // tamaño implícito propio (no el del texto): dentro de un Layout, el contenido no dicta el ancho ni provoca bucles
    implicitWidth: Kirigami.Units.gridUnit * 20
    implicitHeight: Kirigami.Units.gridUnit * 12
    padding: 0
    Kirigami.Theme.colorSet: Kirigami.Theme.View
    Kirigami.Theme.inherit: false
    Accessible.name: nombreAccesible

    background: Rectangle { color: Kirigami.Theme.backgroundColor }

    contentItem: QQC2.ScrollView {
        QQC2.ScrollBar.horizontal.policy: raiz.ajustarLineas ? QQC2.ScrollBar.AlwaysOff : QQC2.ScrollBar.AsNeeded
        QQC2.TextArea {
            id: area
            readOnly: true
            text: raiz.texto
            textFormat: raiz.markdown ? TextEdit.MarkdownText : TextEdit.PlainText
            font: raiz.markdown ? Kirigami.Theme.defaultFont : Kirigami.Theme.fixedWidthFont
            wrapMode: raiz.ajustarLineas ? TextEdit.Wrap : TextEdit.NoWrap
            selectByMouse: true
            background: null
            leftPadding: Kirigami.Units.largeSpacing * (raiz.markdown ? 3 : 1)
            rightPadding: leftPadding
            topPadding: Kirigami.Units.largeSpacing
            bottomPadding: Kirigami.Units.largeSpacing
            onLinkActivated: enlace => Qt.openUrlExternally(enlace)
            Accessible.name: raiz.nombreAccesible
            Loader {
                active: !raiz.markdown && raiz.definicion !== ""
                source: "ResaltadoSalida.qml"
                onLoaded: { item.nombreDefinicion = raiz.definicion; item.textEdit = area }
            }
        }
    }

    Kirigami.PlaceholderMessage {
        anchors.centerIn: parent
        width: parent.width - Kirigami.Units.gridUnit * 4
        visible: raiz.texto === "" && raiz.mensajeVacio !== ""
        text: raiz.mensajeVacio
        icon.name: raiz.iconoVacio
    }
}
