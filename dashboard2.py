import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import os                    # 👈 Agrega esta
import requests             # 👈 Agrega esta
from io import BytesIO      # 👈 Agrega esta
from dotenv import load_dotenv  # 👈 Agrega esta

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
    1: 'Central',
    2: 'Wentworth', 
    3: 'Grand Crossing',
    4: 'South Chicago',
    5: 'Calumet',
    6: 'Gresham',
    7: 'Englewood',
    8: 'Chicago Lawn',
    9: 'Deering',
    10: 'Ogden',
    11: 'Harrison',
    12: 'Monroe',
    13: 'Wood Street',
    14: 'Shakespeare',
    15: 'Austin',
    16: 'Jefferson Park',
    17: 'Albany Park',
    18: 'Near North',
    19: 'Town Hall',
    20: 'Lincoln',
    21: 'Prairie Avenue',
    22: 'Morgan Park',
    23: 'Rogers Park',
    24: 'Roosevelt',
    25: 'Grand Central'
}

# ============================================
# CARGAR DATOS
# ============================================
@st.cache_data(ttl=3600)
def cargar_datos():
    """Carga los datos desde Google Drive usando FILE_ID desde .env"""
    
    # 🔐 Leer FILE_ID desde variable de entorno
    file_id = os.getenv("GDRIVE_FILE_ID")
    
    if not file_id:
        st.error("❌ Error: GDRIVE_FILE_ID no está configurado en el archivo .env")
        st.info("Asegúrate de tener un archivo .env con: GDRIVE_FILE_ID=tu_id_aqui")
        return pd.DataFrame()
    
    # Construir URL de descarga directa
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
            df['Date'] = pd.to_datetime(df['Date'])
            
            # Agregar nombre del distrito
            df['District_Name'] = df['District'].map(distritos_nombres)
            
            return df
            
        except Exception as e:
            st.error(f"Error al cargar datos: {e}")
            return pd.DataFrame()

# Título principal
st.title("🚔 Dashboard de Análisis de Crímenes - Chicago")
st.markdown("---")
# Cargar datos
with st.spinner("🔄 Procesando datos..."):
    df = cargar_datos()

if df.empty:
    st.stop()

# Mostrar éxito
st.success(f"✅ Datos cargados: {len(df):,} registros")

# ============================================
# SIDEBAR - FILTROS MEJORADOS
# ============================================
st.sidebar.header("🔍 Filtros")

# Filtro de fecha
st.sidebar.subheader("📅 Rango de Fechas")
min_date = df['Date'].min().date()
max_date = df['Date'].max().date()
fecha_inicio = st.sidebar.date_input("Fecha inicio", min_date, min_value=min_date, max_value=max_date)
fecha_fin = st.sidebar.date_input("Fecha fin", max_date, min_value=min_date, max_value=max_date)

# Filtro de tipo de crimen
st.sidebar.subheader("📋 Tipo de Crimen")
tipos_crimen = ['Todos'] + sorted(df['Primary Type'].unique().tolist())
tipo_seleccionado = st.sidebar.selectbox("Seleccionar tipo", tipos_crimen)

# Filtro de arresto
st.sidebar.subheader("👮 Arresto")
arresto_opciones = ['Todos', 'Con Arresto', 'Sin Arresto']
arresto_seleccionado = st.sidebar.selectbox("Estado de arresto", arresto_opciones)

# Filtro doméstico
st.sidebar.subheader("🏠 Doméstico")
domestico_opciones = ['Todos', 'Doméstico', 'No Doméstico']
domestico_seleccionado = st.sidebar.selectbox("Tipo", domestico_opciones)

# Filtro de hora del día
st.sidebar.subheader("⏰ Hora del día")
horas = ['Todas', 'Madrugada', 'Mañana', 'Tarde', 'Noche']
hora_seleccionada = st.sidebar.selectbox("Seleccionar hora", horas)

# Filtro de distrito - AHORA CON NOMBRES
st.sidebar.subheader("🏢 Distrito")
# Crear opciones con nombres
distritos_opciones = ['Todos'] + sorted(df['District_Name'].unique().tolist())
distrito_seleccionado = st.sidebar.selectbox("Seleccionar distrito", distritos_opciones)

