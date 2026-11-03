// ResaltadoEditor (3.1) — el resaltador de KSyntaxHighlighting para un TextArea, con el tema claro u oscuro de
// KSyntaxHighlighting según el fondo de Kirigami (`oscuro`). En archivo aparte para que, si el módulo
// `org.kde.syntaxhighlighting` no está instalado, el texto se vea plano: lo cargan con un Loader EditorTexto y
// VistaTexto (y ResaltadoSalida, que lo conserva por compatibilidad).
import QtQuick
import org.kde.syntaxhighlighting

SyntaxHighlighter {
    property string nombreDefinicion: ""
    property bool oscuro: false
    definition: Repository.definitionForName(nombreDefinicion)
    theme: Repository.defaultTheme(oscuro ? Repository.DarkTheme : Repository.LightTheme)
}
