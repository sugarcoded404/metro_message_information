"""
Módulo de generación de gráficos para el Dashboard de Transporte.
Contiene funciones que generan visualizaciones con Plotly.
"""

import pandas as pd
import plotly.express as px
from constants import COLOR_PICO, COLOR_NORMAL, COLOR_NORMAL_DARK, COLOR_UMBRAL


def chart_promedio_por_hora(df, colores_linea, lineas_sel):
    """
    Gráfico de barras apiladas: pasajeros promedio por hora del día.
    """
    hora_linea = (df.groupby(["hora", "linea"])["pasajeros"]
                  .mean().reset_index())
    colores_plot = {l: colores_linea.get(l, "#888780") for l in lineas_sel}

    fig = px.bar(
        hora_linea, x="hora", y="pasajeros", color="linea",
        color_discrete_map=colores_plot,
        labels={"hora": "Hora del día", "pasajeros": "Pax promedio", "linea": "Línea"},
        barmode="stack",
    )
    fig.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        legend=dict(orientation="h", y=-0.15),
        margin=dict(t=20, b=20, l=0, r=0),
        height=320,
    )
    fig.update_xaxes(
        tickmode="array",
        tickvals=list(range(0, 24)),
        ticktext=[f"{h:02d}:00" for h in range(0, 24)],
        gridcolor="#f0f0f0", zeroline=False,
    )
    fig.update_yaxes(gridcolor="#f0f0f0")
    return fig


def chart_comparacion_finde(df):
    """
    Gráfico de líneas: comparación día laboral vs fin de semana.
    """
    comp = (df.groupby(["hora", "es_finde"])["pasajeros"].mean()
            .reset_index())
    comp["Tipo"] = comp["es_finde"].map({True: "Fin de semana", False: "Día laboral"})
    
    fig = px.line(
        comp, x="hora", y="pasajeros", color="Tipo",
        color_discrete_map={"Día laboral": COLOR_NORMAL_DARK, "Fin de semana": COLOR_PICO},
    )
    fig.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(t=10, b=10, l=0, r=0), height=200,
        legend=dict(orientation="h", y=-0.3),
        showlegend=True,
    )
    fig.update_xaxes(
        title="Hora",
        tickmode="array",
        tickvals=list(range(0, 24)),
        ticktext=[f"{h:02d}:00" for h in range(0, 24)],
        gridcolor="#f0f0f0",
    )
    fig.update_yaxes(title="Pax", gridcolor="#f0f0f0")
    return fig


def chart_demanda_ejecutiva(df, umbral_pico, COLOR_PICO_VAL, COLOR_NORMAL_VAL):
    """
    Gráfico de barras ejecutivo: demanda horaria con umbral de alerta.
    """
    hora_avg = df.groupby("hora")["pasajeros"].mean().reset_index()
    hora_avg["categoria"] = hora_avg["pasajeros"].apply(
        lambda v: f"≥ {umbral_pico} pax (alerta)" if v >= umbral_pico else "Operación normal"
    )

    fig = px.bar(
        hora_avg, x="hora", y="pasajeros",
        color="categoria",
        color_discrete_map={
            f"≥ {umbral_pico} pax (alerta)": COLOR_PICO_VAL,
            "Operación normal": COLOR_NORMAL_VAL,
        },
        labels={"hora": "Hora del día", "pasajeros": "Pasajeros promedio/hora", "categoria": ""},
        text="pasajeros",
    )
    fig.update_traces(texttemplate="%{text:.0f}", textposition="outside", textfont_size=10)
    fig.add_hline(
        y=umbral_pico, line_dash="dash",
        line_color=COLOR_UMBRAL, line_width=2,
        annotation_text=f"  Umbral de alerta: {umbral_pico} pax/h",
        annotation_position="top left",
        annotation_font_color=COLOR_UMBRAL,
    )
    fig.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        legend=dict(orientation="h", y=-0.12, x=0),
        margin=dict(t=30, b=20, l=0, r=0), height=400,
        xaxis=dict(
            tickmode="array",
            tickvals=list(range(0, 24)),
            ticktext=[f"{h:02d}:00" for h in range(0, 24)],
            gridcolor="#f0f0f0", zeroline=False,
        ),
        yaxis=dict(gridcolor="#f0f0f0"),
    )
    return fig


def chart_carga_linea_pico(df, horas_alerta, colores_linea):
    """
    Gráfico horizontal: carga relativa por línea en hora pico.
    """
    pax_por_linea_pico = (df[df["hora"].isin(horas_alerta)]
                          .groupby("linea")["pasajeros"].mean().reset_index()
                          .sort_values("pasajeros", ascending=True))
    pax_por_linea_pico.columns = ["linea", "pax_pico"]

    fig = px.bar(
        pax_por_linea_pico, x="pax_pico", y="linea",
        orientation="h",
        color="linea",
        color_discrete_map={l: colores_linea.get(l, "#888780") for l in pax_por_linea_pico["linea"]},
        labels={"pax_pico": "Pasajeros promedio en hora pico", "linea": ""},
        text="pax_pico",
    )
    fig.update_traces(texttemplate="%{text:.0f} pax", textposition="outside")
    fig.update_layout(
        showlegend=False, plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(t=20, b=20, l=0, r=0), height=300,
        xaxis=dict(gridcolor="#f0f0f0"),
    )
    return fig


