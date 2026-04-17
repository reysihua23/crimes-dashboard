import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
    page_title="Security Insights Dashboard | Crime Analytics Chicago",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# CSS PERSONALIZADO - BRANDING CORPORATIVO
# ============================================
st.markdown("""
<style>
    /* Colores corporativos */
    :root {
        --primary-color: #1B3A5C;
        --secondary-color: #4A90E2;
        --accent-color: #E74C3C;
        --success-color: #27AE60;
        --warning-color: #F39C12;
        --light-bg: #F8F9FA;
        --dark-text: #2C3E50;
        --light-text: #7F8C8D;
    }
    
    /* Header principal */
    .main-header {
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--primary-color);
        margin-bottom: 0.2rem;
        letter-spacing: -0.5px;
    }
    
    .sub-header {
        font-size: 0.9rem;
        color: var(--light-text);
        margin-bottom: 1.5rem;
        border-bottom: 2px solid var(--secondary-color);
        display: inline-block;
        padding-bottom: 0.5rem;
    }
    
    /* Tarjetas de KPI */
    .kpi-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.2rem;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        transition: transform 0.3s;
    }
    
    .kpi-card:hover {
        transform: translateY(-5px);
    }
    
    .kpi-value {
        font-size: 2rem;
        font-weight: bold;
        color: white;
    }
    
    .kpi-label {
        font-size: 0.8rem;
        color: rgba(255,255,255,0.9);
        margin-top: 0.5rem;
    }
    
    /* Tarjeta de insight */
    .insight-card {
        background-color: var(--light-bg);
        border-left: 4px solid var(--secondary-color);
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .insight-title {
        font-weight: bold;
        color: var(--primary-color);
        margin-bottom: 0.5rem;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        color: var(--light-text);
        font-size: 0.7rem;
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid #E0E0E0;
    }
    
    /* Sidebar personalizado */
    .sidebar-header {
        font-size: 1.2rem;
        font-weight: bold;
        color: var(--primary-color);
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# HEADER CORPORATIVO
# ============================================
col1, col2, col3 = st.columns([1, 3, 1])

with col1:
    st.markdown("""
    <div style="text-align: center;">
        <span style="font-size: 3rem;">🛡️</span>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="text-align: center;">
        <p class="main-header">SECURITY INSIGHTS DASHBOARD</p>
        <p class="sub-header">Powered by Crime Analytics | Chicago Police Department Data</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style="text-align: center; font-size: 0.7rem; color: #7F8C8D;">
        <p>CONFIDENTIAL</p>
        <p>Q2 2025 Report</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ============================================
# INTRODUCCIÓN DEL PROYECTO (PARA EL CLIENTE)
# ============================================
with st.expander("📋 **Executive Summary**", expanded=True):
    st.markdown("""
    ### 🎯 Problemática Identificada
    
    La ciudad de Chicago enfrenta desafíos significativos en la gestión de seguridad pública con más de **1,000,000 de incidentes** registrados. La falta de herramientas analíticas limita la capacidad de:
    
    - Identificar patrones criminales en tiempo real
    - Optimizar la asignación de recursos policiales
    - Prevenir incidentes mediante análisis predictivo
    
    ### 💡 Solución Propuesta
    
    **Security Insights Dashboard** es una plataforma analítica que permite:
    
    1. **Visualización interactiva** de datos criminales
    2. **Filtros dinámicos** por tipo, ubicación y tiempo
    3. **Identificación de hotspots** de criminalidad
    4. **Métricas clave** para toma de decisiones
    
    ### 📊 Impacto Esperado
    
    | Métrica | Valor Actual | Meta |
    |---------|--------------|------|
    | Tasa de respuesta | 13.3% | 25% |
    | Prevención de incidentes | - | +30% |
    | Optimización de recursos | - | 40% eficiencia |
    """)

st.markdown("---")

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
    file_id = None
    try:
        file_id = st.secrets.get("GDRIVE_FILE_ID")
    except:
        pass
    if not file_id:
        file_id = os.getenv("GDRIVE_FILE_ID")
    if not file_id:
        return pd.DataFrame()
    
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    
    with st.spinner("🔄 Cargando datos del sistema..."):
        try:
            response = requests.get(url, timeout=60)
            if response.status_code != 200:
                return pd.DataFrame()
            bytesio = BytesIO(response.content)
            df = pd.read_csv(bytesio)
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                df = df.dropna(subset=['Date'])
            if 'District' in df.columns:
                df['District_Name'] = df['District'].map(distritos_nombres)
                df['District_Name'] = df['District_Name'].fillna('Desconocido')
            return df
        except:
            return pd.DataFrame()

df = cargar_datos()
if df.empty:
    st.error("⚠️ No se pudieron cargar los datos")
    st.stop()

# ============================================
# SIDEBAR - PANEL DE CONTROL
# ============================================
with st.sidebar:
    st.markdown("## 🎛️ Control Panel")
    st.markdown("---")
    
    # Información del cliente
    st.markdown("### 👥 Client Information")
    st.info("**Chicago Police Department**\n*Strategic Analytics Unit*")
    st.markdown("---")
    
    # Filtros
    st.markdown("### 📅 Analysis Period")
    if 'Date' in df.columns:
        min_date = df['Date'].min().date()
        max_date = df['Date'].max().date()
        fecha_inicio = st.date_input("Start Date", min_date)
        fecha_fin = st.date_input("End Date", max_date)
    
    st.markdown("---")
    
    st.markdown("### 🔍 Filters")
    if 'Primary Type' in df.columns:
        tipos = ['All'] + sorted(df['Primary Type'].dropna().unique().tolist())
        tipo_seleccionado = st.selectbox("Crime Type", tipos)
    
    if 'District_Name' in df.columns:
        distritos_opciones = ['All'] + sorted(df['District_Name'].dropna().unique().tolist())
        distrito_seleccionado = st.selectbox("District", distritos_opciones)
    
    st.markdown("---")
    
    # Leyenda
    st.markdown("### 📌 Legend")
    st.markdown("""
    - 🟢 **Low Risk**: < 100 incidents
    - 🟡 **Medium Risk**: 100-500 incidents  
    - 🔴 **High Risk**: > 500 incidents
    """)

# ============================================
# APLICAR FILTROS
# ============================================
df_filtrado = df.copy()

if 'Date' in df_filtrado.columns:
    df_filtrado = df_filtrado[(df_filtrado['Date'].dt.date >= fecha_inicio) & 
                              (df_filtrado['Date'].dt.date <= fecha_fin)]

if tipo_seleccionado != 'All' and 'Primary Type' in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado['Primary Type'] == tipo_seleccionado]

