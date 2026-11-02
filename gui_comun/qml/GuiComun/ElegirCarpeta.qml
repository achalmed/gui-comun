// ElegirCarpeta — elegir una carpeta (3.0) con el diálogo del escritorio (el de KDE con la QApplication de
// `Aplicacion`). `abrir(carpeta)`; `elegida(ruta)` con la ruta local al aceptar; `cancelado()` si no.
import QtQuick
import QtQuick.Dialogs
import "rutas.js" as Rutas

FolderDialog {
    id: dialogo

    property string titulo: "Elegir una carpeta"
    property string carpetaInicial: ""
    signal elegida(string ruta)
    signal cancelado()

    title: titulo || "Elegir una carpeta"         // 3.0.1: con un título vacío, Qt ponía el suyo, en inglés («Select Folder»)

    function abrir(carpeta) {
        const c = carpeta || carpetaInicial
        if (c) currentFolder = Rutas.aUrl(c)
        open()
    }

    onAccepted: elegida(Rutas.deUrl(selectedFolder))
    onRejected: cancelado()
}
