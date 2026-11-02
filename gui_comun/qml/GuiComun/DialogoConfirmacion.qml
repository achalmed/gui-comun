// DialogoConfirmacion — la confirmación de una operación de riesgo (3.0): nombra la operación (instalación,
// publicación, eliminación, o una escritura que sobrescribe) y sus consecuencias, y el botón dice qué hace («Publicar
// el sitio», no «Aceptar»). El foco empieza en Cancelar. `pedir(peticion, alAceptar)`: `peticion` es el mapa de
// `acciones.peticion(nombre)` ({nombre, titulo, consecuencias, operacion, operacionTexto, icono, textoAceptar,
// destructiva}); sin `alAceptar`, al aceptar llama a `acciones.confirmar(nombre)`. `VentanaBase` ya trae uno y lo abre
// cuando una acción lo pide (`acciones.confirmacionPedida`).
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

Kirigami.Dialog {
    id: dialogo

    property var acciones
    property var peticion: ({})
    property var alAceptar: null
    signal aceptada(string nombre)

    function pedir(p, funcion) {
        peticion = p || {}
        alAceptar = funcion || null
        open()
    }

    title: peticion.titulo || "Confirmar"
    preferredWidth: Kirigami.Units.gridUnit * 28
    padding: Kirigami.Units.largeSpacing * 2
    standardButtons: QQC2.Dialog.Ok | QQC2.Dialog.Cancel

    onOpened: {
        const ok = standardButton(QQC2.Dialog.Ok)
        if (ok) { ok.text = peticion.textoAceptar || "Aceptar"; ok.icon.name = peticion.icono || "dialog-ok" }
        const cancelar = standardButton(QQC2.Dialog.Cancel)
        if (cancelar) cancelar.forceActiveFocus()
    }
    onAccepted: {
        const nombre = peticion.nombre || ""
        if (alAceptar) alAceptar()
        else if (acciones && nombre) acciones.confirmar(nombre)
        aceptada(nombre)
        alAceptar = null
    }
    onRejected: alAceptar = null

    RowLayout {
        spacing: Kirigami.Units.largeSpacing
        Kirigami.Icon {
            Layout.alignment: Qt.AlignTop
            implicitWidth: Kirigami.Units.iconSizes.large
            implicitHeight: implicitWidth
            source: dialogo.peticion.destructiva ? "dialog-warning" : (dialogo.peticion.icono || "dialog-question")
            Accessible.ignored: true
        }
        ColumnLayout {
            spacing: Kirigami.Units.smallSpacing
            Layout.fillWidth: true
            QQC2.Label {
                visible: (dialogo.peticion.operacionTexto || "") !== ""
                text: (dialogo.peticion.operacionTexto || "") + (dialogo.peticion.destructiva ? " · no se puede deshacer desde aquí" : "")
                color: dialogo.peticion.destructiva ? Kirigami.Theme.negativeTextColor : Kirigami.Theme.disabledTextColor
                font.bold: true
            }
            QQC2.Label {
                text: dialogo.peticion.consecuencias || ""
                wrapMode: Text.WordWrap
                textFormat: Text.PlainText
                Layout.fillWidth: true
                Layout.preferredWidth: Kirigami.Units.gridUnit * 22
            }
        }
    }
}
