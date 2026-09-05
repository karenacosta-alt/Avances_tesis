import os
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.graph_objs as go
from streamlit_autorefresh import st_autorefresh
from datetime import date, timedelta

# Configuración de pantalla
st.set_page_config(page_title="Monitor IAGRO", layout="wide")
st_autorefresh(interval=15000, key="datarefresh")

# Variables de entorno para la Base de Datos
DB_USER = os.getenv("DB_USER", "estacion_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "tu_contrasena_aqui")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "estacion_db")

# Conexión limpia a Base de Datos
engine = create_engine(f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')
# ==========================================
# 🎛️ PANEL LATERAL (Filtros y Descargas)
# ==========================================
st.sidebar.header("⚙️ Filtros y Análisis")

# Selector de fechas (Por defecto: últimos 3 días)
fecha_inicio = st.sidebar.date_input("Fecha Inicio", date.today() - timedelta(days=3))
fecha_fin = st.sidebar.date_input("Fecha Fin", date.today())

def get_data(inicio, fin):
    try:
        # Sumamos un día al fin para incluir las lecturas hasta las 23:59 de ese día
        fin_plus_one = fin + timedelta(days=1)
        query = f"""
            SELECT * FROM lecturas 
            WHERE timestamp >= '{inicio}' AND timestamp < '{fin_plus_one}' 
            ORDER BY timestamp ASC
        """
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        st.sidebar.error(f"Error DB: {e}")
        return pd.DataFrame()

# ==========================================
# 📊 PANTALLA PRINCIPAL
# ==========================================
st.title("🖥️ Monitoreo de Calidad del Aire - ITR Centro-Sur")

df = get_data(fecha_inicio, fecha_fin)

if not df.empty:
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # --- DESCARGA DE DATOS CSV ---
    csv = df.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button(
        label="📥 Descargar datos (CSV)",
        data=csv,
        file_name=f'datos_iagro_{fecha_inicio}_al_{fecha_fin}.csv',
        mime='text/csv',
    )

    # ==========================================
    # ⏱️ MÉTRICAS ACTUALES (Última lectura)
    # ==========================================
    st.markdown("### Valores Actuales (Última medición)")
    ultima_lectura = df.iloc[-1]
    hora_actualizacion = ultima_lectura['timestamp'].strftime("%H:%M:%S")
    
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Temperatura", f"{ultima_lectura['temperatura_c']} °C")
    m2.metric("Humedad", f"{ultima_lectura['humedad_pct']} %")
    m3.metric("CO2", f"{ultima_lectura['co2_ppm']} PPM")
    m4.metric("CO", f"{ultima_lectura['co_ppm']} PPM")
    m5.metric("PM 2.5", f"{ultima_lectura['pm25_ugm3']} µg/m³")
    st.caption(f"Última actualización local: {hora_actualizacion}")
    st.divider()

    # ==========================================
    # 📈 GRÁFICOS TEMPORALES CON LÍMITES NORMATIVOS
    # ==========================================
    
    # --- FILA 1: Temperatura y Humedad ---
    col1, col2 = st.columns(2)
    with col1:
        fig_temp = go.Figure()
        fig_temp.add_trace(go.Scatter(x=df["timestamp"], y=df["temperatura_c"], name="Temp °C", line=dict(color='#FF4B4B')))
        fig_temp.update_layout(title=dict(text="Temperatura (°C)", y=0.9), margin=dict(t=80), height=350)
        st.plotly_chart(fig_temp, use_container_width=True)

    with col2:
        fig_hum = go.Figure()
        fig_hum.add_trace(go.Scatter(x=df["timestamp"], y=df["humedad_pct"], name="Hum %", line=dict(color='#1C83E1')))
        fig_hum.update_layout(title=dict(text="Humedad (%)", y=0.9), margin=dict(t=80), height=350)
        st.plotly_chart(fig_hum, use_container_width=True)

    # --- FILA 2: Gases separados (CO2 y CO) ---
    col3, col4 = st.columns(2)
    with col3:
        fig_co2 = go.Figure()
        fig_co2.add_trace(go.Scatter(x=df["timestamp"], y=df["co2_ppm"], name="CO2", line=dict(color='#39FF14')))
        # LÍMITE INTERIOR CO2 (ASHRAE/OMS)
        fig_co2.add_hline(y=1000, line_dash="dash", line_color="red", 
                          annotation_text="Límite Interior (1000 PPM)", annotation_position="top left")
        fig_co2.update_layout(title=dict(text="Dióxido de Carbono - CO2 (PPM)", y=0.9), margin=dict(t=80), height=350)
        st.plotly_chart(fig_co2, use_container_width=True)

    with col4:
        fig_co = go.Figure()
        fig_co.add_trace(go.Scatter(x=df["timestamp"], y=df["co_ppm"], name="CO", line=dict(color='#BC13FE')))
        # LÍMITE CO (Dec. 135/021 - Aprox 9 PPM para 8 horas)
        fig_co.add_hline(y=9, line_dash="dash", line_color="red", 
                         annotation_text="Límite Decreto 135/021 (9 PPM)", annotation_position="top left")
        fig_co.update_layout(title=dict(text="Monóxido de Carbono - CO (PPM)", y=0.9), margin=dict(t=80), height=350)
        st.plotly_chart(fig_co, use_container_width=True)

    # --- FILA 3: Material Particulado ---
    fig_pm = go.Figure()
    fig_pm.add_trace(go.Scatter(x=df["timestamp"], y=df["pm1_ugm3"], name="PM 1.0", line=dict(color='#FFCA28')))
    fig_pm.add_trace(go.Scatter(x=df["timestamp"], y=df["pm25_ugm3"], name="PM 2.5", line=dict(color='#FF7043')))
    fig_pm.add_trace(go.Scatter(x=df["timestamp"], y=df["pm10_ugm3"], name="PM 10", line=dict(color='#8D6E63')))
    
    # LÍMITES MATERIAL PARTICULADO (Decreto 135/021)
    fig_pm.add_hline(y=25, line_dash="dash", line_color="red", 
                     annotation_text="Límite PM 2.5 (25 µg/m³)", annotation_position="top left")
    fig_pm.add_hline(y=75, line_dash="dash", line_color="darkred", 
                     annotation_text="Límite PM 10 (75 µg/m³)", annotation_position="top left")
    
    fig_pm.update_layout(
        title=dict(text="Material Particulado (µg/m³) vs Decreto 135/021", y=0.9),
        margin=dict(t=80),
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    )
    st.plotly_chart(fig_pm, use_container_width=True)

else:
    st.warning("No hay datos disponibles para el rango de fechas seleccionado.")