# ============================================
# APLICAR FILTROS
# ============================================
df_filtrado = df.copy()

# Filtro de fecha
df_filtrado = df_filtrado[(df_filtrado['Date'].dt.date >= fecha_inicio) & 
                          (df_filtrado['Date'].dt.date <= fecha_fin)]

# Filtro de tipo de crimen
if tipo_seleccionado != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['Primary Type'] == tipo_seleccionado]

# Filtro de arresto
if arresto_seleccionado == 'Con Arresto':
    df_filtrado = df_filtrado[df_filtrado['Arrest'] == True]
elif arresto_seleccionado == 'Sin Arresto':
    df_filtrado = df_filtrado[df_filtrado['Arrest'] == False]

# Filtro doméstico
if domestico_seleccionado == 'Doméstico':
    df_filtrado = df_filtrado[df_filtrado['Domestic'] == True]
elif domestico_seleccionado == 'No Doméstico':
    df_filtrado = df_filtrado[df_filtrado['Domestic'] == False]

# Filtro de hora
if hora_seleccionada != 'Todas':
    df_filtrado = df_filtrado[df_filtrado['TimeOfDay'] == hora_seleccionada]

# Filtro de distrito (usando nombre)
if distrito_seleccionado != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['District_Name'] == distrito_seleccionado]

# ============================================
# KPI CARDS
# ============================================
st.subheader("📊 Indicadores Clave")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Crímenes", f"{len(df_filtrado):,}")

with col2:
    tasa_arrestos = (df_filtrado['Arrest'].sum() / len(df_filtrado) * 100) if len(df_filtrado) > 0 else 0
    st.metric("Tasa de Arrestos", f"{tasa_arrestos:.1f}%")

with col3:
    tasa_domestico = (df_filtrado['Domestic'].sum() / len(df_filtrado) * 100) if len(df_filtrado) > 0 else 0
    st.metric("Crímenes Domésticos", f"{tasa_domestico:.1f}%")

with col4:
    distritos_afectados = df_filtrado['District'].nunique()
    st.metric("Distritos Afectados", f"{distritos_afectados}")

st.markdown("---")

# ============================================
# GRÁFICOS PRINCIPALES
# ============================================

# Gráfico 1: Evolución temporal
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 Evolución de Crímenes")
    crimenes_por_fecha = df_filtrado.groupby(df_filtrado['Date'].dt.date).size().reset_index(name='count')
    fig_line = px.line(crimenes_por_fecha, x='Date', y='count', 
                       title="Crímenes por día",
                       labels={'Date': 'Fecha', 'count': 'Número de Crímenes'})
    fig_line.update_layout(height=400)
    st.plotly_chart(fig_line, use_container_width=True)

with col2:
    st.subheader("🥧 Tipos de Crimen")
    top_crimenes = df_filtrado['Primary Type'].value_counts().head(10).reset_index()
    top_crimenes.columns = ['Tipo', 'Cantidad']
    fig_pie = px.pie(top_crimenes, values='Cantidad', names='Tipo', 
                     title="Top 10 Tipos de Crímenes")
    fig_pie.update_layout(height=400)
    st.plotly_chart(fig_pie, use_container_width=True)

# Gráfico 2: Crimen por hora y día
st.subheader("⏰ Patrones Temporales")
col1, col2 = st.columns(2)

with col1:
    crimen_por_hora = df_filtrado.groupby('Hour').size().reset_index(name='count')
    fig_hour = px.bar(crimen_por_hora, x='Hour', y='count',
                      title="Crímenes por Hora",
                      labels={'Hour': 'Hora', 'count': 'Número de Crímenes'})
    fig_hour.update_layout(height=400)
    st.plotly_chart(fig_hour, use_container_width=True)

