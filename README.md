# Monitoreo Distribuido e Inteligente de la Calidad del Aire — ITR Centro-Sur (UTEC)

Red distribuida de nodos IoT de bajo costo con Edge Computing para el monitoreo de la calidad del aire interior, desarrollada como trabajo final de grado en Ingeniería Agroambiental, Universidad Tecnológica del Uruguay (UTEC), ITR Centro-Sur, Durazno.

- **Autora:** Karen Noelia Acosta Cardozo
- **Tutor:** Jorge Iván Zapata
- **Línea de investigación:** Monitoreo ambiental / Internet de las Cosas (IoT) aplicado al ambiente

## Descripción del proyecto

El proyecto escala un prototipo aislado de monitoreo hacia una red de cinco nodos sensores distribuidos en espacios interiores del ITR Centro-Sur, con el objetivo de generar series temporales continuas de CO2, material particulado (PM1, PM2.5, PM10), temperatura y humedad relativa. El CO también se registra, pero solo para detectar eventos que superen el umbral de detección del sensor.

Cada nodo es una Raspberry Pi Compute Module 4 (CM4, 4 GB de RAM) que lee los sensores cada 15 minutos, guarda cada lectura en una base PostgreSQL local y la envía al servidor central mediante una API REST. Una cola de sincronización garantiza que ninguna lectura se pierda ante cortes de red: los registros se marcan como sincronizados solo cuando el servidor confirma su recepción.

## Arquitectura del sistema

1. **Capa de adquisición:** sensores conectados a la CM4 por I2C y UART. Lecturas sincronizadas con el reloj, en cada cuarto de hora exacto (:00, :15, :30, :45).
2. **Capa de procesamiento local (Edge):** almacenamiento en PostgreSQL 15, dashboard local en Streamlit y cola de sincronización hacia el servidor (como máximo 200 registros por ciclo, en orden cronológico).
3. **Capa de consolidación central:** API REST (FastAPI) que recibe, valida y almacena las lecturas de los cinco nodos.

Previsto para las próximas etapas: filtrado de señal (Filtro de Kalman + media móvil k=3) en la visualización y corrección de los datos crudos con XGBoost / Random Forest en el servidor, entrenados con los datos de co-localización frente a la estación de referencia AQM65.

## Contenido del repositorio

| Archivo | Descripción |
|---|---|
| `prueba_rest_estaciones.py` | Programa del nodo. Lee los cuatro sensores, guarda cada lectura en la base local como pendiente de envío y sincroniza los pendientes con el servidor central. Se ejecuta como servicio systemd. |
| `migracion_local.sql` | Migración de la base local de cada nodo (marca temporal con zona horaria y campos de la cola de sincronización). Puede ejecutarse más de una vez sin riesgo. |
| `api_main.py` | API REST del servidor central (FastAPI). |
| `dashboard.py` | Dashboard local del nodo (Streamlit + Plotly): valores actuales, series temporales, resumen estadístico y descarga en CSV. |
| `*_v15_compacta*.scad` / `.stl` | Diseño paramétrico (OpenSCAD) y modelos para impresión 3D de la carcasa del nodo (200 × 180 × 70 mm, PLA+). |

