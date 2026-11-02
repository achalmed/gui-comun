"""gui_comun/i18n.py — las funciones `i18n*` de KI18n para el QML de Kirigami Addons, desde Python.

Kirigami Addons (FormCard, los delegados, los diálogos) traduce con KI18n: llama a `i18nd("kirigami-addons6", …)` e
`i18ndc(…)`, funciones que una aplicación de C++ instala con `KLocalizedContext` como objeto de contexto del motor.
Sin ellas el QML de Addons falla («i18ndc is not defined») y, aun sin fallar, quedaría en inglés. Este módulo pone el
mismo objeto de contexto desde Python: busca la cadena en los catálogos gettext instalados (`/usr/share/locale/<idioma>/
LC_MESSAGES/<dominio>.mo`) con el `gettext` de la biblioteca estándar y sustituye `%1`, `%2`… como hace KI18n.

    from gui_comun.i18n import instalar
    instalar(motor, idioma="es")
"""

from __future__ import annotations

import gettext
import re
from functools import lru_cache

from gui_comun.qt import QObject, Slot

RUTAS_LOCALE = ("/usr/share/locale", "/usr/local/share/locale", "/usr/share/locale-langpack")
DOMINIO_POR_OMISION = "kirigami-addons6"
_MARCA = re.compile(r"%(\d+)")


@lru_cache(maxsize=None)
def catalogo(dominio: str, idioma: str):
    for ruta in RUTAS_LOCALE:
        try:
            return gettext.translation(dominio, ruta, languages=[idioma, idioma.split("_")[0]])
        except OSError:
            continue
    return gettext.NullTranslations()


def sustituir(texto: str, argumentos) -> str:
    """`%1`, `%2`… por los argumentos (KI18n); un `%n` sin argumento se deja como está."""
    def reemplazo(m):
        i = int(m.group(1)) - 1
        return str(argumentos[i]) if 0 <= i < len(argumentos) else m.group(0)
    return _MARCA.sub(reemplazo, texto)


def _sobrecargas(*fijos, hasta: int = 9):
    """Un Slot por aridad: los parámetros fijos más 0…`hasta` argumentos QVariant (los `%1`, `%2`… del texto)."""
    def decorar(metodo):
        for extra in range(hasta, -1, -1):
            metodo = Slot(*fijos, *(["QVariant"] * extra), result=str)(metodo)
        return metodo
    return decorar


class ContextoTraduccion(QObject):
    """El objeto de contexto: sus métodos son funciones globales en todo el QML del motor (como KLocalizedContext)."""

    def __init__(self, idioma: str = "es", dominio: str = DOMINIO_POR_OMISION, parent=None):
        super().__init__(parent)
        self.idioma, self.dominio = idioma, dominio

    def _t(self, dominio: str, contexto: str | None, texto: str, args):
        cat = catalogo(dominio or self.dominio, self.idioma)
        traducido = cat.pgettext(contexto, texto) if contexto else cat.gettext(texto)
        return sustituir(traducido, args)

    def _tp(self, dominio: str, contexto: str | None, singular: str, plural: str, n, args):
        cat = catalogo(dominio or self.dominio, self.idioma)
        try:
            cuantos = int(n)
        except (TypeError, ValueError):
            cuantos = 1
        if contexto:
            traducido = cat.npgettext(contexto, singular, plural, cuantos)
        else:
            traducido = cat.ngettext(singular, plural, cuantos)
        return sustituir(traducido, [n, *args])

    # --- las ocho formas de KI18n y sus variantes xi18n* (con marcado semántico, que aquí no se interpreta) ---
    @_sobrecargas(str)
    def i18n(self, texto, *a):
        return self._t("", None, texto, a)

    @_sobrecargas(str, str)
    def i18nc(self, ctx, texto, *a):
        return self._t("", ctx, texto, a)

    @_sobrecargas(str, str)
    def i18nd(self, dom, texto, *a):
        return self._t(dom, None, texto, a)

    @_sobrecargas(str, str, str)
    def i18ndc(self, dom, ctx, texto, *a):
        return self._t(dom, ctx, texto, a)

    @_sobrecargas(str, str, "QVariant")
    def i18np(self, s, p, n, *a):
        return self._tp("", None, s, p, n, a)

    @_sobrecargas(str, str, str, "QVariant")
    def i18ncp(self, ctx, s, p, n, *a):
        return self._tp("", ctx, s, p, n, a)

    @_sobrecargas(str, str, str, "QVariant")
    def i18ndp(self, dom, s, p, n, *a):
        return self._tp(dom, None, s, p, n, a)

    @_sobrecargas(str, str, str, str, "QVariant")
    def i18ndcp(self, dom, ctx, s, p, n, *a):
        return self._tp(dom, ctx, s, p, n, a)

    @_sobrecargas(str)
    def xi18n(self, texto, *a):
        return self._t("", None, texto, a)

    @_sobrecargas(str, str)
    def xi18nc(self, ctx, texto, *a):
        return self._t("", ctx, texto, a)

    @_sobrecargas(str, str)
    def xi18nd(self, dom, texto, *a):
        return self._t(dom, None, texto, a)

    @_sobrecargas(str, str, str)
    def xi18ndc(self, dom, ctx, texto, *a):
        return self._t(dom, ctx, texto, a)

    @_sobrecargas(str, str, "QVariant")
    def xi18np(self, s, p, n, *a):
        return self._tp("", None, s, p, n, a)

    @_sobrecargas(str, str, str, "QVariant")
    def xi18ncp(self, ctx, s, p, n, *a):
        return self._tp("", ctx, s, p, n, a)

    @_sobrecargas(str, str, str, "QVariant")
    def xi18ndp(self, dom, s, p, n, *a):
        return self._tp(dom, None, s, p, n, a)

    @_sobrecargas(str, str, str, str, "QVariant")
    def xi18ndcp(self, dom, ctx, s, p, n, *a):
        return self._tp(dom, ctx, s, p, n, a)


def instalar(motor, idioma: str = "es") -> ContextoTraduccion:
    """Pone el objeto de contexto en el motor QML. Devuelve el objeto (hay que conservarlo vivo)."""
    contexto = ContextoTraduccion(idioma)
    motor.rootContext().setContextObject(contexto)
    return contexto
