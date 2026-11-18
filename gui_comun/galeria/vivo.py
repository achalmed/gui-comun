"""gui_comun/galeria/vivo.py — la prueba del cambio de esquema con la ventana abierta, aislada (4.1, 2026-11-18).

Cinco studios (Simuladores, Lliphi, Huella, Raphi, Muyu) probaron el cambio de claro a oscuro en vivo igual: la ventana
corre con `XDG_CONFIG_HOME` temporal (`esquema.entorno_con_esquema`) bajo `dbus-run-session` (un bus de sesión propio),
se reescribe el kdeglobals temporal y se emite `notifyChange` SOLO en ese bus. Todos tropezaron con lo mismo: el bus
propio activa a pedido el portal de KDE (`xdg-desktop-portal-kde`), `ksecretd` y otros, que sobreviven a
`dbus-run-session`, quedan huérfanos y retienen la salida de la orden. Aquí, una sola vez:

    from gui_comun.galeria import vivo
    env = entorno_con_esquema(Path("LliphiClaro.colors"), carpeta / "config")
    codigo = vivo.correr_en_bus_propio([sys.executable, "capturar.py", ...], env, carpeta)   # y detiene los huérfanos

    # dentro del proceso hijo, tras la primera captura:
    if vivo.aplicar_esquema_en_vivo(Path("LliphiOscuro.colors")):   # falso (y no emite) si el bus es el de la sesión
        ...  # segunda captura

Los huérfanos se detienen por su PID, y solo los que llevan en su entorno la marca de ESTA prueba (`MARCA=<carpeta>`):
nunca por nombre ni por patrón, que alcanzaría a los de otras sesiones o al propio guion.
"""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
from pathlib import Path

MARCA = "GUI_COMUN_PRUEBA_VIVO"            # la carpeta temporal de la prueba, en el entorno de todo lo que arranque
BUS_SESION = "GUI_COMUN_BUS_SESION"        # el bus de la sesión real, para negarse a emitir en él
AVISO = ["dbus-send", "--session", "--type=signal", "/KGlobalSettings", "org.kde.KGlobalSettings.notifyChange",
         "int32:0", "int32:0"]


def huerfanos(carpeta: str | Path, variable: str = MARCA) -> list[int]:
    """Los PID de los procesos (del usuario) que llevan `variable=<carpeta>` en su entorno, salvo este y su padre."""
    marca = f"{variable}={carpeta}".encode()
    propios = {os.getpid(), os.getppid()}
    pids = []
    for proc in Path("/proc").iterdir():
        if not proc.name.isdigit() or int(proc.name) in propios:
            continue
        try:
            if marca in (proc / "environ").read_bytes().split(b"\0"):
                pids.append(int(proc.name))
        except OSError:                    # terminó entretanto, o es de otro usuario (su entorno no se lee)
            continue
    return sorted(pids)


def detener_huerfanos(carpeta: str | Path, variable: str = MARCA, simular: bool = False) -> list[int]:
    """Detiene (SIGTERM) los procesos de `huerfanos`; con `simular`, solo dice cuáles. Devuelve sus PID."""
    pids = huerfanos(carpeta, variable)
    if not simular:
        for pid in pids:
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError:
                pass
    return pids


def hay_bus_propio() -> bool:
    """Si se puede probar en vivo: está `dbus-run-session`."""
    return shutil.which("dbus-run-session") is not None


def en_bus_propio() -> bool:
    """Si este proceso corre en un bus distinto del de la sesión real (lo arrancó `correr_en_bus_propio`)."""
    bus = os.environ.get("DBUS_SESSION_BUS_ADDRESS", "")
    return bool(bus) and BUS_SESION in os.environ and bus != os.environ[BUS_SESION]


def correr_en_bus_propio(orden: list[str], env: dict[str, str], carpeta: str | Path, **kw) -> int:
    """Corre `orden` bajo `dbus-run-session` con `env` marcado con la carpeta de la prueba; al acabar, detiene los
    servicios que el bus dejó huérfanos (solo los de esta prueba). Devuelve el código de salida de la orden."""
    if not hay_bus_propio():
        raise RuntimeError("falta dbus-run-session: el cambio en vivo no se prueba en el bus de la sesión")
    env = dict(env)
    env[MARCA] = str(carpeta)
    env[BUS_SESION] = os.environ.get("DBUS_SESSION_BUS_ADDRESS", "")
    try:
        return subprocess.run(["dbus-run-session", "--"] + list(orden), env=env, **kw).returncode
    finally:
        detener_huerfanos(carpeta)


def aplicar_esquema_en_vivo(colors: Path, config: Path | None = None) -> bool:
    """Dentro del bus propio: pone `colors` en el kdeglobals de `config` (por omisión, `XDG_CONFIG_HOME`, que ha de ser
    temporal), Kvantum a juego, y emite `notifyChange` en ese bus. Falso, sin tocar nada, si el bus es el de la sesión."""
    from gui_comun.galeria.esquema import kdeglobals_con_esquema, kvantum_a_juego

    if not en_bus_propio():
        return False
    ruta = config or os.environ.get("XDG_CONFIG_HOME")
    if not ruta or Path(ruta).resolve() == (Path.home() / ".config").resolve():
        return False                       # nunca la configuración real del usuario
    config = Path(ruta)
    kdeglobals_con_esquema(colors, config / "kdeglobals", kdeglobals=config / "kdeglobals")
    kvantum_a_juego(colors, config)
    subprocess.run(AVISO, check=False)
    return True
