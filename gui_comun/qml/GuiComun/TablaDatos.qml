// TablaDatos — la vista principal densa de un studio: TableView con cabecera, columnas ordenables (clic en la
// cabecera), redimensionables (arrastre), opcionales (`visible`) y que se ocultan al estrecharse (`estrecho`);
// filas alternas, selección múltiple por filas (Ctrl y Mayús), menú contextual, doble clic e Intro.
// El modelo es un QAbstractTableModel (o un ModeloFiltrado sobre él) con el rol `display` y, si quiere color
// semántico en una columna `semantica`, el rol `nivel` (positivo · neutro · activo · negativo · inactivo); el rol
// `habilitado` (falso) atenúa la fila y `icono` pone un icono delante del texto de las columnas `conIcono`.
// columnas: [{ancho (unidades de rejilla; 0 = toma el resto), minimo, alinear ("izquierda"|"centro"|"derecha"),
//            mono, semantica, conIcono, visible, estrecho, secundaria (texto tenue)}]
// Con `claveAjustes`, los anchos que el usuario arrastró se recuerdan en QSettings entre sesiones (2.1).
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import QtQml.Models
import QtCore
import org.kde.kirigami as Kirigami

QQC2.Control {
    id: raiz

    property var modelo
    property var columnas: []
    property real altoFila: Kirigami.Units.gridUnit * 1.7
    property int umbralEstrecho: Kirigami.Units.gridUnit * 50
    readonly property bool estrecha: width < umbralEstrecho
    property int columnaOrden: -1
    property bool descendente: false
    property QQC2.Menu menuContextual: null
    property string mensajeVacio: ""
    property string iconoVacio: "edit-none"
    property string claveAjustes: ""
    readonly property alias seleccion: seleccionModelo
    readonly property alias vista: tabla
    readonly property int filaActual: tabla.currentRow
    readonly property int filas: tabla.rows

    signal activada(int fila)
    signal ordenar(int columna, bool descendente)
    signal suprimir()
    signal filaActualCambiada(int fila)
    signal seleccionCambiada()

    padding: 0
    Kirigami.Theme.colorSet: Kirigami.Theme.View
    Kirigami.Theme.inherit: false
    focusPolicy: Qt.StrongFocus
    Accessible.role: Accessible.Table

    background: Rectangle { color: Kirigami.Theme.backgroundColor }

    function columna(c) { return raiz.columnas[c] || {} }

    function anchoDe(c) {
        const col = columna(c)
        if (col.visible === false) return 0
        if (raiz.estrecha && col.estrecho) return 0
        const explicito = tabla.explicitColumnWidth(c)
        if (explicito >= 0) return explicito
        if (col.ancho > 0) return col.ancho * Kirigami.Units.gridUnit
        // la que estira: lo que queda tras las fijas, nunca menos que su mínimo
        let fijas = 0
        for (let i = 0; i < tabla.columns; i++) {
            if (i === c) continue
            const o = columna(i)
            if (o.visible === false || (raiz.estrecha && o.estrecho)) continue
            const e = tabla.explicitColumnWidth(i)
            fijas += e >= 0 ? e : (o.ancho > 0 ? o.ancho * Kirigami.Units.gridUnit : (o.minimo || 10) * Kirigami.Units.gridUnit)
        }
        return Math.max((col.minimo || 10) * Kirigami.Units.gridUnit, tabla.width - fijas)
    }

    function mostrarColumna(c, visible) {
        const nuevas = raiz.columnas.slice()
        nuevas[c] = Object.assign({}, nuevas[c] || {}, { visible: visible })
        raiz.columnas = nuevas
        tabla.forceLayout()
    }

    function filasSeleccionadas() {
        const filas = []
        for (const i of seleccionModelo.selectedIndexes) if (i.column === 0) filas.push(i.row)
        filas.sort((a, b) => a - b)
        return filas
    }

    function seleccionarTodo() {
        if (!raiz.modelo) return
        const n = tabla.rows
        if (n === 0) return
        seleccionModelo.select(seleccionModelo.model.index(0, 0), ItemSelectionModel.Clear)
        for (let r = 0; r < n; r++)
            seleccionModelo.select(seleccionModelo.model.index(r, 0), ItemSelectionModel.Select | ItemSelectionModel.Rows)
    }

    function invertirSeleccion() {
        if (!raiz.modelo) return
        for (let r = 0; r < tabla.rows; r++)
            seleccionModelo.select(seleccionModelo.model.index(r, 0), ItemSelectionModel.Toggle | ItemSelectionModel.Rows)
    }

    function seleccionarFila(fila, limpiar) {
        if (fila < 0 || !raiz.modelo) return
        const idx = seleccionModelo.model.index(fila, 0)
        seleccionModelo.setCurrentIndex(idx, ItemSelectionModel.NoUpdate)
        seleccionModelo.select(idx, (limpiar ? ItemSelectionModel.ClearAndSelect : ItemSelectionModel.Select) | ItemSelectionModel.Rows)
    }

    function nivelColor(nivel, habilitado) {
        if (habilitado === false) return Kirigami.Theme.disabledTextColor
        switch (nivel) {
            case "positivo": return Kirigami.Theme.positiveTextColor
            case "neutro": return Kirigami.Theme.neutralTextColor
            case "negativo": return Kirigami.Theme.negativeTextColor
            case "activo": return Kirigami.Theme.activeTextColor
            case "inactivo": return Kirigami.Theme.disabledTextColor
            default: return Kirigami.Theme.textColor
        }
    }

    function alineacion(c) {
        switch (columna(c).alinear) {
            case "centro": return Text.AlignHCenter
            case "derecha": return Text.AlignRight
            default: return Text.AlignLeft
        }
    }

    onEstrechaChanged: tabla.forceLayout()
    onColumnasChanged: tabla.forceLayout()

    // anchos de columna recordados (solo los que el usuario fijó arrastrando)
    Settings {
        id: ajustes
        category: raiz.claveAjustes !== "" ? "tablas/" + raiz.claveAjustes : "tablas/sin-clave"
        property var anchos: []
    }
    function restaurarAnchos() {
        if (raiz.claveAjustes === "" || !ajustes.anchos) return
        for (let c = 0; c < ajustes.anchos.length && c < tabla.columns; c++)
            if (ajustes.anchos[c] > 0) tabla.setColumnWidth(c, ajustes.anchos[c])
        tabla.forceLayout()
    }
    function guardarAnchos() {
        if (raiz.claveAjustes === "") return
        const lista = []
        for (let c = 0; c < tabla.columns; c++) lista.push(tabla.explicitColumnWidth(c))
        ajustes.anchos = lista
    }
    Component.onCompleted: Qt.callLater(restaurarAnchos)
    Component.onDestruction: guardarAnchos()

    contentItem: ColumnLayout {
        spacing: 0

        QQC2.HorizontalHeaderView {
            id: cabecera
            Layout.fillWidth: true
            syncView: tabla
            clip: true
            interactive: false
            delegate: QQC2.Control {
                id: celdaCabecera
                required property int index
                required property var model
                readonly property bool ordenaAqui: raiz.columnaOrden === index
                implicitHeight: Kirigami.Units.gridUnit * 1.6
                padding: Kirigami.Units.smallSpacing
                leftPadding: index === 0 ? Kirigami.Units.largeSpacing : Kirigami.Units.smallSpacing
                Accessible.role: Accessible.ColumnHeader
                Accessible.name: model.display !== undefined ? model.display : ""
                background: Rectangle {
                    color: celdaCabecera.hovered ? Qt.alpha(Kirigami.Theme.hoverColor, 0.3) : Kirigami.Theme.backgroundColor
                    Kirigami.Separator { anchors.right: parent.right; height: parent.height }
                    Kirigami.Separator { anchors.bottom: parent.bottom; width: parent.width }
                }
                contentItem: RowLayout {
                    spacing: Kirigami.Units.smallSpacing
                    QQC2.Label {
                        Layout.fillWidth: true
                        text: celdaCabecera.model.display !== undefined ? celdaCabecera.model.display : ""
                        elide: Text.ElideRight
                        horizontalAlignment: raiz.alineacion(celdaCabecera.index)
                        font.bold: false
                    }
                    Kirigami.Icon {
                        visible: celdaCabecera.ordenaAqui
                        source: raiz.descendente ? "arrow-down-symbolic" : "arrow-up-symbolic"
                        implicitWidth: Kirigami.Units.iconSizes.small
                        implicitHeight: implicitWidth
                    }
                }
                TapHandler {
                    onTapped: {
                        const desc = raiz.columnaOrden === celdaCabecera.index ? !raiz.descendente : false
                        raiz.columnaOrden = celdaCabecera.index
                        raiz.descendente = desc
                        raiz.ordenar(celdaCabecera.index, desc)
                    }
                }
            }
        }

        Item {
        Layout.fillWidth: true
        Layout.fillHeight: true
        TableView {
            id: tabla
            anchors.fill: parent
            clip: true
            model: raiz.modelo
            boundsBehavior: Flickable.StopAtBounds
            columnSpacing: 0
            rowSpacing: 0
            resizableColumns: true
            selectionBehavior: TableView.SelectRows
            selectionMode: TableView.ExtendedSelection
            keyNavigationEnabled: true
            pointerNavigationEnabled: true
            selectionModel: ItemSelectionModel { id: seleccionModelo; model: raiz.modelo }
            columnWidthProvider: function (c) { return raiz.anchoDe(c) }
            rowHeightProvider: function () { return raiz.altoFila }
            onWidthChanged: forceLayout()
            onCurrentRowChanged: raiz.filaActualCambiada(currentRow)
            Connections { target: seleccionModelo; function onSelectionChanged() { raiz.seleccionCambiada() } }
            QQC2.ScrollBar.vertical: QQC2.ScrollBar {}
            QQC2.ScrollBar.horizontal: QQC2.ScrollBar {}

            Keys.onPressed: event => {
                if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) { if (currentRow >= 0) raiz.activada(currentRow); event.accepted = true }
                else if (event.key === Qt.Key_Delete) { raiz.suprimir(); event.accepted = true }
                else if (event.key === Qt.Key_A && (event.modifiers & Qt.ControlModifier)) { raiz.seleccionarTodo(); event.accepted = true }
                else if (event.key === Qt.Key_Menu && raiz.menuContextual) { raiz.menuContextual.popup(); event.accepted = true }
            }

            delegate: Rectangle {
                id: celda
                required property int row
                required property int column
                required property bool selected
                required property bool current
                required property var model
                readonly property var col: raiz.columna(column)
                readonly property bool habilitado: model.habilitado === undefined ? true : model.habilitado
                readonly property string nivel: model.nivel !== undefined ? model.nivel : ""
                implicitHeight: raiz.altoFila
                color: selected ? Kirigami.Theme.highlightColor
                     : (row % 2 === 1 ? Kirigami.Theme.alternateBackgroundColor : Kirigami.Theme.backgroundColor)
                Accessible.role: Accessible.Cell
                Accessible.name: model.display !== undefined ? String(model.display) : ""

                Rectangle {   // la fila actual (teclado) sin selección: un marco fino con el color de realce
                    anchors.fill: parent
                    visible: celda.current && !celda.selected && tabla.activeFocus
                    color: "transparent"
                    border.color: Kirigami.Theme.highlightColor
                    border.width: 1
                }

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: celda.column === 0 ? Kirigami.Units.largeSpacing : Kirigami.Units.smallSpacing
                    anchors.rightMargin: celda.column === tabla.columns - 1 ? Kirigami.Units.largeSpacing * 2 : Kirigami.Units.smallSpacing
                    spacing: Kirigami.Units.smallSpacing
                    Kirigami.Icon {
                        visible: celda.col.conIcono === true && celda.model.icono !== undefined && celda.model.icono !== ""
                        source: visible ? celda.model.icono : ""
                        color: celda.col.semantica ? raiz.nivelColor(celda.nivel, celda.habilitado)
                             : (celda.selected ? Kirigami.Theme.highlightedTextColor : Kirigami.Theme.textColor)
                        implicitWidth: Kirigami.Units.iconSizes.small
                        implicitHeight: implicitWidth
                        opacity: celda.habilitado ? 1 : 0.5
                    }
                    QQC2.Label {
                        Layout.fillWidth: true
                        text: celda.model.display !== undefined && celda.model.display !== null ? celda.model.display : ""
                        elide: Text.ElideRight
                        horizontalAlignment: raiz.alineacion(celda.column)
                        font.family: celda.col.mono ? Kirigami.Theme.fixedWidthFont.family : Kirigami.Theme.defaultFont.family
                        color: celda.selected ? Kirigami.Theme.highlightedTextColor
                             : celda.col.semantica ? raiz.nivelColor(celda.nivel, celda.habilitado)
                             : (!celda.habilitado || celda.col.secundaria) ? Kirigami.Theme.disabledTextColor
                             : Kirigami.Theme.textColor
                    }
                }

                TapHandler {
                    acceptedButtons: Qt.LeftButton
                    onDoubleTapped: raiz.activada(celda.row)
                }
                TapHandler {
                    acceptedButtons: Qt.RightButton
                    onTapped: {
                        if (!celda.selected) raiz.seleccionarFila(celda.row, true)
                        tabla.forceActiveFocus()
                        if (raiz.menuContextual) raiz.menuContextual.popup()
                    }
                }
            }
        }
        Kirigami.PlaceholderMessage {
            anchors.centerIn: parent
            width: parent.width - Kirigami.Units.gridUnit * 4
            visible: tabla.rows === 0 && raiz.mensajeVacio !== ""
            text: raiz.mensajeVacio
            icon.name: raiz.iconoVacio
        }
        }
    }
}
