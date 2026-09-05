# Monitoreo Distribuido e Inteligente de la Calidad del Aire — ITR Centro-Sur (UTEC)

Sistema de monitoreo de calidad del aire basado en una red distribuida de nodos IoT con Edge Computing, desarrollado como trabajo de tesis de grado en Ingeniería Agroambiental, Universidad Tecnológica del Uruguay (UTEC), ITR Centro-Sur, Durazno.

- **Autora:** Karen Noelia Acosta Cardozo
- **Tutor:** Jorge Iván Zapata
- **Línea de investigación:** Monitoreo Ambiental / Internet de las Cosas (IoT) aplicado al ambiente

## Descripción del proyecto

El proyecto escala un prototipo aislado de monitoreo hacia una red distribuida de cinco nodos sensores, basada en los paradigmas de Internet de las Cosas (IoT) y Edge Computing, con el objetivo de caracterizar la dinámica espacio-temporal de CO2, CO, PM2.5, PM10, temperatura y humedad en espacios interiores del ITR Centro-Sur.

Cada nodo opera como una unidad autónoma de procesamiento basada en Raspberry Pi 4, ejecutando localmente una cadena de preprocesamiento estadístico (Filtro de Kalman, Media Móvil de k=3 y modelos de aprendizaje automático — XGBoost/Random Forest — para la corrección de derivas térmicas de los sensores de bajo costo). Los datos se almacenan localmente en PostgreSQL, garantizando tolerancia a fallos ante interrupciones de conectividad, y se transmiten de forma asíncrona a un servidor central mediante una API REST, donde quedan disponibles para su visualización.

## Arquitectura del sistema

El sistema se organiza en tres capas funcionales:

1. **Capa de adquisición (nodo / Edge):** sensores ambientales conectados a una Raspberry Pi 4 por protocolos I2C y UART, con almacenamiento local en PostgreSQL.
2. **Capa de procesamiento local y transmisión:** filtrado de señal (Kalman + media móvil), corrección con modelos de ML y envío por lotes a través de una API REST.
3. **Capa de consolidación central:** servidor que recibe, valida y almacena los datos de los cinco nodos, y los expone para su visualización en un dashboard.

## Contenido del repositorio

| Archivo | Descripción |
|---|---|
| `prueba_rest_estaciones.py` | Script de nodo (Raspberry Pi 4). Lee los sensores de CO2, CO, temperatura/humedad y material particulado, guarda cada lectura en la base de datos local y la envía al servidor central vía REST. |
| `api_main.py` | API REST del servidor central (FastAPI). Recibe las lecturas enviadas por los nodos, gestiona el alta de estaciones y expone endpoints de consulta para alimentar el dashboard. |
| `dashboard.py` | Dashboard de visualización (Streamlit + Plotly). Muestra valores actuales, series temporales por variable y estadística descriptiva del período seleccionado. |

## Hardware y sensores

| Variable | Modelo | Tecnología | Rango | Precisión |
|---|---|---|---|---|
| CO2 | DFRobot SEN0220 | NDIR infrarrojo | 0–5000 ppm | ±5 % |
| PM2.5 / PM10 | DFRobot SEN0460 | Dispersión láser | 0–1000 µg/m³ | Óptica de conteo |
| CO | SEN0466 | Electroquímico (I2C) | 10–1000 ppm | Alta resolución |
| Temperatura / Humedad | BME680 (I2C) | Capacitivo/MEMS | — | — |

La unidad central de procesamiento de cada nodo es una Raspberry Pi 4, elegida por su capacidad de ejecutar un sistema operativo completo, una instancia local de PostgreSQL y el desarrollo lógico en Python de forma concurrente.

## Puntos de despliegue de los nodos

Los cinco nodos de la red están desplegados en los siguientes espacios del ITR Centro-Sur:

- Suelos
- LabEr
- LabMab
- Trituración y Molienda (Laboratorio de Química Analítica)

> Nota: estas son las ubicaciones reales de despliegue. Reemplazan las ubicaciones tentativas descritas en el anteproyecto de tesis (Recepción, Medata, Biblioteca y Laboratorio de Electrónica e Instrumentación).

## Variables de entorno

Cada componente lee su configuración desde variables de entorno; no se deben dejar credenciales reales en el código.

**`api_main.py`** (servidor central)

| Variable | Descripción | Valor por defecto |
|---|---|---|
| `DB_NAME` | Nombre de la base de datos | `tesis_db` |
| `DB_USER` | Usuario de PostgreSQL | `postgres` |
| `DB_PASSWORD` | Contraseña de PostgreSQL | — |
| `DB_HOST` | Host de la base de datos | `127.0.0.1` |
| `DB_PORT` | Puerto de PostgreSQL | `5432` |

**`dashboard.py`** (dashboard)

| Variable | Descripción | Valor por defecto |
|---|---|---|
| `DB_USER` | Usuario de PostgreSQL | `estacion_user` |
| `DB_PASS` | Contraseña de PostgreSQL | — |
| `DB_HOST` | Host de la base de datos | `127.0.0.1` |
| `DB_NAME` | Nombre de la base de datos | `estacion_db` |

**`prueba_rest_estaciones.py`** (nodo)

| Variable | Descripción | Valor por defecto |
|---|---|---|
| `URL_SERVIDOR` | URL del endpoint REST del servidor central | `http://localhost:8000/api/lecturas` |
| `CODIGO_ESTACION` | Código identificador del nodo | `EST01` |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | Conexión a la base de datos local del nodo | ver script |

> Nota: `dashboard.py` usa `DB_PASS` mientras que `api_main.py` y `prueba_rest_estaciones.py` usan `DB_PASSWORD`. Tenerlo en cuenta al definir las variables de entorno en cada entorno de despliegue.

## Instalación y ejecución

### Servidor central (API REST)

```bash
pip install fastapi uvicorn psycopg2-binary pydantic
uvicorn api_main:app --host 0.0.0.0 --port 8000
```

### Dashboard

```bash
pip install streamlit pandas sqlalchemy psycopg2-binary plotly
streamlit run dashboard.py
```

### Nodo sensor (Raspberry Pi 4)

Requiere las librerías de hardware específicas de Raspberry Pi (I2C/UART):

```bash
pip install pyserial psycopg2-binary requests smbus2 adafruit-circuitpython-ads1x15 adafruit-circuitpython-bme680
python prueba_rest_estaciones.py
```

## Estado del proyecto

Este repositorio corresponde a una tesis de grado en curso. El diseño completo del sistema (autenticación JWT, cifrado HTTPS/TLS de extremo a extremo, corrección por ML entrenada contra la estación de referencia AQM65, carcasa protectora impresa en 3D, etc.) se documenta en el anteproyecto de tesis; algunos de estos componentes se encuentran en distintas etapas de implementación respecto de los scripts incluidos aquí.
