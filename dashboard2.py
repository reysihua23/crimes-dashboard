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
    page_title="Dashboard de Crímenes - Chicago",
    page_icon="🚔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# CSS PERSONALIZADO PARA MEJORAR APARIENCIA
# ============================================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E3A5F;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #4A627A;
        text-align: center;
        margin-bottom: 2rem;
    }
    .kpi-card {
        background-color: #F0F2F6;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1E3A5F;
    }
    .kpi-label {
        font-size: 0.9rem;
        color: #4A627A;
    }
    .footer {
        text-align: center;
        color: #8B9DC3;
        font-size: 0.8rem;
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# DICCIONARIO DE DISTRITOS
# ============================================
distritos_nombres = {
    1: '📍 Central', 2: '📍 Wentworth', 3: '📍 Grand Crossing', 4: '📍 South Chicago',
    5: '📍 Calumet', 6: '📍 Gresham', 7: '📍 Englewood', 8: '📍 Chicago Lawn',
    9: '📍 Deering', 10: '📍 Ogden', 11: '📍 Harrison', 12: '📍 Monroe',
    13: '📍 Wood Street', 14: '📍 Shakespeare', 15: '📍 Austin', 16: '📍 Jefferson Park',
    17: '📍 Albany Park', 18: '📍 Near North', 19: '📍 Town Hall', 20: '📍 Lincoln',
    21: '📍 Prairie Avenue', 22: '📍 Morgan Park', 23: '📍 Rogers Park', 24: '📍 Roosevelt', 25: '📍 Grand Central'
}

# ============================================
# CARGAR DATOS
# ============================================
@st.cache_data(ttl=3600)
def cargar_datos():
    """Carga los datos desde Google Drive"""
    
    file_id = None
    
    try:
        file_id = st.secrets.get("GDRIVE_FILE_ID")
        if file_id:
            st.info("🔐 Conectado a Google Drive")
    except:
        pass
    
    if not file_id:
        file_id = os.getenv("GDRIVE_FILE_ID")
    
    if not file_id:
        st.error("❌ Error de configuración")
        return pd.DataFrame()
    
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    
    with st.spinner("📥 Cargando datos... esto puede tomar unos segundos"):
        try:
            response = requests.get(url, timeout=60)
            
            if response.status_code != 200:
                st.error(f"Error: {response.status_code}")
                return pd.DataFrame()
            
            bytesio = BytesIO(response.content)
            df = pd.read_csv(bytesio)
            
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                df = df.dropna(subset=['Date'])
            
            if 'District' in df.columns:
                df['District_Name'] = df['District'].map(distritos_nombres)
                df['District_Name'] = df['District_Name'].fillna('📍 Desconocido')
            
            return df
            
        except Exception as e:
            st.error(f"Error: {e}")
            return pd.DataFrame()

# ============================================
# HEADER PRINCIPAL
# ============================================
st.markdown('<p class="main-header">🚔 Dashboard de Análisis de Crímenes</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Ciudad de Chicago, Illinois | Datos 2021-2025</p>', unsafe_allow_html=True)
st.markdown("---")

# Cargar datos
df = cargar_datos()

if df.empty:
    st.stop()

st.success(f"✅ **{len(df):,}** registros cargados exitosamente")

# ============================================
# SIDEBAR - FILTROS (MEJORADOS)
# ============================================
with st.sidebar:
    st.markdown("## 🔍 Panel de Filtros")
    st.markdown("---")
    
    # Filtro de fecha
    st.markdown("### 📅 Período de Análisis")
    if 'Date' in df.columns:
        min_date = df['Date'].min().date()
        max_date = df['Date'].max().date()
        fecha_inicio = st.date_input("Desde", min_date, min_value=min_date, max_value=max_date)
        fecha_fin = st.date_input("Hasta", max_date, min_value=min_date, max_value=max_date)
    
    st.markdown("---")
    
    # Filtro de tipo de crimen
    st.markdown("### 📋 Tipo de Crimen")
    if 'Primary Type' in df.columns:
        tipos_crimen = ['🏷️ Todos'] + sorted(df['Primary Type'].dropna().unique().tolist())
        tipo_seleccionado = st.selectbox("Seleccionar", tipos_crimen)
        if tipo_seleccionado == '🏷️ Todos':
            tipo_seleccionado = 'Todos'
    
    st.markdown("---")
    
    # Filtro de arresto
    st.markdown("### 👮 Estado de Arresto")
    arresto_opciones = ['🔓 Todos', '✅ Con Arresto', '❌ Sin Arresto']
    arresto_seleccionado = st.radio("", arresto_opciones, horizontal=True)
    arresto_seleccionado = arresto_seleccionado.replace('✅ ', '').replace('❌ ', '').replace('🔓 ', '')
    
    st.markdown("---")
    
    # Filtro doméstico
    st.markdown("### 🏠 Tipo de Incidente")
    domestico_opciones = ['🔓 Todos', '🏠 Doméstico', '🏢 No Doméstico']
    domestico_seleccionado = st.radio("", domestico_opciones, horizontal=True)
    domestico_seleccionado = domestico_seleccionado.replace('🏠 ', '').replace('🏢 ', '').replace('🔓 ', '')
    
    st.markdown("---")
    
    # Filtro de distrito
    st.markdown("### 🗺️ Distrito")
    if 'District_Name' in df.columns:
        distritos_opciones = ['🌎 Todos'] + sorted(df['District_Name'].dropna().unique().tolist())
        distrito_seleccionado = st.selectbox("Seleccionar", distritos_opciones)
        if distrito_seleccionado == '🌎 Todos':
            distrito_seleccionado = 'Todos'

# ============================================
# APLICAR FILTROS
# ============================================
df_filtrado = df.copy()

if 'Date' in df_filtrado.columns:
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
# KPI CARDS MEJORADAS
# ============================================
st.markdown("## 📊 Indicadores Clave")
st.markdown("---")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value">📊 {len(df_filtrado):,}</div>
        <div class="kpi-label">Total de Crímenes</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    if 'Arrest' in df_filtrado.columns and len(df_filtrado) > 0:
        tasa = (df_filtrado['Arrest'].sum() / len(df_filtrado) * 100)
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">👮 {tasa:.1f}%</div>
            <div class="kpi-label">Tasa de Arrestos</div>
        </div>
        """, unsafe_allow_html=True)

with col3:
    if 'Domestic' in df_filtrado.columns and len(df_filtrado) > 0:
        tasa = (df_filtrado['Domestic'].sum() / len(df_filtrado) * 100)
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">🏠 {tasa:.1f}%</div>
            <div class="kpi-label">Crímenes Domésticos</div>
        </div>
        """, unsafe_allow_html=True)

