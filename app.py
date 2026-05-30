"""
Dashboard de Transporte Masivo - Análisis de Demanda
====================================================

Aplicación Streamlit para análisis y visualización de patrones de demanda
en sistemas de transporte masivo.

Estructura modular:
- styles.py: Configuración de estilos CSS
- constants.py: Constantes y configuración global
- data_loader.py: Carga y preparación de datos
- filters.py: Sidebar y lógica de filtros
- metrics.py: Cálculos de métricas y análisis
- charts.py: Generación de gráficos
"""

import streamlit as st
import pandas as pd

# Importar módulos personalizados
from styles import aplicar_estilos
from constants import COLOR_PICO, COLOR_NORMAL, COLOR_UMBRAL, _PALETA_BASE, CAPACIDAD_LINEA_A
from data_loader import cargar_datos, filtrar_datos, preparar_datos_linea_a
from filters import configurar_sidebar
from metrics import (
    calcular_metricas_generales,
    calcular_horas_riesgo,
    calcular_horas_alerta,
    calcular_ratio_finde_laboral,
    calcular_metricas_linea_a,
    generar_mensaje_interpretacion,
    construir_paleta,
    calcular_trenes_y_costos,
)
from charts import (
    chart_promedio_por_hora,
    chart_comparacion_finde,
    chart_demanda_ejecutiva,
    chart_carga_linea_pico,
    chart_distribucion_demanda_linea_a,
    chart_trenes_necesarios,
    chart_costes_operativos,
    chart_trenes_desperdiciados,
)
from constants import VEHICULOS_LINEA_A, PER_TRAIN_CAPACITY


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN INICIAL
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Dashboard Transporte Masivo",
    page_icon="🚇",
    layout="wide",
    initial_sidebar_state="expanded",
)

aplicar_estilos()

# ─── CARGA Y PREPARACIÓN DE DATOS ──────────────────────────────────────────────

df_raw = cargar_datos()

# ─── SIDEBAR Y FILTROS ─────────────────────────────────────────────────────────

config_filtros = configurar_sidebar(df_raw)

# Desempacar configuración
lineas_sel = config_filtros["lineas_sel"]
tipos_sel = config_filtros["tipos_sel"]
rango_fecha = config_filtros["rango_fecha"]
umbral_pico = config_filtros["umbral_pico"]
incluir_finde = config_filtros["incluir_finde"]

# ─── APLICAR FILTROS ──────────────────────────────────────────────────────────

df = filtrar_datos(df_raw, lineas_sel, tipos_sel, rango_fecha, incluir_finde)

if df.empty:
    st.warning("No hay datos con los filtros seleccionados. Ajusta los filtros.")
    st.stop()

# ─── PALETA DINÁMICA Y MÉTRICAS ───────────────────────────────────────────────

COLORES_LINEA = construir_paleta(tuple(sorted(df_raw["linea"].unique())), _PALETA_BASE)

# Calcular métricas generales
metricas = calcular_metricas_generales(df)
total_pax = metricas["total_pax"]
prom_diario = metricas["prom_diario"]
hora_pico_val = metricas["hora_pico_val"]
horas_criticas = metricas["horas_criticas"]
dias_validos = metricas["dias_validos"]
linea_top = metricas["linea_top"]

# Calcular horas en riesgo
horas_en_riesgo, pct_pico = calcular_horas_riesgo(df, umbral_pico)

# Calcular horas de alerta
horas_alerta_info = calcular_horas_alerta(df, umbral_pico)
horas_alerta = horas_alerta_info["horas_alerta"]
rango_am = horas_alerta_info["rango_am"]
rango_pm = horas_alerta_info["rango_pm"]

# Ratio finde vs laboral
ratio_finde_laboral = calcular_ratio_finde_laboral(df)

# NOTE: simulation controls for trains/cost are displayed next to the Line A charts below

# ═══════════════════════════════════════════════════════════════════════════════
# ENCABEZADO Y KPIs PRINCIPALES
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown('<p class="phase-header">Sistema de Transporte Masivo · Análisis de Demanda</p>',
            unsafe_allow_html=True)
