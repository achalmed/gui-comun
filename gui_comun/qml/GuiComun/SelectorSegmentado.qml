// SelectorSegmentado (4.2) — elegir una entre pocas vistas, áreas o filtros («Resumen · Cambios · Historial»,
// «Todos · Errores · Avisos»): las opciones como píldoras (OpcionColor) dentro de un pozo tenue (GrupoOpciones); la
// elegida va teñida del acento y con borde, las demás responden al ratón, y con el teclado ← → cambian de opción. Sirve
// en lugar de un TabBar de cabecera o de una fila de botones sueltos. Cada opción puede traer icono, contador y color
// (un dato; sin él, el acento del tema).
//     SelectorSegmentado { opciones: [{clave: "resumen", texto: "Resumen"}, {clave: "cambios", texto: "Cambios",
//                          contador: 3}]; actual: vista; onElegida: clave => vista = clave }
// `actual` lo fija quien lo usa (enlazado a su estado) y `elegida` le avisa: el selector no se lo asigna, para no
// romper ese enlace (un cambio por atajo o por menú lo sigue moviendo).
import QtQuick
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

GrupoOpciones {
    id: raiz
    // [{clave, texto, icono?, contador?, color?, atajo?, descripcion?, visible?}]
    property var opciones: []
    property string actual: ""
    // más ceñido (barras estrechas, el celular)
    property bool compacto: false
    signal elegida(string clave)

    readonly property var visibles: (opciones || []).filter(o => o.visible !== false)
    function mover(paso) {
        const i = visibles.findIndex(o => o.clave === actual)
        const j = Math.max(0, Math.min(visibles.length - 1, (i < 0 ? 0 : i) + paso))
        if (visibles.length > 0 && visibles[j].clave !== actual) elegida(visibles[j].clave)
    }

    Repeater {
        model: raiz.visibles
        delegate: OpcionColor {
            required property var modelData
            text: modelData.texto + (modelData.contador !== undefined && modelData.contador !== "" ? "  " + modelData.contador : "")
            icon.name: modelData.icono || ""
            color: modelData.color || "transparent"
            atajo: modelData.atajo || ""
            descripcion: modelData.descripcion || ""
            compacta: raiz.compacto
            elegida: raiz.actual === modelData.clave
            Accessible.role: Accessible.PageTab
            onClicked: raiz.elegida(modelData.clave)
            Keys.onRightPressed: raiz.mover(mirrored ? -1 : 1)
            Keys.onLeftPressed: raiz.mover(mirrored ? 1 : -1)
        }
    }
}
