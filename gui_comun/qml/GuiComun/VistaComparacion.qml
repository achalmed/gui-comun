// VistaComparacion (3.1) — la diferencia de un archivo lado a lado, como Meld, Kompare o Sublime Merge: a la izquierda
// lo de antes, a la derecha lo de después, con números de línea; una línea quitada y una añadida contiguas van en la
// misma fila. Arriba, el archivo y sus cifras y, si la diferencia lo dice, qué es cada lado («Repositorio» · «HOME»,
// «Instalado» · «Generado») y sus notas. Cada trozo empieza con su cabecera y los botones que el studio pida
// (`accionesTrozo`: preparar, descartar, quitar…; `trozoPedido(clave, trozo)`). Con `seleccionable`, un clic en una
// fila cambiada la elige (Ctrl o Mayús para varias): preparar líneas sueltas. Une las copias de Git, Dotfiles y
// Lliphi; las filas las da `gui_comun.diferencias` (`analizar` o `comparar`), como diccionario o como objeto con las
// mismas claves. Fondo de lo quitado y lo añadido con los colores semánticos del tema: ningún color propio.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

ColumnLayout {
    id: raiz

    property var diferencia                   // {ruta, filas, trozos, anadidas, quitadas, binario, vacia, recortado, nuevo?, izquierda?, derecha?, notas?}
    property var accionesTrozo: []            // [{clave, texto, icono, accesible?, noEnNuevo?}]
    property bool seleccionable: false
    property var filasElegidas: []            // índices de `diferencia.filas`
    property string mensajeVacio: "Elija un archivo para ver su diferencia"
    property string nombreAccesible: "Diferencia"
    signal trozoPedido(string clave, int trozo)
    signal seleccionCambiada()

    readonly property bool hay: !!raiz.diferencia && !!raiz.diferencia.ruta
    readonly property int nTrozos: !raiz.hay ? 0 : (typeof raiz.diferencia.trozos === "number" ? raiz.diferencia.trozos
                                                    : (raiz.diferencia.trozos ? raiz.diferencia.trozos.length : 0))
    readonly property bool conLados: raiz.hay && !!raiz.diferencia.izquierda
    readonly property real anchoNumero: Kirigami.Units.gridUnit * 2.6
    property int _ancla: -1

    spacing: 0
    Accessible.name: nombreAccesible

    function limpiarSeleccion() { filasElegidas = []; _ancla = -1; seleccionCambiada() }
    function elegida(i) { return filasElegidas.indexOf(i) >= 0 }
    function pulsar(i, tipo, modificadores) {
        if (!seleccionable || ["cambio", "quitada", "anadida"].indexOf(tipo) < 0) return
        let nuevas = (modificadores & (Qt.ControlModifier | Qt.ShiftModifier)) ? filasElegidas.slice() : []
        if ((modificadores & Qt.ShiftModifier) && _ancla >= 0) {
            const filas = lista.model
            for (let k = Math.min(_ancla, i); k <= Math.max(_ancla, i); k++) {
                const t = Array.isArray(filas) ? filas[k].tipo : (filas.fila ? filas.fila(k).tipo : "cambio")   // lista o ModeloLista
                if (["cambio", "quitada", "anadida"].indexOf(t) >= 0 && nuevas.indexOf(k) < 0) nuevas.push(k)
            }
        } else if (nuevas.indexOf(i) >= 0 && (modificadores & Qt.ControlModifier)) {
            nuevas.splice(nuevas.indexOf(i), 1)
        } else if (filasElegidas.length === 1 && filasElegidas[0] === i && !(modificadores & Qt.ControlModifier)) {
            nuevas = []
        } else if (nuevas.indexOf(i) < 0) {
            nuevas.push(i)
        }
        _ancla = i
        filasElegidas = nuevas.sort((a, b) => a - b)
        seleccionCambiada()
    }
    onDiferenciaChanged: { filasElegidas = []; _ancla = -1 }

    function fondo(tipo) {
        switch (tipo) {
        case "quitada": return Kirigami.Theme.negativeBackgroundColor
        case "anadida": return Kirigami.Theme.positiveBackgroundColor
        case "vacia": return Qt.alpha(Kirigami.Theme.textColor, 0.04)
        default: return "transparent"
        }
    }

    // el archivo y sus cifras
    QQC2.ToolBar {
        Layout.fillWidth: true
        visible: raiz.hay
        position: QQC2.ToolBar.Header
        RowLayout {
            anchors.fill: parent
            spacing: Kirigami.Units.smallSpacing
            Kirigami.Icon { source: "text-x-generic"; implicitWidth: Kirigami.Units.iconSizes.small; implicitHeight: implicitWidth }
            QQC2.Label { text: raiz.hay ? raiz.diferencia.ruta : ""; elide: Text.ElideMiddle; Layout.fillWidth: true; font.bold: true }
            QQC2.Label {
                visible: raiz.seleccionable && raiz.filasElegidas.length > 0
                text: raiz.filasElegidas.length + (raiz.filasElegidas.length === 1 ? " línea elegida" : " líneas elegidas")
                color: Kirigami.Theme.highlightColor
                font: Kirigami.Theme.smallFont
            }
            QQC2.Label {
                visible: raiz.hay && !raiz.diferencia.binario && !raiz.diferencia.vacia
                text: raiz.hay ? "+" + raiz.diferencia.anadidas + "  −" + raiz.diferencia.quitadas
                                 + (raiz.nTrozos > 0 ? " · " + raiz.nTrozos + (raiz.nTrozos === 1 ? " trozo" : " trozos") : "") : ""
                color: Kirigami.Theme.disabledTextColor
                font: Kirigami.Theme.smallFont
            }
        }
    }
    // qué es cada lado
    Item {
        Layout.fillWidth: true
        visible: raiz.conLados
        implicitHeight: lados.implicitHeight + Kirigami.Units.smallSpacing * 2
        Rectangle { anchors.fill: parent; color: Kirigami.Theme.alternateBackgroundColor }
        RowLayout {
            id: lados
            anchors.fill: parent
            anchors.margins: Kirigami.Units.smallSpacing
            spacing: 0
            Lado { texto: raiz.conLados ? raiz.diferencia.izquierda : ""; icono: "go-previous"; Layout.preferredWidth: (parent.width - 1) / 2 }
            Kirigami.Separator { Layout.fillHeight: true }
            Lado { texto: raiz.conLados ? (raiz.diferencia.derecha || "") : ""; icono: "go-next"; Layout.fillWidth: true }
        }
    }
    Repeater {
        model: raiz.hay ? (raiz.diferencia.notas || []) : []
        delegate: Kirigami.InlineMessage {
            required property string modelData
            Layout.fillWidth: true
            Layout.margins: Kirigami.Units.smallSpacing
            Layout.bottomMargin: 0
            visible: true
            type: modelData.indexOf("secreto") >= 0 ? Kirigami.MessageType.Warning : Kirigami.MessageType.Information
            text: modelData
        }
    }
    Kirigami.InlineMessage {
        Layout.fillWidth: true
        Layout.margins: Kirigami.Units.smallSpacing
        visible: raiz.hay && !!raiz.diferencia.recortado
        type: Kirigami.MessageType.Information
        text: "La diferencia es muy larga: se muestran las primeras filas. Ábrala en su editor para verla entera."
    }

    ListView {
        id: lista
        Layout.fillWidth: true
        Layout.fillHeight: true
        visible: raiz.hay && !raiz.diferencia.vacia && !raiz.diferencia.binario
        clip: true
        model: raiz.hay ? raiz.diferencia.filas : null
        reuseItems: true
        boundsBehavior: Flickable.StopAtBounds
        QQC2.ScrollBar.vertical: QQC2.ScrollBar {}
        Accessible.name: raiz.nombreAccesible + (raiz.hay ? " de " + raiz.diferencia.ruta : "")

        delegate: Loader {
            id: fila
            required property int index
            required property string tipo
            required property int trozo
            required property int izqNum
            required property string izq
            required property string izqTipo
            required property int derNum
            required property string der
            required property string derTipo
            width: ListView.view.width
            sourceComponent: tipo === "trozo" ? cTrozo : cLinea
        }
    }
    Kirigami.PlaceholderMessage {
        Layout.fillWidth: true
        Layout.fillHeight: true
        visible: !raiz.hay || raiz.diferencia.vacia || raiz.diferencia.binario
        text: !raiz.hay ? raiz.mensajeVacio : raiz.diferencia.binario ? "Archivo binario: no se compara línea a línea" : "Sin diferencias"
        icon.name: raiz.hay && raiz.diferencia.binario ? "application-octet-stream" : "document-compare"
    }

    component Lado: RowLayout {
        property string texto: ""
        property string icono: ""
        spacing: Kirigami.Units.smallSpacing
        Kirigami.Icon { source: parent.icono; implicitWidth: Kirigami.Units.iconSizes.small; implicitHeight: implicitWidth }
        QQC2.Label { text: parent.texto; font.bold: true; elide: Text.ElideRight; Layout.fillWidth: true }
    }

    Component {
        id: cTrozo
        Rectangle {
            readonly property var f: parent
            implicitHeight: filaTrozo.implicitHeight + Kirigami.Units.smallSpacing * 2
            color: Kirigami.Theme.alternateBackgroundColor
            RowLayout {
                id: filaTrozo
                anchors.fill: parent
                anchors.leftMargin: Kirigami.Units.smallSpacing
                anchors.rightMargin: Kirigami.Units.smallSpacing
                spacing: Kirigami.Units.smallSpacing
                QQC2.Label {
                    text: f.izq + (f.der ? "  " + f.der : "")
                    font: Kirigami.Theme.fixedWidthFont
                    color: Kirigami.Theme.disabledTextColor
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                }
                Repeater {
                    model: raiz.accionesTrozo
                    delegate: QQC2.ToolButton {
                        required property var modelData
                        visible: !(modelData.noEnNuevo && raiz.diferencia && raiz.diferencia.nuevo)
                        text: modelData.texto
                        icon.name: modelData.icono || ""
                        display: QQC2.AbstractButton.TextBesideIcon
                        onClicked: raiz.trozoPedido(modelData.clave, f.trozo)
                        Accessible.name: (modelData.accesible || modelData.texto) + " (trozo " + (f.trozo + 1) + ")"
                    }
                }
            }
        }
    }

    Component {
        id: cLinea
        Item {
            readonly property var f: parent
            readonly property bool elegidaAqui: raiz.seleccionable && raiz.filasElegidas.indexOf(f.index) >= 0
            implicitHeight: Math.max(izquierda.implicitHeight, derecha.implicitHeight)
            Mitad { id: izquierda; numero: f.izqNum; texto: f.izq; tipo: f.izqTipo; x: 0; width: Math.floor((parent.width - 1) / 2); height: parent.height }
            Kirigami.Separator { x: izquierda.width; height: parent.height }
            Mitad { id: derecha; numero: f.derNum; texto: f.der; tipo: f.derTipo; x: izquierda.width + 1; width: parent.width - x; height: parent.height }
            Rectangle {                                     // la fila elegida: marco del color de selección
                anchors.fill: parent
                visible: parent.elegidaAqui
                color: Qt.alpha(Kirigami.Theme.highlightColor, 0.18)
                border.color: Kirigami.Theme.highlightColor
                border.width: 1
            }
            TapHandler {
                enabled: raiz.seleccionable
                onTapped: (punto) => raiz.pulsar(f.index, f.tipo, punto.modifiers)
            }
            Accessible.role: raiz.seleccionable ? Accessible.CheckBox : Accessible.StaticText
            Accessible.name: (f.izqNum > 0 ? "antes " + f.izqNum + ": " + f.izq : "") + (f.derNum > 0 ? " después " + f.derNum + ": " + f.der : "")
            Accessible.checked: elegidaAqui
        }
    }

    component Mitad: Rectangle {
        id: mitad
        property int numero: 0
        property string texto: ""
        property string tipo: "igual"
        color: raiz.fondo(tipo)
        implicitHeight: contenido.implicitHeight
        QQC2.Label {
            id: numeroLinea
            width: raiz.anchoNumero
            text: mitad.numero > 0 ? mitad.numero : ""
            horizontalAlignment: Text.AlignRight
            rightPadding: Kirigami.Units.smallSpacing
            font: Kirigami.Theme.fixedWidthFont
            color: Kirigami.Theme.disabledTextColor
            Accessible.ignored: true
        }
        QQC2.Label {
            id: contenido
            anchors.left: numeroLinea.right
            anchors.right: parent.right
            leftPadding: Kirigami.Units.smallSpacing
            text: mitad.tipo === "aviso" ? mitad.texto : mitad.texto.replace(/\t/g, "    ")
            textFormat: Text.PlainText
            wrapMode: Text.WrapAnywhere
            font: Kirigami.Theme.fixedWidthFont
            color: mitad.tipo === "aviso" ? Kirigami.Theme.disabledTextColor : Kirigami.Theme.textColor
        }
    }
}
