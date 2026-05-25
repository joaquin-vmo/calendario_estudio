# Calendario de Estudio — Spaced Repetition

Genera un plan de estudio personalizado usando **repetición espaciada**: los temas que estudias hoy se vuelven a repasar en intervalos que aumentan con el tiempo (1 → 3 → 7 → 14 días…), ajustados automáticamente al tiempo disponible antes de tu evaluación.

---

## Requisitos

**Python 3.10 o superior.** Si no lo tienes instalado:
- [Descargar Python](https://www.python.org/downloads/) → instala la versión más reciente
- Durante la instalación en Windows, marca la opción **"Add Python to PATH"**

Para verificar que quedó bien instalado, abre una terminal y escribe:
```
python --version
```

---

## Instalación

1. Descarga este repositorio: botón verde **Code → Download ZIP**
2. Descomprime la carpeta donde quieras
3. Abre una terminal dentro de esa carpeta

> **¿Cómo abro una terminal aquí?**
> - **Windows**: dentro de la carpeta, haz clic en la barra de dirección del Explorador, escribe `cmd` y presiona Enter
> - **Mac**: clic derecho en la carpeta → *Abrir Terminal aquí* (o búscala en Spotlight)

---

## Estructura del proyecto

```
calendario_estudio/
├── calendario.py    ← ejecuta este archivo (no necesitas editarlo)
├── config.py        ← tus ramos y configuración personal
├── progreso.py      ← lo que ya estudiaste
└── README.md        ← este archivo
```

---

## Paso 1 — Configura tus ramos (`config.py`)

Abre `config.py` con cualquier editor de texto (Bloc de notas, VS Code, etc.) y edita la sección `RAMOS` con tus materias.

**Ejemplo:**
```python
RAMOS = [
    {
        "nombre":           "Microeconomía",
        "sigla":            "MICRO",
        "fecha_evaluacion": date(2026, 7, 10),   # date(año, mes, día)
        "items": [
            {"nombre": "Clase 1",     "tipo": "clase"},
            {"nombre": "Clase 2",     "tipo": "clase"},
            {"nombre": "Ayudantía 1", "tipo": "ayudantia"},
            {"nombre": "Examen 2024", "tipo": "examen"},
        ],
    },
]
```

Agrega un bloque `{ ... }` por cada ramo, separados por coma. Si tienes un solo ramo, borra los demás.

También ajusta `PESOS` (cuánto "cuesta" estudiar cada tipo de ítem) e `ICONOS` para cada tipo que uses, y `CAPACIDAD_POR_DIA` con cuánto puedes estudiar cada día de la semana.

> Solo necesitas hacer esto **una vez** al inicio del semestre.

---

## Paso 2 — Ejecuta el calendario

**Mac / Linux:**
```
python3 calendario.py
```

**Windows:**
```
python calendario.py
```

El programa muestra tu plan de estudio en la terminal. Al final te pregunta si quieres exportarlo a un archivo `.csv` que puedes abrir en Excel.

---

## Paso 3 — Registra tu progreso (`progreso.py`)

Cada vez que estudies algo, agrega la fecha en `progreso.py`. El formato es `"AAAA-MM-DD"` (año-mes-día).

```python
PROGRESO = {
    "Clase 1":     ["2026-05-20"],                      # estudiado el 20 de mayo
    "Clase 2":     ["2026-05-21", "2026-05-24"],        # estudiado y repasado
    "Ayudantía 1": ["2026-05-22"],
}
```

- El nombre debe coincidir **exactamente** con el que pusiste en `config.py`
- La primera fecha es el punto de partida para calcular cuándo repasar
- Los repasos que ya hiciste se omiten automáticamente del plan futuro
- Si registras algo para **hoy**, el calendario parte desde mañana

Luego vuelve a ejecutar `calendario.py` para ver el plan actualizado.

---

## Problemas frecuentes

**`python3: command not found` (Mac)**
Prueba con `python calendario.py` o instala Python desde [python.org](https://www.python.org/downloads/).

**`python: command not found` (Windows)**
Reinstala Python y asegúrate de marcar "Add Python to PATH" durante la instalación.

**`ModuleNotFoundError: No module named 'config'`**
Estás ejecutando el script desde otra carpeta. Asegúrate de que la terminal esté dentro de la carpeta `calendario_estudio/`.

**Los colores no se ven bien en la terminal**
Abre `config.py` y cambia `USAR_COLORES = True` a `USAR_COLORES = False`.
