"""gui_comun/pasos.py — los seis pasos visibles de una escritura (3.1; sin Qt).

Filesystem, Lliphi y Biblioteca los dibujaban cada uno (el encargo del autor del 2026-11-02, §3.2: una escritura nunca
se ejecuta a ciegas):

    1 Plan          qué se va a hacer y con qué opciones
    2 Afectados     cada archivo o carpeta que se escribirá, con su acción
    3 Conflictos    lo que no se puede hacer o se omitirá, y por qué; si alguno bloquea, no se ejecuta
    4 Ejecutar      la escritura, tras la confirmación de la base (`operacion=` de `Acciones`)
    5 Verificar     una comprobación aparte del éxito, en el disco
    6 Informe       el resultado en Markdown

Lo pinta `GuiComun.PasosEscritura` (la barra de los seis pasos) y, para pasos que ocurren fuera de la ventana con su
estado (en espera, en curso, hecho, falló, omitido), `GuiComun.LineaPasos`. Cada studio construye su `Plan` con su
propio servicio; lo común es la forma, la verificación y el informe.

    plan = Plan("carpetas", "Crear carpetas", carpeta, "Crear 3 carpetas…", afectados=[…], conflictos=[…])
    if not plan.bloqueado: resultado = ejecutar(plan)
    v = verificacion([{"ruta": r, "ok": os.path.isdir(r), "detalle": "existe"} for r in …])
    texto = informe(plan, resultado, v, herramienta="Filesystem Studio")
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

PASOS = ("Plan", "Afectados", "Conflictos", "Ejecutar", "Verificar", "Informe")

# los estados de un paso de `LineaPasos` y el nivel semántico con que se pinta cada uno
ESTADOS = ("pendiente", "en_curso", "hecho", "fallo", "omitido")
NIVEL = {"pendiente": "inactivo", "en_curso": "activo", "hecho": "positivo", "fallo": "negativo", "omitido": "inactivo"}


@dataclass
class Plan:
    tipo: str
    titulo: str
    carpeta: str
    descripcion: str
    afectados: list[dict] = field(default_factory=list)      # {ruta, accion, detalle, nivel?}
    conflictos: list[dict] = field(default_factory=list)     # {ruta, motivo, bloquea?}
    interno: object = None                                   # lo que el servicio necesita para ejecutar
    hecho_en: float = field(default_factory=time.time)

    @property
    def bloqueado(self) -> bool:
        """Un conflicto que bloquea impide ejecutar (los demás solo se omiten)."""
        return any(c.get("bloquea") for c in self.conflictos)

    def como_dict(self) -> dict:
        """Lo que QML lee del plan (sin `interno`)."""
        return {"tipo": self.tipo, "titulo": self.titulo, "carpeta": self.carpeta, "descripcion": self.descripcion,
                "afectados": self.afectados, "conflictos": self.conflictos, "bloqueado": self.bloqueado,
                "nAfectados": len(self.afectados), "nConflictos": len(self.conflictos)}


def cuentas(plan: Plan | None, resultado: dict | None = None, verificado: tuple | None = None) -> list[str]:
    """El texto corto de cada paso para `PasosEscritura.cuentas` («12», «2», «hecho», «✓»…)."""
    if plan is None:
        return [""] * 6
    return ["", str(len(plan.afectados)), str(len(plan.conflictos)),
            "" if resultado is None else f"{resultado.get('hechos', 0)} hechos",
            "" if verificado is None else ("✓" if verificado[0] else "✗"), ""]


def verificacion(filas: list[dict]) -> tuple[bool, str, list[dict]]:
    """Resume una verificación: `filas` = [{ruta, ok, detalle}] → (todas bien, texto, filas)."""
    malos = [f for f in filas if not f["ok"]]
    texto = (f"{len(filas)} de {len(filas)} comprobados" if not malos
             else f"{len(malos)} de {len(filas)} no quedaron como se esperaba")
    return not malos, texto, filas


def informe(plan: Plan, resultado: dict, verificado: tuple[bool, str, list[dict]], herramienta: str = "",
            fecha: str | None = None) -> str:
    """El informe en Markdown de los seis pasos (`resultado`: {hechos, errores, detalle})."""
    ok, texto, filas = verificado
    lineas = [f"# {plan.titulo}", "", f"- **Fecha:** {fecha or time.strftime('%Y-%m-%d %H:%M:%S')}"]
    if plan.carpeta:
        lineas.append(f"- **Carpeta:** `{plan.carpeta}`")
    if herramienta:
        lineas.append(f"- **Herramienta:** {herramienta} — operación en seis pasos")
    lineas += ["", "## 1. Plan", "", plan.descripcion, "", "## 2. Afectados", ""]
    lineas += [f"- {a['accion']}: `{a['ruta']}`" + (f" — {a['detalle']}" if a.get("detalle") else "") for a in plan.afectados] or ["(ninguno)"]
    lineas += ["", "## 3. Conflictos (no se ejecutaron)", ""]
    lineas += [f"- `{c['ruta']}` — {c['motivo']}" + (" (bloquea)" if c.get("bloquea") else "") for c in plan.conflictos] or ["(ninguno)"]
    lineas += ["", "## 4. Ejecución", "", f"- Hechos: {resultado.get('hechos', 0)}", f"- Errores: {resultado.get('errores', 0)}"]
    if resultado.get("detalle"):
        lineas.append(f"- {resultado['detalle']}")
    lineas += ["", "## 5. Verificación", "", f"**{'Superada' if ok else 'NO superada'}**: {texto}.", ""]
    lineas += [f"- ✗ `{f['ruta']}` — {f['detalle']}" for f in filas if not f["ok"]][:200]
    lineas += ["", "## 6. Informe", "", "Este documento."]
    return "\n".join(lineas) + "\n"


def nombre_informe(plan: Plan) -> str:
    return f"operacion-{plan.tipo}-{time.strftime('%Y%m%d-%H%M%S')}.md"


# ---------------------------------------------------------------------------------------------------- LineaPasos
def linea(definiciones: list[tuple[str, str, str]]) -> list[dict]:
    """Los pasos de una `LineaPasos` en espera: `definiciones` = [(clave, titulo, explicacion)]."""
    return [{"clave": c, "titulo": t, "explicacion": e, "estado": "pendiente", "detalle": "", "nivel": NIVEL["pendiente"]}
            for c, t, e in definiciones]


def fijar(pasos: list[dict], clave: str, estado: str, detalle: str = "") -> list[dict]:
    """Pone un paso en `estado` (uno de ESTADOS), con su detalle si se da."""
    if estado not in ESTADOS:
        raise ValueError(f"estado desconocido: {estado}")
    for p in pasos:
        if p["clave"] == clave:
            p["estado"], p["nivel"] = estado, NIVEL[estado]
            if detalle:
                p["detalle"] = detalle
    return pasos
