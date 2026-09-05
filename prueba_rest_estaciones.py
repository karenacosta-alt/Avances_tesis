import os
import time
import board
import serial
import requests
import psycopg2
from smbus2 import SMBus

import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import adafruit_bme680

# =========================
# Configuración con Variables de Entorno
# =========================
URL_SERVIDOR = os.getenv("URL_SERVIDOR", "http://localhost:8000/api/lecturas")
CODIGO_ESTACION = os.getenv("CODIGO_ESTACION", "EST01")

# DB local
DB_LOCAL = dict(
    dbname=os.getenv("DB_NAME", "estacion_db"),
    user=os.getenv("DB_USER", "estacion_user"),
    password=os.getenv("DB_PASSWORD", "tu_contrasena_aqui"),
    host=os.getenv("DB_HOST", "127.0.0.1"),
    port=int(os.getenv("DB_PORT", 5432))
)
# Puertos / I2C
PORT_CO2 = "/dev/ttyAMA3"
PORT_PM  = "/dev/ttyAMA5"
I2C_ADDR_SEN0466 = 0x74  # Dirección detectada para el nuevo sensor de CO

# Comando CO2
CMD_CO2 = bytes([0xFF, 0x01, 0x86, 0, 0, 0, 0, 0, 0x79])

# =========================
# Hardware
# =========================
i2c = board.I2C()

# BME680
try:
    bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c, address=0x77)
except Exception:
    bme680 = None

# UARTs
def abrir_serial_co2():
    return serial.Serial(PORT_CO2, 9600, timeout=2)

def abrir_serial_pm():
    return serial.Serial(PORT_PM, 9600, timeout=0.2)

ser_co2 = abrir_serial_co2()
ser_pm = abrir_serial_pm()
pm_buffer = bytearray()

# =========================
# Funciones sensores
# =========================

def leer_co2():
    try:
        ser_co2.write(CMD_CO2)
        time.sleep(0.2)
        r = ser_co2.read(9)
        if len(r) == 9 and r[0] == 0xFF and r[1] == 0x86:
            return r[2] * 256 + r[3]
    except Exception:
        pass
    return None

def leer_co_sen0466():
    """
    Lee el sensor de CO digital SEN0466 vía I2C.
    """
    try:
        with SMBus(1) as bus:
            # Registro 0x09 contiene la lectura de gas
            data = bus.read_i2c_block_data(I2C_ADDR_SEN0466, 0x09, 2)
            ppm = (data[0] << 8) | data[1]
            return float(ppm)
    except Exception as e:
        # print(f"Error SEN0466: {e}")
        return None

def leer_pm():
    global pm_buffer
    try:
        # Acumulamos en el buffer lo que va llegando del sensor
        pm_buffer += ser_pm.read(128)
    except Exception:
        return None, None, None

    # Buscamos la firma de inicio de trama "BM" (0x42 0x4D)
    i = pm_buffer.find(b"\x42\x4D")
    
    # Si encontramos la firma y tenemos al menos 32 bytes desde ese punto
    if i != -1 and len(pm_buffer) >= i + 32:
        frame = bytes(pm_buffer[i : i+32])
        
        # Eliminamos del buffer la trama que vamos a procesar (y la basura anterior)
        del pm_buffer[:i+32]
        
        # Verificación de integridad (Checksum)
        cs_calc = sum(frame[0:30]) & 0xFFFF
        cs_frame = (frame[30] << 8) + frame[31]
        
        if cs_calc != cs_frame:
            return None, None, None
            
        # Extracción de valores PM (Estándar)
        pm1  = (frame[4] << 8) + frame[5]
        pm25 = (frame[6] << 8) + frame[7]
        pm10 = (frame[8] << 8) + frame[9]
        
        return pm1, pm25, pm10

    # Limpieza de seguridad: si el buffer crece demasiado por ruido, lo recortamos
    if len(pm_buffer) > 2048:
        pm_buffer = pm_buffer[-256:]
        
    return None, None, None
# =========================
# DB local y REST
# =========================
# ... (Funciones guardar_local y enviar_rest) ...

def get_or_create_estacion_id(conn, codigo):
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM estaciones WHERE codigo=%s", (codigo,))
        row = cur.fetchone()
        if row: return row[0]
        cur.execute("INSERT INTO estaciones (codigo) VALUES (%s) RETURNING id", (codigo,))
        return cur.fetchone()[0]

def guardar_local(payload):
    conn = None
    try:
        conn = psycopg2.connect(**DB_LOCAL)
        estacion_id = get_or_create_estacion_id(conn, payload["codigo_estacion"])
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO lecturas (
                    estacion_id, timestamp, co2_ppm, co_ppm, temperatura_c, 
                    humedad_pct, pm1_ugm3, pm25_ugm3, pm10_ugm3
                ) VALUES (%s, COALESCE(%s, now()), %s, %s, %s, %s, %s, %s, %s)
            """, (
                estacion_id, payload.get("timestamp"), payload.get("co2_ppm"),
                payload.get("co_ppm"), payload.get("temperatura_c"),
                payload.get("humedad_pct"), payload.get("pm1_ugm3"),
                payload.get("pm25_ugm3"), payload.get("pm10_ugm3"),
            ))
        conn.commit()
        print("DB local: OK")
        return True
    except Exception as e:
        if conn: conn.rollback()
        print("DB local error:", e)
        return False
    finally:
        if conn: conn.close()

def enviar_rest(payload):
    try:
        r = requests.post(URL_SERVIDOR, json=payload, timeout=5)
        print("REST:", r.status_code)
        return r.status_code == 200
    except Exception:
        return False

def asegurar_seriales():
    global ser_co2, ser_pm
    for s, func in [(ser_co2, abrir_serial_co2), (ser_pm, abrir_serial_pm)]:
        try:
            if not s.is_open: s = func()
        except Exception: pass

# =========================
# Loop Principal
# =========================
print(f" Estación {CODIGO_ESTACION} con SEN0466 (CO I2C) iniciada.")

while True:
    try:
        asegurar_seriales()

        # 1. CO2
        co2 = leer_co2()

        # 2. CO (Nuevo sensor SEN0466 en 0x74)
        co_ppm = leer_co_sen0466()

        # 3. BME680
        temp, hum = None, None
        if bme680:
            try:
                temp = bme680.temperature
                hum = bme680.relative_humidity
            except: pass

        # 4. PM
        # PM
        pm1, pm25, pm10 = leer_pm()

        payload = {
            "codigo_estacion": CODIGO_ESTACION,
            "co2_ppm": co2,
            "co_ppm": round(co_ppm, 2) if co_ppm is not None else 0.0,
            "temperatura_c": round(temp, 2) if temp is not None else None,
            "humedad_pct": round(hum, 2) if hum is not None else None,
            "pm1_ugm3": pm1,
            "pm25_ugm3": pm25,
            "pm10_ugm3": pm10,
        }

        print(f"Lectura: CO={payload['co_ppm']} PPM | CO2={co2} | T={temp}°C | PM1.0={pm1} | PM2.5={pm25} | PM10={pm10} µg/m³")

        guardar_local(payload)
        enviar_rest(payload)

    except Exception as e:
        print("Loop error:", e)

    time.sleep(5)
