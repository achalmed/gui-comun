#!/usr/bin/env bash
# tests/run.sh — corre las pruebas de gui-comun con pytest, con la carpeta temporal en disco y sin caché.
# Uso: tests/run.sh [opciones de pytest]   (p. ej. -k qml)
# Las pruebas en proceso usan el binding del Python que corre pytest; las de QML abren un proceso hijo con el Python
# del sistema (/usr/bin/python3, el del Qt con Kirigami) sin pantalla y con XDG_CONFIG_HOME temporal.
set -euo pipefail

DIR_PRUEBAS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_TMP="${XDG_CACHE_HOME:-$HOME/.cache}/pytest/gui-comun"
mkdir -p "$BASE_TMP"

export PYTHONDONTWRITEBYTECODE=1
export QT_QPA_PLATFORM=offscreen
export PRUEBA_TMP="$BASE_TMP"
exec python3 -m pytest "$DIR_PRUEBAS" --basetemp "$BASE_TMP" -p no:cacheprovider -q "$@"
