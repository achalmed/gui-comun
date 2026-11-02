"""gui_comun/acciones.py — el registro de acciones de un studio: cada operación existe una sola vez.

Una acción tiene nombre (`repo.analizar`), texto con mnemónico («&Analizar estado»), icono freedesktop, atajo
(una cadena portable o un `QKeySequence.StandardKey`), grupo (el menú o la categoría en la paleta), si está
habilitada y si es marcable. El QML de `GuiComun` la pinta donde toque (menú, barra, menú contextual, paleta) a
partir del mismo objeto, y al dispararla avisa a Python, que es quien hace algo.

    acciones = Acciones()
    acciones.estandar("Git Studio")                                   # ventana.*, app.*
    acciones.registrar("repo.analizar", "&Analizar estado", "view-refresh", StandardKey.Refresh, "Repositorio",
                       al_disparar=controlador.analizar)
    acciones.definir_menus([("&Archivo", ["repo.anadir", "|", "app.salir"]), ("&Ver", ["ventana.navegacion", ("C&olumnas", [...])])])
    acciones.definir_barra(["repo.analizar", "|", "repo.confirmar"])
    app.exponer("acciones", acciones)

En QML: `acciones.accion("repo.analizar")` devuelve el objeto (texto, icono, atajo, habilitada…; propiedades con
aviso de cambio), `acciones.menus` y `acciones.barra` describen menú y barra, `acciones.buscar("sinc")` alimenta
la paleta y `acciones.ejecutar(nombre)` dispara. Los atajos solo los registra la barra de menú (una vez).

3.0 — **estados de operación** y **atajos por disciplina**:

    acciones.registrar("sitio.publicar", "&Publicar…", "document-send", "Ctrl+Shift+P", "Sitio",
                       operacion="publicacion", al_disparar=publicar,
                       consecuencias=lambda: f"Se subirán {n} archivos a {dominio}. No se puede deshacer desde aquí.")

`operacion` es una de `OPERACIONES` (lectura, simulación, preparación, escritura, instalación, publicación,
eliminación). Instalación, publicación y eliminación **siempre** piden confirmación, y `registrar` exige que sus
`consecuencias` estén redactadas (texto o función que lo calcula al pedirla); cualquier otra la pide con
`confirmar=True` (una escritura que sobrescribe). Disparar una acción así no la ejecuta: `Acciones` emite
`confirmacionPedida({...})`, la ventana (`VentanaBase`) muestra el diálogo y, si el usuario acepta, llama a
`confirmar(nombre)`. La base no impone atajos de disciplina (ni F5): cada studio fija los suyos al registrar, cambia
los estándar con `estandar(..., atajos={...})` o `fijar_atajo`, y comprueba con `conflictos()` que ninguno se repite.
"""

from __future__ import annotations

from typing import Callable

from gui_comun.qt import (QAbstractListModel, QByteArray, QGuiApplication, QKeySequence, QModelIndex, QObject, Qt,
                          Property, Signal, Slot, rol)

StandardKey = QKeySequence.StandardKey

# los atajos estándar de KDE, fijos: sin plataforma `QKeySequence(StandardKey)` aborta y con `offscreen` devuelve «Settings».
# Pantalla completa es Ctrl+Mayús+F (KDE, Dolphin): F11 es el panel de detalles en la familia (rediseno.md §3.3)
_ESTANDAR_SIN_PLATAFORMA = {StandardKey.Refresh: "F5", StandardKey.Quit: "Ctrl+Q", StandardKey.Preferences: "Ctrl+Shift+,",
                            StandardKey.Find: "Ctrl+F", StandardKey.New: "Ctrl+N", StandardKey.Open: "Ctrl+O",
                            StandardKey.Save: "Ctrl+S", StandardKey.SelectAll: "Ctrl+A", StandardKey.FullScreen: "Ctrl+Shift+F",
                            StandardKey.HelpContents: "F1", StandardKey.Delete: "Del", StandardKey.Close: "Ctrl+W",
                            StandardKey.Copy: "Ctrl+C", StandardKey.Paste: "Ctrl+V", StandardKey.Undo: "Ctrl+Z",
                            StandardKey.Print: "Ctrl+P", StandardKey.ZoomIn: "Ctrl++", StandardKey.ZoomOut: "Ctrl+-"}

