"""tests/test_notificaciones.py — los avisos como notificaciones del escritorio (4.1): la orden de notify-send por tipo
y que sin pantalla no se envía nada (4.2: Mensajes los pasa a la barra de estado, nunca a una franja). Nunca se envía un aviso real."""

from __future__ import annotations

from gui_comun import notificaciones as nt


def test_orden_por_tipo():
    info = nt.orden("Compilado en 3 s.", "positivo", "LaTeX Studio", "latex-studio", reemplazar=41)
    assert info[:3] == ["notify-send", "--app-name", "LaTeX Studio"]
    assert "--transient" in info and info[info.index("--replace-id") + 1] == "41"      # reemplaza al anterior
    assert info[info.index("--urgency") + 1] == "low" and "string:desktop-entry:latex-studio" in info
    assert info[-2:] == ["Hecho", "Compilado en 3 s."]
    error = nt.orden("No se pudo abrir.", "error", "LaTeX Studio", "latex-studio", reemplazar=41)
    assert "--transient" not in error and "--replace-id" not in error                  # queda en el historial
    assert error[error.index("--urgency") + 1] == "critical" and error[error.index("--expire-time") + 1] == "0"
    assert nt.orden("x", "rarísimo", "A", "a")[-2:] == ["A", "x"]                         # un tipo desconocido: información


def test_sin_pantalla_no_notifica(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    n = nt.Notificador("prueba", "Prueba")
    assert not n.disponible and not n.notificar("hola", "informacion")
    monkeypatch.setenv("QT_QPA_PLATFORM", "wayland")
    monkeypatch.setenv("GUI_COMUN_SIN_NOTIFICACIONES", "1")
    assert not nt.Notificador("prueba", "Prueba").disponible
