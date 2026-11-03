// PaletaCategorica (3.1) — colores distintos y en armonía para categorías y series, sin colores propios: el tono del
// acento del tema (Kirigami.Theme.highlightColor) girado en séptimos, con su saturación y una luminosidad media, para
// categorías sin significado (las de Filesystem: documentos, imágenes, código…), y los roles con significado (azul,
// rojo, verde, dorado, morado, cian, gris, texto: gui_comun.paleta) pintados con los colores semánticos del tema. El
// esquema oscuro de Lliphi solo trae rojo, naranja y verde entre sus semánticos, y un tema de acento rojo pone el
// enlace rojo: azul, morado y cian se derivan del tema con solo el tono fijado. Viene de Filesystem y Simuladores.
//     PaletaCategorica { id: paleta }   ·   color: paleta.indice(3)   ·   color: paleta.rol("azul")
import QtQuick
import org.kde.kirigami as Kirigami

QtObject {
    readonly property color acento: Kirigami.Theme.highlightColor
    readonly property bool oscuro: Kirigami.Theme.backgroundColor.hslLightness < 0.5
    readonly property int tonos: 7

    // la categoría número `i` (0, 1, 2…): el acento girado `i` séptimos
    function indice(i) {
        const h = acento.hslHue < 0 ? 0 : acento.hslHue
        const s = Math.max(0.45, Math.min(0.75, acento.hslSaturation))
        return Qt.hsla((h + (i % tonos) / tonos) % 1, s, 0.55, 1)
    }
    function tono(h) {
        const b = Kirigami.Theme.positiveTextColor
        const l = oscuro ? Math.max(b.hslLightness, 0.6) : Math.min(b.hslLightness, 0.42)
        return Qt.hsla(h, Math.max(b.hslSaturation, 0.55), l, 1)
    }
    function delTema(c, desde, hasta, h) {
        return c.hslSaturation > 0.3 && c.hslHue >= desde && c.hslHue <= hasta ? c : tono(h)
    }
    // un rol con significado (gui_comun.paleta.rol)
    function rol(nombre) {
        switch (nombre) {
        case "azul": return delTema(Kirigami.Theme.linkColor, 0.53, 0.70, 0.6)
        case "rojo": return Kirigami.Theme.negativeTextColor
        case "verde": return Kirigami.Theme.positiveTextColor
        case "dorado": return Kirigami.Theme.neutralTextColor
        case "morado": return delTema(Kirigami.Theme.visitedLinkColor, 0.72, 0.9, 0.78)
        case "cian": return delTema(Kirigami.Theme.activeTextColor, 0.45, 0.55, 0.5)
        case "gris": return Kirigami.Theme.disabledTextColor
        default: return Kirigami.Theme.textColor
        }
    }
}