# cómo se escribe cada tecla en los menús de la familia (la traducción de Qt dice «Mayúsculas», demasiado largo)
_TECLAS = (("Shift", "Mayús"), ("Return", "Intro"), ("Enter", "Intro"), ("Del", "Supr"), ("Backspace", "Retroceso"),
           ("Space", "Espacio"), ("Esc", "Esc"), ("PgUp", "RePág"), ("PgDown", "AvPág"), ("Home", "Inicio"),
           ("End", "Fin"), ("Ins", "Ins"), ("Meta", "Meta"), ("Up", "↑"), ("Down", "↓"), ("Left", "←"),
           ("Right", "→"))


# 3.0: los estados de una operación. nombre → (etiqueta, icono, confirmación obligatoria)
OPERACIONES = {
    "lectura": ("Lectura", "document-preview", False),
    "simulacion": ("Simulación", "view-preview", False),
    "preparacion": ("Preparación", "document-edit", False),
    "escritura": ("Escritura", "document-save", False),
    "instalacion": ("Instalación", "run-install", True),
    "publicacion": ("Publicación", "document-send", True),
    "eliminacion": ("Eliminación", "edit-delete", True),
}


def texto_operacion(operacion: str) -> str:
    return OPERACIONES[operacion][0] if operacion in OPERACIONES else ""


def atajo_portable(atajo) -> str:
    """`StandardKey` o cadena → la secuencia portable que entiende `shortcut:` en QML («Ctrl+Shift+S», «F5»)."""
    if not atajo:
        return ""
    if isinstance(atajo, str):
        return atajo
    if atajo in _ESTANDAR_SIN_PLATAFORMA or QGuiApplication.instance() is None:   # los de KDE, sin depender del tema
        return _ESTANDAR_SIN_PLATAFORMA.get(atajo, "")
    return QKeySequence(atajo).toString(QKeySequence.SequenceFormat.PortableText).split(", ")[0]


def atajo_legible(portable: str) -> str:
    """«Ctrl+Shift+S» → «Ctrl+Mayús+S»: lo que se muestra junto a la orden."""
    if not portable:
        return ""
    partes = portable.split("+")
    tabla = dict(_TECLAS)
    return "+".join(tabla.get(p, p) for p in partes)