with col2:
    crimen_por_dia = df_filtrado.groupby('DayName').size().reset_index(name='count')
    orden_dias = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    # Traducir días al español
    traduccion_dias = {
        'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
        'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
    }
    crimen_por_dia['DayName_ES'] = crimen_por_dia['DayName'].map(traduccion_dias)
    orden_dias_es = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    crimen_por_dia['DayName_ES'] = pd.Categorical(crimen_por_dia['DayName_ES'], categories=orden_dias_es, ordered=True)
    crimen_por_dia = crimen_por_dia.sort_values('DayName_ES')
    fig_day = px.bar(crimen_por_dia, x='DayName_ES', y='count',
                     title="Crímenes por Día de la Semana",
                     labels={'DayName_ES': 'Día', 'count': 'Número de Crímenes'})
    fig_day.update_layout(height=400)
    st.plotly_chart(fig_day, use_container_width=True)

# Gráfico 3: Top distritos con nombres
st.subheader("🗺️ Crímenes por Distrito")

crimen_por_distrito = df_filtrado.groupby(['District', 'District_Name']).size().reset_index(name='count')
crimen_por_distrito = crimen_por_distrito.sort_values('count', ascending=False).head(15)

fig_district = px.bar(crimen_por_distrito, x='District_Name', y='count',
                      title="Top 15 Distritos con Más Crímenes",
                      labels={'District_Name': 'Distrito', 'count': 'Número de Crímenes'},
                      color='count',
                      color_continuous_scale='Reds')
fig_district.update_layout(height=450, xaxis_tickangle=-45)
st.plotly_chart(fig_district, use_container_width=True)

# Gráfico 4: Mapa de calor
st.subheader("🔥 Mapa de Calor: Hora vs Día")

heatmap_data = df_filtrado.groupby(['DayOfWeek', 'Hour']).size().reset_index(name='count')
dias_es = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}
heatmap_data['DayName_ES'] = heatmap_data['DayOfWeek'].map(dias_es)

fig_heatmap = px.density_heatmap(heatmap_data, x='Hour', y='DayName_ES', z='count',
                                  title="Intensidad de Crímenes por Hora y Día",
                                  labels={'Hour': 'Hora', 'DayName_ES': 'Día', 'count': 'Cantidad'},
                                  color_continuous_scale='YlOrRd')
fig_heatmap.update_layout(height=500)
st.plotly_chart(fig_heatmap, use_container_width=True)

# ============================================
# TABLA DE DATOS MEJORADA
# ============================================
st.subheader("📋 Datos Detallados")
with st.expander("Ver tabla de datos"):
    # Seleccionar columnas para mostrar
    columnas_mostrar = ['ID', 'Date', 'Primary Type', 'Description', 'District_Name', 
                        'Arrest', 'Domestic', 'TimeOfDay', 'Block']
    df_mostrar = df_filtrado[columnas_mostrar].head(100)
    df_mostrar = df_mostrar.rename(columns={
        'Primary Type': 'Tipo de Crimen',
        'District_Name': 'Distrito',
        'TimeOfDay': 'Hora del Día',
        'Block': 'Ubicación'
    })
    st.dataframe(df_mostrar, use_container_width=True)
    
    # Descargar datos
    csv = df_filtrado.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar datos filtrados (CSV)",
        data=csv,
        file_name="crimes_filtrados.csv",
        mime="text/csv",
    )

# ============================================
# ESTADÍSTICAS ADICIONALES
# ============================================
st.markdown("---")
st.subheader("📊 Estadísticas Adicionales")

col1, col2, col3 = st.columns(3)

with col1:
    st.write("**🏆 Top 5 Distritos (por nombre)**")
    top_distritos = df_filtrado['District_Name'].value_counts().head(5)
    for distrito, count in top_distritos.items():
        st.write(f"- **{distrito}** → {count:,} crímenes")

with col2:
    st.write("**⏰ Top 5 Horas con más crímenes**")
    top_horas = df_filtrado['Hour'].value_counts().head(5)
    for hora, count in top_horas.items():
        st.write(f"- {hora:02d}:00 → {count:,} crímenes")

with col3:
    st.write("**📍 Top 5 Ubicaciones**")
    top_locaciones = df_filtrado['Location Description'].value_counts().head(5)
    for loc, count in top_locaciones.items():
        st.write(f"- {loc[:35]} → {count:,}")

# ============================================
# PIE DE PÁGINA
# ============================================
st.markdown("---")
st.caption(f"Dashboard actualizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Datos: {len(df):,} registros de crímenes de Chicago")