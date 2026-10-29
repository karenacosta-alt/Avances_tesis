import os
import sys
import time
from datetime import datetime, timedelta

import board
import serial
import requests
import psycopg2
from smbus2 import SMBus, i2c_msg
import adafruit_bme680

# =========================
# Configuración (archivo /etc/estacion/estacion.env, cargado por systemd)
# =========================
URL_SERVIDOR = os.getenv("URL_SERVIDOR", "http://localhost:8000/api/lecturas")
CODIGO_ESTACION = os.getenv("CODIGO_ESTACION", "EST01")
INTERVALO_MIN = int(os.getenv("INTERVALO_MIN", 15))
MAX_ENVIOS_POR_CICLO = int(os.getenv("MAX_ENVIOS_POR_CICLO", 200))

DB_LOCAL = dict(
    dbname=os.getenv("DB_NAME", "estacion_db"),
    user=os.getenv("DB_USER", "estacion_user"),
    password=os.getenv("DB_PASSWORD", ""),
    host=os.getenv("DB_HOST", "127.0.0.1"),
    port=int(os.getenv("DB_PORT", 5432)),
)

PORT_CO2 = os.getenv("PORT_CO2", "/dev/ttyAMA3")
PORT_PM = os.getenv("PORT_PM", "/dev/ttyAMA5")
I2C_BUS = int(os.getenv("I2C_BUS", 1))
I2C_ADDR_SEN0466 = int(os.getenv("I2C_ADDR_SEN0466", "0x74"), 16)
I2C_ADDR_BME680 = int(os.getenv("I2C_ADDR_BME680", "0x77"), 16)

CMD_CO2 = bytes([0xFF, 0x01, 0x86, 0, 0, 0, 0, 0, 0x79])
CO_INVALIDO = 65000      # valores >= a este se descartan (error de comunicación)
PM_ESPERA_MAX = 3.0      # segundos de espera por una trama nueva del SEN0177

COLUMNAS_REQUERIDAS = {
    "estaciones": {"id", "codigo"},
    "lecturas": {"id", "estacion_id", "timestamp", "co2_ppm", "co_ppm",
                 "temperatura_c", "humedad_pct", "pm1_ugm3", "pm25_ugm3",
                 "pm10_ugm3", "sincronizado", "intentos_envio", "sincronizado_en"},
}

# =========================
# Hardware
# =========================
i2c = board.I2C()

try:
    bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c, address=I2C_ADDR_BME680)
except Exception:
    bme680 = None
    print("BME680 no detectado: se continúa sin temperatura ni humedad.")

def abrir_serial(puerto, timeout):
    try:
        return serial.Serial(puerto, 9600, timeout=timeout)
    except Exception as e:
        print(f"No se pudo abrir {puerto}: {e}")
        return None

ser_co2 = abrir_serial(PORT_CO2, 2)
ser_pm = abrir_serial(PORT_PM, 0.2)

def asegurar_seriales():
    """Verifica los puertos serie y los vuelve a abrir si es necesario."""
    global ser_co2, ser_pm
    if ser_co2 is None or not ser_co2.is_open:
        ser_co2 = abrir_serial(PORT_CO2, 2)
    if ser_pm is None or not ser_pm.is_open:
        ser_pm = abrir_serial(PORT_PM, 0.2)

# =========================
# Lectura de sensores (cada una aislada: si falla devuelve None)
# =========================
def leer_co2():
    try:
        ser_co2.reset_input_buffer()          # descarta datos pendientes
        ser_co2.write(CMD_CO2)
        time.sleep(0.2)
        r = ser_co2.read(9)
        if len(r) != 9 or r[0] != 0xFF or r[1] != 0x86:
            return None
        checksum = (0xFF - (sum(r[1:8]) & 0xFF) + 1) & 0xFF
        if checksum != r[8]:
            return None
        return r[2] * 256 + r[3]
    except Exception:
        return None

CMD_CO_PREGUNTA = [0xFF, 0x01, 0x88, 0, 0, 0, 0, 0, 0x77]

