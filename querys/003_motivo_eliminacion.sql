-- HU12 / HU14: motivo del usuario al solicitar eliminación de un reporte o publicación de hallazgo.
-- Ejecutar UNA vez en el SQL Editor de Supabase (es idempotente).

ALTER TABLE reportes_perdida 
ADD COLUMN IF NOT EXISTS motivo_eliminacion VARCHAR(500);

ALTER TABLE publicaciones_encontradas 
ADD COLUMN IF NOT EXISTS motivo_eliminacion VARCHAR(500);

