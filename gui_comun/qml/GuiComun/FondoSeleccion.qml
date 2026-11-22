// FondoSeleccion (4.2) — el fondo de una fila de lista propia, como el de PanelNavegacion, TablaDatos y las listas de la
// base: elegida, un tinte del acento con su marca a la izquierda; al pasar el ratón, un velo tenue; pulsada, un velo
// algo más hondo; con el foco del teclado, un borde. 4.4: con el esquema «como Dolphin», el bloque lleno (`EstiloSeleccion`). Nunca el bloque lleno de `highlightColor` (con un acento rojo,
// lo elegido parecía un error). Va como `background` de un ItemDelegate (o detrás de cualquier fila):
//     QQC2.ItemDelegate { background: FondoSeleccion { elegida: fila.highlighted; sobre: fila.hovered; pulsada: fila.pressed; foco: fila.visualFocus } }
// Con el delegado, el texto conserva su color (`Kirigami.Theme.textColor`), no `highlightedTextColor`.
import QtQuick
import org.kde.kirigami as Kirigami

Rectangle {
    id: raiz
    property bool elegida: false
    property bool sobre: false
    property bool pulsada: false
    property bool foco: false
    property bool conMarca: true          // la marca de acento a la izquierda de la elegida
    property bool redondeada: true        // false: a todo el ancho (una celda de tabla)

    radius: redondeada ? Kirigami.Units.cornerRadius : 0
    color: elegida ? EstiloSeleccion.fondo(Kirigami.Theme.backgroundColor, Kirigami.Theme.highlightColor, sobre || pulsada ? 0.30 : 0.22)
         : pulsada ? Kirigami.ColorUtils.tintWithAlpha(Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor, 0.14)
         : sobre ? Kirigami.ColorUtils.tintWithAlpha(Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor, 0.07)
         : "transparent"
    border.width: foco ? 1 : 0
    border.color: Kirigami.Theme.focusColor
    Behavior on color { ColorAnimation { duration: Kirigami.Units.shortDuration } }

    Rectangle {
        visible: raiz.elegida && raiz.conMarca && EstiloSeleccion.conMarca
        anchors.left: parent.left
        anchors.leftMargin: Kirigami.Units.smallSpacing / 2
        anchors.verticalCenter: parent.verticalCenter
        width: Kirigami.Units.smallSpacing * 0.75
        height: Math.max(Kirigami.Units.smallSpacing * 2, parent.height - Kirigami.Units.smallSpacing * 2.5)
        radius: width / 2
        color: Kirigami.Theme.highlightColor
    }
}
