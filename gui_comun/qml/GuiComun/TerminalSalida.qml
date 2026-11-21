// TerminalSalida (4.1) — la salida de una orden como una terminal: la orden arriba, en monoespaciada, con el número de
// líneas y un botón opcional (la `Accion` que la corre); debajo, cada línea en el color de estado de lo que dice. Viene
// de la `TerminalSimulacion` de Dotfiles Studio (2026-11-18), que Lliphi y Filesystem también podían usar. No ejecuta
// nada: las líneas las pone el studio (de `Tareas.linea`, de un `--dry-run`…).
//
// `lineas`: textos o `{texto, nivel}` (un `nivel` explícito manda). Sin nivel, el de la primera regla de `reglas` cuyo
// `contiene` aparece en la línea; si ninguna, `nivelPorOmision`. `reglas` (por omisión, `reglasComunes`: «[ERROR», «✗» →
// negativo; «[WARN», «Saltado» → neutro; «✓», «[SUCCESS», «[OK]» → positivo) se reemplaza, o se amplía delante:
// `reglas: [{contiene: "Archivo real existe", nivel: "negativo"}].concat(reglasComunes)`. Niveles: positivo · neutro ·
// activo · negativo · inactivo (tenue) · "" (el color del texto). Sin colores propios: Kirigami.Theme.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

ColumnLayout {
    id: raiz

    property var lineas: []
    property string orden: ""                 // la orden que produjo la salida (o la que se correría)
    property string titulo: "Salida"
    property string icono: "utilities-terminal"
    property var accion: null                 // una Accion de Python: un botón con texto a la derecha de la orden
    property string mensajeVacio: "Sin salida todavía"
    property string explicacionVacia: ""
    property string nombreAccesible: "Salida de la orden"
    property bool seguirAlFinal: true         // cada línea nueva lleva la vista al final
    property bool ajustarLineas: true         // una línea larga se parte (falso: se corta con desplazamiento horizontal)
    property string nivelPorOmision: ""
    readonly property var reglasComunes: [
        { contiene: "[ERROR", nivel: "negativo" }, { contiene: "✗", nivel: "negativo" },
        { contiene: "[WARN", nivel: "neutro" }, { contiene: "Saltado", nivel: "neutro" },
        { contiene: "✓", nivel: "positivo" }, { contiene: "[SUCCESS", nivel: "positivo" }, { contiene: "[OK]", nivel: "positivo" }
    ]
    property var reglas: reglasComunes
    readonly property alias vista: lista
    readonly property int cuantas: lista.count

    spacing: 0

    function texto(linea) { return typeof linea === "string" ? linea : (linea && linea.texto !== undefined ? String(linea.texto) : "") }
    function nivelDe(linea) {
        if (linea && typeof linea === "object" && linea.nivel !== undefined) return linea.nivel
        const t = texto(linea)
        for (const r of raiz.reglas || [])
            if (r.contiene && t.indexOf(r.contiene) >= 0) return r.nivel || ""
        return raiz.nivelPorOmision
    }
    function colorDe(nivel) {
        switch (nivel) {
            case "positivo": return Kirigami.Theme.positiveTextColor
            case "neutro": return Kirigami.Theme.neutralTextColor
            case "negativo": return Kirigami.Theme.negativeTextColor
            case "activo": return Kirigami.Theme.activeTextColor
            case "inactivo": return Kirigami.Theme.disabledTextColor
            default: return Kirigami.Theme.textColor
        }
    }

    RowLayout {
        Layout.fillWidth: true
        Layout.leftMargin: Kirigami.Units.largeSpacing
        Layout.rightMargin: Kirigami.Units.smallSpacing
        Layout.topMargin: Kirigami.Units.smallSpacing
        Layout.bottomMargin: Kirigami.Units.smallSpacing
        spacing: Kirigami.Units.smallSpacing
        Kirigami.Icon {
            source: raiz.icono
            implicitWidth: Kirigami.Units.iconSizes.small
            implicitHeight: implicitWidth
        }
        QQC2.Label { text: raiz.titulo; font.bold: true }
        QQC2.Label {
            Layout.fillWidth: true
            text: raiz.orden
            font: Kirigami.Theme.fixedWidthFont
            color: Kirigami.Theme.disabledTextColor
            elide: Text.ElideMiddle
            textFormat: Text.PlainText
            QQC2.ToolTip.text: raiz.orden
            QQC2.ToolTip.visible: raiz.orden !== "" && zonaOrden.containsMouse && truncated
            QQC2.ToolTip.delay: Kirigami.Units.toolTipDelay
            MouseArea { id: zonaOrden; anchors.fill: parent; hoverEnabled: true; acceptedButtons: Qt.NoButton }
        }
        QQC2.Label {
            visible: lista.count > 0
            text: lista.count + (lista.count === 1 ? " línea" : " líneas")
            color: Kirigami.Theme.disabledTextColor
            font: Kirigami.Theme.smallFont
        }
        BotonAccion { accion: raiz.accion; conTexto: true }
    }
    Kirigami.Separator { Layout.fillWidth: true }

    // el fondo de vista, como el de una terminal o un editor del esquema activo
    Rectangle {
        Layout.fillWidth: true
        Layout.fillHeight: true
        Kirigami.Theme.colorSet: Kirigami.Theme.View
        Kirigami.Theme.inherit: false
        color: Kirigami.Theme.backgroundColor

        ListView {
            id: lista
            anchors.fill: parent
            anchors.margins: Kirigami.Units.smallSpacing
            clip: true
            model: raiz.lineas
            boundsBehavior: Flickable.StopAtBounds
            flickableDirection: raiz.ajustarLineas ? Flickable.VerticalFlick : Flickable.AutoFlickDirection
            contentWidth: raiz.ajustarLineas ? width : Math.max(width, contentItem.childrenRect.width)
            QQC2.ScrollBar.vertical: QQC2.ScrollBar {}
            QQC2.ScrollBar.horizontal: QQC2.ScrollBar { visible: !raiz.ajustarLineas }
            onCountChanged: if (raiz.seguirAlFinal) positionViewAtEnd()
            Accessible.name: raiz.nombreAccesible
            Accessible.role: Accessible.List
            delegate: QQC2.Label {
                required property var modelData
                readonly property string nivel: raiz.nivelDe(modelData)
                width: raiz.ajustarLineas ? ListView.view.width : implicitWidth
                leftPadding: Kirigami.Units.smallSpacing
                text: raiz.texto(modelData)
                textFormat: Text.PlainText
                wrapMode: raiz.ajustarLineas ? Text.WrapAnywhere : Text.NoWrap
                font: Kirigami.Theme.fixedWidthFont
                color: raiz.colorDe(nivel)
                Accessible.name: text
            }
            Kirigami.PlaceholderMessage {
                anchors.centerIn: parent
                width: parent.width - Kirigami.Units.gridUnit * 4
                visible: lista.count === 0
                icon.name: "utilities-terminal"          // 4.2 (view-preview es un paisaje en algunos temas)
                // 4.2: en un panel bajo, un icono mediano: el grande tapaba el texto
                icon.width: parent && parent.height < Kirigami.Units.gridUnit * 16 ? Kirigami.Units.iconSizes.large : Kirigami.Units.iconSizes.huge
                icon.height: icon.width
                text: raiz.mensajeVacio
                explanation: raiz.explicacionVacia
            }
        }
    }
}
