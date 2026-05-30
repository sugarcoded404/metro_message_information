"""
Constantes y configuración global del Dashboard de Transporte.
"""

# ─── COLORES ──────────────────────────────────────────────────────────────────
_PALETA_BASE = [
    "#D85A30", "#1D9E75", "#378ADD", "#EF9F27", "#534AB7",
    "#E24B4A", "#639922", "#C45AB3", "#0F6E56", "#BA7517",
    "#185FA5", "#993C1D", "#3B6D11", "#7F77DD", "#0C447C",
    "#4B1528", "#D4537E", "#1D9E75", "#F0997B", "#2C2C2A",
]

COLOR_PICO   = "#D85A30"
COLOR_NORMAL = "#9FE1CB"
COLOR_NORMAL_DARK = "#1D9E75"
COLOR_UMBRAL = "#BA7517"

# ─── CAPACIDADES ──────────────────────────────────────────────────────────────
CAPACIDAD_LINEA_A = 97306
VEHICULOS_LINEA_A = 60
VEHICULOS_LINEA_B = 6

# Capacidad máxima por tren (personas)
PER_TRAIN_CAPACITY = 900

# ─── RUTAS ────────────────────────────────────────────────────────────────────
from pathlib import Path
PARQUET_PATH = Path("data/trusted.parquet")
