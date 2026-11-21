// PestanasArchivos — las pestañas de los archivos abiertos de un `gui_comun.editor.ControladorEditor` (4.2), con su
// botón de cerrar: la × se ve al pasar el ratón y siempre en la pestaña activa; el clic central también cierra. La
// pestaña no cierra nada por su cuenta: emite `cerrarPedido(ruta)` y el studio decide (preguntar si hay cambios sin
// guardar con `DialogoCambiosSinGuardar`, o `controlador.cerrar(ruta)`). Ctrl+W es la acción del studio (la barra de
// menú es la única que registra atajos). Un archivo modificado lleva «● » delante; uno de solo lectura, el candado.
// Sin archivos abiertos el componente se oculta (`hayAbiertos` falso) y el studio pone su estado vacío. El estilo de
// KDE falla con una TabBar vacía ('height' of null): la TabBar vive en un Loader que solo existe con archivos, y al
// cerrar el último el Repeater la vacía antes de que el Loader la destruya, así que una pestaña final invisible y sin
// ancho la mantiene con un elemento.
import QtQuick
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

Item {
    id: raiz

    property var controlador: null
    property string atajoCerrar: "Ctrl+W"            // solo para la ayuda de la ×
    readonly property bool hayAbiertos: !!controlador && controlador.abiertos.filas > 0
    // 4.2: el nombre de una pestaña: `nombreDe(modelo)` si el studio lo da (Quarto: la carpeta en vez de «index.qmd»)
    property var nombreDe: null
    function nombre(m) { return raiz.nombreDe ? raiz.nombreDe(m) : m.nombre }
    signal cerrarPedido(string ruta)
    signal elegido(string ruta)

    visible: hayAbiertos
    implicitHeight: carga.item ? carga.item.implicitHeight : 0
    implicitWidth: carga.item ? carga.item.implicitWidth : 0

    Loader {
        id: carga
        anchors.fill: parent
        active: raiz.hayAbiertos
        sourceComponent: QQC2.TabBar {
            currentIndex: raiz.controlador ? raiz.controlador.indiceActual : -1
            Accessible.name: "Archivos abiertos"

            Repeater {
                model: raiz.controlador ? raiz.controlador.abiertos : null
                delegate: QQC2.TabButton {
                    id: pestana
                    required property var model
                    required property int index
                    readonly property bool conCerrar: hovered || checked || botonCerrar.hovered
                    // el estilo de KDE dibuja el texto centrado en toda la pestaña e ignora el relleno: dos espacios largos al
                    // final ensanchan la pestaña y corren el nombre a la izquierda, fuera de la ×
                    width: implicitWidth
                    text: (model.modificado ? "● " : "") + model.nombre + "  "
                    Accessible.name: (model.modificado ? "Modificado: " : "") + model.nombre
                    icon.name: model.solo_lectura ? "object-locked" : ""
                    onClicked: { raiz.controlador.fijarActual(model.ruta); raiz.elegido(model.ruta) }
                    QQC2.ToolTip.text: model.ruta + (model.modificado ? " · cambios sin guardar" : "")
                    QQC2.ToolTip.visible: hovered && !botonCerrar.hovered
                    QQC2.ToolTip.delay: Kirigami.Units.toolTipDelay
                    TapHandler { acceptedButtons: Qt.MiddleButton; onTapped: raiz.cerrarPedido(pestana.model.ruta) }

                    QQC2.ToolButton {
                        id: botonCerrar
                        anchors.right: parent.right
                        anchors.rightMargin: Kirigami.Units.smallSpacing
                        anchors.verticalCenter: parent.verticalCenter
                        width: Kirigami.Units.iconSizes.small + Kirigami.Units.smallSpacing * 2
                        height: width
                        padding: Kirigami.Units.smallSpacing / 2
                        flat: true
                        display: QQC2.AbstractButton.IconOnly
                        // 4.2: la X neutra (el tab-close de algunos temas es un círculo rojo en cada pestaña)
                        contentItem: Item {          // la X dibujada, del color del texto (como BotonCierre)
                            opacity: botonCerrar.hovered ? 1 : 0.7
                            Repeater {
                                model: [45, -45]
                                delegate: Rectangle {
                                    required property int modelData
                                    anchors.centerIn: parent
                                    width: Kirigami.Units.iconSizes.small * 0.7
                                    height: 1.5
                                    radius: height / 2
                                    rotation: modelData
                                    antialiasing: true
                                    color: Kirigami.Theme.textColor
                                }
                            }
                        }
                        // ocupa siempre su sitio (la pestaña no cambia de ancho al pasar el ratón); invisible, no responde
                        opacity: pestana.conCerrar ? 1 : 0
                        enabled: pestana.conCerrar
                        focusPolicy: Qt.NoFocus
                        text: "Cerrar " + raiz.nombre(pestana.model)
                        Accessible.name: text
                        onClicked: raiz.cerrarPedido(pestana.model.ruta)
                        QQC2.ToolTip.text: "Cerrar (" + raiz.atajoCerrar + "; clic central en la pestaña)"
                        QQC2.ToolTip.visible: hovered
                        QQC2.ToolTip.delay: Kirigami.Units.toolTipDelay
                    }
                }
            }
            // la pestaña de relleno: la TabBar nunca queda vacía (va al final, los índices de los archivos no cambian)
            QQC2.TabButton {
                width: 0
                visible: false
                enabled: false
                Accessible.ignored: true
            }
        }
    }
}
