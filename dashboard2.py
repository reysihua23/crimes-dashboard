import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import os
import requests
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

# ============================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================
st.set_page_config(
    page_title="Dashboard de Crímenes",
    page_icon="🚔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# DICCIONARIO DE DISTRITOS
# ============================================
distritos_nombres = {
    1: 'Central', 2: 'Wentworth', 3: 'Grand Crossing', 4: 'South Chicago',
    5: 'Calumet', 6: 'Gresham', 7: 'Englewood', 8: 'Chicago Lawn',
    9: 'Deering', 10: 'Ogden', 11: 'Harrison', 12: 'Monroe',
    13: 'Wood Street', 14: 'Shakespeare', 15: 'Austin', 16: 'Jefferson Park',
    17: 'Albany Park', 18: 'Near North', 19: 'Town Hall', 20: 'Lincoln',
    21: 'Prairie Avenue', 22: 'Morgan Park', 23: 'Rogers Park', 24: 'Roosevelt', 25: 'Grand Central'
}

# ============================================
# CARGAR DATOS
# ============================================
@st.cache_data(ttl=3600)
def cargar_datos():
    """Carga los datos desde Google Drive"""
    
    file_id = None
    
    # Intentar desde secrets (Streamlit Cloud)
    try:
        file_id = st.secrets.get("GDRIVE_FILE_ID")
        if file_id:
            st.info("🔐 Usando configuración desde Streamlit Secrets")
    except:
        pass
    
    # Intentar desde .env (local)
    if not file_id:
        file_id = os.getenv("GDRIVE_FILE_ID")
        if file_id:
            st.info("📁 Usando configuración desde archivo .env")
    
    # Si no hay ID, error
    if not file_id:
        st.error("❌ Error: GDRIVE_FILE_ID no está configurado")
        return pd.DataFrame()
    
    # URL de descarga
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    
    with st.spinner("📥 Cargando datos desde Google Drive..."):
        try:
            response = requests.get(url, timeout=60)
            
            if response.status_code != 200:
                st.error(f"Error al descargar: {response.status_code}")
                return pd.DataFrame()
            
            # Leer CSV
            bytesio = BytesIO(response.content)
            df = pd.read_csv(bytesio)
            
            # Procesar fechas
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                df = df.dropna(subset=['Date'])
            
            # Agregar nombre del distrito
            if 'District' in df.columns:
                df['District_Name'] = df['District'].map(distritos_nombres)
                df['District_Name'] = df['District_Name'].fillna('Desconocido')
            
            return df
            
        except Exception as e:
            st.error(f"Error al cargar datos: {e}")
            return pd.DataFrame()

# ============================================
# TÍTULO Y CARGA
# ============================================
st.title("🚔 Dashboard de Análisis de Crímenes - Chicago")
st.markdown("---")

df = cargar_datos()

if df.empty:
    st.stop()

st.success(f"✅ Datos cargados: {len(df):,} registros")

# ============================================
# SIDEBAR - FILTROS
# ============================================
st.sidebar.header("🔍 Filtros")

# Filtro de fecha
st.sidebar.subheader("📅 Rango de Fechas")
if 'Date' in df.columns:
    min_date = df['Date'].min().date()
    max_date = df['Date'].max().date()
    fecha_inicio = st.sidebar.date_input("Fecha inicio", min_date, min_value=min_date, max_value=max_date)
    fecha_fin = st.sidebar.date_input("Fecha fin", max_date, min_value=min_date, max_value=max_date)
else:
    fecha_inicio = None
    fecha_fin = None

# Filtro de tipo de crimen
st.sidebar.subheader("📋 Tipo de Crimen")
if 'Primary Type' in df.columns:
    tipos_crimen = ['Todos'] + sorted(df['Primary Type'].dropna().unique().tolist())
    tipo_seleccionado = st.sidebar.selectbox("Seleccionar tipo", tipos_crimen)
else:
    tipo_seleccionado = 'Todos'

# Filtro de arresto
st.sidebar.subheader("👮 Arresto")
if 'Arrest' in df.columns:
    arresto_opciones = ['Todos', 'Con Arresto', 'Sin Arresto']
    arresto_seleccionado = st.sidebar.selectbox("Estado de arresto", arresto_opciones)
else:
    arresto_seleccionado = 'Todos'

# Filtro doméstico
st.sidebar.subheader("🏠 Doméstico")
if 'Domestic' in df.columns:
    domestico_opciones = ['Todos', 'Doméstico', 'No Doméstico']
    domestico_seleccionado = st.sidebar.selectbox("Tipo", domestico_opciones)
else:
    domestico_seleccionado = 'Todos'

# Filtro de distrito
st.sidebar.subheader("🏢 Distrito")
if 'District_Name' in df.columns:
    distritos_opciones = ['Todos'] + sorted(df['District_Name'].dropna().unique().tolist())
    distrito_seleccionado = st.sidebar.selectbox("Seleccionar distrito", distritos_opciones)
else:
    distrito_seleccionado = 'Todos'

# ============================================
# APLICAR FILTROS
# ============================================
df_filtrado = df.copy()

if fecha_inicio and fecha_fin and 'Date' in df_filtrado.columns:
    df_filtrado = df_filtrado[(df_filtrado['Date'].dt.date >= fecha_inicio) & 
                              (df_filtrado['Date'].dt.date <= fecha_fin)]

if tipo_seleccionado != 'Todos' and 'Primary Type' in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado['Primary Type'] == tipo_seleccionado]

