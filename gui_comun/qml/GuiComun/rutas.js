// rutas.js — rutas locales y URL de archivo para los diálogos de QtQuick.Dialogs (3.0). Los diálogos hablan en URL
// (`file:///home/x/a%20b.pdf`) y los studios en rutas (`/home/x/a b.pdf`): sin esta conversión, una carpeta con espacio
// («00 metodo») volvía como «00%20metodo» (el fallo de CampoRuta hasta 2.7).
.pragma library

function deUrl(url) {
    let texto = String(url || "")
    if (!texto.startsWith("file:")) return texto
    texto = texto.replace(/^file:\/\/(localhost)?/, "")
    try { return decodeURIComponent(texto) } catch (e) { return texto }
}

function aUrl(ruta) {
    const texto = String(ruta || "")
    if (texto === "" || texto.startsWith("file:")) return texto
    return "file://" + texto.split("/").map(encodeURIComponent).join("/")
}

function carpetaDe(ruta) {
    const texto = String(ruta || "").replace(/\/+$/, "")
    const i = texto.lastIndexOf("/")
    return i > 0 ? texto.slice(0, i) : (i === 0 ? "/" : "")
}

function nombreDe(ruta) {
    const texto = String(ruta || "").replace(/\/+$/, "")
    return texto.slice(texto.lastIndexOf("/") + 1)
}

// filtros: ["Documentos PDF (*.pdf)", …] o [{nombre: "Documentos PDF", patrones: ["*.pdf"]}, …] → nameFilters;
// con `conTodos`, «Todos los archivos (*)» al final (si no está ya)
function filtros(lista, conTodos) {
    const salida = []
    for (const f of (lista || [])) {
        if (typeof f === "string") salida.push(f)
        else if (f && f.nombre) salida.push(f.nombre + " (" + (f.patrones || ["*"]).join(" ") + ")")
    }
    if (conTodos && !salida.some(f => /\(\*\)$/.test(f))) salida.push("Todos los archivos (*)")
    return salida
}

function lista(urls) {
    const salida = []
    for (let i = 0; i < (urls ? urls.length : 0); i++) salida.push(deUrl(urls[i]))
    return salida
}