def leer_co_sen0466():
    """Lee el CO del SEN0466 en modo activo (registro 0x09) o, si el sensor
    está en modo pregunta-respuesta, con el comando 0x88."""
    try:
        with SMBus(I2C_BUS) as bus:
            data = bus.read_i2c_block_data(I2C_ADDR_SEN0466, 0x09, 2)
            if data[0] == 0xFF and data[1] == 0x88:
                # Modo pregunta-respuesta: el registro devuelve la cabecera de la trama
                bus.i2c_rdwr(i2c_msg.write(I2C_ADDR_SEN0466, CMD_CO_PREGUNTA))
                time.sleep(0.2)
                r = i2c_msg.read(I2C_ADDR_SEN0466, 7)
                bus.i2c_rdwr(r)
                r = list(r)
                if r[0] != 0xFF or r[1] != 0x88:
                    return None
                ppm = (r[2] << 8) | r[3]
                decimales = r[5] if r[5] in (0, 1, 2) else 0
                return round(ppm / (10 ** decimales), 2)
        ppm = (data[0] << 8) | data[1]
        if ppm >= CO_INVALIDO:
            return None
        return float(ppm)
    except Exception:
        return None

def leer_pm():
    """Descarta las tramas acumuladas y espera hasta 3 s una trama nueva de 32 bytes."""
    try:
        ser_pm.reset_input_buffer()
        buffer = bytearray()
        limite = time.monotonic() + PM_ESPERA_MAX
        while time.monotonic() < limite:
            buffer += ser_pm.read(64)
            i = buffer.find(b"\x42\x4D")
            if i == -1 or len(buffer) < i + 32:
                continue
            frame = bytes(buffer[i:i + 32])
            del buffer[:i + 32]
            if (sum(frame[0:30]) & 0xFFFF) != ((frame[30] << 8) + frame[31]):
                continue                       # checksum incorrecto: esperar la siguiente
            pm1 = (frame[4] << 8) + frame[5]
            pm25 = (frame[6] << 8) + frame[7]
            pm10 = (frame[8] << 8) + frame[9]
            return pm1, pm25, pm10
    except Exception:
        pass
    return None, None, None

def leer_bme680():
    if bme680 is None:
        return None, None
    try:
        return round(bme680.temperature, 2), round(bme680.relative_humidity, 2)
    except Exception:
        return None, None

# =========================
# Base de datos local
# =========================
def conectar():
    return psycopg2.connect(**DB_LOCAL)

def verificar_estructura():
    """Detiene el programa si la base local no tiene la estructura requerida."""
    try:
        with conectar() as conn, conn.cursor() as cur:
            for tabla, requeridas in COLUMNAS_REQUERIDAS.items():
                cur.execute(
                    "SELECT column_name FROM information_schema.columns WHERE table_name=%s",
                    (tabla,))
                faltantes = requeridas - {r[0] for r in cur.fetchall()}
                if faltantes:
                    sys.exit(f"Falta en la tabla '{tabla}': {sorted(faltantes)}. "
                             "Ejecute el script de migración de la base local.")
    except psycopg2.Error as e:
        sys.exit(f"No se pudo conectar a la base local: {e}")