if arresto_seleccionado == 'Con Arresto' and 'Arrest' in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado['Arrest'] == True]
elif arresto_seleccionado == 'Sin Arresto' and 'Arrest' in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado['Arrest'] == False]

if domestico_seleccionado == 'Doméstico' and 'Domestic' in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado['Domestic'] == True]
elif domestico_seleccionado == 'No Doméstico' and 'Domestic' in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado['Domestic'] == False]

if distrito_seleccionado != 'Todos' and 'District_Name' in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado['District_Name'] == distrito_seleccionado]

# ============================================
# KPI CARDS
# ============================================
st.subheader("📊 Indicadores Clave")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Crímenes", f"{len(df_filtrado):,}")

with col2:
    if 'Arrest' in df_filtrado.columns and len(df_filtrado) > 0:
        tasa_arrestos = (df_filtrado['Arrest'].sum() / len(df_filtrado) * 100)
        st.metric("Tasa de Arrestos", f"{tasa_arrestos:.1f}%")
    else:
        st.metric("Tasa de Arrestos", "N/A")

with col3:
    if 'Domestic' in df_filtrado.columns and len(df_filtrado) > 0:
        tasa_domestico = (df_filtrado['Domestic'].sum() / len(df_filtrado) * 100)
        st.metric("Crímenes Domésticos", f"{tasa_domestico:.1f}%")
    else:
        st.metric("Crímenes Domésticos", "N/A")

with col4:
    if 'District' in df_filtrado.columns:
        distritos_afectados = df_filtrado['District'].nunique()
        st.metric("Distritos Afectados", f"{distritos_afectados}")
    else:
        st.metric("Distritos Afectados", "N/A")

st.markdown("---")

# ============================================
# GRÁFICOS
# ============================================

if len(df_filtrado) > 0:
    # Gráfico 1: Evolución temporal
    if 'Date' in df_filtrado.columns:
        st.subheader("📈 Evolución de Crímenes")
        crimenes_por_fecha = df_filtrado.groupby(df_filtrado['Date'].dt.date).size().reset_index(name='count')
        fig_line = px.line(crimenes_por_fecha, x='Date', y='count', 
                           title="Crímenes por día",
                           labels={'Date': 'Fecha', 'count': 'Número de Crímenes'})
        fig_line.update_layout(height=400)
        st.plotly_chart(fig_line, use_container_width=True)

    # Gráfico 2: Tipos de crimen
    if 'Primary Type' in df_filtrado.columns:
        st.subheader("🥧 Tipos de Crimen")
        top_crimenes = df_filtrado['Primary Type'].value_counts().head(10).reset_index()
        top_crimenes.columns = ['Tipo', 'Cantidad']
        fig_pie = px.pie(top_crimenes, values='Cantidad', names='Tipo', 
                         title="Top 10 Tipos de Crímenes")
        fig_pie.update_layout(height=500)
        st.plotly_chart(fig_pie, use_container_width=True)

    # Gráfico 3: Top distritos
    if 'District_Name' in df_filtrado.columns:
        st.subheader("🗺️ Crímenes por Distrito")
        crimen_por_distrito = df_filtrado['District_Name'].value_counts().head(15).reset_index()
        crimen_por_distrito.columns = ['Distrito', 'Cantidad']
        fig_district = px.bar(crimen_por_distrito, x='Distrito', y='Cantidad',
                              title="Top 15 Distritos con Más Crímenes",
                              color='Cantidad',
                              color_continuous_scale='Reds')
        fig_district.update_layout(height=450, xaxis_tickangle=-45)
        st.plotly_chart(fig_district, use_container_width=True)

else:
    st.warning("⚠️ No hay datos con los filtros seleccionados")

# ============================================
# PIE DE PÁGINA
# ============================================
st.markdown("---")
st.caption(f"Dashboard actualizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")