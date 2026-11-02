// GraficoQuickCharts (2.6) — el interior de `Grafico` que importa `org.kde.quickcharts`; se carga con un Loader para que
// `Grafico` exista aunque el módulo falte. `raiz` es el Grafico que lo carga. Sin colores propios: la paleta de
// QuickCharts sobre el acento de Kirigami.Theme para las series, y Kirigami.Theme para el resto.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import org.kde.quickcharts as Charts
import org.kde.quickcharts.controls as ChartsControls

Item {
    id: g
    property var raiz: null
    readonly property var series: raiz ? raiz.series : []
    readonly property bool hayBarras: raiz ? raiz.hayBarras : false
    readonly property int nSeries: series.length
    readonly property var paleta: Charts.ColorGradientSource {
        baseColor: Kirigami.Theme.highlightColor
        itemCount: Math.max(1, g.nSeries)
    }

    function px(x) { return raiz.xMaximo > raiz.xMinimo ? (x - raiz.xMinimo) / (raiz.xMaximo - raiz.xMinimo) * lienzo.width : 0 }
    function py(y) { return raiz.yMaximo > raiz.yMinimo ? lienzo.height - (y - raiz.yMinimo) / (raiz.yMaximo - raiz.yMinimo) * lienzo.height : lienzo.height }
    function formato(v) {
        const a = Math.abs(v)
        if (a >= 1000) return Number(v).toLocaleString(Qt.locale(), "f", 0)
        if (a >= 10) return Number(v).toLocaleString(Qt.locale(), "f", 1)
        return Number(v).toLocaleString(Qt.locale(), "f", 2)
    }
    function etiquetasY() {
        const n = 5, salida = []
        for (let i = 0; i < n; i++) salida.push(formato(raiz.yMaximo - i * (raiz.yMaximo - raiz.yMinimo) / (n - 1)))
        return salida
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: Kirigami.Units.smallSpacing

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: Kirigami.Units.smallSpacing

            Item {                                                       // la etiqueta del eje y, vertical
                visible: raiz && raiz.etiquetaY !== ""
                Layout.fillHeight: true
                Layout.preferredWidth: etiquetaY.implicitHeight
                QQC2.Label {
                    id: etiquetaY
                    anchors.centerIn: parent
                    rotation: -90
                    text: raiz ? raiz.etiquetaY : ""
                    font: Kirigami.Theme.smallFont
                    color: Kirigami.Theme.disabledTextColor
                    width: parent.height
                    horizontalAlignment: Text.AlignHCenter
                    elide: Text.ElideRight
                }
            }
            Item {                                                       // las etiquetas del eje y
                visible: !g.hayBarras
                Layout.fillHeight: true
                Layout.preferredWidth: Kirigami.Units.gridUnit * 3
                Repeater {
                    model: g.etiquetasY()
                    QQC2.Label {
                        required property string modelData
                        required property int index
                        readonly property int total: 5
                        width: parent.width
                        y: Math.min(Math.max(0, index * parent.height / (total - 1) - implicitHeight / 2), parent.height - implicitHeight)
                        horizontalAlignment: Text.AlignRight
                        text: modelData
                        font: Kirigami.Theme.smallFont
                        color: Kirigami.Theme.disabledTextColor
                    }
                }
            }
            Item {                                                       // el lienzo
                id: lienzo
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true

                ChartsControls.GridLines {
                    anchors.fill: parent
                    chart: g.hayBarras ? barras : lineas
                    direction: ChartsControls.GridLines.Vertical
                    major { count: 4; color: Kirigami.Theme.disabledTextColor; lineWidth: 1; visible: !g.hayBarras }
                    minor.visible: false
                    opacity: 0.35
                }
                ChartsControls.GridLines {
                    anchors.fill: parent
                    chart: g.hayBarras ? barras : lineas
                    direction: ChartsControls.GridLines.Horizontal
                    major { count: 4; color: Kirigami.Theme.disabledTextColor; lineWidth: 1 }
                    minor.visible: false
                    opacity: 0.35
                }
                Charts.LineChart {
                    id: lineas
                    anchors.fill: parent
                    visible: !g.hayBarras
                    lineWidth: 2
                    fillOpacity: 0
                    yRange { automatic: false; from: raiz ? raiz.yMinimo : 0; to: raiz ? raiz.yMaximo : 1 }
                    colorSource: g.paleta
                    nameSource: Charts.ArraySource { array: g.series.map(s => s.nombre) }
                }
                Instantiator {
                    model: g.hayBarras ? 0 : g.nSeries
                    delegate: Charts.ArraySource {
                        required property int index
                        array: g.series[index] ? g.series[index].y : []
                    }
                    onObjectAdded: (index, objeto) => lineas.insertValueSource(index, objeto)
                    onObjectRemoved: (index, objeto) => lineas.removeValueSource(objeto)
                }
                Charts.BarChart {
                    id: barras
                    anchors.fill: parent
                    visible: g.hayBarras
                    spacing: Kirigami.Units.largeSpacing
                    yRange { automatic: false; from: raiz ? raiz.yMinimo : 0; to: raiz ? raiz.yMaximo : 1 }
                    colorSource: Charts.SingleValueSource { value: Kirigami.Theme.highlightColor }
                    nameSource: Charts.ArraySource { array: g.hayBarras ? raiz.barras.categorias : [] }
                    valueSources: [Charts.ArraySource { array: g.hayBarras ? raiz.barras.valores : [] }]
                }
                Repeater {                                               // las marcas: una x o una y constante
                    model: raiz ? raiz.marcas : []
                    Item {
                        required property var modelData
                        readonly property bool vertical: modelData.x !== undefined
                        x: vertical ? g.px(modelData.x) : 0
                        y: vertical ? 0 : g.py(modelData.y)
                        width: vertical ? 1 : lienzo.width
                        height: vertical ? lienzo.height : 1
                        Rectangle { anchors.fill: parent; color: Kirigami.Theme.textColor; opacity: 0.6 }
                        QQC2.Label {
                            text: parent.modelData.etiqueta || ""
                            font: Kirigami.Theme.smallFont
                            color: Kirigami.Theme.textColor
                            x: parent.vertical ? Kirigami.Units.smallSpacing : Kirigami.Units.smallSpacing
                            y: parent.vertical ? Kirigami.Units.smallSpacing : -implicitHeight
                        }
                    }
                }
                Repeater {                                               // los puntos marcados
                    model: raiz ? raiz.puntos : []
                    Item {
                        required property var modelData
                        x: g.px(modelData.x) - Kirigami.Units.smallSpacing
                        y: g.py(modelData.y) - Kirigami.Units.smallSpacing
                        width: Kirigami.Units.smallSpacing * 2
                        height: width
                        Rectangle { anchors.fill: parent; radius: width / 2; color: Kirigami.Theme.neutralTextColor }
                        QQC2.Label {
                            text: parent.modelData.etiqueta || ""
                            font: Kirigami.Theme.smallFont
                            color: Kirigami.Theme.textColor
                            x: parent.width + Kirigami.Units.smallSpacing / 2
                            y: -implicitHeight / 2 + parent.height / 2
                        }
                    }
                }
                Item {                                                   // el equilibrio
                    visible: raiz && raiz.equilibrio !== null && raiz.equilibrio !== undefined
                    x: visible ? g.px(raiz.equilibrio.x) - Kirigami.Units.smallSpacing * 1.5 : 0
                    y: visible ? g.py(raiz.equilibrio.y) - Kirigami.Units.smallSpacing * 1.5 : 0
                    width: Kirigami.Units.smallSpacing * 3
                    height: width
                    Rectangle { anchors.fill: parent; radius: width / 2; color: Kirigami.Theme.positiveTextColor; border.color: Kirigami.Theme.backgroundColor; border.width: 1 }
                    QQC2.Label {
                        text: parent.visible ? (raiz.equilibrio.etiqueta || "") : ""
                        font: Kirigami.Theme.smallFont
                        color: Kirigami.Theme.textColor
                        x: parent.width + Kirigami.Units.smallSpacing / 2
                        y: -implicitHeight / 2 + parent.height / 2
                    }
                }
                Rectangle {                                              // la anotación, en la esquina superior izquierda
                    visible: raiz && raiz.anotacion !== ""
                    x: Kirigami.Units.smallSpacing
                    y: Kirigami.Units.smallSpacing
                    width: anotacion.implicitWidth + Kirigami.Units.largeSpacing
                    height: anotacion.implicitHeight + Kirigami.Units.smallSpacing * 2
                    radius: Kirigami.Units.cornerRadius
                    color: Kirigami.Theme.backgroundColor
                    opacity: 0.9
                    border.color: Kirigami.Theme.disabledTextColor
                    border.width: 1
                    QQC2.Label {
                        id: anotacion
                        anchors.centerIn: parent
                        text: raiz ? raiz.anotacion : ""
                        font: Kirigami.Theme.smallFont
                        color: Kirigami.Theme.textColor
                    }
                }
            }
        }
        Item {                                                           // las etiquetas del eje x
            id: filaX
            readonly property real margen: (raiz && raiz.etiquetaY !== "" ? etiquetaY.implicitHeight + Kirigami.Units.smallSpacing : 0) + (g.hayBarras ? 0 : Kirigami.Units.gridUnit * 3 + Kirigami.Units.smallSpacing)
            readonly property var etiquetas: g.hayBarras ? raiz.barras.categorias : (raiz ? raiz.etiquetasX : [])
            Layout.fillWidth: true
            Layout.preferredHeight: medida.implicitHeight
            QQC2.Label { id: medida; visible: false; text: "0"; font: Kirigami.Theme.smallFont }
            Repeater {
                model: filaX.etiquetas
                QQC2.Label {
                    required property var modelData
                    required property int index
                    readonly property int total: filaX.etiquetas.length
                    readonly property real centro: g.hayBarras ? (index + 0.5) / total * lienzo.width : (total > 1 ? index / (total - 1) * lienzo.width : lienzo.width / 2)
                    x: filaX.margen + Math.min(Math.max(0, centro - implicitWidth / 2), lienzo.width - implicitWidth)
                    text: String(modelData)
                    font: Kirigami.Theme.smallFont
                    color: Kirigami.Theme.disabledTextColor
                }
            }
        }
        QQC2.Label {
            visible: raiz && raiz.etiquetaX !== ""
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            text: raiz ? raiz.etiquetaX : ""
            font: Kirigami.Theme.smallFont
            color: Kirigami.Theme.disabledTextColor
        }
        Flow {                                                           // la leyenda
            visible: raiz && raiz.conLeyenda && !g.hayBarras && g.nSeries > 0
            Layout.fillWidth: true
            spacing: Kirigami.Units.largeSpacing
            Repeater {
                model: g.hayBarras ? 0 : g.nSeries
                Row {
                    required property int index
                    spacing: Kirigami.Units.smallSpacing
                    Rectangle {
                        width: Kirigami.Units.gridUnit; height: Kirigami.Units.smallSpacing
                        anchors.verticalCenter: parent.verticalCenter
                        color: g.paleta.colors[index] !== undefined ? g.paleta.colors[index] : Kirigami.Theme.highlightColor
                    }
                    QQC2.Label { text: g.series[index] ? g.series[index].nombre : ""; font: Kirigami.Theme.smallFont }
                }
            }
        }
    }
}
