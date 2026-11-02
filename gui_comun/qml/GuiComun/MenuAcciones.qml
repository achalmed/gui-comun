// MenuAcciones — un menú (de la barra o contextual) generado desde el registro de acciones de Python.
// Cada elemento es {tipo: "accion", nombre} · {tipo: "separador"} · {tipo: "menu", titulo, elementos}; el texto, el
// icono, el atajo, si está habilitada y si está marcada salen del objeto `Accion`, y cambian solos cuando él cambia.
// Solo la barra de menú registra atajos (`conAtajos`): un menú contextual con los mismos los haría ambiguos.
import QtQuick
import QtQuick.Controls as QQC2

QQC2.Menu {
    id: menu

    property var acciones
    property var elementos: []
    property string titulo: ""
    property bool conAtajos: true

    title: titulo

    Component {
        id: cAccion
        QQC2.MenuItem {
            id: item
            required property QtObject accion
            readonly property bool viva: accion !== null && menu !== null     // al destruirse, nada que evaluar
            visible: viva ? accion.visible : false
            height: visible ? implicitHeight : 0
            action: QQC2.Action {
                text: item.viva ? item.accion.texto : ""
                icon.name: item.viva ? item.accion.icono : ""
                shortcut: item.viva && menu.conAtajos ? item.accion.atajo : ""
                enabled: item.viva ? item.accion.habilitada : false
                checkable: item.viva ? item.accion.marcable : false
                onTriggered: if (item.viva) item.accion.disparar()
            }
            Binding { target: item.action; property: "checked"; value: item.viva ? item.accion.marcada : false; when: item.viva && item.accion.marcable }
            Accessible.name: item.viva ? item.accion.textoPlano : ""
            Accessible.description: item.viva ? item.accion.descripcion : ""
        }
    }
    Component { id: cSeparador; QQC2.MenuSeparator {} }

    function limpiar() {
        for (let i = menu.count - 1; i >= 0; i--) {
            const it = menu.itemAt(i)
            if (it && it.subMenu) { const sub = menu.takeMenu(i); if (sub) sub.destroy() }
            else { const quitado = menu.takeItem(i); if (quitado) quitado.destroy() }
        }
    }

    function construir() {
        limpiar()
        if (!acciones) return
        for (const e of elementos) {
            if (e.tipo === "separador") {
                menu.addItem(cSeparador.createObject(menu.contentItem))
            } else if (e.tipo === "menu") {
                const c = Qt.createComponent(Qt.resolvedUrl("MenuAcciones.qml"))
                if (c.status === Component.Ready)
                    menu.addMenu(c.createObject(menu, { acciones: menu.acciones, titulo: e.titulo, elementos: e.elementos, conAtajos: menu.conAtajos }))
                else console.warn("MenuAcciones:", c.errorString())
            } else {
                const a = acciones.accion(e.nombre)
                if (a) menu.addItem(cAccion.createObject(menu.contentItem, { accion: a }))
                else console.warn("MenuAcciones: acción sin registrar", e.nombre)
            }
        }
    }

    property bool _pendiente: false
    function reconstruir() {                       // una sola construcción aunque cambien varias propiedades seguidas
        if (_pendiente) return
        _pendiente = true
        Qt.callLater(() => { _pendiente = false; construir() })
    }
    Component.onCompleted: construir()
    onElementosChanged: reconstruir()
    onAccionesChanged: reconstruir()
}
