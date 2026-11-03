// VistaPdf (3.1) — un PDF integrado en la ventana (de LaTeX Studio; Raphi y Quarto lo necesitaban igual). Con
// QtQuick.Pdf instalado, cada página la pinta Qt (PaginaQtPdf, sobre DocumentoQtPdf); sin él, páginas de pdftoppm que
// renderiza `visor` (gui_comun.visor_pdf.VisorPdf) por demanda, a la resolución del zoom (`visor.motor` dice cuál).
// Barra: miniaturas, página n de N, alejar, zoom, acercar, ajustar al ancho, recargar, abrir con su aplicación y lo
// que el studio añada (`barraExtra`). Doble clic en una página: `dobleClic(pagina, x, y)` en puntos (SyncTeX en
// LaTeX). La marca (`visor.marcarRecuadro`) parpadea sobre el recuadro. Al recargar, la página y el desplazamiento se
// conservan. Sin colores propios: el blanco del papel es del documento (PaginaQtPdf).
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

QQC2.Control {
    id: raiz

    property var visor: null                         // gui_comun.visor_pdf.VisorPdf
    readonly property var v: visor
    property string mensajeVacio: "Ningún PDF abierto"
    property string explicacionVacia: ""
    property alias barraExtra: extra.data            // botones propios del studio: barraExtra: [ QQC2.ToolButton { … } ]
    signal dobleClic(int pagina, real x, real y)
    property bool miniaturas: false
    readonly property int paginaActual: Math.max(1, paginas.indexAt(10, paginas.contentY + paginas.height / 3) + 1)
    property real separacion: Kirigami.Units.largeSpacing
    property int guardadaPagina: -1
    property real guardadaDesplazamiento: 0

    readonly property bool conQtPdf: v.motor === "qtpdf"

    // el documento de QtQuick.Pdf (solo con el módulo): se vuelve a abrir con cada PDF nuevo o recompilado
    Loader {
        id: documentoPdf
        property int revision: -1
        active: raiz.conQtPdf && raiz.v.pdfUrl !== ""
        source: "DocumentoQtPdf.qml"
        onLoaded: { item.source = raiz.v.pdfUrl; revision = raiz.v.revision }
    }
    Connections {
        target: raiz.v
        function onCambiado() {
            if (!raiz.conQtPdf || !documentoPdf.item || documentoPdf.revision === raiz.v.revision) return
            documentoPdf.item.source = ""
            documentoPdf.item.source = raiz.v.pdfUrl
            documentoPdf.revision = raiz.v.revision
        }
    }

    padding: 0
    Kirigami.Theme.colorSet: Kirigami.Theme.View
    Kirigami.Theme.inherit: false
    Accessible.name: "Visor PDF"

    function irA(pagina, yPuntos) {
        if (pagina < 1 || pagina > paginas.count) return
        paginas.positionViewAtIndex(pagina - 1, ListView.Beginning)
        if (yPuntos >= 0) paginas.contentY = Math.max(0, paginas.contentY + yPuntos * raiz.v.zoom - paginas.height / 3)
    }

    background: Rectangle { color: Kirigami.Theme.alternateBackgroundColor }

    Connections {
        target: raiz.v
        function onIrAPagina(pagina, y) { raiz.irA(pagina, y) }
        function onMarcar(pagina, x, y, ancho, alto) { marca.pagina = pagina; marca.rect = Qt.rect(x, y, ancho, alto); marca.mostrar() }
        function onZoomCambiado() { pedirVisibles.restart() }
    }
    // al recompilar: el modelo se rehace; se guarda la posición antes y se repone después
    Connections {
        target: raiz.v.paginas
        function onModelAboutToBeReset() { raiz.guardadaPagina = raiz.paginaActual; raiz.guardadaDesplazamiento = paginas.contentY }
        function onModelReset() { reponer.restart() }
    }
    Timer { id: reponer; interval: 30; onTriggered: if (raiz.guardadaPagina > 0) { paginas.contentY = Math.min(raiz.guardadaDesplazamiento, Math.max(0, paginas.contentHeight - paginas.height)) } }
    Timer { id: pedirVisibles; interval: 120; onTriggered: { for (let i = 0; i < paginas.count; i++) { const it = paginas.itemAtIndex(i); if (it) raiz.v.pedir(i + 1) } } }

    contentItem: ColumnLayout {
        spacing: 0
        QQC2.ToolBar {
            Layout.fillWidth: true
            position: QQC2.ToolBar.Header
            RowLayout {
                anchors.fill: parent
                spacing: Kirigami.Units.smallSpacing
                QQC2.ToolButton { icon.name: "view-preview"; checkable: true; checked: raiz.miniaturas; onToggled: raiz.miniaturas = checked; display: QQC2.AbstractButton.IconOnly; text: "Miniaturas"; Accessible.name: text; QQC2.ToolTip.text: text; QQC2.ToolTip.visible: hovered }
                QQC2.Label { text: raiz.v.total > 0 ? "Página " + raiz.paginaActual + " de " + raiz.v.total : ""; Layout.fillWidth: true; elide: Text.ElideRight }
                QQC2.ToolButton { icon.name: "zoom-out"; display: QQC2.AbstractButton.IconOnly; text: "Alejar"; Accessible.name: text; enabled: raiz.v.total > 0; onClicked: raiz.v.alejar() }
                QQC2.Label { text: Math.round(raiz.v.zoom * 100) + " %"; Layout.minimumWidth: Kirigami.Units.gridUnit * 2.5; horizontalAlignment: Text.AlignHCenter }
                QQC2.ToolButton { icon.name: "zoom-in"; display: QQC2.AbstractButton.IconOnly; text: "Acercar"; Accessible.name: text; enabled: raiz.v.total > 0; onClicked: raiz.v.acercar() }
                QQC2.ToolButton {
                    icon.name: "zoom-fit-width"
                    checkable: true
                    checked: raiz.v.ajustarAncho
                    onToggled: { raiz.v.ajustarAncho = checked; raiz.v.ajustarA(paginas.width - raiz.separacion * 2) }
                    display: QQC2.AbstractButton.IconOnly
                    text: "Ajustar al ancho"
                    Accessible.name: text
                    QQC2.ToolTip.text: text
                    QQC2.ToolTip.visible: hovered
                }
                QQC2.ToolButton { icon.name: "view-refresh"; display: QQC2.AbstractButton.IconOnly; text: "Recargar el PDF"; Accessible.name: text; enabled: raiz.v.pdf !== ""; onClicked: raiz.v.recargar(); QQC2.ToolTip.text: text; QQC2.ToolTip.visible: hovered }
                QQC2.ToolButton {
                    icon.name: "document-open"; display: QQC2.AbstractButton.IconOnly; text: "Abrir con su aplicación"; Accessible.name: text
                    enabled: raiz.v.pdf !== "" && typeof studio !== "undefined" && !!studio.escritorio
                    onClicked: studio.escritorio.abrirConAplicacion(raiz.v.pdf)
                    QQC2.ToolTip.text: text; QQC2.ToolTip.visible: hovered
                }
                RowLayout { id: extra; spacing: Kirigami.Units.smallSpacing }
            }
        }
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            ListView {
                id: listaMiniaturas
                visible: raiz.miniaturas && raiz.v.total > 0
                Layout.fillHeight: true
                Layout.preferredWidth: Kirigami.Units.gridUnit * 6
                clip: true
                model: raiz.v.paginas
                spacing: Kirigami.Units.smallSpacing
                currentIndex: raiz.paginaActual - 1
                Accessible.name: "Miniaturas"
                QQC2.ScrollBar.vertical: QQC2.ScrollBar {}
                delegate: QQC2.ItemDelegate {
                    required property var model
                    required property int index
                    width: listaMiniaturas.width
                    highlighted: ListView.isCurrentItem
                    onClicked: raiz.irA(model.pagina, -1)
                    Accessible.name: "Página " + model.pagina
                    Component.onCompleted: raiz.v.pedirMiniatura(model.pagina)
                    contentItem: ColumnLayout {
                        spacing: 0
                        Item {
                            id: miniatura
                            Layout.alignment: Qt.AlignHCenter
                            Layout.preferredWidth: listaMiniaturas.width - Kirigami.Units.largeSpacing * 2
                            Layout.preferredHeight: Layout.preferredWidth * model.alto / model.ancho
                            readonly property int pagina: model.pagina
                            Image {
                                id: miniaturaPng
                                anchors.fill: parent
                                visible: !raiz.conQtPdf
                                source: raiz.conQtPdf ? "" : model.miniatura
                                asynchronous: true
                                fillMode: Image.PreserveAspectFit
                            }
                            Loader {
                                id: miniaturaQt
                                anchors.fill: parent
                                active: raiz.conQtPdf && documentoPdf.item !== null
                                source: "PaginaQtPdf.qml"
                                onLoaded: {
                                    item.document = Qt.binding(() => documentoPdf.item)
                                    item.pagina = Qt.binding(() => miniatura.pagina)
                                    item.sourceSize = Qt.binding(() => Qt.size(miniatura.width * raiz.v.escala, miniatura.height * raiz.v.escala))
                                }
                            }
                            Rectangle {
                                anchors.fill: parent
                                visible: raiz.conQtPdf ? !(miniaturaQt.item && miniaturaQt.item.status === Image.Ready) : miniaturaPng.status !== Image.Ready
                                color: Kirigami.Theme.backgroundColor; border.color: Kirigami.Theme.disabledTextColor; border.width: 1
                            }
                        }
                        QQC2.Label { Layout.alignment: Qt.AlignHCenter; text: model.pagina; font: Kirigami.Theme.smallFont }
                    }
                }
            }
            Kirigami.Separator { Layout.fillHeight: true; visible: listaMiniaturas.visible }

            ListView {
                id: paginas
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                model: raiz.v.paginas
                spacing: raiz.separacion
                topMargin: raiz.separacion
                bottomMargin: raiz.separacion
                cacheBuffer: Math.max(0, height)
                boundsBehavior: Flickable.StopAtBounds
                Accessible.name: "Páginas del PDF"
                QQC2.ScrollBar.vertical: QQC2.ScrollBar {}
                QQC2.ScrollBar.horizontal: QQC2.ScrollBar {}
                contentWidth: Math.max(width, (raiz.v.total > 0 ? raiz.v.zoom * raiz.v.anchoMaximo : 0) + raiz.separacion * 2)
                flickableDirection: Flickable.AutoFlickIfNeeded
                onWidthChanged: if (raiz.v.ajustarAncho) raiz.v.ajustarA(width - raiz.separacion * 2)
                onCountChanged: if (raiz.v.ajustarAncho) raiz.v.ajustarA(width - raiz.separacion * 2)
                WheelHandler {
                    acceptedModifiers: Qt.ControlModifier
                    onWheel: event => { if (event.angleDelta.y > 0) raiz.v.acercar(); else raiz.v.alejar() }
                }

                delegate: Item {
                    id: hoja
                    required property var model
                    required property int index
                    width: paginas.contentWidth
                    height: model.alto * raiz.v.zoom
                    Component.onCompleted: raiz.v.pedir(model.pagina)

                    Rectangle {
                        id: papel
                        width: hoja.model.ancho * raiz.v.zoom
                        height: hoja.height
                        x: Math.max(raiz.separacion, (paginas.width - width) / 2)
                        color: Kirigami.Theme.backgroundColor
                        border.color: Kirigami.Theme.disabledTextColor
                        border.width: 1
                        Image {
                            anchors.fill: parent
                            anchors.margins: 1
                            visible: !raiz.conQtPdf
                            source: raiz.conQtPdf ? "" : hoja.model.imagen
                            asynchronous: true
                            cache: false
                            smooth: true
                            mipmap: true
                            fillMode: Image.Stretch
                        }
                        Loader {
                            id: paginaQt
                            anchors.fill: parent
                            anchors.margins: 1
                            active: raiz.conQtPdf && documentoPdf.item !== null
                            source: "PaginaQtPdf.qml"
                            onLoaded: {
                                item.document = Qt.binding(() => documentoPdf.item)
                                item.pagina = Qt.binding(() => hoja.model.pagina)
                                item.sourceSize = Qt.binding(() => Qt.size(Math.round(papel.width * raiz.v.escala), Math.round(papel.height * raiz.v.escala)))
                            }
                        }
                        QQC2.BusyIndicator {
                            anchors.centerIn: parent
                            running: raiz.conQtPdf ? !(paginaQt.item && paginaQt.item.status === Image.Ready) : hoja.model.imagen === ""
                            visible: running
                        }
                        Rectangle {
                            visible: marca.visible && marca.pagina === hoja.model.pagina
                            x: marca.rect.x * raiz.v.zoom - 2
                            y: marca.rect.y * raiz.v.zoom - 2
                            width: Math.max(8, marca.rect.width * raiz.v.zoom) + 4
                            height: Math.max(8, marca.rect.height * raiz.v.zoom) + 4
                            color: "transparent"
                            border.color: Kirigami.Theme.highlightColor
                            border.width: 2
                            radius: Kirigami.Units.cornerRadius
                        }
                        TapHandler {
                            onDoubleTapped: (punto) => raiz.dobleClic(hoja.model.pagina, punto.position.x / raiz.v.zoom, punto.position.y / raiz.v.zoom)
                        }
                    }
                }
            }
        }
    }

    // la marca de SyncTeX: visible unos segundos
    Item {
        id: marca
        property int pagina: 0
        property rect rect: Qt.rect(0, 0, 0, 0)
        visible: false
        function mostrar() { visible = true; apagar.restart() }
        Timer { id: apagar; interval: 2500; onTriggered: marca.visible = false }
    }

    Kirigami.PlaceholderMessage {
        anchors.centerIn: parent
        width: parent.width - Kirigami.Units.gridUnit * 4
        visible: raiz.v.total === 0
        icon.name: "application-pdf"
        text: raiz.mensajeVacio
        explanation: raiz.explicacionVacia
    }
}
