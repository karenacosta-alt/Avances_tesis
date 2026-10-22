"""
Panel de visualización — red de monitoreo de calidad del aire, ITR Centro-Sur.

Cambios respecto de la versión anterior:
- Serie filtrada (Filtro de Kalman escalar según Lai et al., 2019, + media
  móvil de k=3) calculada al cargar los datos. No se almacena en la base: se recalcula siempre a partir del
  dato crudo.
- Opciones en el panel lateral para mostrar la serie cruda, la filtrada o ambas.
- La descarga CSV incluye las columnas filtradas.
"""

import os
from datetime import date, timedelta

import numpy as np
import pandas as pd
import plotly.graph_objs as go
<<<<<<< Updated upstream
from datetime import date, timedelta
import os

# Credenciales desde variables de entorno o genéricas para el repositorio público
DB_USER = os.getenv("DB_USER", "estacion_user")
DB_PASS = os.getenv("DB_PASS", "TU_PASSWORD_AQUI")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_NAME = os.getenv("DB_NAME", "estacion_db")

engine = create_engine(f'postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:5432/{DB_NAME}')
# ==========================================
# 🎨 PALETA DE COLORES Y ESTILOS
# ==========================================
PALETTE = {
    "surface": "#fcfcfb",
    "text_primary": "#0b0b0b",
    "text_secondary": "#52514e",
    "muted": "#898781",
    "grid": "#e1e0d9",
    "baseline": "#c3c2b7",
    "blue": "#2a78d6",
    "orange": "#eb6834",
    "aqua": "#1baf7a",
    "violet": "#4a3aa7",
}
STATUS_COLOR = {"good": "#0ca30c", "warning": "#fab219", "critical": "#d03b3b", "nodata": "#898781"}
STATUS_LABEL = {"good": "Buena", "warning": "Moderada", "critical": "Crítica", "nodata": "Sin Datos"}
STATUS_ICON = {"good": "🟢", "warning": "🟡", "critical": "🔴", "nodata": "⚪"}

LIMITE_CO2 = 1000
LIMITE_CO = 9
LIMITE_PM25 = 25
LIMITE_PM10 = 75
WARN_RATIO = 0.75

FONT_FAMILY = "system-ui, -apple-system, 'Segoe UI', sans-serif"

