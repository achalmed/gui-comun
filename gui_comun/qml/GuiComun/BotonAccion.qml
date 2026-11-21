// BotonAccion — un botón de barra de herramientas ligado a una `Accion` de Python: texto, icono, habilitado y marcado
// siguen al objeto; el atajo no se registra aquí (lo registra la barra de menú), pero se muestra en la ayuda emergente.
// 4.2: una acción marcable (un panel visible, una vista, un filtro) se ve marcada con un tinte del acento y su borde,
// no con el bloque lleno que pinta el estilo (con Kvantum, azul saturado aun en un esquema oscuro de otro acento); y
// `plano: false` le pone borde para usarlo fuera de una barra.
import QtQuick
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

QQC2.ToolButton {
    id: boton

    property QtObject accion
    property bool conTexto: true
    property bool plano: true                // 4.2: false, con borde (fuera de una barra de herramientas)
    // 4.2: el fondo propio (tinte al marcar, velo al pasar) solo en las marcables o sin `plano`: los botones de barra
    // corrientes conservan el aspecto del estilo
    readonly property bool fondoPropio: checkable || !plano

    text: accion ? accion.textoPlano : ""
    icon.name: accion ? accion.icono : ""
    enabled: accion ? accion.habilitada : false
    visible: accion ? accion.visible : false
    checkable: accion ? accion.marcable : false
    flat: plano
    display: conTexto ? QQC2.AbstractButton.TextBesideIcon : QQC2.AbstractButton.IconOnly
    onClicked: if (accion) accion.disparar()
    Binding { target: boton; property: "checked"; value: boton.accion ? boton.accion.marcada : false; when: boton.accion && boton.accion.marcable }
    Binding { target: boton; property: "background"; value: fondoTinte; when: boton.fondoPropio }
    // con el estilo de KDE, el fondo del estilo pinta también el icono y el texto: con el fondo propio va su contenido
    Binding { target: boton; property: "contentItem"; value: contenidoPropio; when: boton.fondoPropio }
    Binding { target: boton; property: "leftPadding"; value: Kirigami.Units.largeSpacing; when: !boton.plano }
    Binding { target: boton; property: "rightPadding"; value: Kirigami.Units.largeSpacing; when: !boton.plano }
    Row {
        id: contenidoPropio
        visible: boton.fondoPropio
        spacing: Kirigami.Units.smallSpacing
        Kirigami.Icon {
            visible: boton.icon.name !== ""
            source: boton.icon.name
            anchors.verticalCenter: parent.verticalCenter
            width: Kirigami.Units.iconSizes.smallMedium
            height: width
        }
        QQC2.Label {
            visible: boton.display !== QQC2.AbstractButton.IconOnly && boton.text !== ""
            text: boton.text
            anchors.verticalCenter: parent.verticalCenter
        }
    }

    Rectangle {
        id: fondoTinte
        visible: boton.fondoPropio
        implicitHeight: Kirigami.Units.gridUnit * 1.6
        implicitWidth: implicitHeight
        radius: Kirigami.Units.cornerRadius
        color: boton.checked ? Kirigami.ColorUtils.tintWithAlpha(Kirigami.Theme.backgroundColor, Kirigami.Theme.highlightColor, boton.hovered ? 0.30 : 0.22)
             : boton.down ? Kirigami.ColorUtils.tintWithAlpha(Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor, 0.14)
             : boton.hovered ? Kirigami.ColorUtils.tintWithAlpha(Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor, 0.07)
             : "transparent"
        border.width: boton.visualFocus || boton.checked || !boton.plano ? 1 : 0
        border.color: boton.visualFocus ? Kirigami.Theme.focusColor
                    : boton.checked ? Kirigami.ColorUtils.tintWithAlpha(Kirigami.Theme.backgroundColor, Kirigami.Theme.highlightColor, 0.55)
                    : Kirigami.ColorUtils.linearInterpolation(Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor, 0.2)
        Behavior on color { ColorAnimation { duration: Kirigami.Units.shortDuration } }
    }

    QQC2.ToolTip.visible: hovered && QQC2.ToolTip.text !== ""
    QQC2.ToolTip.delay: Kirigami.Units.toolTipDelay
    QQC2.ToolTip.text: {
        if (!accion) return ""
        const base = accion.descripcion || accion.textoPlano
        return accion.atajoTexto ? base + " (" + accion.atajoTexto + ")" : base
    }
    Accessible.name: accion ? accion.textoPlano : ""
    Accessible.description: accion ? accion.descripcion : ""
}