st.title("Dashboard de Pasajeros")
st.markdown(
    "**Pregunta de negocio:** ¿Cuándo y en qué líneas se concentra la demanda, "
    "y existe sobredemanda que comprometa la calidad del servicio?"
)

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total pasajeros", f"{total_pax/1e6:.2f}M")
k2.metric("Promedio diario", f"{prom_diario:,.0f}")
k3.metric("Hora pico", f"{hora_pico_val}:00 h")
k4.metric("Horas en riesgo/día", f"{horas_en_riesgo}h",
          delta=f"≥{umbral_pico} pax/h", delta_color="inverse")
k5.metric("Demanda en horas pico", f"{pct_pico:.1f}%",
          delta="del total diario", delta_color="inverse")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════════
# FASE 1 · EXPLORACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown('<p class="phase-header">① Fase exploratoria — encontrando señales</p>',
            unsafe_allow_html=True)

col_l, col_r = st.columns([2, 1])

with col_l:
    st.markdown("**Pasajeros promedio por hora del día** (todas las líneas seleccionadas)")
    fig_hora = chart_promedio_por_hora(df, COLORES_LINEA, lineas_sel)
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
    fig_comp = chart_comparacion_finde(df)
    st.plotly_chart(fig_comp, use_container_width=True)

# Insight de Fase 1
st.markdown(
    f'<div class="insight-box">⚑ <b>Señal encontrada:</b> doble pico pronunciado '
    f'en la franja <b>{rango_am}</b> (AM) y <b>{rango_pm}</b> (PM). '
    f'Los días laborales presentan un pico hasta <b>{ratio_finde_laboral}×</b> '
    f'mayor que los fines de semana en hora punta.</div>',
    unsafe_allow_html=True,
)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════════
# FASE 2 · HALLAZGO
# ═══════════════════════════════════════════════════════════════════════════════

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

# ═══════════════════════════════════════════════════════════════════════════════
# FASE 3 · DASHBOARD EJECUTIVO
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown('<p class="phase-header">③ Dashboard ejecutivo — argumento visual aclaratorio</p>',
            unsafe_allow_html=True)
st.subheader("El sistema funciona — excepto cuando más lo necesitamos")
st.caption(
    "Mensaje para gerencia: la ventana crítica concentra riesgo operativo. "
    "El resto del día opera con holgura."
)

# KPIs ejecutivos
e1, e2, e3, e4 = st.columns(4)
e1.metric("Horas en riesgo/día", f"{horas_en_riesgo}h",
          delta="riesgo operativo", delta_color="inverse")
e2.metric("Demanda en esas horas", f"{pct_pico:.0f}%",
          delta="del total diario", delta_color="inverse")
e3.metric("Horas con holgura/día", f"{max(0, 20 - horas_en_riesgo)}h",
          delta="capacidad disponible", delta_color="normal")
e4.metric("Línea más cargada", linea_top)

# Gráficas principales ejecutivas
st.markdown("#### Demanda horaria — dónde está el problema")
fig_ej = chart_demanda_ejecutiva(df, umbral_pico, COLOR_PICO, COLOR_NORMAL)
st.plotly_chart(fig_ej, use_container_width=True)

