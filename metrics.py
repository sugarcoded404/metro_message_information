"""
Módulo de cálculo de métricas y análisis derivados.
Contiene funciones que calculan KPIs y estadísticas.
"""

import pandas as pd
from constants import CAPACIDAD_LINEA_A, PER_TRAIN_CAPACITY
import numpy as np


def calcular_metricas_generales(df):
    """
    Calcula métricas generales del dashboard.
    
    Retorna un diccionario con:
    - total_pax
    - prom_diario
    - hora_pico_val
    - horas_en_riesgo
    - pct_pico
    - linea_top
    - dias_validos
    """
    total_pax = df["pasajeros"].sum()
    prom_diario = df.groupby("fecha")["pasajeros"].sum().mean()
    hora_pico_val = df.groupby("hora")["pasajeros"].mean().idxmax()
    
    horas_criticas = df.groupby("hora")["pasajeros"].mean()
    dias_validos = df["fecha"].nunique()
    linea_top = df.groupby("linea")["pasajeros"].sum().idxmax()
    
    return {
        "total_pax": total_pax,
        "prom_diario": prom_diario,
        "hora_pico_val": hora_pico_val,
        "horas_criticas": horas_criticas,
        "dias_validos": dias_validos,
        "linea_top": linea_top,
    }


def calcular_horas_riesgo(df, umbral_pico):
    """
    Calcula el número de horas en riesgo y el porcentaje de demanda en esas horas.
    """
    horas_criticas = df.groupby("hora")["pasajeros"].mean()
    horas_en_riesgo = (horas_criticas >= umbral_pico).sum()
    pct_pico = (horas_criticas[horas_criticas >= umbral_pico].sum()
                / horas_criticas.sum() * 100)
    
    return horas_en_riesgo, pct_pico


def calcular_horas_alerta(df, umbral_pico):
    """
    Retorna el listado de horas que superan el umbral y sus rangos AM/PM.
    """
    _hora_avg_texto = df.groupby("hora")["pasajeros"].mean()
    _horas_alerta = sorted(_hora_avg_texto[_hora_avg_texto >= umbral_pico].index.tolist())
    _pico_am = [h for h in _horas_alerta if h < 12]
    _pico_pm = [h for h in _horas_alerta if h >= 12]
    _rango_am = f"{min(_pico_am):02d}:00–{max(_pico_am):02d}:00" if _pico_am else "—"
    _rango_pm = f"{min(_pico_pm):02d}:00–{max(_pico_pm):02d}:00" if _pico_pm else "—"
    
    return {
        "horas_alerta": _horas_alerta,
        "rango_am": _rango_am,
        "rango_pm": _rango_pm,
        "pico_am": _pico_am,
        "pico_pm": _pico_pm,
    }


def calcular_ratio_finde_laboral(df):
    """
    Calcula el ratio entre demanda pico laboral vs fin de semana.
    """
    _hora_lab = df[~df["es_finde"]].groupby("hora")["pasajeros"].mean()
    _hora_fin = df[df["es_finde"]].groupby("hora")["pasajeros"].mean()
    _ratio_txt = round(_hora_lab.max() / _hora_fin.max(), 1) if _hora_fin.max() > 0 else "N/D"
    
    return _ratio_txt


def calcular_metricas_linea_a(df_a_hora):
    """
    Calcula métricas de saturación para la Línea A.
    
    Retorna un diccionario con:
    - p75, p95
    - horas_p75, horas_p95, horas_saturadas
    - dias_saturados, max_demanda, utilizacion_max
    - pct_capacidad_p75, pct_capacidad_p95
    """
    p75 = df_a_hora["pasajeros"].quantile(0.75)
    p95 = df_a_hora["pasajeros"].quantile(0.95)
    
    df_a_hora["supera_p75"] = (df_a_hora["pasajeros"] >= p75)
    df_a_hora["supera_p95"] = (df_a_hora["pasajeros"] >= p95)
    df_a_hora["saturado"] = (df_a_hora["pasajeros"] >= CAPACIDAD_LINEA_A)
    
    horas_p75 = int(df_a_hora["supera_p75"].sum())
    horas_p95 = int(df_a_hora["supera_p95"].sum())
    horas_saturadas = int(df_a_hora["saturado"].sum())
    
    dias_saturados = int(df_a_hora[df_a_hora["saturado"]]["fecha"].nunique())
    max_demanda = df_a_hora["pasajeros"].max()
    utilizacion_max = (max_demanda / CAPACIDAD_LINEA_A) * 100
    
    pct_capacidad_p75 = (p75 / CAPACIDAD_LINEA_A) * 100
    pct_capacidad_p95 = (p95 / CAPACIDAD_LINEA_A) * 100
    
    return {
        "p75": p75,
        "p95": p95,
        "horas_p75": horas_p75,
        "horas_p95": horas_p95,
        "horas_saturadas": horas_saturadas,
        "dias_saturados": dias_saturados,
        "max_demanda": max_demanda,
        "utilizacion_max": utilizacion_max,
        "pct_capacidad_p75": pct_capacidad_p75,
        "pct_capacidad_p95": pct_capacidad_p95,
        "dias_totales": df_a_hora["fecha"].nunique(),
        "dias_sobre_p95": int(df_a_hora[df_a_hora["supera_p95"]]["fecha"].nunique()),
        "dias_sobre_capacidad": int(df_a_hora[df_a_hora["saturado"]]["fecha"].nunique()),
    }


