// ElegirArchivos — elegir uno o varios archivos para abrir (3.0), con el diálogo de archivos del escritorio: con la
// QApplication de `Aplicacion` es el de KDE (lugares de Dolphin, vista previa, filtros, barra de rutas), nunca un
// explorador propio. Habla en rutas locales, no en URL. `abrir(carpeta)` lo abre; `elegidos(rutas)` y `elegido(ruta)`
// (la primera) al aceptar; `cancelado()` si no. `filtros`: ["Documentos PDF (*.pdf)"] o [{nombre, patrones: ["*.pdf"]}].
import QtQuick
import QtQuick.Dialogs
import "rutas.js" as Rutas

FileDialog {
    id: dialogo

    property string titulo: multiple ? "Elegir archivos" : "Elegir un archivo"
    property var filtros: []
    property bool conTodos: true                    // añade «Todos los archivos (*)»
    property string carpetaInicial: ""              // ruta local de la carpeta donde abre
    property bool multiple: false
    signal elegidos(var rutas)
    signal elegido(string ruta)
    signal cancelado()

    title: titulo
    fileMode: multiple ? FileDialog.OpenFiles : FileDialog.OpenFile
    nameFilters: Rutas.filtros(filtros, conTodos)

    function abrir(carpeta) {
        const c = carpeta || carpetaInicial
        if (c) currentFolder = Rutas.aUrl(c)
        open()
    }

    onAccepted: {
        const rutas = Rutas.lista(selectedFiles)
        elegidos(rutas)
        if (rutas.length > 0) elegido(rutas[0])
    }
    onRejected: cancelado()
}
