"""
Módulo de carga y preparación de datos.
"""

import pandas as pd
import streamlit as st
from constants import PARQUET_PATH


@st.cache_data
def cargar_datos():
    """
    Lee el parquet desde data/trusted.parquet y normaliza columnas.
    """
    if not PARQUET_PATH.exists():
        st.error(
            f"No se encontró el archivo `{PARQUET_PATH}`. "
            "Asegúrate de que exista la carpeta `data/` con el archivo `trusted.parquet` "
            "en el mismo directorio donde corres Streamlit."
        )
        st.stop()

    df = pd.read_parquet(PARQUET_PATH)

    # ── Normalización de tipos ────────────────────────────────────────────────
    df["fecha"]     = pd.to_datetime(df["fecha"])
    df["hora"]      = df["hora"].astype(int)
    df["pasajeros"] = pd.to_numeric(df["pasajeros"], errors="coerce")
    df["TOTAL"]     = pd.to_numeric(df["TOTAL"],     errors="coerce")
    df["mes"]       = df["fecha"].dt.month
    df["mes_nombre"]= df["fecha"].dt.strftime("%b")
    df["dia_semana"]= df["fecha"].dt.day_name()
    df["semana"]    = df["fecha"].dt.isocalendar().week.astype(int)
    df["es_finde"]  = df["fecha"].dt.weekday >= 5
    return df


def filtrar_datos(df, lineas_sel, tipos_sel, rango_fecha, incluir_finde):
    """
    Aplica los filtros seleccionados al dataframe.
    """
    df_filtrado = df.copy()
    df_filtrado = df_filtrado[df_filtrado["linea"].isin(lineas_sel)]
    df_filtrado = df_filtrado[df_filtrado["tipo_linea"].isin(tipos_sel)]

    if len(rango_fecha) == 2:
        df_filtrado = df_filtrado[(df_filtrado["fecha"] >= pd.to_datetime(rango_fecha[0])) &
                                  (df_filtrado["fecha"] <= pd.to_datetime(rango_fecha[1]))]

    if not incluir_finde:
        df_filtrado = df_filtrado[~df_filtrado["es_finde"]]

    return df_filtrado


def preparar_datos_linea_a(df, df_raw):
    """
    Busca y prepara datos de la Línea A para análisis de saturación.
    """
    df_a = df[
        df["linea"]
        .astype(str)
        .str.upper()
        .str.contains("A", na=False)
    ].copy()

    if len(df_a) == 0:
        return None

    df_a_hora = (
        df_a
        .groupby(["fecha", "hora"], as_index=False)["pasajeros"]
        .sum()
    )

    return df_a_hora
