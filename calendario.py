"""
calendario.py — Motor de spaced repetition. No necesitas editar este archivo.

  · Tus ramos y configuración → config.py
  · Lo que ya estudiaste      → progreso.py
"""

import csv
from datetime import date, timedelta
from collections import defaultdict

from config import (
    RAMOS, PESOS, ICONOS, CAPACIDAD_POR_DIA,
    INTERVALOS_BASE, MIN_FILL_RATIO, SKIP_WEEKENDS, USAR_COLORES,
)
from progreso import PROGRESO as _PROGRESO_CRUDO

_COLORES = ["\033[96m", "\033[93m", "\033[92m", "\033[95m", "\033[91m"]
_RESET   = "\033[0m"

# Convertir las fechas de string ("2026-05-23") a objetos date
PROGRESO: dict[str, list[date]] = {
    nombre: [date.fromisoformat(f) for f in fechas]
    for nombre, fechas in _PROGRESO_CRUDO.items()
}

# ══════════════════════════════════════════════════════════════════

DIAS_ES  = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
MESES_ES = [None, "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
            "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

# Si ya registraste algo hoy, el día está cerrado y el plan parte mañana
HOY = date.today() + timedelta(days=any(date.today() in f for f in PROGRESO.values()))

# Número global de cada ítem (#01, #02, ...) en el orden de config.py
IDX = {item["nombre"]: i for i, item in enumerate((it for r in RAMOS for it in r["items"]), 1)}


def _dias_entre(inicio: date, fin: date) -> list[date]:
    dias = [inicio + timedelta(days=i) for i in range((fin - inicio).days)]
    return [d for d in dias if not (SKIP_WEEKENDS and d.weekday() >= 5)]


def _intervalos_adaptativos(primer_dia: date, evaluacion: date) -> list[int]:
    """Extiende INTERVALOS_BASE con factor ×1.8 hasta cubrir el período al examen."""
    margen     = (evaluacion - primer_dia).days - 2
    intervalos = [i for i in INTERVALOS_BASE if i < margen]
    while intervalos and (siguiente := round(intervalos[-1] * 1.8)) < margen:
        intervalos.append(siguiente)
    return intervalos


def _sesion(item: dict, ramo: dict, sesion: str, es_relleno: bool = False) -> dict:
    return {
        "nombre":     item["nombre"],
        "tipo":       item["tipo"],
        "ramo":       ramo["nombre"],
        "sigla":      ramo["sigla"],
        "sesion":     sesion,
        "peso":       PESOS[item["tipo"]],
        "evaluacion": ramo["fecha_evaluacion"],
        "es_relleno": es_relleno,
    }


def _generar_candidatos(progreso: dict) -> list[tuple[date, dict]]:
    """
    Genera (fecha ideal, sesión) futuras para cada ítem de los ramos con examen pendiente.
    Con historial: ancla en la primera fecha real, omite repasos pasados.
    Sin historial: distribuye los ítems uniformemente en el tiempo disponible.
    """
    candidatos = []

    for ramo in RAMOS:
        evaluacion = ramo["fecha_evaluacion"]
        if evaluacion <= HOY:
            continue
        items     = ramo["items"]
        dias_disp = _dias_entre(HOY, evaluacion)
        paso      = max(len(items), len(dias_disp) // 3) // len(items)

        for i, item in enumerate(items):
            historial = sorted(progreso.get(item["nombre"], []))
            if historial:
                primer_dia = historial[0]
            else:
                if len(dias_disp) < len(items):
                    raise ValueError(f"[{ramo['sigla']}] Sin días suficientes para '{item['nombre']}'.")
                primer_dia = dias_disp[i * paso]
                candidatos.append((primer_dia, _sesion(item, ramo, "Estudio inicial")))

            for j, intervalo in enumerate(_intervalos_adaptativos(primer_dia, evaluacion), 1):
                fecha = primer_dia + timedelta(days=intervalo)
                if fecha >= HOY:
                    candidatos.append((fecha, _sesion(item, ramo, f"Repaso {j}")))

    candidatos.sort(key=lambda c: (c[0], c[1]["evaluacion"]))
    return candidatos


def _rellenar_capacidad(schedule: dict, carga: dict, validos: list) -> None:
    """Rellena días por debajo del mínimo de capacidad con repasos libres."""
    for dia in validos:
        minimo    = MIN_FILL_RATIO * CAPACIDAD_POR_DIA[dia.weekday()] - 1e-9
        cap       = CAPACIDAD_POR_DIA[dia.weekday()] + 1e-9
        ya_en_dia = {s["nombre"] for s in schedule.get(dia, [])}
        activos   = sorted((r for r in RAMOS if r["fecha_evaluacion"] > dia),
                           key=lambda r: r["fecha_evaluacion"])
        for r in activos:
            for item in r["items"]:
                if carga[dia] >= minimo:
                    break
                if item["nombre"] not in ya_en_dia and carga[dia] + PESOS[item["tipo"]] <= cap:
                    schedule[dia].append(_sesion(item, r, "Repaso libre", es_relleno=True))
                    carga[dia] += PESOS[item["tipo"]]


def construir_schedule(progreso: dict) -> dict[date, list]:
    evaluacion_global = max(r["fecha_evaluacion"] for r in RAMOS)
    if evaluacion_global <= HOY:
        raise ValueError("Todas las evaluaciones ya pasaron. Actualiza las fechas en config.py.")
    validos = _dias_entre(HOY, evaluacion_global + timedelta(days=1))
    validos_set = set(validos)

    carga:    dict[date, float] = defaultdict(float)
    schedule: dict[date, list]  = defaultdict(list)

    def _primer_hueco(desde: date, peso: float, deadline: date) -> date | None:
        d = desde
        while d < deadline:
            if d in validos_set and carga[d] + peso <= CAPACIDAD_POR_DIA[d.weekday()] + 1e-9:
                return d
            d += timedelta(days=1)
        return None

    omitidos = []
    for ideal, c in _generar_candidatos(progreso):
        dia = _primer_hueco(ideal, c["peso"], c["evaluacion"])
        if dia is None:
            omitidos.append(c)
            continue
        carga[dia] += c["peso"]
        schedule[dia].append(c)

    if omitidos:
        print(f"\n  ⚠  {len(omitidos)} sesión(es) sin espacio antes del examen:")
        for o in omitidos:
            print(f"     · [{o['sigla']}] {o['nombre']} — {o['sesion']}")

    _rellenar_capacidad(schedule, carga, validos)
    return dict(sorted(schedule.items()))


def _carga(sesiones: list) -> float:
    return sum(s["peso"] for s in sesiones)


def _resumen_progreso(progreso: dict) -> None:
    por_dia: dict[date, list] = defaultdict(list)
    for nombre, fechas in progreso.items():
        for f in fechas:
            if f < HOY:
                por_dia[f].append(nombre)
    if not por_dia:
        return

    item_info = {
        item["nombre"]: (ramo["sigla"], item["tipo"])
        for ramo in RAMOS for item in ramo["items"]
    }

    print()
    print("  ┌─ HISTORIAL (ya estudiado) " + "─" * 45)
    for dia in sorted(por_dia):
        print(f"  │  {DIAS_ES[dia.weekday()]} {dia.day:02d}/{dia.month:02d}/{dia.year}")
        for nombre in por_dia[dia]:
            sig, tipo = item_info.get(nombre, ("?", ""))
            print(f"  │    {ICONOS.get(tipo, '·')} [{sig}] ✓  {nombre}  ({PESOS.get(tipo, 0)}u)")
    print("  └" + "─" * 68)
    print()


def imprimir_schedule(schedule: dict, progreso: dict) -> None:
    BAR_W    = 16
    examenes = defaultdict(list)
    for r in RAMOS:
        examenes[r["fecha_evaluacion"]].append(r)
    color_ramo = {r["sigla"]: _COLORES[i % len(_COLORES)] for i, r in enumerate(RAMOS)} if USAR_COLORES else {}

    def _c(sigla, txt):
        col = color_ramo.get(sigla, "")
        return f"{col}{txt}{_RESET}" if col else txt

    print()
    print("═" * 76)
    print("  PLAN DE ESTUDIO MULTI-RAMO — SPACED REPETITION")
    print(f"  Generado para: HOY {DIAS_ES[HOY.weekday()]} {HOY.day} de {MESES_ES[HOY.month]} de {HOY.year}")
    print()
    print("  Cap/día: " + "  ".join(f"{DIAS_ES[d]}={v:.0f}u" for d, v in sorted(CAPACIDAD_POR_DIA.items())))
    print("  Pesos:   " + "  ".join(f"{t}={p}u" for t, p in PESOS.items()))
    print()

    for r in RAMOS:
        ev = r["fecha_evaluacion"]
        print(f"  {_c(r['sigla'], '[' + r['sigla'] + ']')} {r['nombre']}"
              f"  →  examen {DIAS_ES[ev.weekday()]} {ev.day} de {MESES_ES[ev.month]}")
        for item in r["items"]:
            hist  = progreso.get(item["nombre"], [])
            marca = f"  ✓ estudiado {len(hist)}×" if hist else ""
            print(f"      {ICONOS.get(item['tipo'], '·')} #{IDX[item['nombre']]:02d}  {item['nombre']}"
                  f"  [{item['tipo']}, {PESOS[item['tipo']]}u]{marca}")
        print()

    print("═" * 76)
    _resumen_progreso(progreso)

    for dia in sorted(set(schedule) | set(examenes)):
        for r in examenes.get(dia, []):
            print(f"\n  {'─' * 74}")
            print(f"  {_c(r['sigla'], '🎯  EVALUACIÓN')} "
                  f"{_c(r['sigla'], '[' + r['sigla'] + '] ' + r['nombre'])}"
                  f"  — {DIAS_ES[dia.weekday()]} {dia.day:02d}/{dia.month:02d}")
            print(f"  {'─' * 74}\n")

        if dia not in schedule:
            continue

        cap_dia   = CAPACIDAD_POR_DIA[dia.weekday()]
        carga_dia = _carga(schedule[dia])
        bloques   = round(min(carga_dia / cap_dia, 1.0) * BAR_W)
        barra     = "▓" * bloques + "░" * (BAR_W - bloques)
        proximo   = min(((ev - dia).days for ev in examenes if ev > dia), default=None)
        prox_str  = f"  —  próx. examen en {proximo}d" if proximo is not None else ""

        print(f"  {DIAS_ES[dia.weekday()]} {dia.day:02d}/{dia.month:02d}"
              f"  │{barra}│ {carga_dia:.1f}/{cap_dia:.0f}u ({carga_dia/cap_dia*100:.0f}%){prox_str}")

        for s in sorted(schedule[dia], key=lambda x: (x["es_relleno"], x["sigla"])):
            tag        = _c(s["sigla"], "[" + s["sigla"] + "]")
            sesion_str = ("~ " + s["sesion"]) if s["es_relleno"] else s["sesion"]
            print(f"    {ICONOS.get(s['tipo'], '·')} {tag} #{IDX[s['nombre']]:02d}"
                  f"  {sesion_str:<18}  {s['nombre']}")
        print()

    print("═" * 76)

    todas_sesiones   = [s for ss in schedule.values() for s in ss]
    sesiones_prog    = [s for s in todas_sesiones if not s["es_relleno"]]
    sesiones_relleno = [s for s in todas_sesiones if s["es_relleno"]]
    total_cap        = sum(CAPACIDAD_POR_DIA[d.weekday()] for d in schedule) or 1
    total_usado      = _carga(todas_sesiones)
    items_con_prog   = sum(1 for nombre in IDX if nombre in progreso)

    print()
    print("  Resumen:")
    print(f"    Días con estudio      : {len(schedule)}")
    print(f"    Sesiones programadas  : {len(sesiones_prog)}  +  {len(sesiones_relleno)} repasos libres")
    print(f"    Utilización           : {total_usado:.1f}/{total_cap:.0f}u  ({total_usado/total_cap*100:.1f}%)")
    print(f"    Progreso registrado   : {items_con_prog}/{len(IDX)} ítems")
    print()
    print("  Por ramo:")
    for r in RAMOS:
        sig   = r["sigla"]
        ses_r = [s for s in sesiones_prog    if s["sigla"] == sig]
        rel_r = [s for s in sesiones_relleno if s["sigla"] == sig]
        print(f"    {_c(sig, '[' + sig + ']')} {r['nombre']:<32}"
              f"  {len(ses_r):2d} sesiones  +{len(rel_r)} libres  {_carga(ses_r + rel_r):.1f}u")
    print()


def exportar_csv(schedule: dict, path: str = "plan_estudio.csv") -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Fecha", "Día", "Ramo", "Sigla", "#", "Ítem", "Tipo",
                         "Sesión", "Es relleno", "Peso (u)", "Cap. día (u)",
                         "Días para evaluación"])
        for dia, sesiones in schedule.items():
            for s in sesiones:
                writer.writerow([
                    dia.isoformat(), DIAS_ES[dia.weekday()],
                    s["ramo"], s["sigla"], IDX[s["nombre"]],
                    s["nombre"], s["tipo"], s["sesion"],
                    "sí" if s["es_relleno"] else "no",
                    s["peso"], CAPACIDAD_POR_DIA[dia.weekday()],
                    (s["evaluacion"] - dia).days,
                ])
    print(f"  → Plan exportado a: {path}")


# ══════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    try:
        schedule = construir_schedule(PROGRESO)
        imprimir_schedule(schedule, PROGRESO)

        if input("  ¿Exportar plan a CSV? (s/n): ").strip().lower() == "s":
            exportar_csv(schedule)

    except ValueError as e:
        print(f"\n  ⚠ Error: {e}\n")
