# Instalación del código final en una estación

Guía para pasar la versión de EST01 (cola de sincronización, lecturas cada cuarto de hora, configuración externa) a otra estación. Se hace de a una estación por vez y no se pasa a la siguiente hasta comprobar que la anterior envía datos al servidor.

Si la terminal de la Raspberry usa **fish**, escribir `bash` antes de empezar: algunos comandos de esta guía no funcionan en fish.

Reemplazar en todos los pasos:

- `EST0X`: código de la estación (EST02, EST03, ...).
- `USUARIO`: usuario de la Raspberry.
- `~/prueba`: carpeta donde está el código actual, si es otra.

## 0. Anotar cómo está la estación antes de tocar nada

```bash
systemctl list-units --type=service | grep -i -E "estacion|sensor"   # nombre del servicio actual
systemctl cat NOMBRE_DEL_SERVICIO                                     # qué script ejecuta y desde qué carpeta
psql -U estacion_user -h 127.0.0.1 -d estacion_db -c "SELECT codigo FROM estaciones;"
psql -U estacion_user -h 127.0.0.1 -d estacion_db -c "\d lecturas"
```

Si la tabla `lecturas` no tiene alguna de las columnas `co2_ppm`, `co_ppm`, `temperatura_c`, `humedad_pct`, `pm1_ugm3`, `pm25_ugm3`, `pm10_ugm3`, parar acá: la migración no las crea y hay que revisarlo antes.

## 1. Respaldos

```bash
mkdir -p ~/respaldos
pg_dump -U estacion_user -h 127.0.0.1 estacion_db > ~/respaldos/estacion_db_$(date +%F).sql
cp -r ~/prueba ~/respaldos/prueba_$(date +%F)
```

## 2. Detener el servicio actual

```bash
sudo systemctl stop NOMBRE_DEL_SERVICIO
sudo systemctl disable NOMBRE_DEL_SERVICIO     # solo si el servicio tiene otro nombre que estacion-sensores
```

## 3. Traer el código final

```bash
cd ~/prueba
curl -fsSLO https://raw.githubusercontent.com/karenacosta-alt/Avances_tesis/main/prueba_rest_estaciones.py
curl -fsSLO https://raw.githubusercontent.com/karenacosta-alt/Avances_tesis/main/migracion_local.sql
curl -fsSLO https://raw.githubusercontent.com/karenacosta-alt/Avances_tesis/main/dashboard.py
```

## 4. Dependencias en el entorno virtual

```bash
cd ~/prueba
[ -d entorno ] || python3 -m venv entorno
entorno/bin/pip install pyserial psycopg2-binary requests smbus2 adafruit-blinka adafruit-circuitpython-bme680 RPi.GPIO
```

## 5. Migrar la base local

```bash
psql -U estacion_user -h 127.0.0.1 -d estacion_db -f migracion_local.sql
```

Se puede ejecutar más de una vez. Los registros que ya existían quedan marcados como enviados.

## 6. Configuración

```bash
sudo mkdir -p /etc/estacion
sudo curl -fsSL -o /etc/estacion/estacion.env https://raw.githubusercontent.com/karenacosta-alt/Avances_tesis/main/despliegue/estacion.env.ejemplo
sudo nano /etc/estacion/estacion.env
```

Completar `CODIGO_ESTACION`, `URL_SERVIDOR` (la misma que usa EST01) y `DB_PASSWORD`. El código debe ser el mismo que ya figura en `SELECT codigo FROM estaciones;` del paso 0, así las lecturas nuevas siguen en la misma estación.

```bash
sudo chmod 600 /etc/estacion/estacion.env
sudo chown USUARIO /etc/estacion/estacion.env
```

## 7. Servicio systemd

```bash
sudo curl -fsSL -o /etc/systemd/system/estacion-sensores.service https://raw.githubusercontent.com/karenacosta-alt/Avances_tesis/main/despliegue/estacion-sensores.service
sudo sed -i "s/USUARIO/$USER/g" /etc/systemd/system/estacion-sensores.service
sudo systemctl daemon-reload
sudo systemctl enable --now estacion-sensores
```

Si la carpeta del código no es `~/prueba`, corregir `WorkingDirectory` y `ExecStart` con `sudo nano /etc/systemd/system/estacion-sensores.service`.

## 8. Comprobar

```bash
systemctl status estacion-sensores --no-pager
journalctl -u estacion-sensores -f
```

Debe aparecer `Estación EST0X iniciada` y, en el siguiente cuarto de hora, una línea con los valores y `guardado=True sincronizados=1` o más.

En la base local:

```bash
psql -U estacion_user -h 127.0.0.1 -d estacion_db -c "SELECT l.timestamp, l.co2_ppm, l.pm25_ugm3, l.sincronizado FROM lecturas l JOIN estaciones e ON e.id=l.estacion_id WHERE e.codigo='EST0X' ORDER BY l.id DESC LIMIT 5;"
```

En el servidor central (desde cualquier equipo de la red):

```bash
curl "http://IP_DEL_SERVIDOR:8000/api/lecturas?codigo_estacion=EST0X&limit=5" | head -c 600
```

## Si algo falla

- `Falta en la tabla ...`: no se ejecutó la migración (paso 5).
- `No se pudo conectar a la base local`: revisar `DB_PASSWORD` en `/etc/estacion/estacion.env`.
- `No module named ...`: repetir el paso 4.
- `sincronizados=0` con pendientes: el servidor no responde; las lecturas quedan guardadas y se envían cuando vuelva.
- Volver atrás: `sudo systemctl disable --now estacion-sensores`, restaurar `~/respaldos/prueba_FECHA` y volver a habilitar el servicio anterior.
