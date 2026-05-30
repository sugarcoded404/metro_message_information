# Dashboard de Transporte Masivo - Arquitectura Modular

## 📋 Resumen

La arquitectura ha sido refactorizada para separar responsabilidades, haciendo el código más limpio, mantenible y escalable.

## 🏗️ Estructura de Módulos

```
workshop2/
├── app.py              # 🎯 Aplicación principal (orquestación)
├── constants.py        # ⚙️ Constantes y configuración global
├── styles.py           # 🎨 Configuración de estilos CSS
├── data_loader.py      # 📊 Carga y preparación de datos
├── filters.py          # 🔍 Configuración del sidebar y filtros
├── metrics.py          # 📈 Cálculos de métricas y análisis
├── charts.py           # 📉 Generación de gráficos
├── data/
│   └── trusted.parquet # Datos de entrada
└── requirements.txt    # Dependencias
```

## 📦 Descripción de Módulos

### **constants.py** ⚙️
Almacena todas las constantes del proyecto:
- Paleta de colores
- Capacidades de líneas
- Rutas de archivos

```python
COLOR_PICO = "#D85A30"
CAPACIDAD_LINEA_A = 97306
```

### **styles.py** 🎨
Gestiona la configuración de estilos CSS:
- Función `aplicar_estilos()` que centraliza todo el diseño
- Clases CSS para tarjetas, insights, etc.

```python
aplicar_estilos()  # Llamada única al inicio de app.py
```

### **data_loader.py** 📊
Maneja carga y preparación de datos:
- `cargar_datos()`: Lee el parquet y normaliza columnas
- `filtrar_datos()`: Aplica filtros seleccionados
- `preparar_datos_linea_a()`: Prepara datos específicos de la Línea A

### **filters.py** 🔍
Construye el sidebar interactivo:
- `configurar_sidebar()`: Retorna un diccionario con filtros seleccionados
- Centraliza toda la lógica de entrada del usuario

### **metrics.py** 📈
Funciones de análisis y cálculos:
- `calcular_metricas_generales()`: KPIs principales
- `calcular_horas_riesgo()`: Horas con demanda crítica
- `calcular_metricas_linea_a()`: Análisis de saturación
- `generar_mensaje_interpretacion()`: Interpretación automática

### **charts.py** 📉
Funciones de visualización externas:
- `chart_promedio_por_hora()`: Gráfico de barras apiladas
- `chart_comparacion_finde()`: Comparación laboral vs finde
- `chart_demanda_ejecutiva()`: Dashboard principal
- `chart_carga_linea_pico()`: Carga por línea
- `chart_distribucion_demanda_linea_a()`: Histograma de saturación

### **app.py** 🎯
Aplicación principal - Orquestación limpia:
1. Importa todos los módulos
2. Carga datos y aplica filtros
3. Calcula métricas
4. Llama a funciones de gráficos
5. Muestra todo en la interfaz

## ✨ Ventajas de la Nueva Arquitectura

| Aspecto | Antes | Después |
|--------|-------|---------|
| **Líneas de app.py** | ~500+ | ~200 |
| **Complejidad** | Alta | Baja |
| **Mantenibilidad** | Difícil | Fácil |
| **Reutilización** | No | Sí |
| **Testing** | Complicado | Simple |
| **Depuración** | Lenta | Rápida |

## 🚀 Cómo Usar

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar aplicación
streamlit run app.py
```

## 🔄 Flujo de Datos

```
data/trusted.parquet
        ↓
   data_loader.py (cargar_datos)
        ↓
   filters.py (configurar_sidebar)
        ↓
   data_loader.py (filtrar_datos)
        ↓
   metrics.py (calcular_*)
        ↓
   charts.py (chart_*)
        ↓
   app.py (visualizar)
```

## 📝 Ejemplo de Extensión

Para agregar un nuevo gráfico:

1. **Crear función en `charts.py`**:
```python
def chart_nuevo_grafico(df):
    fig = px.line(df, ...)
    return fig
```

2. **Importar en `app.py`**:
```python
from charts import chart_nuevo_grafico
```

3. **Usar en `app.py`**:
```python
st.markdown("#### Título del gráfico")
fig = chart_nuevo_grafico(df)
st.plotly_chart(fig, use_container_width=True)
```

## 🎓 Buenas Prácticas Aplicadas

- ✅ **Separación de responsabilidades**: Cada módulo tiene una función clara
- ✅ **DRY (Don't Repeat Yourself)**: Código reutilizable
- ✅ **Legibilidad**: Código limpio y bien documentado
- ✅ **Escalabilidad**: Fácil agregar nuevas características
- ✅ **Mantenibilidad**: Errores localizados en módulos específicos
