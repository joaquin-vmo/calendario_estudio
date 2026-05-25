"""
config.py — Edita este archivo con tus ramos y preferencias.
Solo necesitas tocarlo una vez al inicio del semestre.
"""

from datetime import date

# ══════════════════════════════════════════════════════════════════
#  TUS RAMOS
#  Agrega un bloque por cada ramo. Los "items" son las cosas que
#  vas a estudiar (clases, apuntes, ayudantías, exámenes, etc.).
# ══════════════════════════════════════════════════════════════════

RAMOS = [
    {
        "nombre":           "Economía Laboral",
        "sigla":            "LAB",
        "fecha_evaluacion": date(2026, 6, 24),   # date(año, mes, día)
        "items": [
            {"nombre": "Clase 1",  "tipo": "clase_lab"},
            {"nombre": "Clase 2",  "tipo": "clase_lab"},
            {"nombre": "Clase 3",  "tipo": "clase_lab"},
            {"nombre": "Clase 4",  "tipo": "clase_lab"},
            {"nombre": "Clase 5",  "tipo": "clase_lab"},
            {"nombre": "Clase 6",  "tipo": "clase_lab"},
            {"nombre": "Clase 7",  "tipo": "clase_lab"},
            {"nombre": "Clase 8",  "tipo": "clase_lab"},
            {"nombre": "Clase 9",  "tipo": "clase_lab"},
            {"nombre": "Clase 10", "tipo": "clase_lab"},
        ],
    },
    {
        "nombre":           "Econometría Aplicada",
        "sigla":            "ECO",
        "fecha_evaluacion": date(2026, 6, 24),
        "items": [
            {"nombre": "Ayudantía 9",    "tipo": "ayudantia_eco"},
            {"nombre": "Ayudantía 10",   "tipo": "ayudantia_eco"},
            {"nombre": "Ayudantía 11",   "tipo": "ayudantia_eco"},
            {"nombre": "Apunte 5.1",     "tipo": "apunte_eco"},
            {"nombre": "Apunte 5.2-5.4", "tipo": "apunte_eco"},
            {"nombre": "Apunte 6",       "tipo": "apunte_eco"},
            {"nombre": "Apunte 7",       "tipo": "apunte_eco"},
            {"nombre": "Apunte 8.1",     "tipo": "apunte_eco"},
            {"nombre": "Apunte 8.2",     "tipo": "apunte_eco"},
            {"nombre": "Apunte 9",       "tipo": "apunte_eco"},
            {"nombre": "Examen 2025",    "tipo": "examen_eco"},
            {"nombre": "Examen 2024",    "tipo": "examen_eco"},
            {"nombre": "Examen 2023",    "tipo": "examen_eco"},
        ],
    },
]

# ══════════════════════════════════════════════════════════════════
#  PESOS
#  Cuántas "unidades de estudio" cuenta cada tipo de ítem.
#  Útil para reflejar que algunos materiales toman más tiempo.
# ══════════════════════════════════════════════════════════════════

PESOS = {
    "clase_lab":     1,
    "ayudantia_eco": 1,
    "apunte_eco":    1,
    "examen_eco":    2,   # los exámenes cuentan el doble
}

# ══════════════════════════════════════════════════════════════════
#  ÍCONOS (opcional, solo para la visualización en terminal)
#  Si agregas un tipo nuevo en RAMOS, agrega su ícono aquí.
# ══════════════════════════════════════════════════════════════════

ICONOS = {
    "clase_lab":     "🗒️",
    "ayudantia_eco": "🧾",
    "apunte_eco":    "📕",
    "examen_eco":    "📝",
}

# ══════════════════════════════════════════════════════════════════
#  CAPACIDAD POR DÍA
#  Cuántas unidades de estudio puedes hacer cada día de la semana.
#  0 = Lunes, 1 = Martes, ..., 6 = Domingo
# ══════════════════════════════════════════════════════════════════

CAPACIDAD_POR_DIA = {
    0: 3,   # Lunes
    1: 1,   # Martes
    2: 5,   # Miércoles
    3: 4,   # Jueves
    4: 6,   # Viernes
    5: 6,   # Sábado
    6: 6,   # Domingo
}

# ══════════════════════════════════════════════════════════════════
#  OPCIONES AVANZADAS (no es necesario cambiarlas)
# ══════════════════════════════════════════════════════════════════

INTERVALOS_BASE = [1, 3, 7, 14]   # días entre repasos (se extienden automáticamente)
MIN_FILL_RATIO  = 0.5              # fracción mínima de capacidad diaria a usar
SKIP_WEEKENDS   = False            # True para no programar sábado ni domingo
USAR_COLORES    = True             # False si tu terminal no muestra colores bien