class Accion(QObject):
    """Una operación del studio. Sus propiedades avisan al cambiar: el QML que la representa se actualiza solo."""

    textoCambiado = Signal()
    iconoCambiado = Signal()
    habilitadaCambiada = Signal()
    marcadaCambiada = Signal()
    visibleCambiada = Signal()
    atajoCambiado = Signal()
    disparada = Signal(bool)          # el estado marcado tras dispararse (False si no es marcable)
    confirmacionPedida = Signal()     # 3.0: se disparó una acción que exige confirmación; aún no se ejecutó

    def __init__(self, nombre: str, texto: str, icono: str = "", atajo=None, grupo: str = "", *,
                 habilitada: bool = True, marcable: bool = False, marcada: bool = False, descripcion: str = "",
                 visible: bool = True, operacion: str = "", consecuencias="", confirmar: bool | None = None,
                 parent=None):
        super().__init__(parent)
        if operacion and operacion not in OPERACIONES:
            raise ValueError(f"{nombre}: operación desconocida «{operacion}» (una de {', '.join(OPERACIONES)})")
        obligatoria = operacion in OPERACIONES and OPERACIONES[operacion][2]
        if obligatoria and confirmar is False:
            raise ValueError(f"{nombre}: una {texto_operacion(operacion).lower()} siempre pide confirmación")
        if (obligatoria or confirmar) and not consecuencias:
            raise ValueError(f"{nombre}: una acción que pide confirmación necesita sus consecuencias redactadas")
        if (obligatoria or confirmar) and marcable:
            raise ValueError(f"{nombre}: una acción marcable no pide confirmación")
        self._nombre, self._texto, self._icono, self._grupo = nombre, texto, icono, grupo
        self._atajo = atajo_portable(atajo)
        self._habilitada, self._marcable, self._marcada = habilitada, marcable, marcada
        self._descripcion, self._visible = descripcion, visible
        self._operacion, self._consecuencias = operacion, consecuencias
        self._confirmar = bool(obligatoria or confirmar)
        self._manejadores: list[Callable] = []

    # ------------------------------------------------------------ lectura
    @Property(str, constant=True)
    def nombre(self) -> str:
        return self._nombre

    @Property(str, notify=atajoCambiado)
    def atajo(self) -> str:
        return self._atajo

    @Property(str, notify=atajoCambiado)
    def atajoTexto(self) -> str:
        return atajo_legible(self._atajo)

    def fijar_atajo(self, atajo) -> None:
        """3.0: cambia el atajo (la barra de menú lo vuelve a registrar sola)."""
        nuevo = atajo_portable(atajo)
        if nuevo != self._atajo:
            self._atajo = nuevo
            self.atajoCambiado.emit()

    @Property(str, constant=True)
    def operacion(self) -> str:
        """3.0: lectura · simulacion · preparacion · escritura · instalacion · publicacion · eliminacion (o vacío)."""
        return self._operacion

    @Property(str, constant=True)
    def operacionTexto(self) -> str:
        return texto_operacion(self._operacion)

    @Property(bool, constant=True)
    def requiereConfirmacion(self) -> bool:
        return self._confirmar

    @Property(str, notify=textoCambiado)
    def consecuencias(self) -> str:
        """Lo que pasará si se acepta; si se registró una función, se calcula cada vez que se lee."""
        return str(self._consecuencias() if callable(self._consecuencias) else self._consecuencias)

    @Property(str, constant=True)
    def grupo(self) -> str:
        return self._grupo

    @Property(bool, constant=True)
    def marcable(self) -> bool:
        return self._marcable

    @Property(str, constant=True)
    def descripcion(self) -> str:
        return self._descripcion

    @Property(str, notify=textoCambiado)
    def textoPlano(self) -> str:
        """El texto sin el `&` del mnemónico ni los puntos suspensivos finales (para la paleta y la barra)."""
        return self._texto.replace("&&", "\0").replace("&", "").replace("\0", "&").removesuffix("…")

    # ---------------------------------------------------- lectura/escritura
    def _texto_get(self) -> str:
        return self._texto

    def _texto_set(self, valor: str) -> None:
        if valor != self._texto:
            self._texto = valor
            self.textoCambiado.emit()

    texto = Property(str, _texto_get, _texto_set, notify=textoCambiado)

    def _icono_get(self) -> str:
        return self._icono

    def _icono_set(self, valor: str) -> None:
        if valor != self._icono:
            self._icono = valor
            self.iconoCambiado.emit()

    icono = Property(str, _icono_get, _icono_set, notify=iconoCambiado)

    def _habilitada_get(self) -> bool:
        return self._habilitada

    def _habilitada_set(self, valor: bool) -> None:
        if bool(valor) != self._habilitada:
            self._habilitada = bool(valor)
            self.habilitadaCambiada.emit()

    habilitada = Property(bool, _habilitada_get, _habilitada_set, notify=habilitadaCambiada)

    def _marcada_get(self) -> bool:
        return self._marcada

    def _marcada_set(self, valor: bool) -> None:
        if bool(valor) != self._marcada:
            self._marcada = bool(valor)
            self.marcadaCambiada.emit()

    marcada = Property(bool, _marcada_get, _marcada_set, notify=marcadaCambiada)

    def _visible_get(self) -> bool:
        return self._visible

    def _visible_set(self, valor: bool) -> None:
        if bool(valor) != self._visible:
            self._visible = bool(valor)
            self.visibleCambiada.emit()

    visible = Property(bool, _visible_get, _visible_set, notify=visibleCambiada)

    # ---------------------------------------------------------------- uso
    def conectar(self, manejador: Callable) -> "Accion":
        """Qué hacer al dispararse; el manejador recibe el estado marcado si es marcable, si no nada."""
        self._manejadores.append(manejador)
        return self

    @Slot()
    def disparar(self) -> None:
        """Desde un menú, un botón, la paleta o un atajo. Si pide confirmación, solo la pide (`confirmacionPedida`)."""
        if not self._habilitada:
            return
        if self._confirmar:
            self.confirmacionPedida.emit()
            return
        self._ejecutar()

    @Slot()
    def confirmar(self) -> None:
        """Ejecuta la acción ya confirmada por el usuario (la llama el diálogo de confirmación)."""
        if self._habilitada:
            self._ejecutar()

    def _ejecutar(self) -> None:
        if self._marcable:
            self._marcada_set(not self._marcada)
        for manejador in list(self._manejadores):
            if self._marcable:
                manejador(self._marcada)
            else:
                manejador()
        self.disparada.emit(self._marcada)


