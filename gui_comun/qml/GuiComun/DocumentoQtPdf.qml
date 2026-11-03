// DocumentoQtPdf (3.1) — el PDF abierto con QtQuick.Pdf. Vive en su propio archivo para que VistaPdf no importe
// QtQuick.Pdf: VistaPdf lo carga con un Loader solo si el módulo está (`visor.motor === "qtpdf"`); sin él, pdftoppm.
import QtQuick
import QtQuick.Pdf

PdfDocument {}
