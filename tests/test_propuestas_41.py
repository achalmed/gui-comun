"""test_propuestas_41.py — lo que entró en 4.1 desde las propuestas de los studios rediseñados el 2026-11-18:

- `Mensajes.mostrar(texto, "pista")` → `BarraEstado` la muestra en lugar del contexto y se borra sola;
- `TablaDatos.nivelesBorde`: el nivel en el borde izquierdo de la fila, solo para esos niveles;
- `VistaComparacion`: «+n −m» en los colores de estado;
- `TerminalSalida`: cada línea con el nivel de su regla (o el suyo);
- notificaciones con acciones (`notify-send --action`), sin enviar ninguna real;
- `pasos.informe(pasos=)`, `esquema.kvantum_a_juego` (widgetStyle) y `galeria.vivo` (los huérfanos del bus propio).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

from conftest import correr_hijo, requiere_binding, requiere_kirigami

# --------------------------------------------------------------------------------------------------------- QML
GUION = r'''
import os, sys, json
os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, sys.argv[1])
from gui_comun.qt import QGuiApplication, QQmlApplicationEngine, QObject, Slot, QTimer
from gui_comun.nucleo import RUTA_QML
from gui_comun.modelos import ModeloLista

app = QGuiApplication(sys.argv[:1])
resultado = {}
class Salida(QObject):
    @Slot(str)
    def poner(self, texto):
        resultado.update(json.loads(texto)); app.quit()
salida = Salida()
tabla = ModeloLista(("display", "nivel", "habilitado"), [{"display": "alta", "nivel": "negativo", "habilitado": True},
        {"display": "media", "nivel": "neutro", "habilitado": True}, {"display": "baja", "nivel": "positivo", "habilitado": True},
        {"display": "sin", "nivel": "", "habilitado": False}])
motor = QQmlApplicationEngine()
motor.addImportPath(str(RUTA_QML))
motor.rootContext().setContextProperty("salida", salida)
motor.rootContext().setContextProperty("tablaPrueba", tabla)
errores = []
motor.warnings.connect(lambda avisos: errores.extend(a.toString() for a in avisos))
motor.loadData(b"""
import QtQuick
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import GuiComun
QQC2.ApplicationWindow {
    id: ventana
    width: 900; height: 600; visible: true
    property alias mensajes: avisos
    Column {
        anchors.fill: parent
        Mensajes { id: avisos; width: 400; duracionPista: 300 }
        TablaDatos { id: tabla; width: 600; height: 200; modelo: tablaPrueba; columnas: [{ancho: 0, semantica: true}]; nivelesBorde: ["negativo", "neutro"] }
        VistaComparacion { id: comparacion; width: 600; height: 120
            diferencia: ({ruta: "a.txt", filas: [], trozos: 1, anadidas: 2, quitadas: 1, binario: false, vacia: false}) }
        TerminalSalida { id: terminal; width: 600; height: 150; orden: "main.sh --dry-run"
            lineas: ["[ERROR] no", "Saltado x", "\\u2713 hecho", "otra", {texto: "[ERROR] pero activo", nivel: "activo"}]
            reglas: [{contiene: "otra", nivel: "inactivo"}].concat(reglasComunes) }
    }
    footer: BarraEstado { id: barra; contexto: "uno \\u00b7 main" }

    function buscar(item, nombre, lista) {
        if (!item) return lista
        if (item.objectName === nombre) lista.push(item)
        for (let i = 0; i < item.children.length; i++) buscar(item.children[i], nombre, lista)
        return lista
    }
    Timer {
        interval: 400; running: true
        onTriggered: {
            const r = {}
            r.contextoAntes = barra.textoDerecha
            avisos.mostrar("Elige primero un modelo", "pista")
            r.contextoConPista = barra.textoDerecha
            r.mensajesEnLinea = avisos.cuantos
            const bordes = ventana.buscar(tabla.vista.contentItem, "bordeNivel", [])
            r.bordesVisibles = bordes.filter(b => b.visible).length
            r.bordesColores = bordes.filter(b => b.visible).map(b => String(b.color))
            const mas = ventana.buscar(comparacion, "cifraAnadidas", [])[0], menos = ventana.buscar(comparacion, "cifraQuitadas", [])[0]
            r.cifras = [mas.text, menos.text]
            r.cifrasDistintas = String(mas.color) !== String(menos.color) && String(mas.color) !== String(Kirigami.Theme.disabledTextColor)
            r.niveles = terminal.lineas.map(l => terminal.nivelDe(l))
            r.lineasTerminal = terminal.cuantas
            ventana.parcial = r
            fin.start()
        }
    }
    property var parcial: ({})
    Timer {
        id: fin; interval: 700
        onTriggered: salida.poner(JSON.stringify(Object.assign({contextoTrasPista: barra.textoDerecha}, ventana.parcial)))
    }
}
""")
if not motor.rootObjects():
    print(json.dumps({"ok": False, "errores": errores})); sys.exit(0)
QTimer.singleShot(6000, app.quit)
app.exec()
print(json.dumps({"ok": True, "errores": errores, "r": resultado}))
'''


@requiere_kirigami
def test_pista_borde_cifras_y_terminal(tmp_path):
    r = correr_hijo(GUION, tmp_path, plazo=60)
    assert r.returncode == 0, r.stderr[-3000:]
    datos = json.loads(r.stdout.strip().splitlines()[-1])
    assert datos["ok"], datos["errores"]
    graves = [e for e in datos["errores"] if "TypeError" in e or "ReferenceError" in e or "is not a type" in e]
    assert not graves, "\n".join(graves)
    res = datos["r"]
    # la pista ocupa el lugar del contexto, no va a los mensajes en línea, y se borra sola
    assert res["contextoAntes"] == "uno · main"
    assert res["contextoConPista"] == "Elige primero un modelo"
    assert res["mensajesEnLinea"] == 0
    assert res["contextoTrasPista"] == "uno · main"
    # el borde: alta y media, no baja ni la que no tiene nivel; colores distintos
    assert res["bordesVisibles"] == 2 and len(set(res["bordesColores"])) == 2
    # «+2 −1» en dos colores de estado
    assert res["cifras"] == ["+2", "−1"] and res["cifrasDistintas"]
    # la terminal: regla propia antes que las comunes; el nivel explícito manda
    assert res["niveles"] == ["negativo", "neutro", "positivo", "inactivo", "activo"]
    assert res["lineasTerminal"] == 5


# --------------------------------------------------------------------------------------------- notificaciones
def test_orden_con_acciones():
    from gui_comun import notificaciones as nt
    argv = nt.orden("Informe guardado.", "positivo", "Git Studio", "git-studio", reemplazar=9,
                    acciones=[("a0", "Abrir"), ("a1", "Mostrar en Dolphin")])
    assert "--action=a0=Abrir" in argv and "--action=a1=Mostrar en Dolphin" in argv
    assert "--transient" not in argv and "--replace-id" not in argv              # con botones, al historial
    assert argv[argv.index("--expire-time") + 1] == str(nt.DURACION_CON_ACCIONES_MS)
    assert argv[-2:] == ["Hecho", "Informe guardado."]
    error = nt.orden("Falló.", "error", "A", "a", acciones=[("a0", "Ver")])
    assert error[error.index("--expire-time") + 1] == "0"


@requiere_binding
def test_notificar_con_acciones_lee_la_elegida(app, monkeypatch):
    """Sin enviar nada: la orden se cambia por un `printf` que imprime lo que imprimiría notify-send (id y clave)."""
    from gui_comun import notificaciones as nt
    from gui_comun.qt import QCoreApplication

    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    n = nt.Notificador("prueba", "Prueba")
    assert n.notificarConAcciones("x", "informacion", [{"clave": "a0", "texto": "Abrir"}]) == 0      # sin escritorio
    monkeypatch.setenv("QT_QPA_PLATFORM", "wayland")
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-prueba")
    monkeypatch.delenv("GUI_COMUN_SIN_NOTIFICACIONES", raising=False)
    monkeypatch.setattr(nt.shutil, "which", lambda nombre: "/bin/true")
    monkeypatch.setattr(nt, "orden", lambda *a, **k: ["sh", "-c", "printf '4711\\na1\\n'"])
    elegidas, cerradas = [], []
    n.accionElegida.connect(lambda i, c: elegidas.append((i, c)))
    n.notificacionCerrada.connect(cerradas.append)
    ident = n.notificarConAcciones("Informe guardado.", "positivo", [{"clave": "a0", "texto": "Abrir"}, {"clave": "a1", "texto": "Ver"}])
    assert ident > 0
    limite = time.time() + 10
    while not cerradas and time.time() < limite:
        QCoreApplication.processEvents()
        time.sleep(0.02)
    assert elegidas == [(ident, "a1")] and cerradas == [ident]


# ------------------------------------------------------------------------------------------------------ pasos
def test_informe_con_los_nombres_del_studio():
    from gui_comun import pasos as ps
    plan = ps.Plan("t", "Prueba", "/tmp", "Algo.", afectados=[{"ruta": "a", "accion": "crear"}])
    v = ps.verificacion([{"ruta": "a", "ok": True, "detalle": ""}])
    siempre = ps.informe(plan, {"hechos": 1}, v, fecha="2026-11-18 10:00:00")
    assert "## 3. Conflictos (no se ejecutaron)" in siempre and "## 4. Ejecución" in siempre    # sin nombres: igual que antes
    propio = ps.informe(plan, {"hechos": 1}, v, fecha="2026-11-18 10:00:00",
                        pasos=["Planear", "Simular", "Respaldar", "Aplicar", "Verificar", "Deshacer"])
    titulos = [l for l in propio.splitlines() if l.startswith("## ")]
    assert titulos == ["## 1. Planear", "## 2. Simular", "## 3. Respaldar", "## 4. Aplicar", "## 5. Verificar", "## 6. Deshacer"]
    corto = ps.informe(plan, {"hechos": 1}, v, pasos=["Planear"])
    assert "## 1. Planear" in corto and "## 2. Afectados" in corto


# ------------------------------------------------------------------------------------------------- esquema
CLARO = "[General]\nName=Claro\n[Colors:Window]\nBackgroundNormal=239,240,241\n"
OSCURO = "[General]\nName=Oscuro\n[Colors:Window]\nBackgroundNormal=32,35,38\n"


@pytest.mark.parametrize("estilo, esquema, esperado", [
    ("kvantum", OSCURO, "kvantum-dark"), ("kvantum-dark", CLARO, "kvantum"),
    ("kvantum", CLARO, "kvantum"), ("Breeze", OSCURO, "Breeze")])
def test_entorno_con_esquema_fija_la_variante_de_kvantum(tmp_path, monkeypatch, estilo, esquema, esperado):
    from gui_comun.galeria import esquema as es
    usuario = tmp_path / "usuario"
    usuario.mkdir()
    (usuario / "kdeglobals").write_text(f"[KDE]\nwidgetStyle={estilo}\n[Colors:Window]\nBackgroundNormal=1,2,3\n")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(usuario))
    colors = tmp_path / "Esquema.colors"
    colors.write_text(esquema)
    env = es.entorno_con_esquema(colors, tmp_path / "temporal")
    cfg = es._leer(Path(env["XDG_CONFIG_HOME"]) / "kdeglobals")
    assert cfg.get("KDE", "widgetStyle") == esperado
    assert (usuario / "kdeglobals").read_text().count(f"widgetStyle={estilo}") == 1        # el del usuario, intacto


# --------------------------------------------------------------------------------------------------- vivo
def test_detener_huerfanos_solo_los_de_su_marca(tmp_path):
    from gui_comun.galeria import vivo
    marca = str(tmp_path / "esta")
    mio = subprocess.Popen(["sleep", "60"], env=dict(os.environ, **{vivo.MARCA: marca}))
    ajeno = subprocess.Popen(["sleep", "60"], env=dict(os.environ, **{vivo.MARCA: str(tmp_path / "otra")}))
    try:
        time.sleep(0.2)
        assert vivo.detener_huerfanos(marca, simular=True) == [mio.pid] and mio.poll() is None    # simular no toca
        assert vivo.detener_huerfanos(marca) == [mio.pid]
        assert mio.wait(timeout=5) is not None and ajeno.poll() is None
    finally:
        for p in (mio, ajeno):
            if p.poll() is None:
                p.terminate()
                p.wait(timeout=5)


@pytest.mark.skipif(shutil.which("dbus-run-session") is None, reason="sin dbus-run-session")
def test_correr_en_bus_propio_detiene_lo_que_sobrevive(tmp_path):
    """Un proceso que se desprende (como el portal de KDE) sobrevive a dbus-run-session: el ayudante lo detiene."""
    from gui_comun.galeria import vivo
    carpeta = tmp_path / "prueba"
    pid_archivo = tmp_path / "pid"
    guion = f"setsid sleep 60 > /dev/null 2>&1 < /dev/null & echo $! > {pid_archivo}"
    assert vivo.correr_en_bus_propio(["sh", "-c", guion], dict(os.environ), carpeta) == 0
    pid = int(pid_archivo.read_text())
    limite = time.time() + 5
    while time.time() < limite and Path(f"/proc/{pid}").exists() and "Z" not in Path(f"/proc/{pid}/stat").read_text().split()[2]:
        time.sleep(0.05)
    assert not Path(f"/proc/{pid}").exists() or Path(f"/proc/{pid}/stat").read_text().split()[2] == "Z"
    assert vivo.huerfanos(carpeta) == []


def test_aplicar_en_vivo_se_niega_fuera_del_bus_propio(tmp_path, monkeypatch):
    from gui_comun.galeria import vivo
    monkeypatch.delenv(vivo.BUS_SESION, raising=False)
    colors = tmp_path / "Oscuro.colors"
    colors.write_text(OSCURO)
    assert vivo.aplicar_esquema_en_vivo(colors, tmp_path) is False
    assert not (tmp_path / "kdeglobals").exists()
    # dentro de un bus «propio» pero apuntando a la configuración real: tampoco
    monkeypatch.setenv(vivo.BUS_SESION, "unix:path=/real")
    monkeypatch.setenv("DBUS_SESSION_BUS_ADDRESS", "unix:path=/propio")
    assert vivo.aplicar_esquema_en_vivo(colors, Path.home() / ".config") is False


def test_aplicar_en_vivo_con_casa_falsa(tmp_path, monkeypatch):
    """Con `HOME` en una casa falsa (la copia de Lliphi), su `.config` es temporal y se cambia; la real, nunca."""
    from gui_comun.galeria import vivo
    casa = tmp_path / "casa"
    config = casa / ".config"
    config.mkdir(parents=True)
    (config / "kdeglobals").write_text("[KDE]\nwidgetStyle=kvantum\n")
    colors = tmp_path / "Oscuro.colors"
    colors.write_text(OSCURO)
    monkeypatch.setenv("HOME", str(casa))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config))
    monkeypatch.setenv(vivo.BUS_SESION, "unix:path=/real")
    monkeypatch.setenv("DBUS_SESSION_BUS_ADDRESS", "unix:path=/propio")
    avisos = []
    monkeypatch.setattr(vivo.subprocess, "run", lambda orden, **k: avisos.append(orden))
    assert vivo.aplicar_esquema_en_vivo(colors) is True
    assert "widgetStyle=kvantum-dark" in (config / "kdeglobals").read_text() and avisos == [vivo.AVISO]
    assert vivo.aplicar_esquema_en_vivo(colors, vivo.config_real()) is False and len(avisos) == 1