st.markdown(f"""
=======
from sqlalchemy import create_engine
import streamlit as st

DB_USER = os.getenv("DB_USER", "estacion_user")
DB_PASS = os.getenv("DB_PASS", "estacion123")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_NAME = os.getenv("DB_NAME", "estacion_db")
DB_PORT = os.getenv("DB_PORT", "5432")

engine = create_engine(
    f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    connect_args={"connect_timeout": 5},
)

# ==========================================
# Parámetros del filtrado
# ==========================================
# Filtro de Kalman escalar según Lai et al. (2019): se asume que la
# concentración no cambia de estado entre lecturas sucesivas y que no hay
# variables de control (matriz de transición = 1, término de control = 0).
#   Predicción:   x = x            P = P + Q
#   Actualización: K = P / (P + R)  x = x + K (z - x)   P = (1 - K) P
# Q y R son constantes. Siguiendo a Lai et al. (2019), R es la varianza del
# error de medición del sensor y Q se ajusta por búsqueda en grilla
# minimizando el RMSE frente a un instrumento de referencia; ese ajuste se
# hará con los datos de la co-localización con la AQM65.
# El filtrado queda DESHABILITADO hasta ajustar Q y R con los datos de la
# co-localización. Para habilitarlo: reemplazar KALMAN_Q y KALMAN_R por los
# valores ajustados y poner KALMAN_HABILITADO = True.
KALMAN_HABILITADO = False
KALMAN_Q = 1.0
KALMAN_R = 1.0
K_MEDIA_MOVIL = 3        # ventana de la media móvil aplicada sobre la salida del Kalman

VARIABLES_FILTRADAS = [
    "temperatura_c", "humedad_pct", "co2_ppm", "co_ppm",
    "pm1_ugm3", "pm25_ugm3", "pm10_ugm3",
]

PALETTE = {
    "surface": "#fcfcfb",
    "text_primary": "#0b0b0b",
    "text_secondary": "#52514e",
    "muted": "#898781",
    "grid": "#e1e0d9",
    "baseline": "#c3c2b7",
    "blue": "#2a78d6",
    "orange": "#eb6834",
    "aqua": "#1baf7a",
    "violet": "#4a3aa7",
}
FONT_FAMILY = "system-ui, -apple-system, 'Segoe UI', sans-serif"

st.set_page_config(
    page_title="Monitoreo ITR Centro-Sur", page_icon="🌡️", layout="wide"
)

st.markdown(
    f"""
>>>>>>> Stashed changes
<style>
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    .block-container {{ padding-top: 1.6rem; padding-bottom: 2rem; }}

    .app-header {{
        display: flex; align-items: center; justify-content: space-between;
        flex-wrap: wrap; gap: 0.6rem; margin-bottom: 0.4rem;
    }}
    .app-title {{ font-size: 1.65rem; font-weight: 700; color: {PALETTE["text_primary"]}; margin: 0; }}
    .app-subtitle {{ font-size: 0.92rem; color: {PALETTE["text_secondary"]}; margin-top: 2px; }}

<<<<<<< Updated upstream
    .status-pill {{
        display: inline-flex; align-items: center; gap: 6px;
        padding: 6px 14px; border-radius: 999px; font-weight: 600; font-size: 0.9rem;
        white-space: nowrap;
    }}

=======
>>>>>>> Stashed changes
    .kpi-card {{
        background: {PALETTE["surface"]};
        border: 1px solid {PALETTE["grid"]};
        border-left: 4px solid {PALETTE["baseline"]};
        border-radius: 10px;
        padding: 12px 16px;
        height: 100%;
    }}
    .kpi-top {{ display: flex; align-items: center; gap: 6px; margin-bottom: 6px; }}
    .kpi-icon {{ font-size: 1.05rem; }}
    .kpi-label {{ font-size: 0.82rem; color: {PALETTE["text_secondary"]}; font-weight: 600; }}
    .kpi-value {{ font-size: 1.7rem; font-weight: 700; color: {PALETTE["text_primary"]}; line-height: 1.1; }}
    .kpi-unit {{ font-size: 0.95rem; font-weight: 500; color: {PALETTE["muted"]}; margin-left: 3px; }}
<<<<<<< Updated upstream
    .kpi-badge {{
        display: inline-block; margin-top: 8px; padding: 2px 9px; border-radius: 999px;
        font-size: 0.75rem; font-weight: 600;
    }}
=======
>>>>>>> Stashed changes
    .section-title {{
        font-size: 1.05rem; font-weight: 700; color: {PALETTE["text_primary"]};
        margin: 0.3rem 0 0.6rem 0;
    }}
</style>
<<<<<<< Updated upstream
""", unsafe_allow_html=True)


# ==========================================
# 🛠️ FUNCIONES DE APOYO (Tratamiento estricto de 0)
# ==========================================
def evaluar_estado(valor, limite):
    if valor is None or pd.isna(valor):
        return "nodata"
    v = float(valor)
    if v >= limite:
        return "critical"
    if v >= (limite * WARN_RATIO):
        return "warning"
    return "good"


def kpi_card(icon, label, valor_num, unit, estado=None, decimales=1):
    # Verificación estricta: 0 o 0.0 NUNCA son considerados N/A
=======
""",
    unsafe_allow_html=True,
)


# ==========================================
# Filtrado: Kalman + media móvil
# ==========================================
def filtro_kalman(valores):
    """Filtro de Kalman escalar con Q y R constantes (Lai et al., 2019).

    El estado inicial es la primera lectura válida. Las lecturas faltantes
    no se rellenan: quedan vacías y el filtro continúa con la siguiente.
    """
    z = np.asarray(valores, dtype=float)
    salida = np.full(z.shape, np.nan)
    x = None
    P = None
    for i, zk in enumerate(z):
        if np.isnan(zk):
            continue
        if x is None:
            x, P = zk, KALMAN_R
        else:
            P = P + KALMAN_Q                 # predicción
            K = P / (P + KALMAN_R)           # ganancia de Kalman
            x = x + K * (zk - x)             # actualización
            P = (1.0 - K) * P
        salida[i] = x
    return salida


def agregar_series_filtradas(df):
    """Agrega una columna <variable>_filtrado por cada variable medida."""
    for col in VARIABLES_FILTRADAS:
        if col not in df.columns:
            continue
        kalman = filtro_kalman(df[col].to_numpy(dtype=float))
        df[f"{col}_filtrado"] = (
            pd.Series(kalman, index=df.index)
            .rolling(window=K_MEDIA_MOVIL, min_periods=1)
            .mean()
            .where(df[col].notna())
        )
    return df


