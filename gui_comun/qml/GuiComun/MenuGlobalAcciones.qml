// MenuGlobalAcciones (4.4) — un menú del registro de acciones en el menú global de Plasma (la barra de arriba, como
// Dolphin y Kate), con `Qt.labs.platform`: Plasma lo pinta con el estilo del escritorio (con Kvantum, translúcido y
// desenfocado). Misma entrada que `MenuAcciones` ({tipo: "accion", nombre} · {tipo: "separador"} · {tipo: "menu",
// titulo, elementos}); el texto, el icono, el atajo, si está habilitada y si está marcada salen del objeto `Accion`.
// Los atajos los registra este menú (la barra de la ventana se oculta y no registra ninguno).
//
// Lo usa `VentanaBase` cuando hay menú global (`Kirigami.Settings.hasPlatformMenuBar`); un studio no lo usa solo.
import QtQuick
import Qt.labs.platform as Labs

Labs.Menu {
    id: menu

    property var acciones
    property var elementos: []
    property string titulo: ""
    // Qt.labs.platform (Qt 6.10, KDE) se cae si se añade a la barra un menú que ya tiene elementos: el menú se une
    // vacío y solo entonces se llena (`unido`, que pone quien lo añade)
    property bool unido: false

    title: titulo

    Component {
        id: cAccion
        Labs.MenuItem {
            id: item
            property QtObject accion
            readonly property bool viva: accion !== null
            text: viva ? accion.texto : ""
            icon.name: viva ? accion.icono : ""
            shortcut: viva ? accion.atajo : ""
            enabled: viva ? accion.habilitada : false
            visible: viva ? accion.visible : false
            checkable: viva ? accion.marcable : false
            onTriggered: if (viva) accion.disparar()
            property Binding marcada: Binding {
                target: item; property: "checked"
                value: item.viva ? item.accion.marcada : false
                when: item.viva && item.accion.marcable
            }
        }
    }
    Component { id: cSeparador; Labs.MenuSeparator {} }

    // `clear()` de Qt.labs.platform ya borra los elementos (destruirlos otra vez tumba la aplicación)
    function limpiar() { menu.clear() }
    function construir() {
        limpiar()
        if (!acciones) return
        for (const e of elementos) {
            if (e.tipo === "separador") {
                menu.addItem(cSeparador.createObject(menu))
            } else if (e.tipo === "menu") {
                const c = Qt.createComponent(Qt.resolvedUrl("MenuGlobalAcciones.qml"))
                if (c.status !== Component.Ready) { console.warn("MenuGlobalAcciones:", c.errorString()); continue }
                const sub = c.createObject(menu, { acciones: menu.acciones, titulo: e.titulo, elementos: e.elementos })
                menu.addMenu(sub)
                sub.unido = true
            } else {
                const a = acciones.accion(e.nombre)
                if (!a) { console.warn("MenuGlobalAcciones: acción sin registrar", e.nombre); continue }
                menu.addItem(cAccion.createObject(menu, { accion: a }))
            }
        }
    }
    property bool _pendiente: false
    function reconstruir() {
        if (_pendiente) return
        _pendiente = true
        Qt.callLater(() => { _pendiente = false; construir() })
    }
    onUnidoChanged: if (unido) construir()
    onElementosChanged: if (unido) reconstruir()
    onAccionesChanged: if (unido) reconstruir()
}
