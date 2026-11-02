// TarjetaError — un error presentable (3.0): qué pasó, la causa probable, el archivo o recurso afectado, la acción
// recomendada y el detalle técnico desplegable (la anatomía de KMessageBox::detailedError, ampliada). Nadie tiene que
// leer la consola para entender un fallo, pero el detalle sigue a mano. La usa `DialogoError`; cabe también dentro de
// una página (el trabajo fallido de una cola, un repositorio que no sincronizó).
//
// `error`: {descripcion, causa, recurso, accion, detalle, nivel ("error" · "aviso" · "informacion")}, el mapa de
// `gui_comun.errores.Errores`; cada parte puede darse suelta y la que falta no se pinta.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

ColumnLayout {
    id: tarjeta

    property var error: ({})
    property string descripcion: error && error.descripcion ? error.descripcion : ""
    property string causa: error && error.causa ? error.causa : ""
    property string recurso: error && error.recurso ? error.recurso : ""
    property string accion: error && error.accion ? error.accion : ""
    property string detalle: error && error.detalle ? error.detalle : ""
    property string nivel: error && error.nivel ? error.nivel : "error"
    property bool detalleAbierto: false
    property bool conIcono: true
    // la integración con el escritorio para «Mostrar en Dolphin» (la expone Aplicacion); sin ella, no hay botón
    property var escritorio: typeof aplicacionStudio !== "undefined" && aplicacionStudio && aplicacionStudio.escritorio ? aplicacionStudio.escritorio : null

    spacing: Kirigami.Units.largeSpacing
    Accessible.role: Accessible.AlertMessage
    Accessible.name: descripcion
    Accessible.description: [causa, accion].filter(t => t).join(". ")

    function copiar(texto) { portapapeles.text = texto; portapapeles.selectAll(); portapapeles.copy(); portapapeles.text = "" }
    readonly property string textoCompleto: [descripcion, causa ? "Causa probable: " + causa : "", recurso ? "Recurso: " + recurso : "",
                                              accion ? "Qué hacer: " + accion : "", detalle ? "\nDetalle técnico:\n" + detalle : ""].filter(t => t).join("\n")

    TextEdit { id: portapapeles; visible: false }

    RowLayout {
        spacing: Kirigami.Units.largeSpacing
        Layout.fillWidth: true
        Kirigami.Icon {
            visible: tarjeta.conIcono
            Layout.alignment: Qt.AlignTop
            implicitWidth: Kirigami.Units.iconSizes.large
            implicitHeight: implicitWidth
            source: tarjeta.nivel === "aviso" ? "dialog-warning" : tarjeta.nivel === "informacion" ? "dialog-information" : "dialog-error"
            Accessible.ignored: true
        }
        Kirigami.Heading {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignVCenter
            level: 3
            text: tarjeta.descripcion
            wrapMode: Text.WordWrap
        }
    }

    // etiqueta · valor; con poco ancho, una columna. Los valores tienen ancho preferido mínimo para que partan líneas en
    // vez de ensanchar la tarjeta (con FormLayout, una ruta larga recortaba las etiquetas)
    GridLayout {
        id: rejilla
        Layout.fillWidth: true
        columns: tarjeta.width > Kirigami.Units.gridUnit * 20 ? 2 : 1
        columnSpacing: Kirigami.Units.largeSpacing
        rowSpacing: Kirigami.Units.smallSpacing

        QQC2.Label {
            visible: tarjeta.causa !== ""
            text: "Causa probable:"
            color: Kirigami.Theme.disabledTextColor
            Layout.alignment: rejilla.columns > 1 ? Qt.AlignTop | Qt.AlignRight : Qt.AlignLeft
        }
        QQC2.Label {
            visible: tarjeta.causa !== ""
            text: tarjeta.causa
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
            Layout.preferredWidth: Kirigami.Units.gridUnit
        }

        QQC2.Label {
            visible: tarjeta.recurso !== ""
            text: "Afecta a:"
            color: Kirigami.Theme.disabledTextColor
            Layout.alignment: rejilla.columns > 1 ? Qt.AlignTop | Qt.AlignRight : Qt.AlignLeft
        }
        RowLayout {
            visible: tarjeta.recurso !== ""
            Layout.fillWidth: true
            Layout.preferredWidth: Kirigami.Units.gridUnit
            spacing: Kirigami.Units.smallSpacing
            QQC2.Label {
                text: tarjeta.recurso
                font: Kirigami.Theme.fixedWidthFont
                wrapMode: Text.WrapAnywhere
                Layout.fillWidth: true
                Layout.preferredWidth: Kirigami.Units.gridUnit
                Accessible.name: "Recurso afectado: " + text
            }
            QQC2.ToolButton {
                visible: tarjeta.escritorio !== null && tarjeta.recurso.startsWith("/") && tarjeta.escritorio.existe(tarjeta.recurso)
                icon.name: "system-file-manager"
                text: "Mostrar en Dolphin"
                display: QQC2.AbstractButton.IconOnly
                QQC2.ToolTip.text: text
                QQC2.ToolTip.visible: hovered
                Accessible.name: text
                Layout.alignment: Qt.AlignTop
                onClicked: tarjeta.escritorio.mostrarEnDolphin(tarjeta.recurso)
            }
            QQC2.ToolButton {
                icon.name: "edit-copy"
                text: "Copiar la ruta"
                display: QQC2.AbstractButton.IconOnly
                QQC2.ToolTip.text: text
                QQC2.ToolTip.visible: hovered
                Accessible.name: text
                Layout.alignment: Qt.AlignTop
                onClicked: tarjeta.copiar(tarjeta.recurso)
            }
        }

        QQC2.Label {
            visible: tarjeta.accion !== ""
            text: "Qué hacer:"
            color: Kirigami.Theme.disabledTextColor
            Layout.alignment: rejilla.columns > 1 ? Qt.AlignTop | Qt.AlignRight : Qt.AlignLeft
        }
        QQC2.Label {
            visible: tarjeta.accion !== ""
            text: tarjeta.accion
            wrapMode: Text.WordWrap
            font.bold: true
            Layout.fillWidth: true
            Layout.preferredWidth: Kirigami.Units.gridUnit
        }
    }

    RowLayout {
        visible: tarjeta.detalle !== ""
        Layout.fillWidth: true
        spacing: Kirigami.Units.smallSpacing
        QQC2.ToolButton {
            icon.name: tarjeta.detalleAbierto ? "arrow-down" : "arrow-right"
            text: tarjeta.detalleAbierto ? "Ocultar el detalle técnico" : "Detalle técnico"
            checkable: true
            checked: tarjeta.detalleAbierto
            onToggled: tarjeta.detalleAbierto = checked
            Accessible.name: text
        }
        Item { Layout.fillWidth: true }
        QQC2.ToolButton {
            icon.name: "edit-copy"
            text: "Copiar todo"
            QQC2.ToolTip.text: "Copia la descripción, la causa, el recurso, la acción y el detalle (para un informe)"
            QQC2.ToolTip.visible: hovered
            Accessible.name: text
            onClicked: tarjeta.copiar(tarjeta.textoCompleto)
        }
    }

    QQC2.ScrollView {
        visible: tarjeta.detalleAbierto && tarjeta.detalle !== ""
        Layout.fillWidth: true
        Layout.fillHeight: true
        Layout.preferredHeight: Kirigami.Units.gridUnit * 10
        Layout.minimumHeight: Kirigami.Units.gridUnit * 5
        QQC2.TextArea {
            text: tarjeta.detalle
            readOnly: true
            selectByMouse: true
            wrapMode: Text.NoWrap
            font: Kirigami.Theme.fixedWidthFont
            Accessible.name: "Detalle técnico del error"
        }
    }
}