st.markdown("#### Carga relativa por línea en hora pico")
fig_carga = chart_carga_linea_pico(df, horas_alerta, COLORES_LINEA)
st.plotly_chart(fig_carga, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# ANÁLISIS DE SATURACIÓN - LÍNEA A
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("---")

# Preparar datos de la Línea A
df_a_hora = preparar_datos_linea_a(df, df_raw)

if df_a_hora is None:
    st.warning("No se encontraron registros para la Línea A con los filtros actuales.")
else:
    # Calcular métricas de saturación
    metricas_linea_a = calcular_metricas_linea_a(df_a_hora)
    
    p75 = metricas_linea_a["p75"]
    p95 = metricas_linea_a["p95"]
    dias_sobre_p95 = metricas_linea_a["dias_sobre_p95"]
    dias_sobre_capacidad = metricas_linea_a["dias_sobre_capacidad"]
    utilizacion_max = metricas_linea_a["utilizacion_max"]
    dias_totales = metricas_linea_a["dias_totales"]
    pct_dias_p95 = (dias_sobre_p95 / dias_totales) * 100
    pct_dias_capacidad = (dias_sobre_capacidad / dias_totales) * 100
    
    # KPIs de saturación
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Percentil 75", f"{p75:,.0f}")
    c2.metric("Percentil 95", f"{p95:,.0f}")
    c3.metric("Capacidad Línea A", f"{CAPACIDAD_LINEA_A:,.0f}")
    c4.metric("Días > P95", f"{dias_sobre_p95}")
    c5.metric("Días con saturación", f"{dias_sobre_capacidad}")

    # Gráfico de distribución
    st.markdown("#### Distribución de demanda de la Línea A")
    fig_sat = chart_distribucion_demanda_linea_a(
        df_a_hora, p75, p95, CAPACIDAD_LINEA_A, 
        dias_sobre_p95, dias_sobre_capacidad
    )
    st.plotly_chart(fig_sat, use_container_width=True)

    # Insight de saturación
    st.markdown(
        f"""
<div class="insight-box">

<b>⚑ Hallazgo de saturación</b><br><br>

El 95% de las observaciones de demanda se encuentran por debajo de
<b>{p95:,.0f}</b> pasajeros por hora.

Solo <b>{dias_sobre_p95}</b> días
({pct_dias_p95:.1f}% del periodo analizado)
presentaron al menos una hora con demanda extrema
(superior al percentil 95).

La capacidad teórica de la Línea A es
<b>{CAPACIDAD_LINEA_A:,.0f}</b> pasajeros por hora.

<b>{dias_sobre_capacidad}</b> días
({pct_dias_capacidad:.2f}% del periodo)
superaron dicha capacidad.

</div>
""",
        unsafe_allow_html=True,
    )

    # Mensaje automático de interpretación
    mensaje = generar_mensaje_interpretacion(utilizacion_max)
    st.info(mensaje)

    # --------------------------------------------------
    # Análisis operativo y financiero (Línea A)
    # --------------------------------------------------
    st.markdown("## Análisis de capacidad y gastos — Línea A")

    col_chart, col_sim = st.columns([3, 1])

    # Simulación: controles al lado del gráfico (sin coste operativo)
    with col_sim:
        st.markdown("### Simulación")
        trenes_operativos = st.number_input(
            "Trenes operativos Línea A", min_value=1, value=VEHICULOS_LINEA_A, step=1
        )
        st.markdown(f"Capacidad por tren: **{PER_TRAIN_CAPACITY:,} pax**")

    # Calcular según valores de simulación (coste por tren por hora = 0 porque no hay datos)
    coste_por_tren_hora = 0.0
    trains_costs = calcular_trenes_y_costos(
        df_a_hora, CAPACIDAD_LINEA_A, trenes_operativos, coste_por_tren_hora, per_train_capacity=PER_TRAIN_CAPACITY
    )

    # Mostrar gráficos en la columna principal
    with col_chart:
        st.markdown("#### Trenes necesarios por hora")
        fig_tr = chart_trenes_necesarios(trains_costs["trenes_necesarios_por_hora"], trenes_operativos)
        st.plotly_chart(fig_tr, use_container_width=True)

    # KPIs operativos (sin costos)
    op1, op2, op3 = st.columns(3)
    op1.metric("Trenes mínimos necesarios", f"{trains_costs['trenes_max_necesarios']}")
    op2.metric("Horas > capacidad", f"{trains_costs['horas_sobre_capacidad']}")
    op3.metric("Capacidad por tren", f"{PER_TRAIN_CAPACITY:,} pax")

    st.markdown("#### Trenes desperdiciados por hora (si desplegamos el mínimo necesario para cubrir el pico)")
    horas_index = trains_costs["trenes_necesarios_por_hora"].index.tolist()
    desplegados = trains_costs["trenes_max_necesarios"]
    fig_waste = chart_trenes_desperdiciados(horas_index, trains_costs["trenes_necesarios_por_hora"], desplegados)
    st.plotly_chart(fig_waste, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# RECOMENDACIONES Y DATOS
# ═══════════════════════════════════════════════════════════════════════════════

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

st.markdown("---")

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