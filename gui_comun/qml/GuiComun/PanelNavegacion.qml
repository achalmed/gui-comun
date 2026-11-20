// PanelNavegacion — el panel izquierdo compacto (como «Lugares» de Dolphin): secciones con cabecera, filas con icono,
// texto y contador tenue; un clic elige; plegado, solo iconos con su ayuda emergente.
// secciones: [{titulo, filas: [{nombre, texto, icono, contador, nivel, ancestros, plegable}]}]
// Árbol (4.1): una fila con `nivel` > 0 se sangra y solo se ve si todos sus `ancestros` (los `nombre` de las filas de
// arriba, del más alto al más cercano) están desplegados; una fila `plegable` lleva su flecha (clic: desplegar o
// plegar; elegirla también la despliega). Elegir una fila escondida (`actual`) despliega sus ancestros.
// El contenido deja sitio a la barra de desplazamiento: los contadores no quedan debajo de ella (4.1).
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

QQC2.Control {
    id: panel

    property var secciones: []
    property string actual: ""
    property bool plegado: false
    property int anchoPreferido: Kirigami.Units.gridUnit * 13
    property int anchoMinimo: Kirigami.Units.gridUnit * 9
    property var abiertos: ({})          // nombre → true: las filas plegables desplegadas
    signal elegida(string nombre)

    function abierta(nombre) { return panel.abiertos[nombre] === true }
    function fijarAbierta(nombre, abrir) {
        if (abierta(nombre) === abrir) return
        const nuevos = Object.assign({}, panel.abiertos)
        if (abrir) nuevos[nombre] = true
        else delete nuevos[nombre]
        panel.abiertos = nuevos
    }
    function alternar(nombre) { fijarAbierta(nombre, !abierta(nombre)) }
    function visibleEnArbol(fila) {
        for (const a of (fila.ancestros || [])) if (!abierta(a)) return false
        return true
    }
    // despliega los ancestros de la fila actual para que se vea, y la propia si tiene hijas (como al elegirla con el ratón)
    function mostrarActual() {
        for (const s of panel.secciones || [])
            for (const f of s.filas || [])
                if (f.nombre === panel.actual) {
                    const abrir = (f.ancestros || []).concat(f.plegable === true ? [f.nombre] : [])
                    if (abrir.every(a => abierta(a))) return
                    const nuevos = Object.assign({}, panel.abiertos)
                    for (const a of abrir) nuevos[a] = true
                    panel.abiertos = nuevos
                    return
                }
    }
    onActualChanged: mostrarActual()
    onSeccionesChanged: mostrarActual()

    implicitWidth: plegado ? Kirigami.Units.iconSizes.smallMedium + Kirigami.Units.largeSpacing * 3 : anchoPreferido
    padding: Kirigami.Units.smallSpacing
    Kirigami.Theme.colorSet: Kirigami.Theme.Window
    Kirigami.Theme.inherit: false
    Accessible.role: Accessible.List
    Accessible.name: "Navegación"

    background: Rectangle { color: Kirigami.Theme.backgroundColor }

    contentItem: QQC2.ScrollView {
        id: desplazamiento
        QQC2.ScrollBar.horizontal.policy: QQC2.ScrollBar.AlwaysOff
        ColumnLayout {
            // el ancho disponible del ScrollView ya descuenta la barra vertical cuando se ve (el estilo de KDE la suma
            // a su relleno): así no tapa los contadores
            width: desplazamiento.availableWidth
            spacing: 0
            Repeater {
                model: panel.secciones
                delegate: ColumnLayout {
                    id: seccion
                    required property var modelData
                    required property int index
                    readonly property bool conArbol: (modelData.filas || []).some(f => f.plegable === true || (f.nivel || 0) > 0)
                    Layout.fillWidth: true
                    spacing: 0
                    Kirigami.ListSectionHeader {
                        visible: !panel.plegado
                        text: seccion.modelData.titulo
                        Layout.fillWidth: true
                    }
                    Kirigami.Separator { visible: panel.plegado && seccion.index > 0; Layout.fillWidth: true; Layout.margins: Kirigami.Units.smallSpacing }
                    Repeater {
                        model: seccion.modelData.filas
                        delegate: QQC2.ItemDelegate {
                            id: fila
                            required property var modelData
                            readonly property int nivel: modelData.nivel || 0
                            readonly property bool plegable: modelData.plegable === true
                            readonly property bool desplegada: plegable && panel.abierta(modelData.nombre)
                            Layout.fillWidth: true
                            visible: panel.visibleEnArbol(modelData) && (!panel.plegado || nivel === 0)
                            highlighted: panel.actual === modelData.nombre
                            text: modelData.texto
                            icon.name: modelData.icono || ""
                            leftPadding: Kirigami.Units.smallSpacing * 2 + (panel.plegado ? 0 : nivel * Kirigami.Units.gridUnit)
                            rightPadding: Kirigami.Units.smallSpacing * 2
                            topPadding: Kirigami.Units.smallSpacing + Kirigami.Units.smallSpacing / 2
                            bottomPadding: Kirigami.Units.smallSpacing + Kirigami.Units.smallSpacing / 2
                            onClicked: {
                                if (plegable && !desplegada) panel.fijarAbierta(modelData.nombre, true)
                                panel.actual = modelData.nombre
                                panel.elegida(modelData.nombre)
                            }
                            Keys.onRightPressed: if (plegable) panel.fijarAbierta(modelData.nombre, true)
                            Keys.onLeftPressed: if (plegable) panel.fijarAbierta(modelData.nombre, false)
                            hoverEnabled: true
                            // 4.2: la fila elegida, un fondo redondeado teñido del acento con su marca a la izquierda (como
                            // la barra lateral de Preferencias del sistema), no el bloque lleno del color de selección: el
                            // texto conserva su color y gana peso; al pasar el ratón, un velo tenue; el foco, un borde
                            topInset: 1
                            bottomInset: 1
                            leftInset: Kirigami.Units.smallSpacing / 2
                            rightInset: Kirigami.Units.smallSpacing / 2
                            background: Rectangle {
                                radius: Kirigami.Units.cornerRadius
                                color: fila.highlighted ? Kirigami.ColorUtils.tintWithAlpha(Kirigami.Theme.backgroundColor, Kirigami.Theme.highlightColor, fila.hovered || fila.pressed ? 0.30 : 0.22)
                                     : fila.pressed ? Kirigami.ColorUtils.tintWithAlpha(Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor, 0.14)
                                     : fila.hovered ? Kirigami.ColorUtils.tintWithAlpha(Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor, 0.07)
                                     : "transparent"
                                border.width: fila.visualFocus ? 1 : 0
                                border.color: Kirigami.Theme.focusColor
                                Behavior on color { ColorAnimation { duration: Kirigami.Units.shortDuration } }
                                Rectangle {          // la marca de la elegida
                                    visible: fila.highlighted && !panel.plegado
                                    anchors.left: parent.left
                                    anchors.leftMargin: Kirigami.Units.smallSpacing / 2
                                    anchors.verticalCenter: parent.verticalCenter
                                    width: Kirigami.Units.smallSpacing * 0.75
                                    height: parent.height - Kirigami.Units.smallSpacing * 2.5
                                    radius: width / 2
                                    color: Kirigami.Theme.highlightColor
                                }
                            }
                            Accessible.name: modelData.texto + (modelData.contador !== undefined ? ", " + modelData.contador : "")
                                             + (plegable ? (desplegada ? ", desplegada" : ", plegada") : "")
                            QQC2.ToolTip.visible: (panel.plegado || etiqueta.truncated) && hovered
                            QQC2.ToolTip.delay: Kirigami.Units.toolTipDelay
                            QQC2.ToolTip.text: modelData.texto + (modelData.contador !== undefined && modelData.contador !== "" ? " · " + modelData.contador : "")
                            contentItem: RowLayout {
                                spacing: Kirigami.Units.smallSpacing
                                // la flecha del árbol (o su hueco, para que los iconos queden en columna)
                                Item {
                                    visible: seccion.conArbol && !panel.plegado
                                    implicitWidth: Kirigami.Units.iconSizes.small
                                    implicitHeight: implicitWidth
                                    Layout.alignment: Qt.AlignVCenter
                                    Kirigami.Icon {
                                        anchors.fill: parent
                                        visible: fila.plegable
                                        source: fila.desplegada ? "arrow-down" : (fila.mirrored ? "arrow-left" : "arrow-right")
                                        color: Kirigami.Theme.disabledTextColor
                                    }
                                    TapHandler {
                                        enabled: fila.plegable
                                        onTapped: panel.alternar(fila.modelData.nombre)
                                    }
                                }
                                Kirigami.Icon {
                                    source: fila.modelData.icono || "folder"
                                    implicitWidth: Kirigami.Units.iconSizes.small
                                    implicitHeight: implicitWidth
                                    Layout.alignment: Qt.AlignVCenter
                                }
                                QQC2.Label {
                                    id: etiqueta
                                    visible: !panel.plegado
                                    text: fila.modelData.texto
                                    Layout.fillWidth: true
                                    elide: Text.ElideRight
                                    color: Kirigami.Theme.textColor
                                    font.weight: fila.highlighted ? Font.DemiBold : Font.Normal
                                }
                                QQC2.Label {
                                    visible: !panel.plegado && fila.modelData.contador !== undefined && fila.modelData.contador !== ""
                                    text: fila.modelData.contador !== undefined ? fila.modelData.contador : ""
                                    font: Kirigami.Theme.smallFont
                                    color: Kirigami.Theme.disabledTextColor
                                }
                            }
                        }
                    }
                }
            }
            Item { Layout.fillHeight: true }
        }
    }
}
