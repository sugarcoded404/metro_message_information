import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path

# ─── CONFIGURACIÓN DE PÁGINA ─────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard Transporte Masivo",
    page_icon="🚇",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── ESTILOS PERSONALIZADOS ───────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 1rem; }
    .metric-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 16px 20px;
        border-left: 4px solid #1D9E75;
    }
    .metric-card.danger { border-left-color: #D85A30; }
    .metric-card.warn   { border-left-color: #BA7517; }
    .insight-box {
        background: #FAECE7;
        border: 1px solid #F0997B;
        border-radius: 10px;
        padding: 14px 18px;
        margin: 12px 0;
    }
    .insight-ok {
        background: #E1F5EE;
        border: 1px solid #5DCAA5;
        border-radius: 10px;
        padding: 14px 18px;
        margin: 12px 0;
    }
    .phase-header {
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #888;
        margin-bottom: 4px;
    }
</style>
""", unsafe_allow_html=True)

# ─── COLORES DE MARCA ─────────────────────────────────────────────────────────
# Paleta base: 20 colores distintos y saturados — se asignan dinámicamente
_PALETA_BASE = [
    "#D85A30", "#1D9E75", "#378ADD", "#EF9F27", "#534AB7",
    "#E24B4A", "#639922", "#C45AB3", "#0F6E56", "#BA7517",
    "#185FA5", "#993C1D", "#3B6D11", "#7F77DD", "#0C447C",
    "#4B1528", "#D4537E", "#1D9E75", "#F0997B", "#2C2C2A",
]

@st.cache_data
def construir_paleta(lineas: tuple) -> dict:
    """Asigna un color único a cada línea presente en el dataset."""
    return {linea: _PALETA_BASE[i % len(_PALETA_BASE)]
            for i, linea in enumerate(sorted(lineas))}

COLOR_PICO   = "#D85A30"
COLOR_NORMAL = "#9FE1CB"
COLOR_UMBRAL = "#BA7517"

# ─── CARGA DE DATOS ───────────────────────────────────────────────────────────
PARQUET_PATH = Path("data/trusted.parquet")

@st.cache_data
def cargar_datos():
    """Lee el parquet desde data/trusted.parquet y normaliza columnas."""
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


# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Configuración")
    st.markdown("---")

    df_raw = cargar_datos()

    st.markdown("### Filtros")

    lineas_disp = sorted(df_raw["linea"].unique())
    lineas_sel  = st.multiselect("Líneas", lineas_disp, default=lineas_disp)

    tipos_disp = sorted(df_raw["tipo_linea"].unique())
    tipos_sel  = st.multiselect("Tipo de línea", tipos_disp, default=tipos_disp)

    rango_fecha = st.date_input(
        "Rango de fechas",
        value=[df_raw["fecha"].min(), df_raw["fecha"].max()],
        min_value=df_raw["fecha"].min().date(),
        max_value=df_raw["fecha"].max().date(),
    )

    # ── Umbral dinámico: percentil 75 de la demanda horaria real ─────────────
    hora_avg_raw   = df_raw.groupby("hora")["pasajeros"].mean()
    umbral_sugerido = int(hora_avg_raw.quantile(0.75))
    umbral_min     = int(hora_avg_raw.min())
    umbral_max     = int(hora_avg_raw.max())
    paso           = max(100, round((umbral_max - umbral_min) / 50, -2))

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

# ─── FILTRADO ─────────────────────────────────────────────────────────────────
df = df_raw.copy()
df = df[df["linea"].isin(lineas_sel)]
df = df[df["tipo_linea"].isin(tipos_sel)]

if len(rango_fecha) == 2:
    df = df[(df["fecha"] >= pd.to_datetime(rango_fecha[0])) &
            (df["fecha"] <= pd.to_datetime(rango_fecha[1]))]

if not incluir_finde:
    df = df[~df["es_finde"]]

if df.empty:
    st.warning("No hay datos con los filtros seleccionados. Ajusta los filtros.")
    st.stop()

# ─── PALETA DINÁMICA ──────────────────────────────────────────────────────────
COLORES_LINEA = construir_paleta(tuple(sorted(df_raw["linea"].unique())))

# ─── MÉTRICAS DERIVADAS ───────────────────────────────────────────────────────
total_pax       = df["pasajeros"].sum()
prom_diario     = df.groupby("fecha")["pasajeros"].sum().mean()
hora_pico_val   = df.groupby("hora")["pasajeros"].mean().idxmax()
horas_criticas  = df.groupby("hora")["pasajeros"].mean()
horas_en_riesgo = (horas_criticas >= umbral_pico).sum()
pct_pico        = (horas_criticas[horas_criticas >= umbral_pico].sum()
                   / horas_criticas.sum() * 100)
linea_top       = df.groupby("linea")["pasajeros"].sum().idxmax()
dias_validos    = df["fecha"].nunique()

# ─── ENCABEZADO ───────────────────────────────────────────────────────────────
st.markdown('<p class="phase-header">Sistema de Transporte Masivo · Análisis de Demanda</p>',
            unsafe_allow_html=True)
st.title("Dashboard de Pasajeros")
st.markdown(
    "**Pregunta de negocio:** ¿Cuándo y en qué líneas se concentra la demanda, "
    "y existe sobredemanda que comprometa la calidad del servicio?"
)

# ─── KPIs ─────────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("Total pasajeros", f"{total_pax/1e6:.2f}M")
k2.metric("Promedio diario", f"{prom_diario:,.0f}")
k3.metric("Hora pico", f"{hora_pico_val}:00 h")
k4.metric("Horas en riesgo/día", f"{horas_en_riesgo}h",
          delta=f"≥{umbral_pico} pax/h", delta_color="inverse")
k5.metric("Demanda en horas pico", f"{pct_pico:.1f}%",
          delta="del total diario", delta_color="inverse")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# FASE 1 · EXPLORACIÓN
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<p class="phase-header">① Fase exploratoria — encontrando señales</p>',
            unsafe_allow_html=True)

col_l, col_r = st.columns([2, 1])

with col_l:
    st.markdown("**Pasajeros promedio por hora del día** (todas las líneas seleccionadas)")
    hora_linea = (df.groupby(["hora", "linea"])["pasajeros"]
                  .mean().reset_index())
    colores_plot = {l: COLORES_LINEA.get(l, "#888780") for l in lineas_sel}

    fig_hora = px.bar(
        hora_linea, x="hora", y="pasajeros", color="linea",
        color_discrete_map=colores_plot,
        labels={"hora": "Hora del día", "pasajeros": "Pax promedio", "linea": "Línea"},
        barmode="stack",
    )
    fig_hora.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        legend=dict(orientation="h", y=-0.15),
        margin=dict(t=20, b=20, l=0, r=0),
        height=320,
    )
    fig_hora.update_xaxes(
        tickmode="array",
        tickvals=list(range(0, 24)),
        ticktext=[f"{h:02d}:00" for h in range(0, 24)],
        gridcolor="#f0f0f0", zeroline=False,
    )
    fig_hora.update_yaxes(gridcolor="#f0f0f0")
    st.plotly_chart(fig_hora, use_container_width=True)

with col_r:
    st.markdown("**Top 5 horas con mayor demanda**")
    top_horas = (df.groupby("hora")["pasajeros"].mean()
                 .sort_values(ascending=False).head(5).reset_index())
    top_horas.columns = ["Hora", "Pax promedio"]
    top_horas["Hora"] = top_horas["Hora"].apply(lambda h: f"{h}:00 h")
    top_horas["Pax promedio"] = top_horas["Pax promedio"].round(0).astype(int)
    st.dataframe(top_horas, hide_index=True, use_container_width=True)

    st.markdown("**Variación día de semana vs fin de semana**")
    comp = (df.groupby(["hora", "es_finde"])["pasajeros"].mean()
            .reset_index())
    comp["Tipo"] = comp["es_finde"].map({True: "Fin de semana", False: "Día laboral"})
    fig_comp = px.line(
        comp, x="hora", y="pasajeros", color="Tipo",
        color_discrete_map={"Día laboral": "#1D9E75", "Fin de semana": "#D85A30"},
    )
    fig_comp.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(t=10, b=10, l=0, r=0), height=200,
        legend=dict(orientation="h", y=-0.3),
        showlegend=True,
    )
    fig_comp.update_xaxes(
        title="Hora",
        tickmode="array",
        tickvals=list(range(0, 24)),
        ticktext=[f"{h:02d}:00" for h in range(0, 24)],
        gridcolor="#f0f0f0",
    )
    fig_comp.update_yaxes(title="Pax", gridcolor="#f0f0f0")
    st.plotly_chart(fig_comp, use_container_width=True)

# Calcular horas pico reales dinámicamente para los textos
_hora_avg_texto = df.groupby("hora")["pasajeros"].mean()
_horas_alerta   = sorted(_hora_avg_texto[_hora_avg_texto >= umbral_pico].index.tolist())
_pico_am        = [h for h in _horas_alerta if h < 12]
_pico_pm        = [h for h in _horas_alerta if h >= 12]
_rango_am       = f"{min(_pico_am):02d}:00–{max(_pico_am):02d}:00" if _pico_am else "—"
_rango_pm       = f"{min(_pico_pm):02d}:00–{max(_pico_pm):02d}:00" if _pico_pm else "—"

_hora_lab  = df[~df["es_finde"]].groupby("hora")["pasajeros"].mean()
_hora_fin  = df[df["es_finde"]].groupby("hora")["pasajeros"].mean()
_ratio_txt = round(_hora_lab.max() / _hora_fin.max(), 1) if _hora_fin.max() > 0 else "N/D"

st.markdown(
    f'<div class="insight-box">⚑ <b>Señal encontrada:</b> doble pico pronunciado '
    f'en la franja <b>{_rango_am}</b> (AM) y <b>{_rango_pm}</b> (PM). '
    f'Los días laborales presentan un pico hasta <b>{_ratio_txt}×</b> '
    f'mayor que los fines de semana en hora punta.</div>',
    unsafe_allow_html=True,
)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# FASE 2 · HALLAZGO
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<p class="phase-header">② Hallazgo central</p>',
            unsafe_allow_html=True)

st.markdown(
    f'<div class="insight-box">'
    f'<b>⚑ Anomalía detectada: sobreconcentración de demanda en ventana de 4 horas</b><br>'
    f'El <b>{pct_pico:.0f}% del total diario de pasajeros</b> se moviliza en apenas '
    f'<b>{horas_en_riesgo} horas críticas</b> (umbral ≥ {umbral_pico} pax/hora). '
    f'La línea con mayor carga es <b>{linea_top}</b>. '
    f'Un incremento marginal de demanda podría generar saturación sistémica en esas franjas horarias.'
    f'</div>',
    unsafe_allow_html=True,
)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# FASE 3 · DASHBOARD EJECUTIVO
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<p class="phase-header">③ Dashboard ejecutivo — argumento visual aclaratorio</p>',
            unsafe_allow_html=True)
st.subheader("El sistema funciona — excepto cuando más lo necesitamos")
st.caption(
    "Mensaje para gerencia: la ventana crítica concentra riesgo operativo. "
    "El resto del día opera con holgura."
)

# KPIs ejecutivos
e1, e2, e3, e4 = st.columns(4)
e1.metric("Horas en riesgo/día",  f"{horas_en_riesgo}h",
          delta="riesgo operativo", delta_color="inverse")
e2.metric("Demanda en esas horas", f"{pct_pico:.0f}%",
          delta="del total diario", delta_color="inverse")
e3.metric("Horas con holgura/día", f"{max(0, 20 - horas_en_riesgo)}h",
          delta="capacidad disponible", delta_color="normal")
e4.metric("Línea más cargada", linea_top)

# Gráfica principal ejecutiva
st.markdown("#### Demanda horaria — dónde está el problema")
hora_avg = df.groupby("hora")["pasajeros"].mean().reset_index()
hora_avg["categoria"] = hora_avg["pasajeros"].apply(
    lambda v: f"≥ {umbral_pico} pax (alerta)" if v >= umbral_pico else "Operación normal"
)

fig_ej = px.bar(
    hora_avg, x="hora", y="pasajeros",
    color="categoria",
    color_discrete_map={
        f"≥ {umbral_pico} pax (alerta)": COLOR_PICO,
        "Operación normal": COLOR_NORMAL,
    },
    labels={"hora": "Hora del día", "pasajeros": "Pasajeros promedio/hora", "categoria": ""},
    text="pasajeros",
)
fig_ej.update_traces(texttemplate="%{text:.0f}", textposition="outside", textfont_size=10)
fig_ej.add_hline(
    y=umbral_pico, line_dash="dash",
    line_color=COLOR_UMBRAL, line_width=2,
    annotation_text=f"  Umbral de alerta: {umbral_pico} pax/h",
    annotation_position="top left",
    annotation_font_color=COLOR_UMBRAL,
)
fig_ej.update_layout(
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
st.plotly_chart(fig_ej, use_container_width=True)

# Carga por línea en hora pico
st.markdown("#### Carga relativa por línea en hora pico")
pax_por_linea_pico = (df[df["hora"].isin(_horas_alerta)]
                      .groupby("linea")["pasajeros"].mean().reset_index()
                      .sort_values("pasajeros", ascending=True))
pax_por_linea_pico.columns = ["linea", "pax_pico"]

fig_carga = px.bar(
    pax_por_linea_pico, x="pax_pico", y="linea",
    orientation="h",
    color="linea",
    color_discrete_map={l: COLORES_LINEA.get(l, "#888780") for l in pax_por_linea_pico["linea"]},
    labels={"pax_pico": "Pasajeros promedio en hora pico", "linea": ""},
    text="pax_pico",
)
fig_carga.update_traces(texttemplate="%{text:.0f} pax", textposition="outside")
fig_carga.update_layout(
    showlegend=False, plot_bgcolor="white", paper_bgcolor="white",
    margin=dict(t=20, b=20, l=0, r=0), height=300,
    xaxis=dict(gridcolor="#f0f0f0"),
)
st.plotly_chart(fig_carga, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# ANÁLISIS DE SATURACIÓN - LÍNEA A
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("---")

CAPACIDAD_LINEA_A = 48653

# Buscar Línea A de forma robusta
df_a = df[
    df["linea"]
    .astype(str)
    .str.upper()
    .str.contains("A", na=False)
].copy()

# Diagnóstico temporal

if len(df_a) == 0:

    st.warning(
        "No se encontraron registros para la Línea A con los filtros actuales."
    )

else:

    # =====================================================
    # AGRUPAR POR FECHA Y HORA
    # =====================================================
    # Esto permite comparar contra la capacidad real
    # de la línea y no contra registros individuales.

    df_a_hora = (
        df_a
        .groupby(["fecha", "hora"], as_index=False)["pasajeros"]
        .sum()
    )

    # =====================================================
    # PERCENTILES
    # =====================================================

    p75 = df_a_hora["pasajeros"].quantile(0.75)
    p95 = df_a_hora["pasajeros"].quantile(0.95)

    # =====================================================
    # SATURACIÓN
    # =====================================================

    df_a_hora["supera_p75"] = (
        df_a_hora["pasajeros"] >= p75
    )

    df_a_hora["supera_p95"] = (
        df_a_hora["pasajeros"] >= p95
    )

    df_a_hora["saturado"] = (
        df_a_hora["pasajeros"] >= CAPACIDAD_LINEA_A
    )

    horas_p75 = int(df_a_hora["supera_p75"].sum())
    horas_p95 = int(df_a_hora["supera_p95"].sum())
    horas_saturadas = int(df_a_hora["saturado"].sum())

    dias_saturados = (
        df_a_hora[df_a_hora["saturado"]]
        ["fecha"]
        .nunique()
    )

    max_demanda = df_a_hora["pasajeros"].max()

    utilizacion_max = (
        max_demanda / CAPACIDAD_LINEA_A
    ) * 100

    pct_capacidad_p75 = (
        p75 / CAPACIDAD_LINEA_A
    ) * 100

    pct_capacidad_p95 = (
        p95 / CAPACIDAD_LINEA_A
    ) * 100

    # =====================================================
    # KPIs
    # =====================================================

    c1, c2, c3, c4, c5 = st.columns(5)

    # =====================================================
    # DEMANDA PROMEDIO POR HORA
    # =====================================================

    hora_a = (
        df_a_hora
        .groupby("hora")["pasajeros"]
        .mean()
        .reset_index()
    )

    fig_sat = go.Figure()

    fig_sat.add_trace(
        go.Bar(
            x=hora_a["hora"],
            y=hora_a["pasajeros"],
            name="Demanda promedio",
            marker_color="#1D9E75"
        )
    )

    fig_sat.add_hline(
        y=p75,
        line_dash="dash",
        line_color="#BA7517",
        annotation_text=f"P75 = {p75:,.0f}"
    )

    fig_sat.add_hline(
        y=p95,
        line_dash="dot",
        line_color="#D85A30",
        annotation_text=f"P95 = {p95:,.0f}"
    )

    fig_sat.add_hline(
        y=CAPACIDAD_LINEA_A,
        line_width=3,
        line_color="red",
        annotation_text=f"Capacidad = {CAPACIDAD_LINEA_A:,}"
    )

    fig_sat.update_layout(
        title="Demanda promedio por hora vs capacidad Línea A",
        height=500,
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(t=60, b=20, l=0, r=0)
    )

    fig_sat.update_xaxes(
        title="Hora",
        tickmode="array",
        tickvals=list(range(24)),
        ticktext=[f"{h:02d}:00" for h in range(24)]
    )

    fig_sat.update_yaxes(
        title="Pasajeros",
        gridcolor="#f0f0f0"
    )

    st.plotly_chart(
        fig_sat,
        use_container_width=True
    )

    # =====================================================
    # INTERPRETACIÓN AUTOMÁTICA
    # =====================================================

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

    st.info(mensaje)


st.markdown(
    '<div class="insight-ok">'
    '<b>✅ Recomendación derivada del hallazgo</b><br>'
    f'Aumentar frecuencia en <b>{linea_top}</b> y las líneas de mayor carga durante '
    f'las horas críticas identificadas. El resto del día opera con holgura suficiente '
    f'— no se requiere inversión de flota adicional, solo redistribución de horarios. '
    f'Monitorear las {horas_en_riesgo} horas en riesgo como indicador KPI operativo.'
    '</div>',
    unsafe_allow_html=True,
)



with st.expander("📋 Ver datos filtrados"):
    cols_mostrar = [c for c in ["fecha", "linea", "tipo_linea", "hora", "pasajeros", "TOTAL"]
                    if c in df.columns]
    st.dataframe(
        df[cols_mostrar]
        .sort_values(["fecha", "linea", "hora"])
        .reset_index(drop=True),
        use_container_width=True,
        height=300,
    )
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Descargar datos filtrados (CSV)",
        data=csv,
        file_name="transporte_filtrado.csv",
        mime="text/csv",
    )