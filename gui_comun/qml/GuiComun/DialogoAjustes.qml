// DialogoAjustes — «Configurar <Studio>…»: la anatomía de los diálogos de configuración de KDE (lista de módulos a la
// izquierda, la página del módulo a la derecha, con FormCard) sobre Kirigami.Dialog. Kirigami Addons 1.11 en Kubuntu
// 26.04 no trae `org.kde.kirigamiaddons.settings` (ConfigurationView); cuando llegue, este diálogo se apoya en él
// sin cambiar su API. Cada módulo es {titulo, icono, pagina (Component)}; una página puede declarar
// `function guardar()`, que se llama al aceptar o aplicar.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

Kirigami.Dialog {
    id: dialogo

    property var modulos: []
    property alias moduloActual: lista.currentIndex
    signal guardado()

    title: "Configurar"
    preferredWidth: Kirigami.Units.gridUnit * 44
    preferredHeight: Kirigami.Units.gridUnit * 30
    padding: 0
    standardButtons: QQC2.Dialog.Ok | QQC2.Dialog.Apply | QQC2.Dialog.Cancel

    function guardar() {
        for (let i = 0; i < paginas.count; i++) {
            const p = paginas.itemAt(i)
            if (p && p.item && typeof p.item.guardar === "function") p.item.guardar()
        }
        guardado()
    }
    onAccepted: guardar()
    onApplied: guardar()

    RowLayout {
        spacing: 0
        ListView {
            id: lista
            Layout.preferredWidth: Kirigami.Units.gridUnit * 12
            Layout.fillHeight: true
            clip: true
            model: dialogo.modulos
            currentIndex: 0
            delegate: QQC2.ItemDelegate {
                required property int index
                required property var modelData
                width: ListView.view.width
                highlighted: ListView.isCurrentItem
                text: modelData.titulo
                icon.name: modelData.icono || "configure"
                onClicked: lista.currentIndex = index
            }
            Kirigami.Theme.colorSet: Kirigami.Theme.View
            Kirigami.Theme.inherit: false
            Rectangle { anchors.fill: parent; z: -1; color: Kirigami.Theme.backgroundColor }
        }
        Kirigami.Separator { Layout.fillHeight: true }
        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: lista.currentIndex
            Repeater {
                id: paginas
                model: dialogo.modulos
                delegate: Loader {
                    required property var modelData
                    sourceComponent: modelData.pagina
                }
            }
        }
    }
}
