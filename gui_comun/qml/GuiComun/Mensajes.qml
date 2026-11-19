// Mensajes — los avisos de la ventana. 4.2 (2026-11-19): ninguno en una franja de la ventana: con botones también van a
// KDE y, sin escritorio, a la barra de estado (ver `mostrar`). Desde 4.1 (2026-11-08) un aviso SIN acciones va a las notificaciones del
// escritorio (las de KDE Plasma, `notificador` de gui_comun.notificaciones): no ocupa la ventana ni se apila. Solo lo que
// pide una decisión (un aviso con acciones: «¿guardar?», «¿recargar?») queda aquí, en línea (Kirigami.InlineMessage),
// arriba del centro; también todo aviso cuando no hay escritorio que lo muestre (pruebas, offscreen). Un resumen no va
// aquí (va a la barra de estado).
// mostrar(texto, tipo, acciones): tipo = "informacion" | "positivo" | "aviso" | "error" | "pista"; acciones = [{texto, icono, ejecutar}]
// 4.1 (2026-11-18): una «pista» («elige primero un modelo») no es un aviso: va a `pista`, que `BarraEstado` muestra en
// lugar de su contexto durante `duracionPista` (6 s) y luego se borra; nunca a las notificaciones ni en línea. Lo
// repetían Datafw, Quarto, Simuladores y Huella, cada uno con su `Timer`.
// notificarConAcciones(texto, tipo, acciones) (4.1): el aviso CON botones va a las notificaciones de Plasma («Informe
// guardado» → «Abrir»); el botón que se pulse allí corre su `ejecutar`. Sin escritorio, en línea como `mostrar`.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

ColumnLayout {
    id: raiz
    spacing: Kirigami.Units.smallSpacing
    visible: modelo.count > 0

    readonly property alias cuantos: modelo.count
    property string pista: ""                  // 4.1: lo efímero, para la barra de estado
    property int duracionPista: 6000
    property var _pendientes: ({})             // 4.1: id de la notificación → sus acciones (con `ejecutar`)

    function mostrar(texto, tipo, acciones) {
        if (tipo === "pista") { mostrarPista(texto); return }
        // 4.2 (2026-11-19, pedido del autor: «ningún aviso dentro de la ventana en la familia de programas»): un aviso con
        // botones también va a las notificaciones de KDE (notificarConAcciones), y uno sin botones, si no hay escritorio
        // que lo muestre (pruebas, capturas sin pantalla, sin notify-send), va a la barra de estado como pista, nunca a una
        // franja. Solo una decisión sin escritorio queda en línea: una pregunta no se puede perder.
        if (!!acciones && acciones.length > 0) { notificarConAcciones(texto, tipo, acciones); return }
        if (typeof notificador !== "undefined" && notificador && notificador.disponible
                && notificador.notificar(texto, tipo || "informacion"))
            return
        mostrarPista(texto)
    }
    function _enLinea(texto, tipo, acciones) { modelo.append({ texto: texto, tipo: tipo || "informacion", acciones: acciones || [] }) }
    function limpiar() { modelo.clear() }
    function mostrarPista(texto) {
        raiz.pista = texto || ""
        if (raiz.pista !== "") relojPista.restart()
        else relojPista.stop()
    }
    function notificarConAcciones(texto, tipo, acciones) {
        const lista = acciones || []
        if (lista.length > 0 && typeof notificador !== "undefined" && notificador && notificador.disponible) {
            const botones = lista.map((a, i) => ({ clave: "a" + i, texto: a.texto }))
            const id = notificador.notificarConAcciones(texto, tipo || "informacion", botones)
            if (id > 0) {
                const p = raiz._pendientes
                p[id] = lista
                raiz._pendientes = p
                return
            }
        }
        if (lista.length > 0) _enLinea(texto, tipo, lista)   // una decisión sin escritorio: en línea, para no perderla
        else mostrar(texto, tipo, [])
    }

    Timer { id: relojPista; interval: raiz.duracionPista; onTriggered: raiz.pista = "" }
    Connections {
        target: typeof notificador !== "undefined" ? notificador : null
        ignoreUnknownSignals: true
        function onAccionElegida(id, clave) {
            const lista = raiz._pendientes[id]
            if (!lista) return
            const i = parseInt(String(clave).slice(1))
            if (clave !== "" && lista[i] && lista[i].ejecutar) lista[i].ejecutar()
        }
        function onNotificacionCerrada(id) {
            const p = raiz._pendientes
            delete p[id]
            raiz._pendientes = p
        }
    }

    ListModel { id: modelo }

    Repeater {
        model: modelo
        delegate: Kirigami.InlineMessage {
            id: mensaje
            required property int index
            required property string texto
            required property string tipo
            required property var acciones
            Layout.fillWidth: true
            Layout.margins: Kirigami.Units.smallSpacing
            visible: true
            showCloseButton: true
            text: texto
            type: tipo === "error" ? Kirigami.MessageType.Error
                : tipo === "aviso" ? Kirigami.MessageType.Warning
                : tipo === "positivo" ? Kirigami.MessageType.Positive
                : Kirigami.MessageType.Information
            onVisibleChanged: if (!visible) Qt.callLater(() => { if (mensaje.index < modelo.count) modelo.remove(mensaje.index) })
            Component.onCompleted: {
                const lista = []
                for (let i = 0; i < acciones.count; i++) {
                    const a = acciones.get(i)
                    const accion = componenteAccion.createObject(mensaje, { text: a.texto, ejecutar: a.ejecutar })
                    accion.icon.name = a.icono || ""
                    lista.push(accion)
                }
                actions = lista
            }
            Component {
                id: componenteAccion
                Kirigami.Action {
                    property var ejecutar
                    onTriggered: { if (ejecutar) ejecutar(); mensaje.visible = false }
                }
            }
        }
    }
}
