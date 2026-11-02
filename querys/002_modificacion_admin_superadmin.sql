-- Crea (o repara) un SUPERADMIN y un ADMIN. Es seguro correrlo varias veces:
-- si el correo ya existe, solo le restablece la contraseña, el rol y el estado.
-- Contraseña de ambos: Admin123!
INSERT INTO usuarios (
    usuario_id, nombre_completo, cedula, correo, hashed_password,
    rol, tipo_vinculacion, sede_id,
    is_verified, is_active, is_blocked
)
VALUES
-- SUPERADMIN: sin sede propia (elige cuál supervisar desde el sitio)
(
    gen_random_uuid(), 'Superadmin Fraternidad', '9000000001',
    'admin.fraternidad@itm.edu.co',
    '$2b$12$Jyinoeu9dos/bMO.ThB2hucEAW1iKMrLrHnoouVkN9ur3styCbY2y',
    'SUPERADMIN'::rolusuario, 'ADMINISTRATIVO'::tipovinculacion, NULL,
    true, true, false
),
-- ADMIN de la sede Robledo
(
    gen_random_uuid(), 'Admin Robledo', '9000000002',
    'admin.robledo@itm.edu.co',
    '$2b$12$Jyinoeu9dos/bMO.ThB2hucEAW1iKMrLrHnoouVkN9ur3styCbY2y',
    'ADMIN'::rolusuario, 'ADMINISTRATIVO'::tipovinculacion,
    (SELECT sede_id FROM sedes WHERE nombre ILIKE 'Robledo%' LIMIT 1),
    true, true, false
)
ON CONFLICT (correo) DO UPDATE SET
    hashed_password = EXCLUDED.hashed_password,
    rol             = EXCLUDED.rol,
    sede_id         = EXCLUDED.sede_id,
    is_verified     = true,
    is_active       = true,
    is_blocked      = false,
    motivo_bloqueo  = NULL;

-- Revisa el resultado: el ADMIN debe tener sede_id (si sale vacío, no existe
-- una sede cuyo nombre empiece por "Robledo"; revisa la tabla sedes).
SELECT correo, rol, sede_id, is_verified, is_active, is_blocked
FROM usuarios
WHERE correo IN ('admin.fraternidad@itm.edu.co', 'admin.robledo@itm.edu.co');