if distrito_seleccionado != 'All' and 'District_Name' in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado['District_Name'] == distrito_seleccionado]

# ============================================
# KPI DASHBOARD - MÉTRICAS CLAVE
# ============================================
st.markdown("## 📊 Key Performance Indicators")
st.markdown("---")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value">{len(df_filtrado):,}</div>
        <div class="kpi-label">Total Incidents</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    tasa_arrestos = (df_filtrado['Arrest'].sum() / len(df_filtrado) * 100) if len(df_filtrado) > 0 else 0
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value">{tasa_arrestos:.1f}%</div>
        <div class="kpi-label">Clearance Rate</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    tasa_domestico = (df_filtrado['Domestic'].sum() / len(df_filtrado) * 100) if len(df_filtrado) > 0 else 0
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value">{tasa_domestico:.1f}%</div>
        <div class="kpi-label">Domestic Incidents</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    distritos = df_filtrado['District'].nunique() if 'District' in df_filtrado.columns else 0
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value">{distritos}</div>
        <div class="kpi-label">Affected Districts</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ============================================
# ANÁLISIS PRINCIPAL
# ============================================

if len(df_filtrado) > 0:
    
    # ============================================
    # INSIGHTS CLAVE PARA EL CLIENTE
    # ============================================
    st.markdown("## 💡 Strategic Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Insight 1: Horas pico
        if 'Hour' in df_filtrado.columns:
            hora_pico = df_filtrado['Hour'].mode()[0] if not df_filtrado['Hour'].mode().empty else 0
            incidentes_hora_pico = len(df_filtrado[df_filtrado['Hour'] == hora_pico])
            st.markdown(f"""
            <div class="insight-card">
                <div class="insight-title">⏰ Peak Hours Detection</div>
                <p>El <b>{((incidentes_hora_pico/len(df_filtrado))*100):.1f}%</b> de los incidentes ocurren entre las <b>{hora_pico:02d}:00 - {hora_pico+1:02d}:00</b></p>
                <p><b>Recomendación:</b> Incrementar patrullaje en este horario</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        # Insight 2: Distrito crítico
        if 'District_Name' in df_filtrado.columns:
            distrito_critico = df_filtrado['District_Name'].value_counts().index[0] if len(df_filtrado) > 0 else "N/A"
            incidentes_distrito = df_filtrado['District_Name'].value_counts().iloc[0] if len(df_filtrado) > 0 else 0
            st.markdown(f"""
            <div class="insight-card">
                <div class="insight-title">📍 Critical District Identified</div>
                <p><b>{distrito_critico}</b> concentra <b>{incidentes_distrito:,}</b> incidentes ({((incidentes_distrito/len(df_filtrado))*100):.1f}% del total)</p>
                <p><b>Recomendación:</b> Asignar recursos adicionales prioritarios</p>
            </div>
            """, unsafe_allow_html=True)
    
    # ============================================
    # GRÁFICOS PRINCIPALES
    # ============================================
    
    # Gráfico 1: Evolución temporal
    if 'Date' in df_filtrado.columns:
        st.markdown("## 📈 Temporal Analysis")
        crimenes_por_fecha = df_filtrado.groupby(df_filtrado['Date'].dt.date).size().reset_index(name='count')
        fig_line = px.line(crimenes_por_fecha, x='Date', y='count', 
                           title="Daily Incident Evolution",
                           labels={'Date': 'Date', 'count': 'Number of Incidents'},
                           color_discrete_sequence=['#4A90E2'])
        fig_line.update_layout(height=400, hovermode='x unified')
        fig_line.add_hline(y=crimenes_por_fecha['count'].mean(), line_dash="dash", 
                           line_color="#E74C3C", annotation_text="Daily Average")
        st.plotly_chart(fig_line, use_container_width=True)
        st.caption("📌 The red line indicates the daily average incident rate")
    
    # Gráfico 2: Top crímenes
    if 'Primary Type' in df_filtrado.columns:
        st.markdown("## 🎯 Crime Pattern Analysis")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            top_crimenes = df_filtrado['Primary Type'].value_counts().head(10).reset_index()
            top_crimenes.columns = ['Crime Type', 'Count']
            fig_bar = px.bar(top_crimenes, x='Count', y='Crime Type', 
                             title="Top 10 Crime Categories",
                             labels={'Count': 'Number of Cases', 'Crime Type': ''},
                             orientation='h',
                             color='Count',
                             color_continuous_scale='Reds')
            fig_bar.update_layout(height=500)
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with col2:
            st.markdown("### 📊 Distribution")
            total = top_crimenes['Count'].sum()
            for i, row in top_crimenes.head(5).iterrows():
                pct = (row['Count'] / total) * 100
                st.markdown(f"- **{row['Crime Type'][:25]}**: {pct:.1f}%")
    
    # Gráfico 3: Top distritos
    if 'District_Name' in df_filtrado.columns:
        st.markdown("## 🗺️ Geographic Analysis")
        crimen_por_distrito = df_filtrado['District_Name'].value_counts().head(15).reset_index()
        crimen_por_distrito.columns = ['District', 'Incidents']
        
        # Agregar categoría de riesgo
        def riesgo(incidentes):
            if incidentes < 100:
                return 'Low Risk'
            elif incidentes < 500:
                return 'Medium Risk'
            else:
                return 'High Risk'
        
        crimen_por_distrito['Risk Level'] = crimen_por_distrito['Incidents'].apply(riesgo)
        
        fig_district = px.bar(crimen_por_distrito, x='District', y='Incidents',
                              title="District Incident Distribution",
                              color='Risk Level',
                              color_discrete_map={'Low Risk': '#27AE60', 
                                                  'Medium Risk': '#F39C12', 
                                                  'High Risk': '#E74C3C'})
        fig_district.update_layout(height=500, xaxis_tickangle=-45)
        st.plotly_chart(fig_district, use_container_width=True)
        
        # Insight adicional
        high_risk = crimen_por_distrito[crimen_por_distrito['Risk Level'] == 'High Risk']
        if not high_risk.empty:
            st.warning(f"🚨 **ALERTA**: {len(high_risk)} distritos en nivel de riesgo ALTO requieren atención inmediata")

else:
    st.warning("⚠️ No data available for the selected filters")

# ============================================
# RECOMENDACIONES ESTRATÉGICAS
# ============================================
st.markdown("---")
st.markdown("## 🎯 Strategic Recommendations")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 👮 Resource Allocation
    - Incrementar patrullaje en horario nocturno
    - Asignar unidades especializadas a distritos de alto riesgo
    - Implementar sistema de respuesta rápida
    """)

with col2:
    st.markdown("""
    ### 🛡️ Prevention Programs
    - Implementar programas comunitarios en zonas críticas
    - Fortalecer iluminación en hotspots identificados
    - Campañas de prevención de robos
    """)

with col3:
    st.markdown("""
    ### 📊 Monitoring
    - Dashboard actualizado semanalmente
    - Alertas automáticas para desviaciones
    - Reportes ejecutivos mensuales
    """)

# ============================================
# PIE DE PÁGINA
# ============================================
st.markdown("---")
st.markdown(f"""
<div class="footer">
    <strong>Security Insights Dashboard</strong> | Confidential Report for Chicago Police Department<br>
    Data Source: Chicago Data Portal | Analysis Period: {fecha_inicio} - {fecha_fin}<br>
    Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Version 2.0
</div>
""", unsafe_allow_html=True)