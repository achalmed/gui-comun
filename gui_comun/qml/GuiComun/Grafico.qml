// Grafico (2.6) — un gráfico de líneas o de barras sobre `org.kde.quickcharts`: las series (`{nombre, y}`) sobre una
// rejilla común de x (QuickCharts posiciona cada valor por su índice: quien lo usa remuestrea sus curvas), las
// etiquetas de los ejes, la rejilla, la leyenda, los puntos marcados, el equilibrio, las marcas verticales u
// horizontales y una anotación. Los colores de las series salen de la paleta de QuickCharts (`ColorGradientSource`
// sobre el acento de Kirigami.Theme), nunca de una lista propia. Si el módulo QuickCharts no está, muestra `imagen`
// (un PNG, p. ej. la figura de matplotlib) y, sin ella, el mensaje de vacío. Lo que Simuladores Studio pidió al marco.
import QtQuick
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

QQC2.Control {
    id: raiz

    property var series: []                // [{nombre: "IS", y: [..]}]: todas con el mismo número de valores (la rejilla común)
    property var etiquetasX: []            // las etiquetas del eje x, repartidas de izquierda a derecha (p. ej. cinco valores)
    property real xMinimo: 0               // el rango de x de la rejilla común: sitúa puntos, equilibrio y marcas
    property real xMaximo: 1
    property real yMinimo: 0               // el rango de y que se dibuja (quien lo usa deja un margen)
    property real yMaximo: 1
    property var barras: ({})              // {categorias: [..], valores: [..]}: un gráfico de barras en vez de líneas
    property var puntos: []                // [{x, y, etiqueta}]
    property var equilibrio: null          // {x, y, etiqueta} o null
    property var marcas: []                // [{x: 3, etiqueta: "Y*"}] o [{y: 2, etiqueta: "r*"}]: líneas verticales u horizontales
    property string etiquetaX: ""
    property string etiquetaY: ""
    property string anotacion: ""
    property bool conLeyenda: true
    property url imagen                    // la imagen alternativa (sin QuickCharts, o si quien lo usa la prefiere)
    property bool preferirImagen: false
    property string mensajeVacio: ""
    property string iconoVacio: "office-chart-line"
    property string nombreAccesible: "Gráfico"
    readonly property bool hayBarras: barras && barras.categorias !== undefined && barras.categorias.length > 0
    readonly property bool hayDatos: series.length > 0 || hayBarras
    readonly property bool hayModulo: cargador.status === Loader.Ready
    readonly property bool conImagen: imagen != "" && (preferirImagen || !hayModulo)

    implicitWidth: Kirigami.Units.gridUnit * 24
    implicitHeight: Kirigami.Units.gridUnit * 14
    padding: Kirigami.Units.smallSpacing
    Kirigami.Theme.colorSet: Kirigami.Theme.View
    Kirigami.Theme.inherit: false
    Accessible.role: Accessible.Graphic
    Accessible.name: nombreAccesible + (hayDatos ? ": " + series.map(s => s.nombre).join(", ") : "")

    background: Rectangle { color: Kirigami.Theme.backgroundColor }

    contentItem: Item {
        Loader {
            id: cargador
            anchors.fill: parent
            active: raiz.hayDatos
            visible: active && status === Loader.Ready && !raiz.conImagen
            Component.onCompleted: setSource("GraficoQuickCharts.qml", { raiz: raiz })   // raiz antes de que el interior se complete
        }
        Image {
            anchors.fill: parent
            visible: raiz.conImagen
            source: raiz.conImagen ? raiz.imagen : ""
            fillMode: Image.PreserveAspectFit
            smooth: true
            mipmap: true
            Accessible.name: raiz.nombreAccesible + " (imagen)"
        }
        Kirigami.PlaceholderMessage {
            anchors.centerIn: parent
            width: parent.width - Kirigami.Units.gridUnit * 4
            visible: !raiz.conImagen && (!raiz.hayDatos || cargador.status === Loader.Error)
            text: !raiz.hayDatos ? raiz.mensajeVacio : "Falta el módulo QML org.kde.quickcharts"
            icon.name: raiz.iconoVacio
        }
    }
}
