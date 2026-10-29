"""Dashboard central: todas las estaciones en el servidor.

Lee la base del servidor (la misma que usa api_main.py) y muestra, para cada
variable, un gráfico con una línea por estación.

Ejecutar con:
    streamlit run dashboard_central.py --server.port 8501
"""
import os
from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "tesis_db")
ZONA_HORARIA = "America/Montevideo"
INTERVALO_MIN = 15
ATRASO_MAX_MIN = 30  # una estación sin datos hace más de esto se marca como atrasada

# Un color fijo por estación, el mismo en todos los gráficos
COLORES = {
    "EST01": "#2a78d6",
    "EST02": "#eb6834",
    "EST03": "#1baf7a",
    "EST04": "#4a3aa7",
    "EST05": "#c2185b",
}
COLORES_EXTRA = ["#8a6d00", "#00838f", "#6d4c41", "#546e7a"]

VARIABLES = [
    ("co2_ppm", "CO₂", "ppm"),
    ("co_ppm", "CO", "ppm"),
    ("temperatura_c", "Temperatura", "°C"),
    ("humedad_pct", "Humedad relativa", "%"),
    ("pm1_ugm3", "PM1", "µg/m³"),
    ("pm25_ugm3", "PM2.5", "µg/m³"),
    ("pm10_ugm3", "PM10", "µg/m³"),
]

st.set_page_config(page_title="Red de estaciones ITR Centro-Sur", page_icon="🌡️", layout="wide")


@st.cache_resource
def get_db_engine():
    url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    # Sesión en hora de Uruguay: el filtro por fechas se interpreta en hora local
    return create_engine(url, connect_args={"options": f"-c timezone={ZONA_HORARIA}"})


def a_hora_local(serie):
    serie = pd.to_datetime(serie)
    if serie.dt.tz is not None:
        serie = serie.dt.tz_convert(ZONA_HORARIA).dt.tz_localize(None)
    return serie


@st.cache_data(ttl=60)
def get_estaciones():
    with get_db_engine().connect() as conn:
        return [r[0] for r in conn.execute(text("SELECT codigo FROM estaciones ORDER BY codigo"))]


@st.cache_data(ttl=60)
def get_ultimas():
    query = text("""
        SELECT DISTINCT ON (e.codigo) e.codigo AS estacion, l.timestamp,
               l.co2_ppm, l.co_ppm, l.temperatura_c, l.humedad_pct, l.pm25_ugm3
        FROM lecturas l JOIN estaciones e ON e.id = l.estacion_id
        ORDER BY e.codigo, l.timestamp DESC
    """)
    with get_db_engine().connect() as conn:
        df = pd.read_sql_query(query, conn)
    if not df.empty:
        df["timestamp"] = a_hora_local(df["timestamp"])
    return df


@st.cache_data(ttl=60)
def get_lecturas(estaciones, inicio, fin):
    query = text("""
        SELECT e.codigo AS estacion, l.timestamp, l.co2_ppm, l.co_ppm,
               l.temperatura_c, l.humedad_pct, l.pm1_ugm3, l.pm25_ugm3, l.pm10_ugm3
        FROM lecturas l JOIN estaciones e ON e.id = l.estacion_id
        WHERE e.codigo = ANY(:estaciones)
          AND l.timestamp >= :inicio AND l.timestamp < :fin
        ORDER BY l.timestamp
    """)
    with get_db_engine().connect() as conn:
        df = pd.read_sql_query(
            query, conn,
            params={"estaciones": list(estaciones), "inicio": str(inicio), "fin": str(fin)},
        )
    if not df.empty:
        df["timestamp"] = a_hora_local(df["timestamp"])
    return df


def promediar(df, regla):
    """Promedia por estación en intervalos regulares. Los intervalos sin datos
    quedan vacíos, así el gráfico muestra los cortes en lugar de unir los puntos."""
    columnas = [v[0] for v in VARIABLES]
    partes = []
    for estacion, grupo in df.groupby("estacion"):
        g = grupo.set_index("timestamp")[columnas].astype(float).resample(regla).mean()
        g["estacion"] = estacion
        partes.append(g.reset_index())
    return pd.concat(partes, ignore_index=True) if partes else df


def color_de(estacion, todas):
    if estacion in COLORES:
        return COLORES[estacion]
    otras = [e for e in todas if e not in COLORES]
    return COLORES_EXTRA[otras.index(estacion) % len(COLORES_EXTRA)]


