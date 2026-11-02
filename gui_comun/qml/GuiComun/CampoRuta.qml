// CampoRuta — un campo de ruta con su botón de elegir (2.1): FolderDialog para carpetas, FileDialog para archivos.
// Intro o el diálogo emiten `aceptada(texto)`; `texto` siempre refleja lo escrito. Lo usan la barra de Filesystem
// Studio (la carpeta de trabajo), los diálogos de directorio y las preferencias de los studios.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import QtQuick.Dialogs
import org.kde.kirigami as Kirigami

RowLayout {
    id: campo

    property string texto: ""
    property bool carpeta: true
    property string titulo: carpeta ? "Elegir carpeta" : "Elegir archivo"
    property string marcador: carpeta ? "Carpeta…" : "Archivo…"
    property string nombreAccesible: titulo
    property var filtros: []                         // FileDialog.nameFilters (solo con carpeta: false)
    property alias campoTexto: entrada
    signal aceptada(string texto)

    spacing: Kirigami.Units.smallSpacing

    function abrir() {
        if (campo.carpeta) { selectorCarpeta.currentFolder = campo.texto ? "file://" + campo.texto : ""; selectorCarpeta.open() }
        else { selectorArchivo.currentFile = campo.texto ? "file://" + campo.texto : ""; selectorArchivo.open() }
    }
    function enfocar() { entrada.forceActiveFocus(); entrada.selectAll() }

    QQC2.TextField {
        id: entrada
        Layout.fillWidth: true
        text: campo.texto
        placeholderText: campo.marcador
        onTextEdited: campo.texto = text
        onAccepted: campo.aceptada(text)
        Accessible.name: campo.nombreAccesible
    }
    QQC2.ToolButton {
        icon.name: campo.carpeta ? "folder-open" : "document-open"
        text: campo.titulo + "…"
        display: QQC2.AbstractButton.IconOnly
        QQC2.ToolTip.text: text
        QQC2.ToolTip.visible: hovered
        Accessible.name: text
        onClicked: campo.abrir()
    }
    FolderDialog {
        id: selectorCarpeta
        title: campo.titulo
        onAccepted: { campo.texto = selectedFolder.toString().replace("file://", ""); campo.aceptada(campo.texto) }
    }
    FileDialog {
        id: selectorArchivo
        title: campo.titulo
        nameFilters: campo.filtros
        onAccepted: { campo.texto = selectedFile.toString().replace("file://", ""); campo.aceptada(campo.texto) }
    }
}
