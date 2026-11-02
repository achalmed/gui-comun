// GuardarComo — elegir dónde guardar (3.0) con el diálogo del escritorio (el de KDE con la QApplication de
// `Aplicacion`; él mismo pregunta antes de sobrescribir). `abrir(carpeta, nombre)`; `elegido(ruta)` con la ruta
// local; `cancelado()`. `sufijo` es la extensión que se añade si el usuario no escribe ninguna («pdf»).
import QtQuick
import QtQuick.Dialogs
import "rutas.js" as Rutas

FileDialog {
    id: dialogo

    property string titulo: "Guardar como"
    property var filtros: []
    property bool conTodos: false
    property string carpetaInicial: ""
    property string nombreSugerido: ""
    property string sufijo: ""
    signal elegido(string ruta)
    signal cancelado()

    title: titulo
    fileMode: FileDialog.SaveFile
    nameFilters: Rutas.filtros(filtros, conTodos)
    defaultSuffix: sufijo

    function abrir(carpeta, nombre) {
        const c = carpeta || carpetaInicial
        const n = nombre || nombreSugerido
        if (c) currentFolder = Rutas.aUrl(c)
        if (c && n) selectedFile = Rutas.aUrl(c.replace(/\/+$/, "") + "/" + n)
        open()
    }

    onAccepted: elegido(Rutas.deUrl(selectedFile))
    onRejected: cancelado()
}
