// FondoVentana — el fondo de una superficie del marco (4.3): barras, paneles laterales, lo que en Dolphin con Kvantum
// deja ver el escritorio desenfocado. Con la ventana translúcida (`aplicacionStudio.translucidez.activa`) no pinta
// nada y se ve la única capa translúcida de la ventana (dos capas con alfa se suman y el panel quedaría más opaco que
// el marco); con la ventana opaca, el color de fondo de su conjunto de colores, como siempre.
//
// Solo para superficies que están directamente sobre la ventana. Las zonas de lectura (la hoja del PDF, los editores,
// las tablas, la consola) siguen con su `colorSet: View` y su fondo opaco: ahí no se usa.
//
//     background: FondoVentana {}                         // un panel lateral
//     background: FondoVentana { separador: "abajo" }     // una barra de herramientas arriba, con su raya
import QtQuick
import org.kde.kirigami as Kirigami

Rectangle {
    id: fondo

    property string separador: ""          // "arriba", "abajo" o "": la raya de las barras de herramientas
    readonly property var translucidez: typeof aplicacionStudio !== "undefined" && aplicacionStudio
                                        ? aplicacionStudio.translucidez : null
    readonly property bool translucida: translucidez ? translucidez.activa : false

    color: translucida ? "transparent" : Kirigami.Theme.backgroundColor

    Kirigami.Separator {
        visible: fondo.separador !== ""
        width: parent.width
        y: fondo.separador === "arriba" ? 0 : parent.height - height
    }
}
