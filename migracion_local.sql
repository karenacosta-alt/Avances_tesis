-- ============================================================
-- MIGRACIÓN DE LA BASE LOCAL (ejecutar en cada Raspberry Pi)
-- ============================================================
-- Antes de ejecutar, hacer un respaldo:
--   pg_dump -U estacion_user -h 127.0.0.1 estacion_db > respaldo_antes_migracion.sql
--
-- Ejecutar con:
--   psql -U estacion_user -h 127.0.0.1 -d estacion_db -f migracion_local.sql
--
-- Se puede ejecutar más de una vez sin riesgo: cada paso verifica
-- si ya fue aplicado.
-- ============================================================

BEGIN;

-- 1) Marca de tiempo con zona horaria.
--    Si la columna es "timestamp without time zone", se convierte a
--    "timestamp with time zone". Los valores existentes se interpretan
--    en la zona horaria configurada en PostgreSQL, que es la que usó
--    now() al guardarlos.
DO $$
BEGIN
    IF (SELECT data_type FROM information_schema.columns
        WHERE table_name = 'lecturas' AND column_name = 'timestamp')
        = 'timestamp without time zone' THEN
        EXECUTE format(
            'ALTER TABLE lecturas ALTER COLUMN "timestamp" TYPE TIMESTAMPTZ '
            'USING "timestamp" AT TIME ZONE %L',
            current_setting('TimeZone'));
        RAISE NOTICE 'Columna timestamp convertida a TIMESTAMPTZ (zona %).',
            current_setting('TimeZone');
    END IF;
END $$;

-- 2) Identificador de fila, necesario para marcar qué registros se enviaron.
ALTER TABLE lecturas ADD COLUMN IF NOT EXISTS id BIGSERIAL;

-- 3) Campos de la cola de sincronización.
--    Los registros que ya existían se marcan como sincronizados para no
--    reenviarlos: el servidor ya los tiene (con la hora de recepción como
--    marca de tiempo), y reenviarlos generaría duplicados.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'lecturas' AND column_name = 'sincronizado') THEN
        ALTER TABLE lecturas ADD COLUMN sincronizado BOOLEAN NOT NULL DEFAULT FALSE;
        UPDATE lecturas SET sincronizado = TRUE;
        RAISE NOTICE 'Campo sincronizado agregado; registros previos marcados como enviados.';
    END IF;
END $$;

ALTER TABLE lecturas ADD COLUMN IF NOT EXISTS intentos_envio INTEGER NOT NULL DEFAULT 0;
ALTER TABLE lecturas ADD COLUMN IF NOT EXISTS sincronizado_en TIMESTAMPTZ;

-- 4) Índice para encontrar rápido los registros pendientes.
CREATE INDEX IF NOT EXISTS idx_lecturas_pendientes
    ON lecturas (id) WHERE sincronizado = FALSE;

COMMIT;

-- Verificación: debería mostrar las columnas nuevas.
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'lecturas'
ORDER BY ordinal_position;