# ==========================================
# Componentes visuales
# ==========================================
def kpi_card(icon, label, valor_num, unit, decimales=1):
>>>>>>> Stashed changes
    if valor_num is None or pd.isna(valor_num):
        value_text = "N/A"
    else:
        value_text = f"{float(valor_num):.{decimales}f}"

<<<<<<< Updated upstream
    if estado and estado in STATUS_COLOR:
        color = STATUS_COLOR[estado]
        badge = (f'<span class="kpi-badge" style="background:{color}22; color:{color};">'
                 f'{STATUS_ICON[estado]} {STATUS_LABEL[estado]}</span>')
    else:
        color = PALETTE["baseline"]
        badge = ""

    st.markdown(f"""
    <div class="kpi-card" style="border-left-color:{color};">
        <div class="kpi-top"><span class="kpi-icon">{icon}</span><span class="kpi-label">{label}</span></div>
        <div class="kpi-value">{value_text}<span class="kpi-unit">{unit}</span></div>
        {badge}
    </div>
    """, unsafe_allow_html=True)


def hex_to_rgba(hex_color, alpha):
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
=======
    st.markdown(
        f"""
    <div class="kpi-card">
        <div class="kpi-top"><span class="kpi-icon">{icon}</span><span class="kpi-label">{label}</span></div>
        <div class="kpi-value">{value_text}<span class="kpi-unit">{unit}</span></div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def hex_to_rgba(hex_color, alpha):
    hex_color = hex_color.lstrip("#")
    r, g, b = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
>>>>>>> Stashed changes
    return f"rgba({r},{g},{b},{alpha})"


def style_fig(fig, titulo, show_legend=False, y_title=None):
    fig.update_layout(
        template="plotly_white",
        font=dict(family=FONT_FAMILY, color=PALETTE["text_primary"], size=13),
<<<<<<< Updated upstream
        title=dict(text=titulo, x=0.01, xanchor="left", y=0.94,
                   font=dict(size=16, color=PALETTE["text_primary"])),
        plot_bgcolor=PALETTE["surface"],
        paper_bgcolor=PALETTE["surface"],
        hovermode="x unified",
        hoverlabel=dict(bgcolor="white", bordercolor=PALETTE["grid"],
                        font_size=12, font_color=PALETTE["text_primary"]),
        showlegend=show_legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.06, xanchor="center", x=0.5,
                    bgcolor="rgba(0,0,0,0)") if show_legend else None,
        margin=dict(t=70, b=40, l=55, r=30),
        height=360,
    )
    fig.update_xaxes(showgrid=False, showline=True, linecolor=PALETTE["baseline"], color=PALETTE["muted"])
    fig.update_yaxes(showgrid=True, gridcolor=PALETTE["grid"], gridwidth=1, zeroline=False,
                     color=PALETTE["muted"], title=y_title)
    return fig


def linea(x, y, nombre, color, con_relleno=True):
    trace = go.Scatter(x=x, y=y, name=nombre, mode="lines", line=dict(color=color, width=2))
    if con_relleno:
        trace.fill = "tozeroy"
        trace.fillcolor = hex_to_rgba(color, 0.08)
    return trace


=======
        title=dict(
            text=titulo,
            x=0.01,
            xanchor="left",
            y=0.94,
            font=dict(size=16, color=PALETTE["text_primary"]),
        ),
        plot_bgcolor=PALETTE["surface"],
        paper_bgcolor=PALETTE["surface"],
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="white",
            bordercolor=PALETTE["grid"],
            font_size=12,
            font_color=PALETTE["text_primary"],
        ),
        showlegend=show_legend,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.06,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(0,0,0,0)",
        )
        if show_legend
        else None,
        margin=dict(t=70, b=40, l=55, r=30),
        height=360,
    )
    fig.update_xaxes(
        showgrid=False,
        showline=True,
        linecolor=PALETTE["baseline"],
        color=PALETTE["muted"],
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=PALETTE["grid"],
        gridwidth=1,
        zeroline=False,
        color=PALETTE["muted"],
        title=y_title,
    )
    return fig


>>>>>>> Stashed changes
def marcador_actual(fig, x, y, color):
    s_valid = y.dropna()
    if s_valid.empty:
        return
    last_idx = s_valid.index[-1]
<<<<<<< Updated upstream
    fig.add_trace(go.Scatter(
        x=[x.loc[last_idx]], y=[s_valid.loc[last_idx]], mode="markers",
        marker=dict(size=9, color=color, line=dict(width=2, color="white")),
        showlegend=False, hoverinfo="skip",
    ))


def linea_limite(fig, y_valor, texto):
    fig.add_hline(
        y=y_valor, line_dash="dash", line_color=STATUS_COLOR["critical"], line_width=1.5,
        annotation_text=texto, annotation_position="top left",
        annotation_font=dict(size=11, color=PALETTE["text_secondary"]),
        annotation_bgcolor="rgba(255,255,255,0.85)",
    )


# ==========================================
# 🎛️ PANEL LATERAL Y CONSULTA A BASE DE DATOS
# ==========================================
st.sidebar.header("⚙️ Filtros y Análisis")

fecha_inicio = st.sidebar.date_input("Fecha Inicio", date.today() - timedelta(days=3))
fecha_fin = st.sidebar.date_input("Fecha Fin", date.today())

st.sidebar.caption("⏱️ Frecuencia de muestreo: Cada 15 minutos.")


@st.cache_data(ttl=10)
def get_data(inicio, fin):
    try:
        fin_plus_one = fin + timedelta(days=1)
        query = f"""
            SELECT timestamp, temperatura_c, humedad_pct, co2_ppm, co_ppm, pm1_ugm3, pm25_ugm3, pm10_ugm3 
            FROM lecturas
            WHERE timestamp >= '{inicio}' AND timestamp < '{fin_plus_one}'
            ORDER BY timestamp DESC
            LIMIT 1000
        """
        df = pd.read_sql(query, engine)
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values("timestamp").reset_index(drop=True)
        return df
    except Exception as e:
        st.sidebar.error(f"Error DB: {e}")
        return pd.DataFrame()


# ==========================================
# 📊 PANTALLA PRINCIPAL
# ==========================================
df = get_data(fecha_inicio, fecha_fin)

if not df.empty:
    # Función para recuperar el último dato numérico válido (conservando 0)
    def obtener_ultimo_valido(columna):
        if columna in df.columns:
            serie_valida = df[columna].dropna()
            if not serie_valida.empty:
                return serie_valida.iloc[-1]
        return None

    temp_val = obtener_ultimo_valido('temperatura_c')
    hum_val  = obtener_ultimo_valido('humedad_pct')
    co2_val  = obtener_ultimo_valido('co2_ppm')
    co_val   = obtener_ultimo_valido('co_ppm')
    pm25_val = obtener_ultimo_valido('pm25_ugm3')
    pm10_val = obtener_ultimo_valido('pm10_ugm3')

    ultima_lectura = df.iloc[-1]
    hora_actualizacion = ultima_lectura['timestamp'].strftime("%H:%M:%S")

    # --- Estado general ---
    estados = [
        evaluar_estado(co2_val, LIMITE_CO2),
        evaluar_estado(co_val, LIMITE_CO),
        evaluar_estado(pm25_val, LIMITE_PM25),
        evaluar_estado(pm10_val, LIMITE_PM10),
    ]
    orden = {"critical": 3, "warning": 2, "good": 1, "nodata": 0}
    estado_general = max(estados, key=lambda e: orden[e])
    color_general = STATUS_COLOR[estado_general]

    col_header1, col_header2 = st.columns([3, 1])
    with col_header1:
        st.markdown(f"""
        <div class="app-header">
            <div>
                <p class="app-title">🖥️ Monitoreo de Calidad del Aire — ITR Centro-Sur</p>
                <p class="app-subtitle">Red de sensores IoT · Última medición {hora_actualizacion}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col_header2:
        st.markdown(f"""
        <div style="text-align:right; padding-top:8px;">
            <span class="status-pill" style="background:{color_general}22; color:{color_general};">
                {STATUS_ICON[estado_general]} Estado general: {STATUS_LABEL[estado_general]}
            </span>
        </div>
        """, unsafe_allow_html=True)

    # --- DESCARGA DE DATOS CSV ---
    csv = df.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button(
        label="📥 Descargar datos (CSV)",
        data=csv,
        file_name=f'datos_iagro_{fecha_inicio}_al_{fecha_fin}.csv',
        mime='text/csv',
=======
    fig.add_trace(
        go.Scatter(
            x=[x.loc[last_idx]],
            y=[s_valid.loc[last_idx]],
            mode="markers",
            marker=dict(
                size=9, color=color, line=dict(width=2, color="white")
            ),
            showlegend=False,
            hoverinfo="skip",
        )
    )


def agregar_variable(fig, df, col, nombre, color, con_relleno=True):
    """Agrega la serie cruda y/o filtrada de una variable, según lo elegido."""
    x = df["timestamp"]
    col_filt = f"{col}_filtrado"
    ambas = mostrar_crudo and mostrar_filtrado and col_filt in df.columns

    if mostrar_crudo:
        fig.add_trace(
            go.Scatter(
                x=x, y=df[col], name=f"{nombre} (crudo)" if ambas else nombre,
                mode="lines",
                line=dict(color=hex_to_rgba(color, 0.35) if ambas else color,
                          width=1 if ambas else 2),
                fill="tozeroy" if (con_relleno and not ambas) else None,
                fillcolor=hex_to_rgba(color, 0.08),
            )
        )
    if mostrar_filtrado and col_filt in df.columns:
        fig.add_trace(
            go.Scatter(
                x=x, y=df[col_filt], name=f"{nombre} (filtrado)" if ambas else nombre,
                mode="lines",
                line=dict(color=color, width=2),
                fill="tozeroy" if (con_relleno and not ambas) else None,
                fillcolor=hex_to_rgba(color, 0.08),
            )
        )

    serie_marcador = df[col_filt] if (mostrar_filtrado and col_filt in df.columns) else df[col]
    marcador_actual(fig, x, serie_marcador, color)
    return ambas


# ==========================================
# Panel lateral y consulta
# ==========================================
st.sidebar.header("⚙️ Filtros y Análisis")


@st.cache_data(ttl=30)
def get_estaciones():
    try:
        return pd.read_sql(
            "SELECT codigo FROM estaciones ORDER BY codigo",
            engine,
        )["codigo"].tolist()
    except Exception as e:
        st.sidebar.error(f"Error DB al obtener estaciones: {e}")
        return []


estaciones_disponibles = get_estaciones()

if not estaciones_disponibles:
    st.sidebar.warning("Todavía no hay estaciones registradas en la base.")
    st.stop()

estacion_sel = st.sidebar.selectbox(
    "Selecciona Estación", estaciones_disponibles
)

fecha_inicio = st.sidebar.date_input(
    "Fecha Inicio", date.today() - timedelta(days=3)
)
fecha_fin = st.sidebar.date_input("Fecha Fin", date.today())

st.sidebar.caption("⏱️ Frecuencia de muestreo: Cada 15 minutos.")

if KALMAN_HABILITADO:
    st.sidebar.subheader("Series a mostrar")
    mostrar_crudo = st.sidebar.checkbox("Datos crudos", value=True)
    mostrar_filtrado = st.sidebar.checkbox("Serie filtrada (Kalman + media móvil)", value=True)
    if not (mostrar_crudo or mostrar_filtrado):
        st.sidebar.warning("Seleccioná al menos una serie.")
        mostrar_crudo = True
    st.sidebar.caption(
        f"La serie filtrada se calcula al cargar los datos (Filtro de Kalman y media "
        f"móvil de {K_MEDIA_MOVIL} registros) y no se almacena en la base."
    )
else:
    mostrar_crudo = True
    mostrar_filtrado = False


@st.cache_data(ttl=10)
def get_data(codigo_estacion, inicio, fin):
    try:
        fin_plus_one = fin + timedelta(days=1)
        query = """
            SELECT l.timestamp, l.temperatura_c, l.humedad_pct, l.co2_ppm, l.co_ppm,
                   l.pm1_ugm3, l.pm25_ugm3, l.pm10_ugm3
            FROM lecturas l
            JOIN estaciones e ON e.id = l.estacion_id
            WHERE e.codigo = %(codigo)s
              AND l.timestamp >= %(inicio)s AND l.timestamp < %(fin_plus_one)s
            ORDER BY l.timestamp ASC
        """
        df = pd.read_sql(
            query,
            engine,
            params={
                "codigo": codigo_estacion,
                "inicio": inicio,
                "fin_plus_one": fin_plus_one,
            },
        )
        if not df.empty:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.sort_values("timestamp").reset_index(drop=True)
            if KALMAN_HABILITADO:
                df = agregar_series_filtradas(df)
        return df
    except Exception as e:
        st.sidebar.error(f"Error DB al consultar mediciones: {e}")
        return pd.DataFrame()


df = get_data(estacion_sel, fecha_inicio, fecha_fin)

if not df.empty:

    def obtener_ultimo_valido(columna):
        if columna in df.columns:
            serie_valida = df[columna].dropna()
            if not serie_valida.empty:
                return serie_valida.iloc[-1]
        return None

    temp_val = obtener_ultimo_valido("temperatura_c")
    hum_val = obtener_ultimo_valido("humedad_pct")
    co2_val = obtener_ultimo_valido("co2_ppm")
    co_val = obtener_ultimo_valido("co_ppm")
    pm25_val = obtener_ultimo_valido("pm25_ugm3")

    ultima_lectura = df.iloc[-1]
    hora_actualizacion = ultima_lectura["timestamp"].strftime("%H:%M:%S")

    st.markdown(
        f"""
    <div class="app-header">
        <div>
            <p class="app-title">🖥️ Monitoreo de Calidad del Aire — ITR Centro-Sur</p>
            <p class="app-subtitle">Estación {estacion_sel} · Última medición {hora_actualizacion}</p>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    csv = df.to_csv(index=False).encode("utf-8")
    st.sidebar.download_button(
        label="📥 Descargar datos (CSV)",
        data=csv,
        file_name=f"datos_{estacion_sel}_{fecha_inicio}_al_{fecha_fin}.csv",
        mime="text/csv",
>>>>>>> Stashed changes
    )

    st.divider()

<<<<<<< Updated upstream
    # ==========================================
    # ⏱️ MÉTRICAS ACTUALES
    # ==========================================
    st.markdown('<p class="section-title">Valores actuales</p>', unsafe_allow_html=True)
=======
    st.markdown(
        '<p class="section-title">Valores actuales</p>', unsafe_allow_html=True
    )
>>>>>>> Stashed changes
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        kpi_card("🌡️", "Temperatura", temp_val, "°C", decimales=1)
    with m2:
        kpi_card("💧", "Humedad", hum_val, "%", decimales=0)
    with m3:
<<<<<<< Updated upstream
        kpi_card("🫧", "CO2", co2_val, "PPM", evaluar_estado(co2_val, LIMITE_CO2), decimales=0)
    with m4:
        kpi_card("⚠️", "CO", co_val, "PPM", evaluar_estado(co_val, LIMITE_CO), decimales=1)
    with m5:
        kpi_card("🌫️", "PM 2.5", pm25_val, "µg/m³", evaluar_estado(pm25_val, LIMITE_PM25), decimales=1)
=======
        kpi_card("🫧", "CO2", co2_val, "PPM", decimales=0)
    with m4:
        kpi_card("⚠️", "CO", co_val, "PPM", decimales=1)
    with m5:
        kpi_card("🌫️", "PM 2.5", pm25_val, "µg/m³", decimales=1)
>>>>>>> Stashed changes

    st.write("")
    st.divider()

<<<<<<< Updated upstream
    # ==========================================
    # 📈 GRÁFICOS TEMPORALES
    # ==========================================
    tab_confort, tab_gases, tab_pm = st.tabs([
        "🌡️ Temperatura y Humedad", "🫧 Gases (CO2 y CO)", "🌫️ Material Particulado",
    ])
=======
    tab_confort, tab_gases, tab_pm = st.tabs(
        [
            "🌡️ Temperatura y Humedad",
            "🫧 Gases (CO2 y CO)",
            "🌫️ Material Particulado",
        ]
    )
>>>>>>> Stashed changes

    with tab_confort:
        col1, col2 = st.columns(2)
        with col1:
            fig_temp = go.Figure()
<<<<<<< Updated upstream
            fig_temp.add_trace(linea(df["timestamp"], df["temperatura_c"], "Temp °C", PALETTE["orange"]))
            marcador_actual(fig_temp, df["timestamp"], df["temperatura_c"], PALETTE["orange"])
            style_fig(fig_temp, "Temperatura (°C)")
=======
            leyenda = agregar_variable(fig_temp, df, "temperatura_c", "Temp °C", PALETTE["orange"])
            style_fig(fig_temp, "Temperatura (°C)", show_legend=leyenda)
>>>>>>> Stashed changes
            st.plotly_chart(fig_temp, use_container_width=True, config={"displaylogo": False})

        with col2:
            fig_hum = go.Figure()
<<<<<<< Updated upstream
            fig_hum.add_trace(linea(df["timestamp"], df["humedad_pct"], "Hum %", PALETTE["blue"]))
            marcador_actual(fig_hum, df["timestamp"], df["humedad_pct"], PALETTE["blue"])
            style_fig(fig_hum, "Humedad (%)")
=======
            leyenda = agregar_variable(fig_hum, df, "humedad_pct", "Hum %", PALETTE["blue"])
            style_fig(fig_hum, "Humedad (%)", show_legend=leyenda)
>>>>>>> Stashed changes
            st.plotly_chart(fig_hum, use_container_width=True, config={"displaylogo": False})

    with tab_gases:
        col3, col4 = st.columns(2)
        with col3:
            fig_co2 = go.Figure()
<<<<<<< Updated upstream
            fig_co2.add_trace(linea(df["timestamp"], df["co2_ppm"], "CO2", PALETTE["aqua"]))
            marcador_actual(fig_co2, df["timestamp"], df["co2_ppm"], PALETTE["aqua"])
            linea_limite(fig_co2, LIMITE_CO2, f"Límite interior ({LIMITE_CO2} PPM)")
            style_fig(fig_co2, "Dióxido de Carbono — CO2 (PPM)")
=======
            leyenda = agregar_variable(fig_co2, df, "co2_ppm", "CO2", PALETTE["aqua"])
            style_fig(fig_co2, "Dióxido de Carbono — CO2 (PPM)", show_legend=leyenda)
>>>>>>> Stashed changes
            st.plotly_chart(fig_co2, use_container_width=True, config={"displaylogo": False})

        with col4:
            fig_co = go.Figure()
<<<<<<< Updated upstream
            fig_co.add_trace(linea(df["timestamp"], df["co_ppm"], "CO", PALETTE["violet"]))
            marcador_actual(fig_co, df["timestamp"], df["co_ppm"], PALETTE["violet"])
            linea_limite(fig_co, LIMITE_CO, f"Decreto 135/021 ({LIMITE_CO} PPM)")
            style_fig(fig_co, "Monóxido de Carbono — CO (PPM)")
=======
            leyenda = agregar_variable(fig_co, df, "co_ppm", "CO", PALETTE["violet"])
            style_fig(fig_co, "Monóxido de Carbono — CO (PPM)", show_legend=leyenda)
>>>>>>> Stashed changes
            st.plotly_chart(fig_co, use_container_width=True, config={"displaylogo": False})

    with tab_pm:
        fig_pm = go.Figure()
<<<<<<< Updated upstream
        fig_pm.add_trace(linea(df["timestamp"], df["pm1_ugm3"], "PM 1.0", PALETTE["blue"], con_relleno=False))
        fig_pm.add_trace(linea(df["timestamp"], df["pm25_ugm3"], "PM 2.5", PALETTE["orange"], con_relleno=False))
        fig_pm.add_trace(linea(df["timestamp"], df["pm10_ugm3"], "PM 10", PALETTE["aqua"], con_relleno=False))

        linea_limite(fig_pm, LIMITE_PM25, f"Límite PM 2.5 ({LIMITE_PM25} µg/m³)")
        fig_pm.add_hline(
            y=LIMITE_PM10, line_dash="dash", line_color=PALETTE["text_secondary"], line_width=1.5,
            annotation_text=f"Límite PM 10 ({LIMITE_PM10} µg/m³)", annotation_position="top left",
            annotation_font=dict(size=11, color=PALETTE["text_secondary"]),
            annotation_bgcolor="rgba(255,255,255,0.85)",
        )

        style_fig(fig_pm, "Material Particulado (µg/m³) vs Decreto 135/021", show_legend=True)
        fig_pm.update_layout(height=420)
        st.plotly_chart(fig_pm, use_container_width=True, config={"displaylogo": False})

    # ==========================================
    # 📊 RESUMEN ESTADÍSTICO DE SENSORES
    # ==========================================
    st.divider()
    st.markdown('<p class="section-title">📊 Resumen Estadístico del Período</p>', unsafe_allow_html=True)

    columnas_sensores = {
        "co2_ppm": "CO₂ (PPM)",
        "co_ppm": "CO (PPM)",
        "pm25_ugm3": "PM 2.5 (µg/m³)",
        "pm10_ugm3": "PM 10 (µg/m³)",
        "temperatura_c": "Temperatura (°C)",
        "humedad_pct": "Humedad (%)"
    }

    cols_existentes = [col for col in columnas_sensores.keys() if col in df.columns]

    if cols_existentes:
        sensor_sel = st.selectbox(
            "Selecciona un parámetro para ver métricas detalladas:",
            options=cols_existentes,
            format_func=lambda x: columnas_sensores[x]
        )

=======
        agregar_variable(fig_pm, df, "pm1_ugm3", "PM 1.0", PALETTE["blue"], con_relleno=False)
        agregar_variable(fig_pm, df, "pm25_ugm3", "PM 2.5", PALETTE["orange"], con_relleno=False)
        agregar_variable(fig_pm, df, "pm10_ugm3", "PM 10", PALETTE["aqua"], con_relleno=False)
        style_fig(fig_pm, "Material Particulado (µg/m³)", show_legend=True)
        fig_pm.update_layout(height=420)
        st.plotly_chart(fig_pm, use_container_width=True, config={"displaylogo": False})

    st.divider()
    st.markdown(
        '<p class="section-title">📊 Resumen Estadístico del Período</p>',
        unsafe_allow_html=True,
    )
    st.caption("Calculado sobre los datos crudos.")

    columnas_sensores = {
        "co2_ppm": "CO₂ (PPM)",
        "co_ppm": "CO (PPM)",
        "pm25_ugm3": "PM 2.5 (µg/m³)",
        "pm10_ugm3": "PM 10 (µg/m³)",
        "temperatura_c": "Temperatura (°C)",
        "humedad_pct": "Humedad (%)",
    }

    cols_existentes = [
        col for col in columnas_sensores.keys() if col in df.columns
    ]

    if cols_existentes:
        sensor_sel = st.selectbox(
            "Selecciona un parámetro para ver métricas detalladas:",
            options=cols_existentes,
            format_func=lambda x: columnas_sensores[x],
        )

>>>>>>> Stashed changes
        if sensor_sel:
            col_est1, col_est2, col_est3, col_est4 = st.columns(4)
            prom = df[sensor_sel].mean()
            mini = df[sensor_sel].min()
            maxi = df[sensor_sel].max()
            desv = df[sensor_sel].std()

<<<<<<< Updated upstream
            col_est1.metric("Promedio", f"{prom:.2f}" if pd.notnull(prom) else "N/A")
            col_est2.metric("Mínimo", f"{mini:.2f}" if pd.notnull(mini) else "N/A")
            col_est3.metric("Máximo", f"{maxi:.2f}" if pd.notnull(maxi) else "N/A")
            col_est4.metric("Desviación Estándar", f"{desv:.2f}" if pd.notnull(desv) else "N/A")

        st.write("")

        df_stats = df[cols_existentes].rename(columns=columnas_sensores).describe().T[
            ['count', 'mean', 'std', 'min', '50%', 'max']
        ]
        df_stats.columns = ['Lecturas', 'Promedio', 'Desv. Estándar', 'Mínimo', 'Mediana', 'Máximo']

        st.dataframe(
            df_stats.style.format("{:.2f}", na_rep="N/A"),
            use_container_width=True
        )

else:
    st.warning("No hay datos disponibles para el rango de fechas seleccionado.")
=======
            col_est1.metric(
                "Promedio", f"{prom:.2f}" if pd.notnull(prom) else "N/A"
            )
            col_est2.metric(
                "Mínimo", f"{mini:.2f}" if pd.notnull(mini) else "N/A"
            )
            col_est3.metric(
                "Máximo", f"{maxi:.2f}" if pd.notnull(maxi) else "N/A"
            )
            col_est4.metric(
                "Desviación Estándar",
                f"{desv:.2f}" if pd.notnull(desv) else "N/A",
            )

        st.write("")

        df_stats = (
            df[cols_existentes]
            .rename(columns=columnas_sensores)
            .describe()
            .T[["count", "mean", "std", "min", "50%", "max"]]
        )
        df_stats.columns = [
            "Lecturas",
            "Promedio",
            "Desv. Estándar",
            "Mínimo",
            "Mediana",
            "Máximo",
        ]

        st.dataframe(
            df_stats.style.format("{:.2f}", na_rep="N/A"),
            use_container_width=True,
        )

else:
    st.warning(
        f"No hay datos registrados para la estación {estacion_sel} en el rango de fechas seleccionado."
    )
>>>>>>> Stashed changes
