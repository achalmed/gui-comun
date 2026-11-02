// ArbolDatos — la vista en árbol de un studio (2.1), hermana de TablaDatos: TreeView de Qt Quick con cabecera,
// columnas con la misma descripción (`columnas`: ancho, minimo, alinear, mono, semantica, conIcono, visible, estrecho,
// secundaria), filas alternas, selección por filas (Ctrl y Mayús), menú contextual, doble clic e Intro, expandir y
// contraer con el ratón (la flecha) y el teclado (← →). El modelo es cualquier QAbstractItemModel jerárquico con los
// roles `display`, `nivel`, `icono` y `habilitado` (p. ej. `gui_comun.modelos.ModeloArbol`); `raiz` acota la vista a un
// índice del modelo (el explorador de carpetas). Sin colores propios: Kirigami.Theme y Kirigami.Units.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import QtQml.Models
import org.kde.kirigami as Kirigami

QQC2.Control {
    id: raiz

    property var modelo
    property var columnas: []
    property var raiz: null
    property real altoFila: Kirigami.Units.gridUnit * 1.7
    property int umbralEstrecho: Kirigami.Units.gridUnit * 50
    readonly property bool estrecha: width < umbralEstrecho
    property QQC2.Menu menuContextual: null
    property string mensajeVacio: ""
    property string iconoVacio: "edit-none"
    property int expandirAlCargar: 0                 // niveles que se expanden solos al poner el modelo (0: ninguno; -1: todos)
    readonly property alias seleccion: seleccionModelo
    readonly property alias vista: arbol
    readonly property int filaActual: arbol.currentRow
    readonly property int filas: arbol.rows

    signal activada(var indice)                      // doble clic o Intro: el QModelIndex de la fila
    signal suprimir()
    signal filaActualCambiada(int fila)
    signal seleccionCambiada()

    padding: 0
    Kirigami.Theme.colorSet: Kirigami.Theme.View
    Kirigami.Theme.inherit: false
    focusPolicy: Qt.StrongFocus
    Accessible.role: Accessible.Tree

    background: Rectangle { color: Kirigami.Theme.backgroundColor }

    function columna(c) { return raiz.columnas[c] || {} }

    function anchoDe(c) {
        const col = columna(c)
        if (col.visible === false) return 0
        if (raiz.estrecha && col.estrecho) return 0
        const explicito = arbol.explicitColumnWidth(c)
        if (explicito >= 0) return explicito
        if (col.ancho > 0) return col.ancho * Kirigami.Units.gridUnit
        let fijas = 0
        for (let i = 0; i < arbol.columns; i++) {
            if (i === c) continue
            const o = columna(i)
            if (o.visible === false || (raiz.estrecha && o.estrecho)) continue
            const e = arbol.explicitColumnWidth(i)
            fijas += e >= 0 ? e : (o.ancho > 0 ? o.ancho * Kirigami.Units.gridUnit : (o.minimo || 10) * Kirigami.Units.gridUnit)
        }
        return Math.max((col.minimo || 10) * Kirigami.Units.gridUnit, arbol.width - fijas)
    }

    function mostrarColumna(c, visible) {
        const nuevas = raiz.columnas.slice()
        nuevas[c] = Object.assign({}, nuevas[c] || {}, { visible: visible })
        raiz.columnas = nuevas
        arbol.forceLayout()
    }

    function indiceDe(fila) { return fila >= 0 ? arbol.index(fila, 0) : null }
    function indiceActual() { return indiceDe(arbol.currentRow) }
    function expandirTodo(niveles) { arbol.expandRecursively(-1, niveles === undefined ? -1 : niveles) }
    function contraerTodo() { arbol.collapseRecursively(-1) }
    function expandir(fila) { if (fila >= 0) arbol.expand(fila) }
    function contraer(fila) { if (fila >= 0) arbol.collapse(fila) }
    function alternar(fila) { if (fila >= 0) arbol.toggleExpanded(fila) }

    function filasSeleccionadas() {
        const filas = []
        for (const i of seleccionModelo.selectedIndexes) if (i.column === 0) filas.push(arbol.rowAtIndex(i))
        filas.sort((a, b) => a - b)
        return filas.filter(f => f >= 0)
    }
    function indicesSeleccionados() {
        const lista = []
        for (const i of seleccionModelo.selectedIndexes) if (i.column === 0) lista.push(i)
        return lista
    }
    function seleccionarTodo() {
        for (let r = 0; r < arbol.rows; r++)
            seleccionModelo.select(arbol.index(r, 0), ItemSelectionModel.Select | ItemSelectionModel.Rows)
    }
    function seleccionarFila(fila, limpiar) {
        if (fila < 0 || !raiz.modelo) return
        const idx = arbol.index(fila, 0)
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

    onEstrechaChanged: arbol.forceLayout()
    onColumnasChanged: arbol.forceLayout()
    onModeloChanged: Qt.callLater(() => { if (raiz.expandirAlCargar !== 0 && raiz.modelo) arbol.expandRecursively(-1, raiz.expandirAlCargar) })

    contentItem: ColumnLayout {
        spacing: 0

        QQC2.HorizontalHeaderView {
            id: cabecera
            Layout.fillWidth: true
            syncView: arbol
            clip: true
            interactive: false
            delegate: QQC2.Control {
                id: celdaCabecera
                required property int index
                required property var model
                implicitHeight: Kirigami.Units.gridUnit * 1.6
                padding: Kirigami.Units.smallSpacing
                leftPadding: index === 0 ? Kirigami.Units.largeSpacing : Kirigami.Units.smallSpacing
                Accessible.role: Accessible.ColumnHeader
                Accessible.name: model.display !== undefined ? model.display : ""
                background: Rectangle {
                    color: Kirigami.Theme.backgroundColor
                    Kirigami.Separator { anchors.right: parent.right; height: parent.height }
                    Kirigami.Separator { anchors.bottom: parent.bottom; width: parent.width }
                }
                contentItem: QQC2.Label {
                    text: celdaCabecera.model.display !== undefined ? celdaCabecera.model.display : ""
                    elide: Text.ElideRight
                    horizontalAlignment: raiz.alineacion(celdaCabecera.index)
                }
            }
        }

        TreeView {
            id: arbol
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: raiz.modelo
            Binding { target: arbol; property: "rootIndex"; value: raiz.raiz; when: raiz.raiz !== null && raiz.raiz !== undefined }
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
                const fila = currentRow
                if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) { if (fila >= 0) raiz.activada(arbol.index(fila, 0)); event.accepted = true }
                else if (event.key === Qt.Key_Delete) { raiz.suprimir(); event.accepted = true }
                else if (event.key === Qt.Key_Right) { if (fila >= 0 && !isExpanded(fila)) expand(fila); event.accepted = true }
                else if (event.key === Qt.Key_Left) {
                    if (fila >= 0) {
                        if (isExpanded(fila)) collapse(fila)
                        else { const p = arbol.rowAtIndex(raiz.modelo.parent(arbol.index(fila, 0))); if (p >= 0) raiz.seleccionarFila(p, true) }
                    }
                    event.accepted = true
                }
                else if (event.key === Qt.Key_A && (event.modifiers & Qt.ControlModifier)) { raiz.seleccionarTodo(); event.accepted = true }
                else if (event.key === Qt.Key_Menu && raiz.menuContextual) { raiz.menuContextual.popup(); event.accepted = true }
            }

            delegate: Rectangle {
                id: celda
                required property int row
                required property int column
                required property bool selected
                required property bool current
                required property bool isTreeNode
                required property bool expanded
                required property bool hasChildren
                required property int depth
                required property TreeView treeView
                required property var model
                readonly property var col: raiz.columna(column)
                readonly property bool habilitado: model.habilitado === undefined ? true : model.habilitado
                readonly property string nivel: model.nivel !== undefined ? model.nivel : ""
                readonly property real sangria: Kirigami.Units.iconSizes.small + Kirigami.Units.smallSpacing
                implicitHeight: raiz.altoFila
                color: selected ? Kirigami.Theme.highlightColor
                     : (row % 2 === 1 ? Kirigami.Theme.alternateBackgroundColor : Kirigami.Theme.backgroundColor)
                Accessible.role: Accessible.Cell
                Accessible.name: model.display !== undefined ? String(model.display) : ""

                Rectangle {
                    anchors.fill: parent
                    visible: celda.current && !celda.selected && arbol.activeFocus
                    color: "transparent"
                    border.color: Kirigami.Theme.highlightColor
                    border.width: 1
                }

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: celda.column === 0 ? Kirigami.Units.smallSpacing + celda.depth * celda.sangria : Kirigami.Units.smallSpacing
                    anchors.rightMargin: Kirigami.Units.smallSpacing
                    spacing: Kirigami.Units.smallSpacing
                    Item {                                   // la flecha de expandir, solo en la primera columna
                        visible: celda.column === 0
                        Layout.preferredWidth: Kirigami.Units.iconSizes.small
                        Layout.preferredHeight: Kirigami.Units.iconSizes.small
                        Kirigami.Icon {
                            anchors.fill: parent
                            visible: celda.isTreeNode && celda.hasChildren
                            source: celda.expanded ? "arrow-down" : "arrow-right"
                            color: celda.selected ? Kirigami.Theme.highlightedTextColor : Kirigami.Theme.textColor
                            Accessible.role: Accessible.Button
                            Accessible.name: celda.expanded ? "Contraer" : "Expandir"
                        }
                        TapHandler { enabled: celda.isTreeNode && celda.hasChildren; onTapped: celda.treeView.toggleExpanded(celda.row) }
                    }
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
                        elide: celda.column === 0 ? Text.ElideMiddle : Text.ElideRight
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
                    onDoubleTapped: raiz.activada(arbol.index(celda.row, 0))
                }
                TapHandler {
                    acceptedButtons: Qt.RightButton
                    onTapped: {
                        if (!celda.selected) raiz.seleccionarFila(celda.row, true)
                        arbol.forceActiveFocus()
                        if (raiz.menuContextual) raiz.menuContextual.popup()
                    }
                }
            }

            Kirigami.PlaceholderMessage {
                anchors.centerIn: parent
                width: parent.width - Kirigami.Units.gridUnit * 4
                visible: arbol.rows === 0 && raiz.mensajeVacio !== ""
                text: raiz.mensajeVacio
                icon.name: raiz.iconoVacio
            }
        }
    }
}
