// CampoRuta — un campo de ruta con su botón de elegir (2.1). 3.0: el botón abre `ElegirCarpeta`, `ElegirArchivos` o
// `GuardarComo` (el diálogo de KDE, nunca un explorador propio) y las rutas con espacios vuelven bien (antes
// «00%20metodo»). Intro o el diálogo emiten `aceptada(texto)`; `texto` siempre refleja lo escrito. Lo usan la barra de
// Filesystem Studio (la carpeta de trabajo), los diálogos de directorio, las preferencias y `PaginaFormulario`.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import "rutas.js" as Rutas

RowLayout {
    id: campo

    property string texto: ""
    property bool carpeta: true
    property bool guardar: false                     // 3.0: con carpeta: false, elige dónde guardar (GuardarComo)
    property string titulo: carpeta ? "Elegir carpeta" : (guardar ? "Guardar como" : "Elegir archivo")
    property string marcador: carpeta ? "Carpeta…" : "Archivo…"
    property string nombreAccesible: titulo
    property var filtros: []                         // ["Documentos PDF (*.pdf)"] o [{nombre, patrones}] (archivos)
    property string carpetaInicial: ""               // 3.0: dónde abre el diálogo si el campo está vacío
    property alias campoTexto: entrada
    signal aceptada(string texto)

    spacing: Kirigami.Units.smallSpacing

    function abrir() {
        const actual = campo.texto
        if (campo.carpeta) selectorCarpeta.abrir(actual || campo.carpetaInicial)
        else if (campo.guardar) selectorGuardar.abrir(actual ? Rutas.carpetaDe(actual) : campo.carpetaInicial, actual ? Rutas.nombreDe(actual) : "")
        else selectorArchivo.abrir(actual ? Rutas.carpetaDe(actual) : campo.carpetaInicial)
    }
    function enfocar() { entrada.forceActiveFocus(); entrada.selectAll() }
    function poner(ruta) { campo.texto = ruta; campo.aceptada(ruta) }

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
        icon.name: campo.carpeta ? "folder-open" : (campo.guardar ? "document-save-as" : "document-open")
        text: campo.titulo + "…"
        display: QQC2.AbstractButton.IconOnly
        QQC2.ToolTip.text: text
        QQC2.ToolTip.visible: hovered
        Accessible.name: text
        onClicked: campo.abrir()
    }
    ElegirCarpeta { id: selectorCarpeta; titulo: campo.titulo; onElegida: ruta => campo.poner(ruta) }
    ElegirArchivos { id: selectorArchivo; titulo: campo.titulo; filtros: campo.filtros; onElegido: ruta => campo.poner(ruta) }
    GuardarComo { id: selectorGuardar; titulo: campo.titulo; filtros: campo.filtros; onElegido: ruta => campo.poner(ruta) }
}
