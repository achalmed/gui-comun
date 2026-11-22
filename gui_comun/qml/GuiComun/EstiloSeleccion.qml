pragma Singleton
// EstiloSeleccion (4.4) — cómo se marca lo elegido en las listas, tablas y la navegación de la familia.
//
// Con el esquema predeterminado, el tinte del acento con su marca a la izquierda (4.2). Con el esquema «como Dolphin»
// (`aplicacionStudio.esquemas.seleccionLlena`), un bloque lleno del color de selección como lo pinta Dolphin con
// Kvantum (la selección al 65 % sobre el fondo de la fila), sin marca y con el texto en `highlightedTextColor`.
//
//     color: elegida ? EstiloSeleccion.fondo(Kirigami.Theme.backgroundColor, Kirigami.Theme.highlightColor, 0.22) : …
//     Rectangle { visible: elegida && EstiloSeleccion.conMarca … }                 // la marca
//     color: elegida ? EstiloSeleccion.texto(Kirigami.Theme.textColor, Kirigami.Theme.highlightedTextColor) : …
//
// Sin importar Kirigami a propósito: Qt resuelve los singletons del qmldir al cargar cualquier archivo de la carpeta, y
// quien carga un componente suelto sin Kirigami (las pruebas del visor PDF de LaTeX Studio) no podría.
import QtQuick

QtObject {
    readonly property var esquemas: typeof aplicacionStudio !== "undefined" && aplicacionStudio
                                    ? (aplicacionStudio.esquemas ?? null) : null
    readonly property bool llena: esquemas ? esquemas.seleccionLlena : false
    readonly property real alfa: esquemas ? esquemas.alfaSeleccion : 0.65
    readonly property bool conMarca: !llena

    // el fondo de lo elegido sobre `base`: el bloque lleno o el tinte de `tinte` (el de cada componente)
    function fondo(base, acento, tinte) { return teñir(base, acento, llena ? alfa : tinte) }
    // lo mismo que `Kirigami.ColorUtils.tintWithAlpha(base, acento, a)`
    function teñir(base, acento, a) {
        const t = acento.a * a, r = 1 - t
        return Qt.rgba(acento.r * t + base.r * r, acento.g * t + base.g * r, acento.b * t + base.b * r, t + r * base.a)
    }
    // el color de un texto de lo elegido: el resaltado sobre el bloque lleno, el suyo sobre el tinte
    function texto(normal, resaltado) { return llena ? resaltado : normal }
}
