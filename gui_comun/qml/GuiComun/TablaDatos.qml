// TablaDatos — la vista principal densa de un studio: TableView con cabecera, columnas ordenables (clic en la
// cabecera), redimensionables (arrastre del borde derecho de su cabecera; doble clic en él la devuelve a su ancho),
// opcionales (`visible`; el clic derecho en la cabecera las muestra u oculta y restablece los anchos) y que se ocultan
// al estrechar la tabla (`estrecho`); filas alternas, selección múltiple por filas (Ctrl y Mayús), menú contextual,
// doble clic e Intro.
// El modelo es un QAbstractTableModel (o un ModeloFiltrado sobre él) con el rol `display` y, si quiere color
// semántico en una columna `semantica`, el rol `nivel` (positivo · neutro · activo · negativo · inactivo); el rol
// `habilitado` (falso) atenúa la fila y `icono` pone un icono delante del texto de las columnas `conIcono`.
// columnas: [{ancho (unidades de rejilla; 0 = toma el resto), minimo, alinear ("izquierda"|"centro"|"derecha"),
//            mono, semantica, conIcono, visible, estrecho, secundaria (texto tenue),
//            lineas (4.1: el texto se parte en hasta tantas líneas y la fila crece lo justo; 1 por omisión),
//            cortarTras (4.1: caracteres tras los que se prefiere partir, p. ej. "/" en una ruta)}]
// `nivelesBorde` (4.1): los `nivel` que se pintan además en el borde izquierdo de la fila (p. ej. ["negativo", "neutro"]
// para los hallazgos de Huella: alta y media; los demás sin color), con su color de estado, también si la fila está
// elegida; vacío (por omisión), sin borde.
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
    property var nivelesBorde: []
    readonly property int anchoBorde: Math.max(3, Math.round(Kirigami.Units.smallSpacing * 0.75))
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

    // un ancho fijado a mano (arrastre de la cabecera); negativo lo devuelve al de la definición
    function fijarAncho(c, ancho) {
        if (ancho < 0) tabla.setColumnWidth(c, -1)
        else tabla.setColumnWidth(c, Math.max(Kirigami.Units.gridUnit * 3, Math.round(ancho)))
        tabla.forceLayout()
    }
    function restablecerAnchos() {
        tabla.clearColumnWidths()
        tabla.forceLayout()
        guardarAnchos()
    }

    // el texto de una celda, con un espacio de ancho cero tras los caracteres de `cortarTras` (donde partir la línea)
    function textoCelda(c, valor) {
        if (valor === undefined || valor === null) return ""
        const cortes = columna(c).cortarTras
        let texto = String(valor)
        if (cortes && (columna(c).lineas || 1) > 1)
            for (const ch of cortes) texto = texto.split(ch).join(ch + "\u200B")
        return texto
    }

    // las columnas de varias líneas y el alto de una fila: el del texto partido más largo, nunca menos que `altoFila`
    readonly property var columnasMultilinea: {
        const l = []
        for (let i = 0; i < raiz.columnas.length; i++)
            if ((raiz.columnas[i].lineas || 1) > 1 && raiz.columnas[i].visible !== false) l.push(i)
        return l
    }
    function altoDeFila(r) {
        if (raiz.columnasMultilinea.length === 0 || !raiz.modelo) return raiz.altoFila
        let alto = raiz.altoFila
        for (const c of raiz.columnasMultilinea) {
            const ancho = raiz.anchoDe(c)
            if (ancho <= 0) continue
            const col = columna(c)
            const margenes = (c === 0 ? Kirigami.Units.largeSpacing : Kirigami.Units.smallSpacing)
                           + (c === tabla.columns - 1 ? Kirigami.Units.largeSpacing * 2 : Kirigami.Units.smallSpacing)
                           + (col.conIcono ? Kirigami.Units.iconSizes.small + Kirigami.Units.smallSpacing : 0)
            medidor.width = Math.max(1, ancho - margenes)
            medidor.maximumLineCount = col.lineas
            medidor.text = textoCelda(c, raiz.modelo.data(raiz.modelo.index(r, c)))
            alto = Math.max(alto, Math.ceil(medidor.contentHeight) + Kirigami.Units.smallSpacing * 2)
        }
        return alto
    }
    Text {   // mide el texto partido de las columnas de varias líneas (no se ve)
        id: medidor
        visible: false
        wrapMode: Text.Wrap
        elide: Text.ElideRight
        font: Kirigami.Theme.defaultFont
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
        raiz.ancla = fila
    }

    // el clic en una fila (4.1): la TableView de Qt 6 solo mueve la celda actual; aquí se selecciona la fila entera,
    // como en una lista: sin modificador, solo ella; Ctrl la añade o la quita; Mayús, el tramo desde la última elegida
    property int ancla: -1
    property int filaSobre: -1           // la fila bajo el ratón (su resalte)
    property var celdaSobre: null
    function clicEnFila(fila, modificadores) {
        if (fila < 0 || !raiz.modelo) return
        tabla.forceActiveFocus()
        const idx = seleccionModelo.model.index(fila, 0)
        if ((modificadores & Qt.ShiftModifier) && raiz.ancla >= 0) {
            const desde = Math.min(raiz.ancla, fila), hasta = Math.max(raiz.ancla, fila)
            if (!(modificadores & Qt.ControlModifier)) seleccionModelo.clearSelection()
            for (let r = desde; r <= hasta; r++)
                seleccionModelo.select(seleccionModelo.model.index(r, 0), ItemSelectionModel.Select | ItemSelectionModel.Rows)
        } else if (modificadores & Qt.ControlModifier) {
            seleccionModelo.select(idx, ItemSelectionModel.Toggle | ItemSelectionModel.Rows)
            raiz.ancla = fila
        } else {
            seleccionModelo.select(idx, ItemSelectionModel.ClearAndSelect | ItemSelectionModel.Rows)
            raiz.ancla = fila
        }
        seleccionModelo.setCurrentIndex(seleccionModelo.model.index(fila, Math.max(0, tabla.currentColumn)), ItemSelectionModel.NoUpdate)
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
                    acceptedButtons: Qt.LeftButton
                    onTapped: {
                        const desc = raiz.columnaOrden === celdaCabecera.index ? !raiz.descendente : false
                        raiz.columnaOrden = celdaCabecera.index
                        raiz.descendente = desc
                        raiz.ordenar(celdaCabecera.index, desc)
                    }
                }
                TapHandler {
                    acceptedButtons: Qt.RightButton
                    onTapped: menuCabecera.popup()
                }
                // el asa del borde derecho: arrastrar cambia el ancho; doble clic lo devuelve al de la definición
                MouseArea {
                    id: asa
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.right: parent.right
                    width: Kirigami.Units.smallSpacing * 2
                    cursorShape: Qt.SplitHCursor
                    hoverEnabled: true
                    preventStealing: true
                    property real xInicio: 0
                    property real anchoInicio: 0
                    Accessible.role: Accessible.Separator
                    Accessible.name: "Cambiar el ancho de la columna"
                    onPressed: m => {
                        asa.xInicio = asa.mapToItem(null, m.x, m.y).x
                        asa.anchoInicio = tabla.columnWidth(celdaCabecera.index)
                    }
                    onPositionChanged: m => {
                        if (asa.pressed) raiz.fijarAncho(celdaCabecera.index, asa.anchoInicio + asa.mapToItem(null, m.x, m.y).x - asa.xInicio)
                    }
                    onReleased: raiz.guardarAnchos()
                    onDoubleClicked: { raiz.fijarAncho(celdaCabecera.index, -1); raiz.guardarAnchos() }
                    Rectangle {
                        anchors.right: parent.right
                        width: 2
                        height: parent.height
                        visible: asa.containsMouse || asa.pressed
                        color: Kirigami.Theme.highlightColor
                    }
                }
            }
        }

        QQC2.Menu {
            id: menuCabecera
            QQC2.MenuItem {
                text: "Restablecer los anchos de columna"
                icon.name: "edit-reset"
                onTriggered: raiz.restablecerAnchos()
            }
            QQC2.MenuSeparator {}
            Instantiator {
                model: raiz.modelo ? tabla.columns : 0
                delegate: QQC2.MenuItem {
                    required property int index
                    text: raiz.modelo ? String(raiz.modelo.headerData(index, Qt.Horizontal)) : ""
                    checkable: true
                    checked: raiz.columna(index).visible !== false
                    enabled: index !== 0
                    onTriggered: raiz.mostrarColumna(index, checked)
                }
                onObjectAdded: (i, objeto) => menuCabecera.insertItem(i + 2, objeto)
                onObjectRemoved: (i, objeto) => menuCabecera.removeItem(objeto)
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
            pointerNavigationEnabled: false      // el clic lo atiende `clicEnFila` (Qt borraría la selección tras él)
            selectionModel: ItemSelectionModel { id: seleccionModelo; model: raiz.modelo }
            columnWidthProvider: function (c) { return raiz.anchoDe(c) }
            rowHeightProvider: function (r) { return raiz.altoDeFila(r) }
            onWidthChanged: forceLayout()
            onCurrentRowChanged: {
                // con el teclado (flechas, Inicio, RePág), la fila actual pasa a ser la elegida, como en una lista
                if (currentRow >= 0 && !seleccionModelo.isRowSelected(currentRow, seleccionModelo.currentIndex.parent)
                        && seleccionModelo.selectedIndexes.length <= tabla.columns) {
                    seleccionModelo.select(seleccionModelo.model.index(currentRow, 0), ItemSelectionModel.ClearAndSelect | ItemSelectionModel.Rows)
                    raiz.ancla = currentRow
                }
                raiz.filaActualCambiada(currentRow)
            }
            Connections { target: seleccionModelo; function onSelectionChanged() { raiz.seleccionCambiada() } }
            QQC2.ScrollBar.vertical: QQC2.ScrollBar {}
            QQC2.ScrollBar.horizontal: QQC2.ScrollBar {}

            Keys.onPressed: event => {
                if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) { if (currentRow >= 0) raiz.activada(currentRow); event.accepted = true }
                else if ((event.key === Qt.Key_Up || event.key === Qt.Key_Down) && (event.modifiers & Qt.ShiftModifier)) {
                    // Mayús+flecha alarga el tramo desde la fila de partida, como en una lista
                    const nueva = Math.max(0, Math.min(rows - 1, currentRow + (event.key === Qt.Key_Down ? 1 : -1)))
                    if (raiz.ancla < 0) raiz.ancla = Math.max(0, currentRow)
                    const ancla = raiz.ancla
                    raiz.clicEnFila(nueva, Qt.ShiftModifier)
                    raiz.ancla = ancla
                    positionViewAtRow(nueva, TableView.Contain)
                    event.accepted = true
                }
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
                readonly property bool sobre: raiz.filaSobre === row
                readonly property bool primera: column === 0
                readonly property bool ultima: column === tabla.columns - 1
                implicitHeight: raiz.altoFila
                // 4.2: la fila elegida, teñida del acento (no el bloque lleno del color de selección): el texto y los
                // colores semánticos se conservan; su marca de acento va en el borde izquierdo de la primera celda
                readonly property color fondoFila: row % 2 === 1 ? Kirigami.Theme.alternateBackgroundColor : Kirigami.Theme.backgroundColor
                color: selected ? Kirigami.ColorUtils.tintWithAlpha(fondoFila, Kirigami.Theme.highlightColor, sobre ? 0.32 : 0.24)
                     : fondoFila
                Accessible.role: Accessible.Cell
                Accessible.name: model.display !== undefined ? String(model.display) : ""

                Rectangle {   // la fila bajo el ratón: el tinte de «pasar por encima» del tema, en toda la fila
                    anchors.fill: parent
                    visible: celda.sobre && !celda.selected
                    color: Qt.alpha(Kirigami.Theme.hoverColor, 0.25)
                }
                // la fila actual sin selección (Ctrl+clic la quitó): un marco fino alrededor de la fila entera, no de
                // la celda (cada celda pone sus bordes de arriba y abajo, y la primera y la última los de los lados)
                Item {
                    anchors.fill: parent
                    visible: tabla.currentRow === celda.row && !celda.selected && tabla.activeFocus
                    Rectangle { anchors { left: parent.left; right: parent.right; top: parent.top } height: 1; color: Kirigami.Theme.highlightColor }
                    Rectangle { anchors { left: parent.left; right: parent.right; bottom: parent.bottom } height: 1; color: Kirigami.Theme.highlightColor }
                    Rectangle { visible: celda.primera; anchors { left: parent.left; top: parent.top; bottom: parent.bottom } width: 1; color: Kirigami.Theme.highlightColor }
                    Rectangle { visible: celda.ultima; anchors { right: parent.right; top: parent.top; bottom: parent.bottom } width: 1; color: Kirigami.Theme.highlightColor }
                }
                Rectangle {   // 4.2: la marca de la fila elegida (si el borde de nivel no ocupa ese sitio)
                    visible: celda.primera && celda.selected && !(celda.nivel !== "" && raiz.nivelesBorde.indexOf(celda.nivel) >= 0)
                    anchors { left: parent.left; top: parent.top; bottom: parent.bottom; topMargin: 2; bottomMargin: 2 }
                    width: Kirigami.Units.smallSpacing * 0.75
                    radius: width / 2
                    z: 1
                    color: Kirigami.Theme.highlightColor
                }
                Rectangle {   // 4.1: el nivel de la fila en su borde izquierdo (`nivelesBorde`)
                    objectName: "bordeNivel"
                    visible: celda.primera && celda.nivel !== "" && raiz.nivelesBorde.indexOf(celda.nivel) >= 0
                    anchors { left: parent.left; top: parent.top; bottom: parent.bottom }
                    width: raiz.anchoBorde
                    z: 1
                    color: raiz.nivelColor(celda.nivel, true)
                    opacity: celda.habilitado ? 1 : 0.4
                }
                HoverHandler {
                    // la celda bajo el ratón manda: salir de una solo apaga el resalte si nadie entró en otra
                    onHoveredChanged: {
                        if (hovered) { raiz.celdaSobre = celda; raiz.filaSobre = celda.row }
                        else if (raiz.celdaSobre === celda) { raiz.celdaSobre = null; raiz.filaSobre = -1 }
                    }
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
                             : Kirigami.Theme.textColor
                        implicitWidth: Kirigami.Units.iconSizes.small
                        implicitHeight: implicitWidth
                        opacity: celda.habilitado ? 1 : 0.5
                    }
                    QQC2.Label {
                        Layout.fillWidth: true
                        text: raiz.textoCelda(celda.column, celda.model.display)
                        elide: Text.ElideRight
                        wrapMode: (celda.col.lineas || 1) > 1 ? Text.Wrap : Text.NoWrap
                        maximumLineCount: celda.col.lineas || 1
                        horizontalAlignment: raiz.alineacion(celda.column)
                        font.family: celda.col.mono ? Kirigami.Theme.fixedWidthFont.family : Kirigami.Theme.defaultFont.family
                        color: celda.col.semantica ? raiz.nivelColor(celda.nivel, celda.habilitado)
                             : (!celda.habilitado || celda.col.secundaria) ? Kirigami.Theme.disabledTextColor
                             : Kirigami.Theme.textColor
                    }
                }

                TapHandler {
                    id: toque
                    acceptedButtons: Qt.LeftButton
                    onTapped: raiz.clicEnFila(celda.row, toque.point.modifiers)
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