### Endpoints de la API

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/lecturas` | Recibe una lectura de un nodo; registra la estación si es nueva. Ante un error deshace la operación y responde con código de error, de modo que el nodo mantiene el registro como pendiente. |
| `GET` | `/api/lecturas` | Devuelve las últimas lecturas de una estación (300 por defecto). |
| `GET` | `/api/estaciones` | Lista los códigos de las estaciones registradas. |

## Hardware y sensores

| Variable | Sensor | Tecnología | Interfaz | Rango |
|---|---|---|---|---|
| CO2 | DFRobot SEN0220 | NDIR | UART3 (`/dev/ttyAMA3`), 9600 bps | 0–50.000 ppm |
| PM1 / PM2.5 / PM10 | DFRobot SEN0177 | Dispersión láser | UART5 (`/dev/ttyAMA5`), 9600 bps | 0–999 µg/m³ |
| CO | DFRobot SEN0466 | Electroquímico | I2C, dirección 0x74 | 0–1.000 ppm |
| Temperatura / HR | Bosch BME680 | Capacitivo / MEMS | I2C, dirección 0x77 | -40 a 85 °C / 0–100 % |

En `/boot/config.txt` deben estar habilitados `dtoverlay=uart3`, `dtoverlay=uart5` y `dtparam=i2c_arm=on`.

## Ubicación de los nodos

| Nodo | Ubicación |
|---|---|
| Nodo 1 | Laboratorio de Química Analítica |
| Nodo 2 | Laboratorio de Suelos |
| Nodo 3 | LabMAb |
| Nodo 4 | Laboratorio de Efluentes y Residuos (LabEr) |
| Nodo 5 | Trituración y Molienda |

La instalación es progresiva. El nodo 1 (EST01) registra datos desde febrero de 2026. Para la co-localización, los cinco nodos se trasladarán temporalmente al Laboratorio de Electrónica e Instrumentación, donde está la estación AQM65.

## Configuración

Las credenciales y parámetros se leen de variables de entorno; no deben quedar credenciales reales en el código. En el nodo se definen en `/etc/estacion/estacion.env`, que el servicio systemd carga con `EnvironmentFile`. Los archivos `.env` están excluidos del repositorio.

**Nodo (`prueba_rest_estaciones.py`)**

| Variable | Descripción | Por defecto |
|---|---|---|
| `CODIGO_ESTACION` | Código del nodo | `EST01` |
| `URL_SERVIDOR` | Endpoint de la API central | `http://localhost:8000/api/lecturas` |
| `INTERVALO_MIN` | Intervalo de lectura (min) | `15` |
| `MAX_ENVIOS_POR_CICLO` | Máximo de registros pendientes enviados por ciclo | `200` |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | Base local | `estacion_db`, `estacion_user`, —, `127.0.0.1`, `5432` |
| `PORT_CO2`, `PORT_PM` | Puertos serie | `/dev/ttyAMA3`, `/dev/ttyAMA5` |
| `I2C_BUS`, `I2C_ADDR_SEN0466`, `I2C_ADDR_BME680` | Bus y direcciones I2C | `1`, `0x74`, `0x77` |

**Dashboard (`dashboard.py`)**: `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` (lee también un archivo `.env` en la carpeta).

**Servidor (`api_main.py`)**: `DB_NAME` (`tesis_db`), `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`.

## Instalación y ejecución

### Nodo sensor

```bash
python3 -m venv entorno && source entorno/bin/activate
pip install pyserial psycopg2-binary requests smbus2 adafruit-blinka adafruit-circuitpython-bme680 RPi.GPIO
psql -U estacion_user -h 127.0.0.1 -d estacion_db -f migracion_local.sql
python prueba_rest_estaciones.py      # en producción: servicio systemd
```

### Dashboard local

```bash
pip install streamlit pandas sqlalchemy psycopg2-binary plotly python-dotenv
streamlit run dashboard.py
```

### Servidor central

```bash
pip install fastapi uvicorn psycopg2-binary pydantic
uvicorn api_main:app --host 0.0.0.0 --port 8000
```

## Estado del proyecto

Trabajo de grado en curso (primera etapa entregada en octubre de 2026).

- Implementado: cinco nodos armados con carcasa impresa en 3D; adquisición cada 15 minutos; base local con cola de sincronización; API REST; dashboard local. Tres nodos transmiten al servidor central.
- En desarrollo: cifrado HTTPS/TLS y autenticación de nodos con JWT (hoy la transmisión es HTTP dentro de la red institucional); conexión de los dos nodos restantes; co-localización con la AQM65; Filtro de Kalman y corrección por aprendizaje automático; panel centralizado con las cinco estaciones.
