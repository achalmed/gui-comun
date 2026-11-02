// PaginaFormulario (2.7) — un formulario generado desde una lista de campos (la ficha de una herramienta), sobre
// Kirigami.FormLayout: un control por tipo (texto, multilinea, entero, decimal, opcion, casilla, clave, color, ruta,
// carpeta), la ayuda de cada campo debajo, el asterisco de lo obligatorio; `valores` es lo escrito (sin los vacíos:
// quien lo usa pone el valor por omisión), `cambiado(clave, valor)` avisa de cada edición, `poner(valores)` y
// `restablecer()` lo rellenan. Lo que Raphi Studio hacía a mano con QtWidgets y lo que pide cualquier studio que arme
// pantallas desde fichas. Sin colores propios: Kirigami.Theme y Kirigami.Units.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import QtQuick.Dialogs
import org.kde.kirigami as Kirigami

ColumnLayout {
    id: raiz

    // [{clave, etiqueta, tipo, defecto, opciones: [[valor, etiqueta]…], minimo, maximo, ayuda, obligatorio, marcador}]
    property var campos: []
    property string nombreAccesible: "Formulario"
    property string mensajeVacio: "Sin opciones"
    readonly property var valores: _valores                    // {clave: valor} de lo escrito (sin vacíos)
    readonly property int nCampos: campos.length
    property var _valores: ({})

    signal cambiado(string clave, var valor)

    function campo(clave) { return campos.find(c => c.clave === clave) || null }
    function valor(clave) {
        if (_valores[clave] !== undefined) return _valores[clave]
        const c = campo(clave)
        return c && c.defecto !== undefined && c.defecto !== null ? c.defecto : ""
    }
    function fijar(clave, v) {
        const nuevos = Object.assign({}, _valores)
        if (v === "" || v === null || v === undefined) delete nuevos[clave]
        else nuevos[clave] = v
        _valores = nuevos
        cambiado(clave, v)
    }
    function poner(mapa) {
        const nuevos = {}
        for (const k in (mapa || {})) if (mapa[k] !== "" && mapa[k] !== null && mapa[k] !== undefined) nuevos[k] = mapa[k]
        _valores = nuevos
    }
    function restablecer() { _valores = ({}) }
    function textoDe(c) { const v = valor(c.clave); return v === null || v === undefined ? "" : String(v) }

    readonly property alias formulario: forma            // el Kirigami.FormLayout de dentro
    spacing: Kirigami.Units.smallSpacing
    Accessible.name: nombreAccesible
    onCamposChanged: restablecer()

    QQC2.Label {
        Layout.fillWidth: true
        visible: raiz.campos.length === 0 && raiz.mensajeVacio !== ""
        text: raiz.mensajeVacio
        wrapMode: Text.WordWrap
        color: Kirigami.Theme.disabledTextColor
    }

    Kirigami.FormLayout {
        id: forma
        Layout.fillWidth: true
        visible: raiz.campos.length > 0
        Repeater {
        model: raiz.campos
        Loader {
            id: cargador
            required property var modelData
            required property int index
            readonly property var c: modelData
            readonly property string tipo: String(modelData.tipo || "texto")
            Kirigami.FormData.label: tipo === "casilla" ? "" : (modelData.etiqueta || modelData.clave) + (modelData.obligatorio ? " *" : "") + ":"
            Kirigami.FormData.labelAlignment: (tipo === "multilinea" || tipo === "color") ? Qt.AlignTop : Qt.AlignVCenter
            Layout.fillWidth: true
            sourceComponent: {
                switch (tipo) {
                case "multilinea": return areaTexto
                case "entero": return entero
                case "decimal": return decimal
                case "opcion": return opcion
                case "casilla": return casilla
                case "color": return color
                case "ruta": case "carpeta": return ruta
                default: return texto
                }
            }
            onLoaded: { item.cargador = cargador }
        }
        }
    }

    // --- los controles, uno por tipo ------------------------------------------------------------------------
    component Ayuda: QQC2.Label {
        required property var c
        visible: text !== ""
        Layout.fillWidth: true
        text: c.ayuda || ""
        wrapMode: Text.WordWrap
        font: Kirigami.Theme.smallFont
        color: Kirigami.Theme.disabledTextColor
    }

    Component {
        id: texto
        ColumnLayout {
            id: caja
            property var cargador
            readonly property var c: cargador ? cargador.c : ({})
            spacing: 0
            QQC2.TextField {
                id: campoTexto
                Layout.fillWidth: true
                text: raiz.textoDe(c)
                echoMode: c.tipo === "clave" ? TextInput.Password : TextInput.Normal
                placeholderText: c.marcador || ""
                onTextEdited: raiz.fijar(c.clave, text)
                Accessible.name: c.etiqueta || c.clave
                Connections { target: raiz; function on_ValoresChanged() { if (!campoTexto.activeFocus) campoTexto.text = raiz.textoDe(caja.c) } }
            }
            Ayuda { c: caja.c }
        }
    }
    Component {
        id: areaTexto
        ColumnLayout {
            id: caja
            property var cargador
            readonly property var c: cargador ? cargador.c : ({})
            spacing: 0
            QQC2.ScrollView {
                Layout.fillWidth: true
                Layout.preferredHeight: Kirigami.Units.gridUnit * 5
                QQC2.TextArea {
                    id: area
                    text: raiz.textoDe(caja.c)
                    placeholderText: caja.c.marcador || ""
                    wrapMode: TextEdit.Wrap
                    onTextChanged: if (activeFocus) raiz.fijar(caja.c.clave, text)
                    Accessible.name: caja.c.etiqueta || caja.c.clave
                    Connections { target: raiz; function on_ValoresChanged() { if (!area.activeFocus) area.text = raiz.textoDe(caja.c) } }
                }
            }
            Ayuda { c: caja.c }
        }
    }
    Component {
        id: entero
        ColumnLayout {
            id: caja
            property var cargador
            readonly property var c: cargador ? cargador.c : ({})
            spacing: 0
            QQC2.SpinBox {
                id: giro
                editable: true
                from: c.minimo !== undefined && c.minimo !== null ? Math.round(c.minimo) : -1000000
                to: c.maximo !== undefined && c.maximo !== null ? Math.round(c.maximo) : 1000000
                value: Math.round(Number(raiz.valor(c.clave)) || 0)
                onValueModified: raiz.fijar(c.clave, value)
                Accessible.name: c.etiqueta || c.clave
                Connections { target: raiz; function on_ValoresChanged() { giro.value = Math.round(Number(raiz.valor(caja.c.clave)) || 0) } }
            }
            Ayuda { c: caja.c }
        }
    }
    Component {
        id: decimal
        ColumnLayout {
            id: caja
            property var cargador
            readonly property var c: cargador ? cargador.c : ({})
            spacing: 0
            QQC2.TextField {
                id: campoDecimal
                Layout.preferredWidth: Kirigami.Units.gridUnit * 8
                text: raiz.textoDe(c)
                validator: DoubleValidator { bottom: c.minimo !== undefined && c.minimo !== null ? c.minimo : -1e12; top: c.maximo !== undefined && c.maximo !== null ? c.maximo : 1e12; notation: DoubleValidator.StandardNotation }
                inputMethodHints: Qt.ImhFormattedNumbersOnly
                onTextEdited: raiz.fijar(c.clave, text === "" ? "" : Number(text.replace(",", ".")))
                Accessible.name: c.etiqueta || c.clave
                Connections { target: raiz; function on_ValoresChanged() { if (!campoDecimal.activeFocus) campoDecimal.text = raiz.textoDe(caja.c) } }
            }
            Ayuda { c: caja.c }
        }
    }
    Component {
        id: opcion
        ColumnLayout {
            id: caja
            property var cargador
            readonly property var c: cargador ? cargador.c : ({})
            readonly property var lista: (c.opciones || []).map(o => (typeof o !== "string" && o !== null && o.length !== undefined) ? ({ valor: o[0], etiqueta: o.length > 1 ? String(o[1]) : String(o[0]) }) : ({ valor: o, etiqueta: String(o) }))
            spacing: 0
            QQC2.ComboBox {
                id: selector
                Layout.fillWidth: true
                model: caja.lista
                textRole: "etiqueta"
                valueRole: "valor"
                currentIndex: Math.max(0, caja.lista.findIndex(o => String(o.valor) === raiz.textoDe(caja.c)))
                onActivated: index => raiz.fijar(caja.c.clave, caja.lista[index].valor)
                Accessible.name: caja.c.etiqueta || caja.c.clave
                Connections { target: raiz; function on_ValoresChanged() { selector.currentIndex = Math.max(0, caja.lista.findIndex(o => String(o.valor) === raiz.textoDe(caja.c))) } }
            }
            Ayuda { c: caja.c }
        }
    }
    Component {
        id: casilla
        ColumnLayout {
            id: caja
            property var cargador
            readonly property var c: cargador ? cargador.c : ({})
            spacing: 0
            QQC2.CheckBox {
                id: marca
                text: (c.etiqueta || c.clave) + (c.obligatorio ? " *" : "")
                checked: { const v = raiz.valor(c.clave); return v === true || v === "true" || v === 1 || v === "1" }
                onToggled: raiz.fijar(c.clave, checked)
                Accessible.name: c.etiqueta || c.clave
                Connections { target: raiz; function on_ValoresChanged() { const v = raiz.valor(caja.c.clave); marca.checked = (v === true || v === "true" || v === 1 || v === "1") } }
            }
            Ayuda { c: caja.c; Layout.leftMargin: Kirigami.Units.gridUnit * 1.5 }
        }
    }
    Component {
        id: color
        ColumnLayout {
            id: caja
            property var cargador
            readonly property var c: cargador ? cargador.c : ({})
            spacing: 0
            RowLayout {
                spacing: Kirigami.Units.smallSpacing
                Rectangle {
                    implicitWidth: Kirigami.Units.gridUnit * 2
                    implicitHeight: Kirigami.Units.gridUnit * 1.4
                    radius: Kirigami.Units.cornerRadius
                    color: raiz.textoDe(caja.c) || "transparent"
                    border.color: Kirigami.Theme.disabledTextColor
                    border.width: 1
                }
                QQC2.TextField {
                    id: campoColor
                    Layout.preferredWidth: Kirigami.Units.gridUnit * 7
                    text: raiz.textoDe(caja.c)
                    placeholderText: "#rrggbb"
                    onTextEdited: raiz.fijar(caja.c.clave, text)
                    Accessible.name: caja.c.etiqueta || caja.c.clave
                    Connections { target: raiz; function on_ValoresChanged() { if (!campoColor.activeFocus) campoColor.text = raiz.textoDe(caja.c) } }
                }
                QQC2.ToolButton {
                    icon.name: "color-picker"
                    text: "Elegir"
                    display: QQC2.AbstractButton.IconOnly
                    onClicked: { dialogoColor.selectedColor = raiz.textoDe(caja.c) || Kirigami.Theme.textColor; dialogoColor.open() }
                    Accessible.name: "Elegir el color"
                    QQC2.ToolTip.text: "Elegir el color"; QQC2.ToolTip.visible: hovered
                }
                ColorDialog {
                    id: dialogoColor
                    title: caja.c.etiqueta || "Color"
                    onAccepted: raiz.fijar(caja.c.clave, selectedColor.toString())
                }
            }
            Ayuda { c: caja.c }
        }
    }
    Component {
        id: ruta
        ColumnLayout {
            id: caja
            property var cargador
            readonly property var c: cargador ? cargador.c : ({})
            spacing: 0
            CampoRuta {
                id: campoRuta
                Layout.fillWidth: true
                carpeta: caja.c.tipo === "carpeta"
                texto: raiz.textoDe(caja.c)
                titulo: caja.c.etiqueta || caja.c.clave
                nombreAccesible: caja.c.etiqueta || caja.c.clave
                onTextoChanged: if (texto !== raiz.textoDe(caja.c)) raiz.fijar(caja.c.clave, texto)
                onAceptada: t => raiz.fijar(caja.c.clave, t)
            }
            Ayuda { c: caja.c }
        }
    }
}