def chart_distribucion_demanda_linea_a(df_a_hora, p75, p95, CAPACIDAD_LINEA_A, dias_sobre_p95, dias_sobre_capacidad):
    """
    Histograma: distribución de demanda de la Línea A con percentiles y capacidad.
    """
    fig = px.histogram(
        df_a_hora,
        x="pasajeros",
        nbins=60,
        opacity=0.85,
    )

    fig.add_vline(
        x=p75,
        line_dash="dash",
        line_color="#BA7517",
        annotation_text=f"P75<br>{p75:,.0f}",
    )

    fig.add_vline(
        x=p95,
        line_dash="dash",
        line_color="#D85A30",
        annotation_text=(
            f"P95<br>{p95:,.0f}<br>"
            f"{dias_sobre_p95} días"
        ),
    )

    fig.add_vline(
        x=CAPACIDAD_LINEA_A,
        line_color="red",
        line_width=3,
        annotation_text=(
            f"Capacidad<br>{CAPACIDAD_LINEA_A:,.0f}<br>"
            f"{dias_sobre_capacidad} días"
        ),
    )

    fig.update_layout(
        height=550,
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(t=80, b=20, l=0, r=0),
        xaxis_title="Pasajeros por hora",
        yaxis_title="Frecuencia",
        showlegend=False,
    )

    fig.update_yaxes(gridcolor="#f0f0f0")
    fig.update_xaxes(gridcolor="#f0f0f0")

    return fig


def chart_trenes_necesarios(trenes_necesarios_series, trenes_operativos):
    """
    Línea temporal de trenes necesarios por hora vs trenes operativos.
    """
    df_plot = trenes_necesarios_series.reset_index()
    df_plot.columns = ["hora", "trenes_necesarios"]
    fig = px.line(
        df_plot,
        x="hora",
        y="trenes_necesarios",
        markers=True,
        title="Trenes necesarios por hora (Línea A)",
        color_discrete_sequence=[COLOR_NORMAL_DARK],
    )
    fig.add_hline(
        y=trenes_operativos,
        line_dash="dash",
        line_color=COLOR_PICO,
        annotation_text=f"Trenes operativos: {trenes_operativos}",
        annotation_position="top left",
    )
    fig.update_xaxes(tickmode="array", tickvals=list(range(0,24)), ticktext=[f"{h:02d}:00" for h in range(0,24)])
    fig.update_layout(height=350, plot_bgcolor="white", paper_bgcolor="white")
    return fig


def chart_costes_operativos(horas_index, coste_necesario_hora, coste_waste_hora):
    """
    Gráfico apilado de costos por hora: costo necesario vs costo desperdiciado.
    """
    dfc = pd.DataFrame({
        "hora": horas_index,
        "coste_necesario": coste_necesario_hora,
        "coste_waste": coste_waste_hora,
    })
    dfc = dfc.melt(id_vars=["hora"], value_vars=["coste_necesario", "coste_waste"], var_name="tipo", value_name="coste")
    fig = px.bar(dfc, x="hora", y="coste", color="tipo", barmode="stack", title="Costos operativos por hora — Línea A")
    fig.update_xaxes(tickmode="array", tickvals=list(range(0,24)), ticktext=[f"{h:02d}:00" for h in range(0,24)])
    fig.update_layout(height=350, plot_bgcolor="white", paper_bgcolor="white")
    return fig


def chart_trenes_desperdiciados(horas_index, trenes_necesarios_series, trenes_desplegados):
    """
    Gráfico apilado por hora: trenes necesarios vs trenes desperdiciados (unidades de trenes).
    - `horas_index`: lista de horas (0-23)
    - `trenes_necesarios_series`: Serie indexada por hora con trenes necesarios
    - `trenes_desplegados`: número entero de trenes desplegados en todas las horas (p.ej. el máximo necesario en pico)
    """
    dfn = trenes_necesarios_series.reset_index()
    dfn.columns = ["hora", "trenes_necesarios"]
    dfn["trenes_desplegados"] = trenes_desplegados
    dfn["trenes_desperdiciados"] = (dfn["trenes_desplegados"] - dfn["trenes_necesarios"]).clip(lower=0)

    dfm = dfn.melt(id_vars=["hora"], value_vars=["trenes_necesarios", "trenes_desperdiciados"],
                   var_name="tipo", value_name="trenes")
    dfm["tipo"] = dfm["tipo"].map({
        "trenes_necesarios": "Trenes necesarios",
        "trenes_desperdiciados": "Trenes desperdiciados",
    })

    fig = px.bar(
        dfm,
        x="hora",
        y="trenes",
        color="tipo",
        barmode="stack",
        title="Trenes necesarios vs desperdiciados por hora (Línea A)",
        color_discrete_map={"Trenes necesarios": COLOR_NORMAL_DARK, "Trenes desperdiciados": COLOR_PICO}
    )
    fig.update_xaxes(tickmode="array", tickvals=list(range(0,24)), ticktext=[f"{h:02d}:00" for h in range(0,24)])
    fig.update_layout(height=350, plot_bgcolor="white", paper_bgcolor="white")
    fig.update_yaxes(title_text="Trenes (unidades)")
    return fig
