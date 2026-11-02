// BotonAccion — un botón de barra de herramientas ligado a una `Accion` de Python: texto, icono, habilitado y marcado
// siguen al objeto; el atajo no se registra aquí (lo registra la barra de menú), pero se muestra en la ayuda emergente.
import QtQuick
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

QQC2.ToolButton {
    id: boton

    property QtObject accion
    property bool conTexto: true

    text: accion ? accion.textoPlano : ""
    icon.name: accion ? accion.icono : ""
    enabled: accion ? accion.habilitada : false
    visible: accion ? accion.visible : false
    checkable: accion ? accion.marcable : false
    display: conTexto ? QQC2.AbstractButton.TextBesideIcon : QQC2.AbstractButton.IconOnly
    onClicked: if (accion) accion.disparar()
    Binding { target: boton; property: "checked"; value: boton.accion ? boton.accion.marcada : false; when: boton.accion && boton.accion.marcable }

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
