"""
Módulo de configuración del sidebar y lógica de filtros.
"""

import streamlit as st
import pandas as pd


def configurar_sidebar(df_raw):
    """
    Construye el sidebar con todos los filtros.
    
    Retorna un diccionario con:
    - lineas_sel
    - tipos_sel
    - rango_fecha
    - umbral_pico
    - incluir_finde
    """
    with st.sidebar:
        st.title("⚙️ Configuración")
        st.markdown("---")

        st.markdown("### Filtros")

        lineas_disp = sorted(df_raw["linea"].unique())
        lineas_sel = st.multiselect("Líneas", lineas_disp, default=lineas_disp)

        tipos_disp = sorted(df_raw["tipo_linea"].unique())
        tipos_sel = st.multiselect("Tipo de línea", tipos_disp, default=tipos_disp)

        rango_fecha = st.date_input(
            "Rango de fechas",
            value=[df_raw["fecha"].min(), df_raw["fecha"].max()],
            min_value=df_raw["fecha"].min().date(),
            max_value=df_raw["fecha"].max().date(),
        )

        # ── Umbral dinámico: percentil 75 de la demanda horaria real ─────────────
        hora_avg_raw = df_raw.groupby("hora")["pasajeros"].mean()
        umbral_sugerido = int(hora_avg_raw.quantile(0.75))
        umbral_min = int(hora_avg_raw.min())
        umbral_max = int(hora_avg_raw.max())
        paso = max(100, round((umbral_max - umbral_min) / 50, -2))

        umbral_pico = st.slider(
            "Umbral de alerta (pasajeros/hora)",
            min_value=umbral_min,
            max_value=umbral_max,
            value=umbral_sugerido,
            step=int(paso),
            help=(
                f"Valor por defecto: percentil 75 de la demanda horaria = **{umbral_sugerido:,} pax/h**. "
                f"Las horas que superen este umbral se marcan en rojo. "
                f"Ajusta según el criterio operativo de tu sistema."
            ),
        )
        st.caption(f"📊 Umbral sugerido (p75): {umbral_sugerido:,} pax/h")

        incluir_finde = st.checkbox("Incluir fines de semana", value=True)

        st.markdown("---")
        st.caption("Dashboard · Transporte Masivo 2023")

    return {
        "lineas_sel": lineas_sel,
        "tipos_sel": tipos_sel,
        "rango_fecha": rango_fecha,
        "umbral_pico": umbral_pico,
        "incluir_finde": incluir_finde,
    }