# =========================
# Barra lateral
# =========================
st.sidebar.header("Filtros")
try:
    todas = get_estaciones()
except Exception as e:
    st.error(f"No se pudo conectar a la base del servidor: {e}")
    st.stop()

seleccion = st.sidebar.multiselect("Estaciones", todas, default=todas)
fecha_inicio = st.sidebar.date_input("Desde", date.today() - timedelta(days=2))
fecha_fin = st.sidebar.date_input("Hasta", date.today())
promedio = st.sidebar.selectbox(
    "Promedio",
    ["Sin promediar (15 min)", "1 hora", "1 día"],
    help="Promediar ayuda a comparar estaciones en períodos largos.",
)
vista = st.sidebar.radio("Gráficos", ["Todas las estaciones juntas", "Una fila por estación"])
if st.sidebar.button("Actualizar ahora"):
    st.cache_data.clear()

# =========================
# Encabezado y estado de cada estación
# =========================
st.title("Red de monitoreo de calidad del aire · ITR Centro-Sur")
st.caption(f"Hora de Uruguay · lecturas cada {INTERVALO_MIN} minutos · se actualiza cada 1 minuto")

ultimas = get_ultimas()
if not ultimas.empty:
    ahora = pd.Timestamp.now(tz=ZONA_HORARIA).tz_localize(None)
    estado = ultimas.copy()
    atraso = ((ahora - estado["timestamp"]).dt.total_seconds() // 60).astype(int)
    estado["Estado"] = ["✅ Al día" if m <= ATRASO_MAX_MIN else f"⚠️ Sin datos hace {m} min" for m in atraso]
    estado["Última lectura"] = estado["timestamp"].dt.strftime("%d/%m %H:%M")
    estado["temperatura_c"] = estado["temperatura_c"].round(1)
    estado["humedad_pct"] = estado["humedad_pct"].round(1)
    estado = estado.rename(columns={
        "estacion": "Estación", "co2_ppm": "CO₂ (ppm)", "co_ppm": "CO (ppm)",
        "temperatura_c": "T (°C)", "humedad_pct": "HR (%)", "pm25_ugm3": "PM2.5 (µg/m³)",
    })
    st.subheader("Estado de las estaciones")
    st.dataframe(
        estado[["Estación", "Estado", "Última lectura", "CO₂ (ppm)", "CO (ppm)",
                "T (°C)", "HR (%)", "PM2.5 (µg/m³)"]],
        hide_index=True, width="stretch",
    )

if not seleccion:
    st.info("Elegí al menos una estación en la barra lateral.")
    st.stop()

df = get_lecturas(tuple(seleccion), fecha_inicio, fecha_fin + timedelta(days=1))
if df.empty:
    st.warning("No hay lecturas de las estaciones elegidas en ese rango de fechas.")
    st.stop()

regla = {"Sin promediar (15 min)": f"{INTERVALO_MIN}min", "1 hora": "1h", "1 día": "1D"}[promedio]
datos = promediar(df, regla)
mapa_colores = {e: color_de(e, todas) for e in seleccion}

# =========================
# Un gráfico por variable, una línea por estación
# =========================
pestanas = st.tabs([
    "📊 Comparación entre estaciones",
    "🌡️ Temperatura y humedad",
    "🧪 Gases (CO₂ y CO)",
    "🌫️ Material particulado",
])

with pestanas[0]:
    columnas = st.columns(2)
    for i, (col, nombre, unidad) in enumerate(VARIABLES):
        con_datos = [e for e in seleccion if datos.loc[datos["estacion"] == e, col].notna().any()]
        sin_datos = [e for e in seleccion if e not in con_datos]
        with columnas[i % 2]:
            if not con_datos:
                st.markdown(f"**{nombre} ({unidad})**")
                st.caption("Ninguna estación tiene datos de esta variable en el rango elegido.")
                continue
            sub = datos[datos["estacion"].isin(con_datos)]
            if vista == "Todas las estaciones juntas":
                fig = go.Figure()
                for estacion in con_datos:
                    d = sub[sub["estacion"] == estacion]
                    fig.add_trace(go.Scatter(
                        x=d["timestamp"], y=d[col], name=estacion, mode="lines",
                        line=dict(color=mapa_colores[estacion], width=2), connectgaps=False,
                    ))
                alto = 320
            else:
                fig = px.line(
                    sub, x="timestamp", y=col, color="estacion", facet_row="estacion",
                    color_discrete_map=mapa_colores, category_orders={"estacion": con_datos},
                )
                fig.update_traces(connectgaps=False)
                fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
                fig.update_yaxes(title_text="")
                alto = 140 * len(con_datos) + 60
            fig.update_layout(
                title=f"{nombre} ({unidad})", height=alto, hovermode="x unified",
                margin=dict(l=10, r=10, t=50, b=10), legend_title_text="",
                legend=dict(orientation="h", y=1.12, x=1, xanchor="right"),
                xaxis_title="", yaxis_title=unidad if vista == "Todas las estaciones juntas" else None,
            )
            st.plotly_chart(fig, width="stretch")
            if sin_datos:
                st.caption("Sin datos de esta variable: " + ", ".join(sin_datos))


# =========================
# Pestañas por variable: un gráfico por estación
# =========================
COLORES_PM = {"pm1_ugm3": "#9ecae1", "pm25_ugm3": "#3182bd", "pm10_ugm3": "#08519c"}


def rango_comun(variables):
    """Mismo rango del eje Y en todas las estaciones, para poder compararlas a simple vista."""
    valores = datos[[v[0] for v in variables]].stack()
    if valores.empty:
        return None
    minimo, maximo = valores.min(), valores.max()
    margen = (maximo - minimo) * 0.05 or 1
    return [minimo - margen, maximo + margen]


def grafico_estacion(d, variables, titulo, colores, rango):
    fig = go.Figure()
    for col, nombre, _ in variables:
        fig.add_trace(go.Scatter(
            x=d["timestamp"], y=d[col], name=nombre, mode="lines",
            line=dict(color=colores[col], width=2), connectgaps=False,
        ))
    fig.update_layout(
        title=titulo, height=280, hovermode="x unified", showlegend=len(variables) > 1,
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(orientation="h", y=1.15, x=1, xanchor="right"),
        xaxis_title="", yaxis_title=variables[0][2], yaxis_range=rango,
    )
    return fig


def pestana_por_estacion(variables, juntas):
    """juntas=False: un gráfico por variable, lado a lado, para cada estación.
    juntas=True: un solo gráfico por estación con todas las variables del grupo."""
    rangos = {v[0]: rango_comun([v]) for v in variables}
    for estacion in seleccion:
        d = datos[datos["estacion"] == estacion]
        st.markdown(f"#### {estacion}")
        if juntas:
            grupo = [v for v in variables if d[v[0]].notna().any()]
            if not grupo:
                st.caption("Sin datos de estas variables en el rango elegido.")
                continue
            titulo = " · ".join(v[1] for v in grupo) + f" ({grupo[0][2]})"
            st.plotly_chart(
                grafico_estacion(d, grupo, titulo, COLORES_PM, rango_comun(variables)),
                width="stretch", key=f"{estacion}-{titulo}",
            )
            continue
        for columna, (col, nombre, unidad) in zip(st.columns(len(variables)), variables):
            with columna:
                if not d[col].notna().any():
                    st.markdown(f"**{nombre} ({unidad})**")
                    st.caption("Sin datos en el rango elegido.")
                    continue
                st.plotly_chart(
                    grafico_estacion(d, [(col, nombre, unidad)], f"{nombre} ({unidad})",
                                     {col: mapa_colores[estacion]}, rangos[col]),
                    width="stretch", key=f"{estacion}-{col}",
                )


VAR = {v[0]: v for v in VARIABLES}
with pestanas[1]:
    pestana_por_estacion([VAR["temperatura_c"], VAR["humedad_pct"]], juntas=False)
with pestanas[2]:
    pestana_por_estacion([VAR["co2_ppm"], VAR["co_ppm"]], juntas=False)
with pestanas[3]:
    pestana_por_estacion([VAR["pm1_ugm3"], VAR["pm25_ugm3"], VAR["pm10_ugm3"]], juntas=True)

# =========================
# Descarga
# =========================
st.download_button(
    "Descargar datos (CSV)",
    df.rename(columns={"estacion": "codigo_estacion"}).to_csv(index=False).encode("utf-8"),
    file_name=f"red_estaciones_{fecha_inicio}_al_{fecha_fin}.csv",
    mime="text/csv",
)
