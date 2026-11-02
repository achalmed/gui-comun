// ResaltadoSalida — el resaltador de KSyntaxHighlighting para un TextArea; en archivo aparte para que, si el módulo
// `org.kde.syntaxhighlighting` no está instalado, el panel siga funcionando con texto plano (lo carga un Loader).
import QtQuick
import org.kde.syntaxhighlighting

SyntaxHighlighter {
    property string nombreDefinicion: "Bash"
    definition: Repository.definitionForName(nombreDefinicion)
}
