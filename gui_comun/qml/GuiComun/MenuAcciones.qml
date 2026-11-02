// MenuAcciones — un menú (de la barra o contextual) generado desde el registro de acciones de Python.
// Cada elemento es {tipo: "accion", nombre} · {tipo: "separador"} · {tipo: "menu", titulo, elementos}; el texto, el
// icono, el atajo, si está habilitada y si está marcada salen del objeto `Accion`, y cambian solos cuando él cambia.
// Solo la barra de menú registra atajos (`conAtajos`): un menú contextual con los mismos los haría ambiguos.
//
// El contenido de cada elemento se pinta aquí (icono · texto con mnemónico · atajo) y no con el del estilo: el
// MenuItem de org.kde.desktop (KF 6.24, Qt 6.10) no suma el ancho del atajo al suyo —ni siquiera en un menú estático—
// y el atajo se dibujaba encima del texto; además escribe «Control+Mayúsculas+N». Aquí el ancho se mide con
// TextMetrics y el atajo sale corto y en español («Ctrl+Mayús+N»), igual que en la paleta.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

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

            readonly property string atajoVisible: item.viva ? item.accion.atajoTexto : ""
            readonly property real anchoMarca: item.checkable ? (item.indicator ? item.indicator.width : Kirigami.Units.iconSizes.small) : Kirigami.Units.smallSpacing
            TextMetrics { id: medidaTexto; font: item.font; text: item.text.replace(/&&/g, "\u0001").replace(/&/g, "").replace(/\u0001/g, "&") }
            TextMetrics { id: medidaAtajo; font: item.font; text: item.atajoVisible }
            implicitWidth: leftPadding + rightPadding + anchoMarca + Kirigami.Units.iconSizes.small + Kirigami.Units.smallSpacing * 3
                           + Math.ceil(medidaTexto.advanceWidth)
                           + (atajoVisible ? Kirigami.Units.gridUnit * 2 + Math.ceil(medidaAtajo.advanceWidth) : 0)

            contentItem: RowLayout {
                spacing: Kirigami.Units.smallSpacing
                Item { Layout.preferredWidth: item.anchoMarca }
                Kirigami.Icon {
                    Layout.alignment: Qt.AlignVCenter
                    Layout.preferredWidth: Kirigami.Units.iconSizes.small
                    Layout.preferredHeight: Kirigami.Units.iconSizes.small
                    source: item.icon.name
                    color: item.icon.color
                    enabled: item.enabled
                }
                QQC2.Label {
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignVCenter
                    text: item.Kirigami.MnemonicData.richTextLabel
                    textFormat: Text.StyledText
                    font: item.font
                    elide: Text.ElideRight
                    enabled: item.enabled
                }
                QQC2.Label {
                    visible: item.atajoVisible !== ""
                    Layout.alignment: Qt.AlignVCenter
                    Layout.leftMargin: Kirigami.Units.gridUnit
                    text: item.atajoVisible
                    font: item.font
                    color: Kirigami.Theme.disabledTextColor
                    horizontalAlignment: Text.AlignRight
                    enabled: item.enabled
                }
                Item { Layout.preferredWidth: Kirigami.Units.smallSpacing }
            }
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
    // El ancho del menú se fija al abrirlo con el mayor de sus elementos: el cálculo del estilo (una reducción sobre los
    // hijos de su ListView) a veces se queda en el mínimo del fondo en la sesión real (visto en «Ver», con marcables).
    function ajustarAncho() {
        let necesario = 0
        for (let i = 0; i < menu.count; i++) {
            const it = menu.itemAt(i)
            if (it && it.visible) necesario = Math.max(necesario, it.implicitWidth)
        }
        if (necesario > 0)
            menu.width = Math.max(Kirigami.Units.gridUnit * 8, necesario + menu.leftPadding + menu.rightPadding)
    }
    onAboutToShow: ajustarAncho()

    Component.onCompleted: construir()
    onElementosChanged: reconstruir()
    onAccionesChanged: reconstruir()
}
