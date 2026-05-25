"""
calendario.py — Motor de spaced repetition. No necesitas editar este archivo.

  · Tus ramos y configuración → config.py
  · Lo que ya estudiaste      → progreso.py
"""

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
MESES_ES = {
    1: "enero",    2: "febrero",   3: "marzo",      4: "abril",
    5: "mayo",     6: "junio",     7: "julio",       8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}


def _calcular_hoy(progreso: dict) -> date:
    hoy     = date.today()
    cerrado = any(hoy in fechas for fechas in progreso.values())
    return hoy + timedelta(days=1) if cerrado else hoy


HOY = _calcular_hoy(PROGRESO)


def _dias_entre(inicio: date, fin: date) -> list[date]:
    dias = [inicio + timedelta(days=i) for i in range((fin - inicio).days)]
    return [d for d in dias if not (SKIP_WEEKENDS and d.weekday() >= 5)]


def _intervalos_adaptativos(primer_dia: date, evaluacion: date) -> list[int]:
    """Extiende INTERVALOS_BASE con factor ×1.8 hasta cubrir el período al examen."""
    margen     = (evaluacion - primer_dia).days - 2
    intervalos = [i for i in INTERVALOS_BASE if i < margen]
    if not intervalos:
        return []
    ultimo = intervalos[-1]
    while (siguiente := round(ultimo * 1.8)) < margen:
        intervalos.append(siguiente)
        ultimo = siguiente
    return intervalos


def _nueva_sesion(ideal: date, nombre_sesion: str, item: dict, ramo: dict) -> dict:
    return {
        "nombre":     item["nombre"],
        "tipo":       item["tipo"],
        "ramo":       ramo["nombre"],
        "sigla":      ramo["sigla"],
        "sesion":     nombre_sesion,
        "peso":       PESOS[item["tipo"]],
        "evaluacion": ramo["fecha_evaluacion"],
        "es_relleno": False,
        "completado": False,
        "_ideal":     ideal,
    }