with col4:
    if 'District' in df_filtrado.columns:
        distritos = df_filtrado['District'].nunique()
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">🗺️ {distritos}</div>
            <div class="kpi-label">Distritos Afectados</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ============================================
# GRÁFICOS MEJORADOS
# ============================================

if len(df_filtrado) > 0:
    
    # Gráfico 1: Evolución temporal
    if 'Date' in df_filtrado.columns:
        st.markdown("## 📈 Evolución Temporal de Crímenes")
        crimenes_por_fecha = df_filtrado.groupby(df_filtrado['Date'].dt.date).size().reset_index(name='count')
        fig_line = px.line(crimenes_por_fecha, x='Date', y='count', 
                           title="Número de crímenes por día",
                           labels={'Date': 'Fecha', 'count': 'Cantidad de Crímenes'},
                           color_discrete_sequence=['#1E3A5F'])
        fig_line.update_layout(height=450, hovermode='x unified')
        fig_line.add_hline(y=crimenes_por_fecha['count'].mean(), line_dash="dash", 
                           line_color="red", annotation_text="Promedio")
        st.plotly_chart(fig_line, use_container_width=True)
        st.caption("📌 La línea roja muestra el promedio diario de crímenes")

    # Gráfico 2: Top crímenes
    if 'Primary Type' in df_filtrado.columns:
        st.markdown("## 🥧 Distribución por Tipo de Crimen")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            top_crimenes = df_filtrado['Primary Type'].value_counts().head(10).reset_index()
            top_crimenes.columns = ['Tipo', 'Cantidad']
            fig_bar = px.bar(top_crimenes, x='Cantidad', y='Tipo', 
                             title="Top 10 Tipos de Crímenes",
                             labels={'Cantidad': 'Número de Casos', 'Tipo': ''},
                             orientation='h',
                             color='Cantidad',
                             color_continuous_scale='Reds')
            fig_bar.update_layout(height=500)
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with col2:
            st.markdown("### 📊 Porcentajes")
            total = top_crimenes['Cantidad'].sum()
            for i, row in top_crimenes.head(5).iterrows():
                pct = (row['Cantidad'] / total) * 100
                st.markdown(f"- **{row['Tipo'][:20]}**: {pct:.1f}%")

    # Gráfico 3: Top distritos
    if 'District_Name' in df_filtrado.columns:
        st.markdown("## 🗺️ Crímenes por Distrito")
        crimen_por_distrito = df_filtrado['District_Name'].value_counts().head(15).reset_index()
        crimen_por_distrito.columns = ['Distrito', 'Cantidad']
        fig_district = px.bar(crimen_por_distrito, x='Distrito', y='Cantidad',
                              title="Top 15 Distritos con Más Crímenes",
                              color='Cantidad',
                              color_continuous_scale='Reds')
        fig_district.update_layout(height=500, xaxis_tickangle=-45)
        st.plotly_chart(fig_district, use_container_width=True)
        
        # Insight
        st.info(f"💡 **Insight**: El distrito con más crímenes es **{crimen_por_distrito.iloc[0]['Distrito']}** con {crimen_por_distrito.iloc[0]['Cantidad']:,} casos")

    # Gráfico 4: Patrones temporales
    st.markdown("## ⏰ Patrones Temporales")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if 'Hour' in df_filtrado.columns:
            st.markdown("### 📊 Por Hora del Día")
            crimen_por_hora = df_filtrado.groupby('Hour').size().reset_index(name='count')
            fig_hour = px.bar(crimen_por_hora, x='Hour', y='count',
                              title="Crímenes por hora",
                              labels={'Hour': 'Hora', 'count': 'Número de Crímenes'},
                              color_discrete_sequence=['#1E3A5F'])
            fig_hour.update_layout(height=400)
            st.plotly_chart(fig_hour, use_container_width=True)
    
    with col2:
        if 'DayName' in df_filtrado.columns:
            st.markdown("### 📅 Por Día de la Semana")
            crimen_por_dia = df_filtrado.groupby('DayName').size().reset_index(name='count')
            orden_dias = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            traduccion = {'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
                         'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'}
            crimen_por_dia['Dia'] = crimen_por_dia['DayName'].map(traduccion)
            crimen_por_dia['Dia'] = pd.Categorical(crimen_por_dia['Dia'], 
                                                   categories=['Lunes', 'Martes', 'Miércoles', 'Jueves', 
                                                              'Viernes', 'Sábado', 'Domingo'], ordered=True)
            crimen_por_dia = crimen_por_dia.sort_values('Dia')
            fig_day = px.bar(crimen_por_dia, x='Dia', y='count',
                             title="Crímenes por día",
                             labels={'Dia': '', 'count': 'Número de Crímenes'},
                             color_discrete_sequence=['#1E3A5F'])
            fig_day.update_layout(height=400)
            st.plotly_chart(fig_day, use_container_width=True)

else:
    st.warning("⚠️ **No hay datos** con los filtros seleccionados. Prueba cambiando los filtros.")

# ============================================
# TABLA DE DATOS
# ============================================
with st.expander("📋 Ver detalles de los datos"):
    columnas_mostrar = ['ID', 'Date', 'Primary Type', 'District_Name', 'Arrest', 'Domestic', 'Block']
    columnas_existentes = [col for col in columnas_mostrar if col in df_filtrado.columns]
    if columnas_existentes:
        st.dataframe(df_filtrado[columnas_existentes].head(100), use_container_width=True)
        
        # Botón de descarga
        csv = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar datos filtrados (CSV)",
            data=csv,
            file_name=f"crimes_filtrados_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )

# ============================================
# PIE DE PÁGINA
# ============================================
st.markdown("---")
st.markdown(f"""
<div class="footer">
    🚔 Dashboard de Análisis de Crímenes | Datos: Ciudad de Chicago<br>
    📅 Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}<br>
    📊 Total de registros en base: {len(df):,} | Registros mostrados: {len(df_filtrado):,}
</div>
""", unsafe_allow_html=True)