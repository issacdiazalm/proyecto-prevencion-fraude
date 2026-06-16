import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import os
import plotly.express as px

# 1. CONFIGURACIÓN DE LA PÁGINA INTERACTIVA
st.set_page_config(
    page_title="Dashboard Retail Loss Prevention",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ Portal de Control y Prevención de Fraudes en Retail")
st.markdown("### Análisis de Riesgo Operacional y Mitigación de Pérdidas (AWS Aurora)")
st.divider()

# 2. CONEXIÓN SEGURA A LA NUBE (Variables de Entorno)
@st.cache_resource
def get_db_engine():
    db_user = "postgres"
    db_pass = os.getenv("AWS_DB_PASS")
    db_host = os.getenv("AWS_DB_HOST")
    db_port = "5432"
    db_name = "northwind"
    
    if not db_pass or not db_host:
        st.error("❌ Error de Infraestructura: Variables de entorno no detectadas en este entorno.")
        st.stop()
        
    return create_engine(f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}?sslmode=require")
try:
    engine = get_db_engine()
except Exception as e:
    st.error(f"❌ Error de Conexión con el Clúster de Aurora: {e}")
    st.stop()

# 3. CARGA DE DATOS OPTIMIZADA CON CACHÉ
@st.cache_data
def cargar_datos_base():
    # Usamos minúsculas puras tal como existen en AWS Aurora
    query = """
        SELECT f.*, c.nombre_comercio, c.ubicacion, t.fecha_completa
        FROM loss_prevention_dwh.fact_transacciones f
        JOIN loss_prevention_dwh.dim_comercios c ON f.comercio_key = c.comercio_key
        JOIN loss_prevention_dwh.dim_tiempo t ON f.tiempo_key = t.tiempo_key;
    """
    return pd.read_sql(query, con=engine)

with st.spinner("📥 Sincronizando transacciones desde AWS Cloud..."):
    df_base = cargar_datos_base()

# 4. FILTROS DINÁMICOS (Barra Lateral - Slicers)
st.sidebar.header("🎯 Parámetros de Auditoría")
categorias_disponibles = df_base["categoria"].unique()
categorias_seleccionadas = st.sidebar.multiselect(
    "Filtrar por Categoría de Comercio:",
    options=categorias_disponibles,
    default=categorias_disponibles
)

# Aplicación del filtro en memoria instantánea
df_filtrado = df_base[df_base["categoria"].isin(categorias_seleccionadas)]

# 5. RESUMEN DE INDICADORES CLAVE (KPIs)
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="💰 Capital Auditado", value=f"${df_filtrado['monto'].sum():,.2f}")
with col2:
    st.metric(label="📦 Volumen Operaciones", value=f"{len(df_filtrado):,}")
with col3:
    st.metric(label="🚨 Incidentes Confirmados", value=f"{df_filtrado['es_fraude'].sum():,}")
with col4:
    st.metric(label="🧠 Riesgo de Anomalía Promedio", value=f"{df_filtrado['anomaly_score'].mean():.4f}")

st.markdown("---")

# 6. GRÁFICAS DE SQL AVANZADO INTERACTIVAS
col_izq, col_der = st.columns(2)

with col_izq:
    st.subheader("🏬 Ranking de Riesgo por Comercio (Top 5)")
    # Replicando analíticamente nuestra Query Avanzada 2 (Ranking de pérdidas)
    df_comercio_riesgo = df_filtrado[df_filtrado["es_fraude"] == 1].groupby("nombre_comercio")["monto"].sum().reset_index()
    df_comercio_riesgo = df_comercio_riesgo.sort_values(by="monto", ascending=False).head(5)
    
    fig_bar = px.bar(
        df_comercio_riesgo,
        x="nombre_comercio",
        y="monto",
        title="Pérdida Financiera Acumulada por Fraude ($)",
        labels={"nombre_comercio": "Comercio", "monto": "Pérdida ($)"},
        color="monto",
        color_continuous_scale="Reds"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col_der:
    st.subheader("📊 Distribución de Alertas por Categoría")
    # Replicando analíticamente nuestra Query Avanzada 3 (% de Bateo de Fraude)
    df_cat_stats = df_filtrado.groupby("categoria").agg(
        total=("transaction_id", "count"),
        fraudes=("es_fraude", "sum")
    ).reset_index()
    df_cat_stats["% Fraude"] = (df_cat_stats["fraudes"] / df_cat_stats["total"]) * 100
    
    fig_pie = px.pie(
        df_cat_stats,
        names="categoria",
        values="% Fraude",
        title="Porcentaje de Efectividad del Fraude por Categoría de Retail",
        hole=0.4
    )
    st.plotly_chart(fig_pie, use_container_width=True)