class Acciones(QAbstractListModel):
    """El registro: lista de `Accion` (modelo para la paleta) más la descripción del menú y la barra."""

    R_NOMBRE, R_TEXTO, R_ICONO, R_ATAJO, R_GRUPO, R_HABILITADA, R_MARCADA, R_OBJETO = (rol(i) for i in range(1, 9))

    disparada = Signal(str, bool)      # nombre, marcada: para quien prefiera escuchar el registro entero
    confirmacionPedida = Signal("QVariantMap")   # 3.0: {nombre, titulo, consecuencias, operacion, operacionTexto, icono, textoAceptar, destructiva}
    menusCambiados = Signal()
    barraCambiada = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._acciones: list[Accion] = []
        self._por_nombre: dict[str, Accion] = {}
        self._menus: list = []
        self._barra: list = []
        self._fuentes: list[Callable[[str], list[dict]]] = []
        self._dinamicas: dict[str, Callable] = {}

    # --------------------------------------------------------------- alta
    def registrar(self, nombre: str, texto: str, icono: str = "", atajo=None, grupo: str = "", *,
                  habilitada: bool = True, marcable: bool = False, marcada: bool = False, descripcion: str = "",
                  visible: bool = True, al_disparar: Callable | None = None, operacion: str = "",
                  consecuencias="", confirmar: bool | None = None) -> Accion:
        """Registra una acción. 3.0: `operacion` (ver `OPERACIONES`), `consecuencias` (texto o función) y `confirmar`."""
        if nombre in self._por_nombre:
            raise ValueError(f"acción repetida: {nombre}")
        accion = Accion(nombre, texto, icono, atajo, grupo, habilitada=habilitada, marcable=marcable,
                        marcada=marcada, descripcion=descripcion, visible=visible, operacion=operacion,
                        consecuencias=consecuencias, confirmar=confirmar, parent=self)
        if al_disparar:
            accion.conectar(al_disparar)
        fila = len(self._acciones)
        self.beginInsertRows(QModelIndex(), fila, fila)
        self._acciones.append(accion)
        self._por_nombre[nombre] = accion
        self.endInsertRows()
        accion.disparada.connect(lambda marcada, n=nombre: self.disparada.emit(n, marcada))
        accion.confirmacionPedida.connect(lambda n=nombre: self.confirmacionPedida.emit(self.peticion(n)))
        for senal in (accion.textoCambiado, accion.iconoCambiado, accion.habilitadaCambiada, accion.marcadaCambiada,
                      accion.atajoCambiado):
            senal.connect(lambda n=nombre: self._cambio(n))
        return accion

    def estandar(self, nombre_app: str, *, paneles: bool = True, atajos: dict | None = None) -> None:
        """Las acciones que toda ventana de la familia tiene (la ventana las atiende; el studio puede escucharlas).

        3.0: `paneles=False` omite los conmutadores de los tres paneles de `VentanaStudio` (una ventana sobre
        `VentanaBase` sin navegación, detalles ni panel inferior no los necesita); `atajos` cambia los atajos de las
        estándar ({"ventana.detalles": "F3", "ventana.paleta": ""}) para que el studio use los de su disciplina."""
        if paneles:
            self.registrar("ventana.navegacion", "Panel de &navegación", "view-sidetree", "F9", "Ver", marcable=True,
                           marcada=True, descripcion="Muestra u oculta el panel de navegación")
            self.registrar("ventana.detalles", "Panel de &detalles", "view-right-new", "F11", "Ver", marcable=True,
                           marcada=True, descripcion="Muestra u oculta el panel de detalles")
            self.registrar("ventana.inferior", "Panel &inferior", "utilities-terminal", "F4", "Ver", marcable=True,
                           marcada=False, descripcion="Muestra u oculta la salida y el registro")
        self.registrar("ventana.pantalla_completa", "Pantalla &completa", "view-fullscreen", StandardKey.FullScreen,
                       "Ver", marcable=True)
        self.registrar("ventana.paleta", "&Paleta de órdenes", "edit-find", "Ctrl+Alt+I", "Herramientas",
                       descripcion="Busca y ejecuta cualquier orden por su nombre (también Ctrl+K)")
        self.registrar("app.ajustes", f"Configurar &{nombre_app}…", "configure", StandardKey.Preferences, "Ajustes")
        self.registrar("app.acerca", f"&Acerca de {nombre_app}", "help-about", None, "Ayuda")
        self.registrar("app.salir", "&Salir", "application-exit", StandardKey.Quit, "Archivo")
        for nombre, atajo in (atajos or {}).items():
            self.fijar_atajo(nombre, atajo)

    def fijar_atajo(self, nombre: str, atajo) -> None:
        """3.0: el atajo de una acción ya registrada (vacío lo quita)."""
        if nombre not in self._por_nombre:
            raise KeyError(f"atajo para una acción sin registrar: {nombre}")
        self._por_nombre[nombre].fijar_atajo(atajo)

    def conflictos(self) -> dict[str, list[str]]:
        """3.0: los atajos que comparten dos o más acciones visibles ({"Ctrl+Return": ["a", "b"]}); un atajo repetido
        es ambiguo y no dispara ninguna. Las pruebas de cada studio piden que esté vacío."""
        por_atajo: dict[str, list[str]] = {}
        for a in self._acciones:
            if a.atajo and a.visible:
                por_atajo.setdefault(a.atajo.lower(), []).append(a.nombre)
        return {self._por_nombre[n[0]].atajo: n for n in por_atajo.values() if len(n) > 1}

    def definir_menus(self, menus: list) -> None:
        """[(título, [nombre | "|" | (título, [...])]), …] → `menus` para QML (lista de {titulo, elementos})."""
        self._menus = [self._menu(titulo, elementos) for titulo, elementos in menus]
        self.menusCambiados.emit()

    def _menu(self, titulo: str, elementos: list) -> dict:
        salida = []
        for e in elementos:
            if e == "|":
                salida.append({"tipo": "separador"})
            elif isinstance(e, tuple):
                salida.append(self._menu(e[0], e[1]))
            else:
                if e not in self._por_nombre:
                    raise KeyError(f"el menú «{titulo}» cita una acción sin registrar: {e}")
                salida.append({"tipo": "accion", "nombre": e})
        return {"tipo": "menu", "titulo": titulo, "elementos": salida}

    def definir_barra(self, nombres: list[str]) -> None:
        """Los nombres de la barra de herramientas, con "|" como separador."""
        for n in nombres:
            if n != "|" and n not in self._por_nombre:
                raise KeyError(f"la barra cita una acción sin registrar: {n}")
        self._barra = list(nombres)
        self.barraCambiada.emit()

    def anadir_fuente(self, fuente: Callable[[str], list[dict]]) -> None:
        """Entradas dinámicas de la paleta (ir a un repositorio, abrir un informe…): `fuente(texto)` devuelve
        [{nombre, texto, grupo, icono, ejecutar}] y aquí se guarda qué ejecutar para cada nombre."""
        self._fuentes.append(fuente)

    # ------------------------------------------------------------ consulta
    def __contains__(self, nombre: str) -> bool:
        return nombre in self._por_nombre

    def __getitem__(self, nombre: str) -> Accion:
        return self._por_nombre[nombre]

    def nombres(self) -> list[str]:
        return [a.nombre for a in self._acciones]

    @Slot(str, result=QObject)
    def accion(self, nombre: str) -> Accion | None:
        return self._por_nombre.get(nombre)

    @Slot(str, result=bool)
    def existe(self, nombre: str) -> bool:
        return nombre in self._por_nombre

    @Property("QVariantList", notify=menusCambiados)
    def menus(self) -> list:
        return self._menus

    @Property("QVariantList", notify=barraCambiada)
    def barra(self) -> list:
        return self._barra

    @Slot(str, result="QVariantMap")
    def peticion(self, nombre: str) -> dict:
        """3.0: lo que el diálogo de confirmación de `nombre` muestra (las consecuencias, calculadas ahora)."""
        a = self._por_nombre.get(nombre)
        if a is None:
            return {}
        return {"nombre": a.nombre, "titulo": a.textoPlano, "consecuencias": a.consecuencias, "operacion": a.operacion,
                "operacionTexto": a.operacionTexto, "icono": a.icono or OPERACIONES.get(a.operacion, ("", "dialog-question"))[1],
                "textoAceptar": a.textoPlano, "destructiva": a.operacion == "eliminacion"}

    # ---------------------------------------------------------------- uso
    @Slot(str)
    def confirmar(self, nombre: str) -> None:
        """3.0: ejecuta una acción que el usuario ya confirmó en el diálogo."""
        accion = self._por_nombre.get(nombre)
        if accion is not None:
            accion.confirmar()

    @Slot(str)
    def ejecutar(self, nombre: str) -> None:
        accion = self._por_nombre.get(nombre)
        if accion is not None:
            accion.disparar()
        elif nombre in self._dinamicas:
            self._dinamicas[nombre]()

    @Slot(str, bool)
    def habilitar(self, nombre: str, valor: bool) -> None:
        if nombre in self._por_nombre:
            self._por_nombre[nombre].habilitada = valor

    @Slot(str, bool)
    def marcar(self, nombre: str, valor: bool) -> None:
        if nombre in self._por_nombre:
            self._por_nombre[nombre].marcada = valor

    @Slot(str, result="QVariantList")
    def buscar(self, texto: str) -> list[dict]:
        """Entradas de la paleta que casan con `texto` (coincidencia difusa: las letras en orden), ordenadas por
        afinidad; sin texto, todas las acciones visibles y habilitadas por su grupo."""
        consulta = texto.strip().lower()
        candidatos = [{"nombre": a.nombre, "texto": a.textoPlano, "grupo": a.grupo, "icono": a.icono,
                       "atajo": a.atajoTexto, "descripcion": a.descripcion, "operacion": a.operacionTexto}
                      for a in self._acciones if a.visible and a.habilitada]
        self._dinamicas.clear()
        for fuente in self._fuentes:
            for entrada in fuente(consulta):
                self._dinamicas[entrada["nombre"]] = entrada.pop("ejecutar")
                entrada.setdefault("icono", "")
                entrada.setdefault("atajo", "")
                entrada.setdefault("descripcion", "")
                entrada.setdefault("operacion", "")
                candidatos.append(entrada)
        if not consulta:
            return candidatos
        puntuados = []
        for c in candidatos:
            puntos = _afinidad(consulta, c["texto"].lower()) or (20.0 if consulta in c["grupo"].lower() else 0.0)
            if puntos:
                puntuados.append((puntos, c))
        puntuados.sort(key=lambda p: (-p[0], p[1]["texto"]))
        return [c for _, c in puntuados]

    # ------------------------------------------------------------- modelo
    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._acciones)

    def roleNames(self):
        return {self.R_NOMBRE: QByteArray(b"nombre"), self.R_TEXTO: QByteArray(b"texto"),
                self.R_ICONO: QByteArray(b"icono"), self.R_ATAJO: QByteArray(b"atajo"),
                self.R_GRUPO: QByteArray(b"grupo"), self.R_HABILITADA: QByteArray(b"habilitada"),
                self.R_MARCADA: QByteArray(b"marcada"), self.R_OBJETO: QByteArray(b"objeto")}

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._acciones):
            return None
        a = self._acciones[index.row()]
        if role in (Qt.ItemDataRole.DisplayRole, self.R_TEXTO):
            return a.textoPlano
        return {self.R_NOMBRE: a.nombre, self.R_ICONO: a.icono, self.R_ATAJO: a.atajoTexto, self.R_GRUPO: a.grupo,
                self.R_HABILITADA: a.habilitada, self.R_MARCADA: a.marcada, self.R_OBJETO: a}.get(role)

    def _cambio(self, nombre: str) -> None:
        fila = self._acciones.index(self._por_nombre[nombre])
        indice = self.index(fila, 0)
        self.dataChanged.emit(indice, indice)


def _afinidad(consulta: str, texto: str) -> float:
    """0 si falta alguna letra; más alto cuanto más juntas y más al principio estén."""
    if consulta in texto:
        return 100.0 - texto.index(consulta)
    pos, puntos, previa = 0, 0.0, -2
    for letra in consulta:
        i = texto.find(letra, pos)
        if i < 0:
            return 0.0
        puntos += 3.0 if i == previa + 1 else 1.0
        previa, pos = i, i + 1
    return puntos