def _generar_candidatos(progreso: dict) -> list[dict]:
    """
    Genera sesiones futuras para cada ítem.
    Con historial: ancla en la primera fecha real, omite repasos pasados.
    Sin historial: distribuye los ítems uniformemente en el tiempo disponible.
    """
    candidatos = []

    for ramo in RAMOS:
        evaluacion = ramo["fecha_evaluacion"]
        items      = ramo["items"]
        dias_disp  = _dias_entre(HOY, evaluacion)
        n          = len(items)
        paso       = max(1, max(n, len(dias_disp) // 3) // n)

        for i, item in enumerate(items):
            historial  = sorted(progreso.get(item["nombre"], []))
            primer_dia = historial[0] if historial else dias_disp[min(i * paso, len(dias_disp) - 1)]

            if not historial:
                if len(dias_disp) < n:
                    raise ValueError(f"[{ramo['sigla']}] Sin días suficientes para '{item['nombre']}'.")
                candidatos.append(_nueva_sesion(primer_dia, "Estudio inicial", item, ramo))

            for j, intervalo in enumerate(_intervalos_adaptativos(primer_dia, evaluacion)):
                fecha = primer_dia + timedelta(days=intervalo)
                if fecha >= HOY:
                    candidatos.append(_nueva_sesion(fecha, f"Repaso {j + 1}", item, ramo))

    candidatos.sort(key=lambda c: (c["_ideal"], c["evaluacion"]))
    return candidatos


def _rellenar_capacidad(schedule: dict, carga: dict, validos: set) -> None:
    """Rellena días por debajo del mínimo de capacidad con repasos libres."""
    for dia in sorted(validos):
        if dia < HOY:
            continue
        cap           = CAPACIDAD_POR_DIA[dia.weekday()]
        ramos_activos = sorted(
            [r for r in RAMOS if r["fecha_evaluacion"] > dia],
            key=lambda r: r["fecha_evaluacion"],
        )
        if not ramos_activos:
            continue

        pool      = [(r, item) for r in ramos_activos for item in r["items"]]
        ya_en_dia = {s["nombre"] for s in schedule.get(dia, [])}

        while carga[dia] < MIN_FILL_RATIO * cap - 1e-9:
            added = False
            for r, item in pool:
                peso = PESOS[item["tipo"]]
                if item["nombre"] not in ya_en_dia and carga[dia] + peso <= cap + 1e-9:
                    schedule[dia].append({
                        "nombre": item["nombre"], "tipo": item["tipo"],
                        "ramo": r["nombre"], "sigla": r["sigla"],
                        "sesion": "Repaso libre", "peso": peso,
                        "evaluacion": r["fecha_evaluacion"],
                        "es_relleno": True, "completado": False,
                    })
                    carga[dia] += peso
                    ya_en_dia.add(item["nombre"])
                    added = True
                    if carga[dia] >= MIN_FILL_RATIO * cap - 1e-9:
                        break
            if not added:
                break


def construir_schedule(progreso: dict) -> tuple[dict, dict]:
    evaluacion_global = max(r["fecha_evaluacion"] for r in RAMOS)
    validos = set(_dias_entre(HOY, evaluacion_global + timedelta(days=1)))

    carga:    dict[date, float] = defaultdict(float)
    schedule: dict[date, list]  = defaultdict(list)

    def _primer_hueco(desde: date, peso: float, deadline: date) -> date | None:
        d = desde
        while d < deadline:
            if d in validos and carga[d] + peso <= CAPACIDAD_POR_DIA[d.weekday()] + 1e-9:
                return d
            d += timedelta(days=1)
        return None

    omitidos = []
    for c in _generar_candidatos(progreso):
        ideal = c.pop("_ideal")
        dia   = _primer_hueco(ideal, c["peso"], c["evaluacion"])
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
    return dict(sorted(schedule.items())), dict(carga)


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


def imprimir_schedule(schedule: dict, carga: dict, progreso: dict) -> None:
    BAR_W    = 16
    examenes = {r["fecha_evaluacion"]: r for r in RAMOS}
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

    all_items = []
    for r in RAMOS:
        ev = r["fecha_evaluacion"]
        print(f"  {_c(r['sigla'], '[' + r['sigla'] + ']')} {r['nombre']}"
              f"  →  examen {DIAS_ES[ev.weekday()]} {ev.day} de {MESES_ES[ev.month]}")
        for item in r["items"]:
            all_items.append((r["sigla"], item))
            hist  = progreso.get(item["nombre"], [])
            marca = f"  ✓ estudiado {len(hist)}×" if hist else ""
            print(f"      {ICONOS.get(item['tipo'], '·')} #{len(all_items):02d}  {item['nombre']}"
                  f"  [{item['tipo']}, {PESOS[item['tipo']]}u]{marca}")
        print()

    print("═" * 76)
    _resumen_progreso(progreso)

    idx_global   = {item["nombre"]: i + 1 for i, (_, item) in enumerate(all_items)}
    todas_fechas = sorted(set(schedule) | set(examenes))

    for dia in todas_fechas:
        if dia in examenes:
            r = examenes[dia]
            print(f"\n  {'─' * 74}")
            print(f"  {_c(r['sigla'], '🎯  EVALUACIÓN')} "
                  f"{_c(r['sigla'], '[' + r['sigla'] + '] ' + r['nombre'])}"
                  f"  — {DIAS_ES[dia.weekday()]} {dia.day:02d}/{dia.month:02d}")
            print(f"  {'─' * 74}\n")

        if dia not in schedule:
            continue

        cap_dia   = CAPACIDAD_POR_DIA[dia.weekday()]
        carga_dia = carga.get(dia, 0.0)
        bloques   = round(min(carga_dia / cap_dia, 1.0) * BAR_W)
        barra     = "▓" * bloques + "░" * (BAR_W - bloques)
        proximos  = sorted((ev - dia).days for ev in examenes if ev > dia)
        prox_str  = f"  —  próx. examen en {proximos[0]}d" if proximos else ""

        print(f"  {DIAS_ES[dia.weekday()]} {dia.day:02d}/{dia.month:02d}"
              f"  │{barra}│ {carga_dia:.1f}/{cap_dia:.0f}u ({carga_dia/cap_dia*100:.0f}%){prox_str}")

        for s in sorted(schedule[dia], key=lambda x: (x["es_relleno"], x["sigla"])):
            tag        = _c(s["sigla"], "[" + s["sigla"] + "]")
            sesion_str = ("~ " + s["sesion"]) if s["es_relleno"] else s["sesion"]
            print(f"    {ICONOS.get(s['tipo'], '·')} {tag} #{idx_global[s['nombre']]:02d}"
                  f"  {sesion_str:<18}  {s['nombre']}")
        print()

    print("═" * 76)

    todas_sesiones   = [s for ss in schedule.values() for s in ss]
    sesiones_prog    = [s for s in todas_sesiones if not s["es_relleno"]]
    sesiones_relleno = [s for s in todas_sesiones if s["es_relleno"]]
    total_cap        = sum(CAPACIDAD_POR_DIA[d.weekday()] for d in schedule)
    total_usado      = sum(carga.get(d, 0) for d in schedule)
    items_con_prog   = sum(1 for r in RAMOS for item in r["items"] if item["nombre"] in progreso)
    total_items      = sum(len(r["items"]) for r in RAMOS)

    print()
    print("  Resumen:")
    print(f"    Días con estudio      : {len(schedule)}")
    print(f"    Sesiones programadas  : {len(sesiones_prog)}  +  {len(sesiones_relleno)} repasos libres")
    print(f"    Utilización           : {total_usado:.1f}/{total_cap:.0f}u  ({total_usado/total_cap*100:.1f}%)")
    print(f"    Progreso registrado   : {items_con_prog}/{total_items} ítems")
    print()
    print("  Por ramo:")
    for r in RAMOS:
        sig   = r["sigla"]
        ses_r = [s for s in sesiones_prog    if s["sigla"] == sig]
        rel_r = [s for s in sesiones_relleno if s["sigla"] == sig]
        u_r   = sum(s["peso"] for s in ses_r + rel_r)
        print(f"    {_c(sig, '[' + sig + ']')} {r['nombre']:<32}"
              f"  {len(ses_r):2d} sesiones  +{len(rel_r)} libres  {u_r:.1f}u")
    print()


def exportar_csv(schedule: dict, path: str = "plan_estudio.csv") -> None:
    import csv
    all_items  = [(r["sigla"], item) for r in RAMOS for item in r["items"]]
    idx_global = {item["nombre"]: i + 1 for i, (_, item) in enumerate(all_items)}

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Fecha", "Día", "Ramo", "Sigla", "#", "Ítem", "Tipo",
                         "Sesión", "Es relleno", "Peso (u)", "Cap. día (u)",
                         "Días para evaluación"])
        for dia, sesiones in schedule.items():
            for s in sesiones:
                writer.writerow([
                    dia.strftime("%Y-%m-%d"), DIAS_ES[dia.weekday()],
                    s["ramo"], s["sigla"], idx_global[s["nombre"]],
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
        schedule, carga = construir_schedule(PROGRESO)
        imprimir_schedule(schedule, carga, PROGRESO)

        if input("  ¿Exportar plan a CSV? (s/n): ").strip().lower() == "s":
            exportar_csv(schedule)

    except ValueError as e:
        print(f"\n  ⚠ Error: {e}\n")
