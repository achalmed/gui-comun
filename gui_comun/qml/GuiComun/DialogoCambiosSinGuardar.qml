// DialogoCambiosSinGuardar — la pregunta de siempre antes de cerrar algo con cambios sin guardar (4.2): «Guardar»,
// «Descartar» o «Cancelar», como KMessageBox en KDE. No guarda ni cierra nada: `pedir(nombres, alGuardar, alDescartar)`
// abre la pregunta y llama a la función que corresponda (o emite `guardar()` / `descartar()`); cancelar no hace nada.
// `nombres` es un nombre de archivo o una lista. Quien guarda decide qué pasa si guardar falla (el diálogo ya cerró).
// `explicacion`, `textoGuardar` y `textoDescartar` se ajustan a lo que se cierra («Guardar y salir», por ejemplo).
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

Kirigami.Dialog {
    id: dialogo

    property var nombres: []
    property string explicacion: "Si lo cierras sin guardar, esos cambios se pierden."
    property string textoGuardar: "Guardar"
    property string textoDescartar: "Descartar"
    property var alGuardar: null
    property var alDescartar: null
    signal guardar()
    signal descartar()

    readonly property var lista: Array.isArray(nombres) ? nombres : (nombres ? [nombres] : [])

    function pedir(n, funcionGuardar, funcionDescartar) {
        nombres = n || []
        alGuardar = funcionGuardar || null
        alDescartar = funcionDescartar || null
        open()
    }
    function _limpiar() { alGuardar = null; alDescartar = null }

    title: "Cambios sin guardar"
    preferredWidth: Kirigami.Units.gridUnit * 26
    padding: Kirigami.Units.largeSpacing * 2
    standardButtons: QQC2.Dialog.Cancel
    customFooterActions: [
        Kirigami.Action {
            text: dialogo.textoDescartar
            icon.name: "document-close"
            onTriggered: { const f = dialogo.alDescartar; dialogo._limpiar(); dialogo.close(); if (f) f(); dialogo.descartar() }
        },
        Kirigami.Action {
            text: dialogo.textoGuardar
            icon.name: "document-save"
            onTriggered: { const f = dialogo.alGuardar; dialogo._limpiar(); dialogo.close(); if (f) f(); dialogo.guardar() }
        }
    ]
    onRejected: _limpiar()

    RowLayout {
        spacing: Kirigami.Units.largeSpacing
        Kirigami.Icon {
            Layout.alignment: Qt.AlignTop
            implicitWidth: Kirigami.Units.iconSizes.large
            implicitHeight: implicitWidth
            source: "document-save"
            Accessible.ignored: true
        }
        ColumnLayout {
            Layout.fillWidth: true
            spacing: Kirigami.Units.smallSpacing
            QQC2.Label {
                Layout.fillWidth: true
                Layout.preferredWidth: Kirigami.Units.gridUnit * 20
                text: dialogo.lista.length > 1
                      ? "Hay " + dialogo.lista.length + " archivos con cambios sin guardar: " + dialogo.lista.join(", ") + "."
                      : "«" + (dialogo.lista[0] || "El archivo") + "» tiene cambios sin guardar."
                wrapMode: Text.WordWrap
                textFormat: Text.PlainText
                font.bold: true
            }
            QQC2.Label {
                Layout.fillWidth: true
                text: dialogo.explicacion
                wrapMode: Text.WordWrap
                textFormat: Text.PlainText
                color: Kirigami.Theme.disabledTextColor
            }
        }
    }
}
