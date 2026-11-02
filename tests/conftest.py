"""conftest.py — utilidades de las pruebas de gui-comun.

Dos clases de prueba:
- en proceso (acciones, consola, tareas, modelos, i18n): una QGuiApplication `offscreen` por sesión, con el binding
  que tenga el Python que corre pytest (basta QtCore y QtGui);
- en un proceso hijo (carga de cada .qml, la galería): con el Python del sistema (`/usr/bin/python3`), el único
  cuyo Qt trae Kirigami, y un XDG_CONFIG_HOME temporal para que QSettings no toque la configuración del autor.

    tests/run.sh            # = python3 -m pytest tests --basetemp ~/.cache/pytest/gui-comun -p no:cacheprovider
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
PAQUETE = REPO / "gui_comun"
QML = PAQUETE / "qml" / "GuiComun"

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

HAY_BINDING = importlib.util.find_spec("PySide6") is not None or importlib.util.find_spec("PyQt6") is not None
requiere_binding = pytest.mark.skipif(not HAY_BINDING, reason="sin PySide6 ni PyQt6")


def _python_del_sistema() -> str | None:
    """El intérprete con el Qt del sistema (Kirigami): /usr/bin/python3 si tiene un binding; si no, ninguno."""
    candidato = "/usr/bin/python3"
    if not Path(candidato).is_file():
        return None
    r = subprocess.run([candidato, "-c", "import importlib.util as u; print(bool(u.find_spec('PySide6') or u.find_spec('PyQt6')))"],
                       capture_output=True, text=True)
    return candidato if r.stdout.strip() == "True" else None


PYTHON_SISTEMA = _python_del_sistema()


def entorno_hijo(tmp_path: Path | None, **extra: str) -> dict:
    env = {k: v for k, v in os.environ.items() if k not in ("DOCS_ROOT", "CORE_DIR", "META_DIR", "RESPALDOS_DIR")}
    base = tmp_path or Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "pytest" / "gui-comun" / "hijo"
    base.mkdir(parents=True, exist_ok=True)
    env.update({"QT_QPA_PLATFORM": "offscreen", "XDG_CONFIG_HOME": str(base / "config"), "XDG_CACHE_HOME": str(base / "cache"),
                "XDG_STATE_HOME": str(base / "state"), "PYTHONDONTWRITEBYTECODE": "1", "LC_ALL": "C.UTF-8",
                "PYTHONPATH": str(REPO), "PRUEBA_TMP": str(base)})
    env.update(extra)
    return env


def correr_hijo(guion: str, tmp_path: Path, *args: str, plazo: int = 120) -> subprocess.CompletedProcess:
    """Corre `guion` (Python) con el Python del sistema; argv[1] es la raíz del repo."""
    return subprocess.run([PYTHON_SISTEMA or sys.executable, "-c", guion, str(REPO), *args], env=entorno_hijo(tmp_path),
                          capture_output=True, text=True, timeout=plazo)


def _hay_kirigami() -> bool:
    if PYTHON_SISTEMA is None:
        return False
    guion = ("import os,sys; os.environ['QT_QPA_PLATFORM']='offscreen'; sys.path.insert(0, sys.argv[1])\n"
             "from gui_comun.qt import QGuiApplication, QQmlApplicationEngine, QUrl\n"
             "a=QGuiApplication([]); m=QQmlApplicationEngine(); import tempfile, pathlib\n"
             "p=pathlib.Path(tempfile.mkdtemp())/'K.qml'; p.write_text('import org.kde.kirigami as K\\nK.Icon{}')\n"
             "m.load(QUrl.fromLocalFile(str(p))); print(bool(m.rootObjects()))")
    r = subprocess.run([PYTHON_SISTEMA, "-c", guion, str(REPO)], capture_output=True, text=True, env=entorno_hijo(None))
    return r.stdout.strip().endswith("True")


HAY_KIRIGAMI = _hay_kirigami()
requiere_kirigami = pytest.mark.skipif(not HAY_KIRIGAMI, reason="sin Kirigami en el Qt del Python del sistema")


@pytest.fixture(scope="session")
def app():
    """Una QGuiApplication offscreen para las pruebas en proceso (QKeySequence y los iconos la necesitan)."""
    from gui_comun.qt import QGuiApplication
    instancia = QGuiApplication.instance() or QGuiApplication([sys.argv[0]])
    yield instancia
