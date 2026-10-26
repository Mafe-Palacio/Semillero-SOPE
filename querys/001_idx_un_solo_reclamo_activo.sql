-- HU08: un solo reclamo "vivo" por objeto en custodia.
-- create_tables() no modifica tablas que ya existen, así que en la base de datos
-- ya creada (Supabase) este índice debe aplicarse manualmente, una sola vez.

-- 1) Revisar si hay objetos con más de un reclamo vivo (el índice fallaría):
SELECT "objetoEnCustodia_id", COUNT(*) AS reclamos_vivos
FROM reclamos
WHERE estado IN ('ENVIADO', 'EN_REVISION', 'APROBADO', 'LISTO_PARA_RECOGER')
GROUP BY "objetoEnCustodia_id"
HAVING COUNT(*) > 1;
-- Si devuelve filas: cancelar o rechazar los reclamos sobrantes antes de seguir.

-- 2) Crear el índice único parcial:
CREATE UNIQUE INDEX IF NOT EXISTS idx_un_solo_reclamo_activo
ON reclamos ("objetoEnCustodia_id")
WHERE estado IN ('ENVIADO', 'EN_REVISION', 'APROBADO', 'LISTO_PARA_RECOGER');

-------------------------------------

ALTER TYPE rolusuario ADD VALUE IF NOT EXISTS 'SUPERADMIN';
UPDATE usuarios SET rol = 'SUPERADMIN' WHERE correo = 'admin.fraternidad@correo.itm.edu.co';