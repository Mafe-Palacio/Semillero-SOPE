-- =====================================================================
-- OPE - Usuarios de prueba (corregido contra el esquema real)
-- Tabla: usuarios (PK usuario_id) | enums: rolusuario, tipovinculacion
-- Contraseña de los 3 usuarios: Admin123!  (hash bcrypt verificado)
-- Requisito: haber corrido 001_idx_un_solo_reclamo_activo.sql
--            (agrega 'SUPERADMIN' al enum rolusuario)
-- Idempotente: si el correo ya existe, repara rol/contraseña/estado.
-- =====================================================================

-- 1) USUARIO NORMAL ----------------------------------------------------
INSERT INTO usuarios (
    usuario_id, nombre_completo, cedula, carnet, celular, correo,
    hashed_password, rol, tipo_vinculacion, sede_id,
    is_verified, is_active, is_blocked
) VALUES (
    gen_random_uuid(), 'Estudiante Prueba OPE', '1020304050', 'EST-2026-01', '3001234567',
    'estudiante.prueba@correo.itm.edu.co',
    '$2b$12$Jyinoeu9dos/bMO.ThB2hucEAW1iKMrLrHnoouVkN9ur3styCbY2y',
    'USER'::rolusuario, 'ESTUDIANTE'::tipovinculacion, NULL,
    TRUE, TRUE, FALSE
)
ON CONFLICT (correo) DO UPDATE SET
    hashed_password = EXCLUDED.hashed_password, rol = EXCLUDED.rol,
    is_verified = TRUE, is_active = TRUE, is_blocked = FALSE, motivo_bloqueo = NULL;

-- 2) ADMIN DE FRATERNIDAD ---------------------------------------------
-- (correo distinto: admin.fraternidad@itm.edu.co ya lo usa el SUPERADMIN de 002_...)
INSERT INTO usuarios (
    usuario_id, nombre_completo, cedula, carnet, celular, correo,
    hashed_password, rol, tipo_vinculacion, sede_id,
    is_verified, is_active, is_blocked
) VALUES (
    gen_random_uuid(), 'Administrador Fraternidad', '1098765432', 'ADM-FRAT-01', '3109876543',
    'admin.sede.fraternidad@itm.edu.co',
    '$2b$12$Jyinoeu9dos/bMO.ThB2hucEAW1iKMrLrHnoouVkN9ur3styCbY2y',
    'ADMIN'::rolusuario, 'ADMINISTRATIVO'::tipovinculacion,
    (SELECT sede_id FROM sedes WHERE codigo = 'FRAT' LIMIT 1),
    TRUE, TRUE, FALSE
)
ON CONFLICT (correo) DO UPDATE SET
    hashed_password = EXCLUDED.hashed_password, rol = EXCLUDED.rol, sede_id = EXCLUDED.sede_id,
    is_verified = TRUE, is_active = TRUE, is_blocked = FALSE, motivo_bloqueo = NULL;

-- 3) SUPERADMIN (sin sede: la elige con la cabecera X-Sede-Id) ----------
INSERT INTO usuarios (
    usuario_id, nombre_completo, cedula, carnet, celular, correo,
    hashed_password, rol, tipo_vinculacion, sede_id,
    is_verified, is_active, is_blocked
) VALUES (
    gen_random_uuid(), 'Superadministrador General', '9999999999', 'SA-001', '3009999999',
    'superadmin@itm.edu.co',
    '$2b$12$Jyinoeu9dos/bMO.ThB2hucEAW1iKMrLrHnoouVkN9ur3styCbY2y',
    'SUPERADMIN'::rolusuario, 'ADMINISTRATIVO'::tipovinculacion, NULL,
    TRUE, TRUE, FALSE
)
ON CONFLICT (correo) DO UPDATE SET
    hashed_password = EXCLUDED.hashed_password, rol = EXCLUDED.rol, sede_id = NULL,
    is_verified = TRUE, is_active = TRUE, is_blocked = FALSE, motivo_bloqueo = NULL;

-- Verificación
SELECT correo, rol, sede_id, is_verified, is_active, is_blocked
FROM usuarios
WHERE correo IN ('estudiante.prueba@correo.itm.edu.co',
                 'admin.sede.fraternidad@itm.edu.co',
                 'superadmin@itm.edu.co');

-- =====================================================================
-- 4) ELIMINAR SUPERADMIN
-- - NO borra logs_auditoria (es la bitácora inmutable) ni actas.
-- - Si el usuario ya tiene historial (FK ON DELETE RESTRICT), lo
--   DESACTIVA en vez de borrarlo, igual que el DELETE /usuarios/{id}.
-- - No permite borrar al último SUPERADMIN activo.
-- =====================================================================
DO $$
DECLARE
    v_correo TEXT := 'superadmin@itm.edu.co';   -- <- cambia este correo
    v_id     UUID;
BEGIN
    SELECT usuario_id INTO v_id
    FROM usuarios WHERE correo = v_correo AND rol = 'SUPERADMIN';

    IF v_id IS NULL THEN
        RAISE NOTICE 'No existe un SUPERADMIN con el correo %', v_correo;
        RETURN;
    END IF;

    IF (SELECT count(*) FROM usuarios
        WHERE rol = 'SUPERADMIN' AND is_active AND usuario_id <> v_id) = 0 THEN
        RAISE EXCEPTION 'No se puede eliminar al último SUPERADMIN activo';
    END IF;

    DELETE FROM codigos_verificacion WHERE usuario_id = v_id;  -- (ya es CASCADE, por claridad)
    DELETE FROM tokens_revocados     WHERE usuario_id = v_id;  -- sin FK, quedaría huérfano

    BEGIN
        DELETE FROM usuarios WHERE usuario_id = v_id;
        RAISE NOTICE 'SUPERADMIN % eliminado definitivamente.', v_correo;
    EXCEPTION WHEN foreign_key_violation THEN
        UPDATE usuarios SET is_active = FALSE WHERE usuario_id = v_id;
        RAISE NOTICE '% tiene historial (auditoría/actas/custodia): se DESACTIVÓ en lugar de borrarse.', v_correo;
    END;
END $$;