def obtener_estacion_id(cur, codigo):
    cur.execute("SELECT id FROM estaciones WHERE codigo=%s", (codigo,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute("INSERT INTO estaciones (codigo) VALUES (%s) RETURNING id", (codigo,))
    return cur.fetchone()[0]

def guardar_local(lectura):
    """Guarda la lectura marcada como pendiente de envío."""
    conn = None
    try:
        conn = conectar()
        with conn.cursor() as cur:
            estacion_id = obtener_estacion_id(cur, CODIGO_ESTACION)
            cur.execute("""
                INSERT INTO lecturas (estacion_id, timestamp, co2_ppm, co_ppm, temperatura_c,
                    humedad_pct, pm1_ugm3, pm25_ugm3, pm10_ugm3, sincronizado, intentos_envio)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, false, 0)
            """, (estacion_id, lectura["timestamp"], lectura["co2_ppm"], lectura["co_ppm"],
                  lectura["temperatura_c"], lectura["humedad_pct"], lectura["pm1_ugm3"],
                  lectura["pm25_ugm3"], lectura["pm10_ugm3"]))
        conn.commit()
        return True
    except Exception as e:
        if conn:
            conn.rollback()
        print("DB local error:", e)
        return False
    finally:
        if conn:
            conn.close()

# =========================
# Cola de sincronización
# =========================
def sincronizar_pendientes():
    """Envía los registros pendientes en orden cronológico; se detiene ante el primer fallo."""
    enviados = 0
    conn = None
    try:
        conn = conectar()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT l.id, l.timestamp, l.co2_ppm, l.co_ppm, l.temperatura_c, l.humedad_pct,
                       l.pm1_ugm3, l.pm25_ugm3, l.pm10_ugm3
                FROM lecturas l JOIN estaciones e ON e.id = l.estacion_id
                WHERE NOT l.sincronizado AND e.codigo = %s
                ORDER BY l.timestamp
                LIMIT %s
            """, (CODIGO_ESTACION, MAX_ENVIOS_POR_CICLO))
            pendientes = cur.fetchall()

        for (id_, ts, co2, co, temp, hum, pm1, pm25, pm10) in pendientes:
            payload = {
                "codigo_estacion": CODIGO_ESTACION,
                "timestamp": ts.isoformat(),        # hora de la lectura, no de la recepción
                "co2_ppm": co2, "co_ppm": co, "temperatura_c": temp, "humedad_pct": hum,
                "pm1_ugm3": pm1, "pm25_ugm3": pm25, "pm10_ugm3": pm10,
            }
            try:
                r = requests.post(URL_SERVIDOR, json=payload, timeout=5)
                ok = r.status_code == 200
            except Exception:
                ok = False

            with conn.cursor() as cur:
                if ok:
                    cur.execute("UPDATE lecturas SET sincronizado = true, sincronizado_en = now() "
                                "WHERE id = %s", (id_,))
                else:
                    cur.execute("UPDATE lecturas SET intentos_envio = intentos_envio + 1 "
                                "WHERE id = %s", (id_,))
            conn.commit()
            if not ok:
                break
            enviados += 1
    except Exception as e:
        if conn:
            conn.rollback()
        print("Error de sincronización:", e)
    finally:
        if conn:
            conn.close()
    return enviados

# =========================
# Temporización: cada cuarto de hora exacto
# =========================
def esperar_proximo_cuarto():
    ahora = datetime.now()
    minutos = (ahora.minute // INTERVALO_MIN + 1) * INTERVALO_MIN
    proximo = ahora.replace(minute=0, second=0, microsecond=0) + timedelta(minutes=minutos)
    time.sleep(max(0, (proximo - datetime.now()).total_seconds()))

# =========================
# Programa principal
# =========================
verificar_estructura()
print(f"Estación {CODIGO_ESTACION} iniciada. Servidor: {URL_SERVIDOR}")

while True:
    esperar_proximo_cuarto()
    try:
        asegurar_seriales()
        ts = datetime.now().astimezone()       # marca temporal con zona horaria

        co2 = leer_co2()
        co = leer_co_sen0466()
        temp, hum = leer_bme680()
        pm1, pm25, pm10 = leer_pm()

        lectura = {
            "timestamp": ts, "co2_ppm": co2,
            "co_ppm": round(co, 2) if co is not None else None,   # nulo, nunca 0.0
            "temperatura_c": temp, "humedad_pct": hum,
            "pm1_ugm3": pm1, "pm25_ugm3": pm25, "pm10_ugm3": pm10,
        }
        guardado = guardar_local(lectura)
        enviados = sincronizar_pendientes()
        print(f"{ts:%Y-%m-%d %H:%M} | CO2={co2} CO={co} T={temp} HR={hum} "
              f"PM1={pm1} PM2.5={pm25} PM10={pm10} | guardado={guardado} sincronizados={enviados}")
    except Exception as e:
        print("Error en el ciclo:", e)