def calcular_trenes_y_costos(df_a_hora, capacidad_linea_a, trenes_operativos, coste_por_tren_hora, per_train_capacity=None):
    """
    Calcula el número mínimo de trenes requeridos por hora para atender la demanda
    y los costos operativos asociados.

    Retorna un diccionario con series y métricas agregadas:
    - per_train_capacity
    - trenes_necesarios_por_hora (Series)
    - horas_sobre_capacidad (int)
    - trenes_max_necesarios (int)
    - coste_total_hora (Series)
    - coste_necesario_hora (Series)
    - coste_waste_hora (Series)
    - coste_total_periodo, coste_waste_total
    """
    # capacidad por tren: usar argumento o la constante por defecto
    if per_train_capacity is None:
        per_train_capacity = PER_TRAIN_CAPACITY

    # demanda por hora (promedio por hora)
    hora_prom = df_a_hora.groupby("hora")["pasajeros"].mean()

    # trenes necesarios por hora (siempre al menos 1)
    trenes_necesarios = np.ceil(hora_prom / per_train_capacity).astype(int)
    trenes_necesarios[trenes_necesarios < 1] = 1

    # métricas
    trenes_max_necesarios = int(trenes_necesarios.max())
    horas_sobre_capacidad = int((trenes_necesarios > trenes_operativos).sum())

    # costos por hora
    coste_total_hora = trenes_operativos * coste_por_tren_hora
    coste_necesario_hora = trenes_necesarios * coste_por_tren_hora
    coste_waste_hora = (trenes_operativos - trenes_necesarios).clip(lower=0) * coste_por_tren_hora

    # totales para el periodo analizado (sumando horas presentes en hora_prom index)
    horas_contadas = len(hora_prom)
    coste_total_periodo = float(coste_total_hora * horas_contadas)
    coste_waste_total = float(coste_waste_hora.sum())

    return {
        "per_train_capacity": per_train_capacity,
        "trenes_necesarios_por_hora": trenes_necesarios,
        "trenes_max_necesarios": trenes_max_necesarios,
        "horas_sobre_capacidad": horas_sobre_capacidad,
        "coste_total_hora": coste_total_hora,
        "coste_necesario_hora": coste_necesario_hora,
        "coste_waste_hora": coste_waste_hora,
        "coste_total_periodo": coste_total_periodo,
        "coste_waste_total": float(coste_waste_hora.sum()),
    }


def generar_mensaje_interpretacion(utilizacion_max):
    """
    Genera un mensaje de interpretación basado en el % de utilización máxima.
    """
    if utilizacion_max < 70:
        mensaje = (
            f"La máxima demanda observada utiliza solo "
            f"{utilizacion_max:.1f}% de la capacidad. "
            f"No existe evidencia de saturación operativa."
        )
    elif utilizacion_max < 90:
        mensaje = (
            f"La Línea A alcanza hasta "
            f"{utilizacion_max:.1f}% de utilización. "
            f"Existen periodos de alta ocupación que deben monitorearse."
        )
    else:
        mensaje = (
            f"La Línea A alcanza "
            f"{utilizacion_max:.1f}% de utilización. "
            f"Existe riesgo de saturación durante las horas pico."
        )
    
    return mensaje


def construir_paleta(lineas: tuple, paleta_base) -> dict:
    """
    Asigna un color único a cada línea presente en el dataset.
    """
    return {linea: paleta_base[i % len(paleta_base)]
            for i, linea in enumerate(sorted(lineas))}
