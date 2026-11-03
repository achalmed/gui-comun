// EditorTexto (3.1) — un archivo abierto en un editor: TextArea con resaltado de KSyntaxHighlighting (el tema claro u
// oscuro según el fondo de Kirigami), números de línea (solo las visibles), ir a línea, comentar la selección con el
// comentario del lenguaje (Ctrl+T en LaTeX), autocompletado opcional (`completar`, una función que da el studio) y
// Ctrl+clic (`ctrlClic`: SyncTeX en LaTeX). Cada archivo tiene su TextArea y con él su historial de deshacer. Nunca
// escribe en disco: `guardar()` lo pide el studio con su acción (Ctrl+S) a `controlador` (gui_comun.editor). Viene de
// LaTeX Studio y Quarto Studio (que lo copió); «modificado» compara con el texto leído (el resaltado vuelve a emitir
// textChanged al engancharse: suponerlo marcaba el archivo como modificado nada más abrirlo). Sin colores propios.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

Item {
    id: raiz

    property var controlador: null                   // gui_comun.editor.ControladorEditor
    property string ruta: ""
    property string definicion: ""                   // «LaTeX», «Markdown», «YAML»…; vacía, sin resaltar
    property bool soloLectura: false
    property bool ajustarLineas: false
    property real tamanoLetra: 0                     // 0: el de la fuente monoespaciada del tema
    property bool conNumeros: true
    property var completar: null                     // function(textoAntes) -> {tipo, prefijo, elementos: [{texto, detalle, insertar}]}
    property var disparaCompletado: null             // function(textoAntes, tecla) -> bool: ¿abrir las sugerencias?
    property bool cargado: false
    property bool modificado: false
    property string original: ""                     // el texto como está en disco
    property var inicios: [0]                        // la posición de inicio de cada línea lógica
    property var lineasVisibles: []
    readonly property alias area: area
    readonly property int lineaActual: lineaDe(area.cursorPosition)
    readonly property int columnaActual: area.cursorPosition - (inicios[lineaActual - 1] || 0)
    readonly property bool oscuro: (Kirigami.Theme.backgroundColor.r * 0.299 + Kirigami.Theme.backgroundColor.g * 0.587
                                    + Kirigami.Theme.backgroundColor.b * 0.114) < 0.5
    // el comentario de línea del lenguaje: [abre, cierra]
    readonly property var comentario: ({ LaTeX: ["% ", ""], BibTeX: ["% ", ""], Markdown: ["<!-- ", " -->"], HTML: ["<!-- ", " -->"],
                                         XML: ["<!-- ", " -->"], YAML: ["# ", ""], Python: ["# ", ""], Bash: ["# ", ""], Zsh: ["# ", ""],
                                         TOML: ["# ", ""], "INI Files": ["; ", ""], Perl: ["# ", ""], "R Script": ["# ", ""], Lua: ["-- ", ""],
                                         SQL: ["-- ", ""], JavaScript: ["// ", ""], TypeScript: ["// ", ""], QML: ["// ", ""], SCSS: ["// ", ""],
                                         CSS: ["/* ", " */"] })[definicion] || ["# ", ""]

    signal ctrlClic(int linea, int columna)
    signal guardado()

    Accessible.name: "Editor de " + raiz.ruta.split("/").pop()

    // ------------------------------------------------------------------ carga y estado
    function cargar() {
        original = controlador ? controlador.leer(ruta) : ""
        area.text = original
        area.cursorPosition = 0
        cargado = true
        modificado = false
        recalcular()
    }
    function recargarDesdeDisco() {
        const pos = area.cursorPosition
        cargar()
        area.cursorPosition = Math.min(pos, area.length)
        if (controlador) { controlador.aceptarDisco(ruta); controlador.marcarModificado(ruta, false) }
    }
    // "" si guardó; «externo» si cambió fuera (y no se forzó); o el error
    function guardar(forzar) {
        if (!controlador) return "Sin controlador"
        const r = controlador.guardar(ruta, area.text, forzar === true)
        if (r === "") { original = area.text; modificado = false; guardado() }
        return r
    }
    onModificadoChanged: if (cargado && controlador) controlador.marcarModificado(ruta, modificado)

    // ------------------------------------------------------------------ líneas
    function recalcular() {
        const t = area.text
        const lista = [0]
        let i = t.indexOf("\n")
        while (i >= 0) { lista.push(i + 1); i = t.indexOf("\n", i + 1) }
        inicios = lista
        visibles()
    }
    function lineaDe(pos) {
        let lo = 0, hi = inicios.length - 1
        while (lo < hi) { const mid = (lo + hi + 1) >> 1; if (inicios[mid] <= pos) lo = mid; else hi = mid - 1 }
        return lo + 1
    }
    function visibles() {
        const flick = desplazamiento.contentItem
        const arriba = flick.contentY, abajo = arriba + desplazamiento.height
        let lo = 0, hi = inicios.length - 1
        while (lo < hi) {
            const mid = (lo + hi) >> 1
            const r = area.positionToRectangle(inicios[mid])
            if (r.y + r.height < arriba) lo = mid + 1; else hi = mid
        }
        const salida = []
        for (let k = lo; k < inicios.length; k++) {
            const r = area.positionToRectangle(inicios[k])
            if (r.y > abajo) break
            salida.push({ n: k + 1, y: r.y - arriba, alto: r.height })
        }
        lineasVisibles = salida
    }
    function irALinea(linea, columna) {
        const n = Math.max(1, Math.min(linea, inicios.length))
        area.cursorPosition = Math.min(area.length, (inicios[n - 1] || 0) + Math.max(0, columna || 0))
        area.forceActiveFocus()
        centrarCursor()
    }
    function centrarCursor() {
        const flick = desplazamiento.contentItem
        const r = area.cursorRectangle
        if (r.y < flick.contentY || r.y + r.height > flick.contentY + desplazamiento.height)
            flick.contentY = Math.max(0, Math.min(flick.contentHeight - desplazamiento.height, r.y - desplazamiento.height / 3))
    }
    function seleccionar(inicio, fin) {
        area.select(inicio, fin)
        centrarCursor()
    }

    // ------------------------------------------------------------------ comentar
    function comentar() {
        if (soloLectura) return
        const ab = comentario[0], ci = comentario[1]
        const a = lineaDe(area.selectionStart), b = lineaDe(Math.max(area.selectionStart, area.selectionEnd - (area.selectionEnd > area.selectionStart ? 1 : 0)))
        let todas = true
        for (let n = a; n <= b; n++) {
            const ini = inicios[n - 1], fin = n < inicios.length ? inicios[n] - 1 : area.length
            const linea = area.getText(ini, fin)
            if (linea.trim() !== "" && !linea.trim().startsWith(ab.trim())) todas = false
        }
        for (let n = b; n >= a; n--) {
            const ini = inicios[n - 1], fin = n < inicios.length ? inicios[n] - 1 : area.length
            const linea = area.getText(ini, fin)
            if (linea.trim() === "") continue
            if (todas) {
                const sangria = linea.length - linea.trimStart().length
                let resto = linea.trimStart().slice(ab.trim().length).replace(/^ /, "")
                if (ci && resto.trimEnd().endsWith(ci.trim())) resto = resto.trimEnd().slice(0, -ci.trim().length).replace(/ $/, "")
                area.remove(ini, fin)
                area.insert(ini, linea.slice(0, sangria) + resto)
            } else {
                area.insert(fin, ci)
                area.insert(ini, ab)
            }
        }
    }

    // ------------------------------------------------------------------ autocompletado (opcional)
    function textoAntes() {
        const ini = inicios[lineaDe(area.cursorPosition) - 1] || 0
        return area.getText(ini, area.cursorPosition)
    }
    function abrirSugerencias(forzado) {
        if (typeof raiz.completar !== "function") return
        const r = raiz.completar(textoAntes(), forzado === true)
        if (!r || !r.tipo || !r.elementos || r.elementos.length === 0) { sugerencias.close(); return }
        sugerencias.prefijo = r.prefijo || ""
        sugerencias.tipo = r.tipo
        listaSugerencias.model = r.elementos
        listaSugerencias.currentIndex = 0
        const c = area.cursorRectangle
        sugerencias.x = Math.min(raiz.width - sugerencias.width, area.mapToItem(raiz, c.x, c.y).x)
        sugerencias.y = area.mapToItem(raiz, c.x, c.y + c.height).y
        sugerencias.open()
    }
    function aceptarSugerencia() {
        const e = listaSugerencias.model[listaSugerencias.currentIndex]
        if (!e) return
        const p = area.cursorPosition
        area.remove(p - sugerencias.prefijo.length, p)
        area.insert(area.cursorPosition, e.insertar)
        if (e.cierre) {                              // el cierre va tras el cursor: \fra → \frac{|}{}
            const p0 = area.cursorPosition
            const resto = area.getText(p0, Math.min(area.length, p0 + e.cierre.length))
            if (resto !== e.cierre) area.insert(p0, e.cierre)
            area.cursorPosition = p0
        }
        sugerencias.close()
    }

    // ------------------------------------------------------------------ la vista
    RowLayout {
        anchors.fill: parent
        spacing: 0

        Item {
            id: margen
            visible: raiz.conNumeros
            Layout.fillHeight: true
            Layout.preferredWidth: metricas.advanceWidth("0") * Math.max(3, String(raiz.inicios.length).length) + Kirigami.Units.largeSpacing * 2
            clip: true
            Accessible.ignored: true
            Rectangle { anchors.fill: parent; color: Kirigami.Theme.alternateBackgroundColor }
            Repeater {
                model: raiz.lineasVisibles
                delegate: QQC2.Label {
                    required property var modelData
                    x: 0
                    y: modelData.y
                    width: margen.width - Kirigami.Units.smallSpacing * 2
                    height: modelData.alto
                    horizontalAlignment: Text.AlignRight
                    verticalAlignment: Text.AlignVCenter
                    text: modelData.n
                    font: area.font
                    color: modelData.n === raiz.lineaActual ? Kirigami.Theme.textColor : Kirigami.Theme.disabledTextColor
                }
            }
        }
        Kirigami.Separator { Layout.fillHeight: true; visible: raiz.conNumeros }

        QQC2.ScrollView {
            id: desplazamiento
            Layout.fillWidth: true
            Layout.fillHeight: true
            QQC2.ScrollBar.horizontal.policy: raiz.ajustarLineas ? QQC2.ScrollBar.AlwaysOff : QQC2.ScrollBar.AsNeeded

            QQC2.TextArea {
                id: area
                readOnly: raiz.soloLectura
                textFormat: TextEdit.PlainText
                wrapMode: raiz.ajustarLineas ? TextEdit.Wrap : TextEdit.NoWrap
                font.family: Kirigami.Theme.fixedWidthFont.family
                font.pointSize: raiz.tamanoLetra > 0 ? raiz.tamanoLetra : Kirigami.Theme.fixedWidthFont.pointSize
                selectByMouse: true
                persistentSelection: true
                tabStopDistance: metricas.advanceWidth(" ") * 2
                Accessible.name: raiz.Accessible.name
                background: Rectangle { color: Kirigami.Theme.backgroundColor }

                onTextChanged: { if (raiz.cargado) raiz.modificado = area.text !== raiz.original; temporizador.restart() }
                onWidthChanged: temporizador.restart()
                onCursorPositionChanged: if (sugerencias.opened && area.cursorPosition < sugerencias.inicio) sugerencias.close()

                Keys.onPressed: event => {
                    if (sugerencias.opened) {
                        if (event.key === Qt.Key_Down) { listaSugerencias.incrementCurrentIndex(); event.accepted = true; return }
                        if (event.key === Qt.Key_Up) { listaSugerencias.decrementCurrentIndex(); event.accepted = true; return }
                        if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter || event.key === Qt.Key_Tab) { raiz.aceptarSugerencia(); event.accepted = true; return }
                        if (event.key === Qt.Key_Escape) { sugerencias.close(); event.accepted = true; return }
                    }
                }
                Keys.onReleased: event => {
                    if (typeof raiz.disparaCompletado !== "function") return
                    if (event.key === Qt.Key_Backspace && sugerencias.opened) { raiz.abrirSugerencias(false); return }
                    if (event.text === "") return
                    if (raiz.disparaCompletado(raiz.textoAntes(), event.text)) raiz.abrirSugerencias(false)
                    else if (sugerencias.opened) sugerencias.close()
                }

                TapHandler {
                    acceptedModifiers: Qt.ControlModifier
                    onTapped: (punto) => {
                        const pos = area.positionAt(punto.position.x, punto.position.y)
                        area.cursorPosition = pos
                        raiz.ctrlClic(raiz.lineaDe(pos), pos - raiz.inicios[raiz.lineaDe(pos) - 1])
                    }
                }
            }
        }
    }

    Connections {
        target: desplazamiento.contentItem
        function onContentYChanged() { raiz.visibles() }
        function onHeightChanged() { raiz.visibles() }
    }
    Timer { id: temporizador; interval: 60; onTriggered: raiz.recalcular() }
    FontMetrics { id: metricas; font: area.font }

    Loader {
        active: raiz.definicion !== ""
        source: "ResaltadoEditor.qml"
        onLoaded: { item.nombreDefinicion = raiz.definicion; item.oscuro = Qt.binding(() => raiz.oscuro); item.textEdit = area }
    }

    QQC2.Popup {
        id: sugerencias
        property string prefijo: ""
        property string tipo: ""
        property int inicio: area.cursorPosition - prefijo.length
        width: Kirigami.Units.gridUnit * 24
        height: Math.min(Kirigami.Units.gridUnit * 12, listaSugerencias.contentHeight + topPadding + bottomPadding)
        padding: 1
        focus: false
        closePolicy: QQC2.Popup.CloseOnPressOutside
        contentItem: ListView {
            id: listaSugerencias
            clip: true
            keyNavigationEnabled: false
            Accessible.name: "Sugerencias"
            delegate: QQC2.ItemDelegate {
                required property var modelData
                required property int index
                width: listaSugerencias.width
                highlighted: ListView.isCurrentItem
                onClicked: { listaSugerencias.currentIndex = index; raiz.aceptarSugerencia() }
                contentItem: RowLayout {
                    spacing: Kirigami.Units.smallSpacing
                    QQC2.Label { text: modelData.texto; font.family: Kirigami.Theme.fixedWidthFont.family; elide: Text.ElideRight; Layout.maximumWidth: parent.width * 0.55 }
                    QQC2.Label { text: modelData.detalle || ""; color: Kirigami.Theme.disabledTextColor; elide: Text.ElideRight; Layout.fillWidth: true; font: Kirigami.Theme.smallFont }
                }
            }
        }
    }
}
