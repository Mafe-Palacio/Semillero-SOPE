-- Detalle del lugar ("Bloque L, salón L503") y observaciones libres del reportante.
-- Aplica a hallazgos (publicaciones_encontradas) y pérdidas (reportes_perdida).
-- Idempotente: se puede correr varias veces.
ALTER TABLE publicaciones_encontradas
    ADD COLUMN IF NOT EXISTS detalle_lugar VARCHAR(200) NULL,
    ADD COLUMN IF NOT EXISTS observaciones VARCHAR(500) NULL;

ALTER TABLE reportes_perdida
    ADD COLUMN IF NOT EXISTS detalle_lugar VARCHAR(200) NULL,
    ADD COLUMN IF NOT EXISTS observaciones VARCHAR(500) NULL;
