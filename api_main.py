import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2

# Lee credenciales desde variables de entorno o usa valores genéricos
DB = dict(
    dbname=os.getenv("DB_NAME", "tesis_db"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD", "tu_contraseña_aqui"),
    host=os.getenv("DB_HOST", "127.0.0.1"),
    port=int(os.getenv("DB_PORT", 5432)),
)

app = FastAPI()


class LecturaIn(BaseModel):
    codigo_estacion: str

    co2_ppm: int | None = None
    co_ppm: float | None = None
    temperatura_c: float | None = None
    humedad_pct: float | None = None

    pm1_ugm3: int | None = None
    pm25_ugm3: int | None = None
    pm10_ugm3: int | None = None

    timestamp: datetime | None = None


@app.post("/api/lecturas")
def insertar_lectura(data: LecturaIn):
    ts = data.timestamp or datetime.utcnow()

    conn = None
    cur = None
    try:
        conn = psycopg2.connect(**DB)
        cur = conn.cursor()

        # 1) Obtener (o crear) estación
        cur.execute("SELECT id FROM estaciones WHERE codigo=%s", (data.codigo_estacion,))
        row = cur.fetchone()
        if row is None:
            cur.execute(
                "INSERT INTO estaciones (codigo) VALUES (%s) RETURNING id",
                (data.codigo_estacion,)
            )
            estacion_id = cur.fetchone()[0]
        else:
            estacion_id = row[0]

        # 2) Insert lectura
        cur.execute("""
            INSERT INTO lecturas (
                estacion_id, timestamp,
                co2_ppm, co_ppm, temperatura_c, humedad_pct,
                pm1_ugm3, pm25_ugm3, pm10_ugm3
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            estacion_id, ts,
            data.co2_ppm, data.co_ppm, data.temperatura_c, data.humedad_pct,
            data.pm1_ugm3, data.pm25_ugm3, data.pm10_ugm3
        ))

        conn.commit()
        return {"status": "ok"}

    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.get("/api/lecturas")
def ultimas_lecturas(codigo_estacion: str, limit: int = 300):
    """
    Devuelve las últimas lecturas (JSON) para alimentar Streamlit u otros clientes.
    """
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(**DB)
        cur = conn.cursor()

        cur.execute("SELECT id FROM estaciones WHERE codigo=%s", (codigo_estacion,))
        row = cur.fetchone()
        if not row:
            return []

        estacion_id = row[0]

        cur.execute("""
            SELECT timestamp, co2_ppm, co_ppm, temperatura_c, humedad_pct,
                   pm1_ugm3, pm25_ugm3, pm10_ugm3
            FROM lecturas
            WHERE estacion_id=%s
            ORDER BY timestamp DESC
            LIMIT %s
        """, (estacion_id, limit))

        rows = cur.fetchall()

        data = [
            {
                "timestamp": r[0].isoformat() if r[0] else None,
                "co2_ppm": r[1],
                "co_ppm": r[2],
                "temperatura_c": r[3],
                "humedad_pct": r[4],
                "pm1_ugm3": r[5],
                "pm25_ugm3": r[6],
                "pm10_ugm3": r[7],
            }
            for r in rows
        ]
        data.reverse()  # ascendente para graficar fácil
        return data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.get("/api/estaciones")
def listar_estaciones():
    """
    Lista códigos de estaciones registradas.
    Útil cuando tengas 5 estaciones y quieras un dropdown en Streamlit.
    """
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(**DB)
        cur = conn.cursor()
        cur.execute("SELECT codigo FROM estaciones ORDER BY codigo")
        rows = cur.fetchall()
        return [r[0] for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
