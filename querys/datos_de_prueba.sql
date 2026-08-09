-- ============================================================================
-- DATOS DE PRUEBA — Sistema de Objetos Perdidos y Encontrados ITM
-- Ejecutar DESPUÉS de correr script_bd_sope.sql (crea la estructura primero).
-- Los UUID son fijos y legibles a propósito, para que sea fácil copiarlos
-- al probar los endpoints en Swagger (/docs) sin tener que ir a buscarlos
-- en la base de datos cada vez.
--
-- Usuarios de prueba (contraseña sin hashear, para hacer login):
--   admin.fraternidad@correo.itm.edu.co  -> Admin1234!
--   admin.robledo@correo.itm.edu.co      -> Admin1234!
--   juan.perez@correo.itm.edu.co         -> Usuario1234!
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. SEDES
-- ----------------------------------------------------------------------------
INSERT INTO sedes (sede_id, nombre, codigo, activa) VALUES
('10000000-0000-0000-0000-000000000001', 'Sede Fraternidad', 'FRAT', true),
('10000000-0000-0000-0000-000000000002', 'Sede Robledo', 'ROBLEDO', true);

-- ----------------------------------------------------------------------------
-- 2. USUARIOS (antes que ubicaciones/puntos_entrega, porque estas referencian
--    usuario_crea_id — lo dejamos NULL para simplificar el seed y evitar
--    dependencia circular; usuario_crea_id es opcional en el esquema).
-- ----------------------------------------------------------------------------
INSERT INTO usuarios (
    usuario_id, nombre_completo, cedula, carnet, celular, correo,
    hashed_password, rol, tipo_vinculacion, sede_id,
    is_verified, is_active, is_blocked
) VALUES
('40000000-0000-0000-0000-000000000001', 'Admin Fraternidad', '1000000001', 'ADM-001', '3001111111',
 'admin.fraternidad@correo.itm.edu.co',
 '$2b$12$5jjEnnqxSC0BTFNG7b5bdeS5WFlBF2IgZeFVaveWWKqD58ht76l1.',
 'ADMIN', 'ADMINISTRATIVO', '10000000-0000-0000-0000-000000000001',
 true, true, false),

('40000000-0000-0000-0000-000000000002', 'Admin Robledo', '1000000002', 'ADM-002', '3002222222',
 'admin.robledo@correo.itm.edu.co',
 '$2b$12$5jjEnnqxSC0BTFNG7b5bdeS5WFlBF2IgZeFVaveWWKqD58ht76l1.',
 'ADMIN', 'ADMINISTRATIVO', '10000000-0000-0000-0000-000000000002',
 true, true, false),

('40000000-0000-0000-0000-000000000003', 'Juan Pérez', '1000000003', 'EST-2026-001', '3003333333',
 'juan.perez@correo.itm.edu.co',
 '$2b$12$WNzq8qNEtwtgz9XSxsCNb.0fIF6wtfEGM3U/LcFTeURUZi4xy6KDe',
 'USER', 'ESTUDIANTE', NULL,
 true, true, false);

-- Nota: las dos contraseñas de arriba son distintas, pero puse el MISMO hash
-- de 'Admin1234!' en los dos admins solo para copiar/pegar más fácil en el
-- seed — no significa que compartan hash en un caso real, cada registro por
-- /auth/registro genera el suyo propio con salt distinto.

-- ----------------------------------------------------------------------------
-- 3. UBICACIONES
-- ----------------------------------------------------------------------------
INSERT INTO ubicaciones (ubicacion_id, sede_id, nombre, tipo, activa, usuario_crea_id) VALUES
('20000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000001',
 'Bloque 5', 'BLOQUE', true, '40000000-0000-0000-0000-000000000001'),
('20000000-0000-0000-0000-000000000002', '10000000-0000-0000-0000-000000000001',
 'Portería Principal', 'PORTERIA', true, '40000000-0000-0000-0000-000000000001'),
('20000000-0000-0000-0000-000000000003', '10000000-0000-0000-0000-000000000002',
 'Bloque A', 'BLOQUE', true, '40000000-0000-0000-0000-000000000002');

-- ----------------------------------------------------------------------------
-- 4. PUNTOS DE ENTREGA
-- ----------------------------------------------------------------------------
INSERT INTO puntos_entrega ("puntoEntrega_id", sede_id, nombre, tipo, activa, usuario_crea_id) VALUES
('30000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000001',
 'Oficina de Objetos Perdidos - Fraternidad', 'OFICINA', true, '40000000-0000-0000-0000-000000000001'),
('30000000-0000-0000-0000-000000000002', '10000000-0000-0000-0000-000000000002',
 'Oficina de Objetos Perdidos - Robledo', 'OFICINA', true, '40000000-0000-0000-0000-000000000002');

-- ----------------------------------------------------------------------------
-- 5. CÓDIGOS DE VERIFICACIÓN
-- ----------------------------------------------------------------------------
INSERT INTO codigos_verificacion ("codigoVerificacion_id", usuario_id, codigo, tipo, expira_en, usado) VALUES
('50000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000003',
 '123456', 'REGISTRO', NOW() - INTERVAL '1 day', true),
('50000000-0000-0000-0000-000000000002', '40000000-0000-0000-0000-000000000003',
 '654321', 'RECUPERACION_PASSWORD', NOW() + INTERVAL '15 minutes', false);

-- ----------------------------------------------------------------------------
-- 6. REPORTES DE PÉRDIDA
-- ----------------------------------------------------------------------------
INSERT INTO reportes_perdida (
    "reportePerdida_id", usuario_id, categoria, descripcion, lugar_perdida_id,
    fecha_perdida, hora_aproximada, estado
) VALUES
('60000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000003',
 'ELECTRONICOS', 'Audífonos inalámbricos negros marca Sony', '20000000-0000-0000-0000-000000000001',
 CURRENT_DATE - 3, '14:30', 'APROBADA'),
('60000000-0000-0000-0000-000000000002', '40000000-0000-0000-0000-000000000003',
 'LLAVES', 'Llavero con 3 llaves y una manito de la suerte', '20000000-0000-0000-0000-000000000003',
 CURRENT_DATE - 1, '09:00', 'PENDIENTE');

-- ----------------------------------------------------------------------------
-- 7. PUBLICACIONES ENCONTRADAS
-- ----------------------------------------------------------------------------
INSERT INTO publicaciones_encontradas (
    "publicacionEncontrado_id", usuario_id, categoria, descripcion,
    lugar_hallazgo_id, lugar_entrega_fisica_id, fecha_hallazgo, estado
) VALUES
('70000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000003',
 'ELECTRONICOS', 'Audífonos Sony negros encontrados en una banca',
 '20000000-0000-0000-0000-000000000001', '30000000-0000-0000-0000-000000000001',
 CURRENT_DATE - 2, 'APROBADA'),
('70000000-0000-0000-0000-000000000002', '40000000-0000-0000-0000-000000000003',
 'LLAVES', 'Manojo de llaves encontrado cerca al bloque A',
 '20000000-0000-0000-0000-000000000003', '30000000-0000-0000-0000-000000000002',
 CURRENT_DATE, 'PENDIENTE');

-- ----------------------------------------------------------------------------
-- 8. OBJETOS EN CUSTODIA
-- ----------------------------------------------------------------------------
INSERT INTO objetos_en_custodia (
    "objetoEnCustodia_id", admin_id, "publicacionEncontrado_id", categoria,
    descripcion, lugar_origen_id, fecha_ingreso, estado
) VALUES
('80000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000001',
 '70000000-0000-0000-0000-000000000001', 'ELECTRONICOS', 'Audífonos Sony negros',
 '30000000-0000-0000-0000-000000000001', CURRENT_DATE - 2, 'EN_CUSTODIA'),
('80000000-0000-0000-0000-000000000002', '40000000-0000-0000-0000-000000000002',
 NULL, 'LLAVES', 'Manojo de 3 llaves, entregado directamente en oficina',
 '30000000-0000-0000-0000-000000000002', CURRENT_DATE - 5, 'EN_CUSTODIA');

-- ----------------------------------------------------------------------------
-- 9. PREGUNTAS DE SEGURIDAD (para el objeto 1)
-- ----------------------------------------------------------------------------
INSERT INTO preguntas_seguridad ("preguntaSeguridad_id", "objetoEnCustodia_id", pregunta, respuesta_correcta, orden) VALUES
('90000000-0000-0000-0000-000000000001', '80000000-0000-0000-0000-000000000001',
 '¿De qué color es el estuche de los audífonos?', 'Negro', 1),
('90000000-0000-0000-0000-000000000002', '80000000-0000-0000-0000-000000000001',
 '¿Qué marca son los audífonos?', 'Sony', 2);

-- ----------------------------------------------------------------------------
-- 10. RECLAMOS
-- ----------------------------------------------------------------------------
INSERT INTO reclamos ("reclamo_id", "objetoEnCustodia_id", usuario_id, estado, fecha_cita, horario_cita, es_presencial) VALUES
('a0000000-0000-0000-0000-000000000001', '80000000-0000-0000-0000-000000000001',
 '40000000-0000-0000-0000-000000000003', 'EN_REVISION', NULL, NULL, false),
('a0000000-0000-0000-0000-000000000002', '80000000-0000-0000-0000-000000000002',
 '40000000-0000-0000-0000-000000000003', 'RECLAMADO', NOW() - INTERVAL '1 day', '10:00 AM - 12:00 PM', true);

-- ----------------------------------------------------------------------------
-- 11. RESPUESTAS DE SEGURIDAD (para el reclamo 1, sobre el objeto 1)
-- ----------------------------------------------------------------------------
INSERT INTO respuestas_seguridad ("respuestaSeguridad_id", reclamo_id, "preguntaSeguridad_id", respuesta_usuario) VALUES
('b0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001',
 '90000000-0000-0000-0000-000000000001', 'Negro'),
('b0000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000001',
 '90000000-0000-0000-0000-000000000002', 'Sony');

-- ----------------------------------------------------------------------------
-- 12. POSIBLES COINCIDENCIAS (Smart Match)
-- ----------------------------------------------------------------------------
INSERT INTO posibles_coincidencias ("posibleCoincidencia_id", "objetoEnCustodia_id", "reportePerdida_id", usuario_id, score, notificado) VALUES
('c0000000-0000-0000-0000-000000000001', '80000000-0000-0000-0000-000000000001',
 '60000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000003', 92, true),
('c0000000-0000-0000-0000-000000000002', '80000000-0000-0000-0000-000000000002',
 '60000000-0000-0000-0000-000000000002', '40000000-0000-0000-0000-000000000003', 65, false);

-- ----------------------------------------------------------------------------
-- 13. ACTA DE ENTREGA (solo para el reclamo 2, que ya está en estado RECLAMADO)
-- ----------------------------------------------------------------------------
INSERT INTO actas_entrega (
    "actaEntrega_id", reclamo_id, nombre_reclamante, cedula_reclamante,
    correo_reclamante, celular_reclamante, carnet_reclamante, firma_url,
    procesada_por_admin_id, validacion_verbal
) VALUES
('d0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000002',
 'Juan Pérez', '1000000003', 'juan.perez@correo.itm.edu.co', '3003333333', 'EST-2026-001',
 'https://ejemplo-storage.supabase.co/firmas/firma-demo.png',
 '40000000-0000-0000-0000-000000000002', true);

-- ----------------------------------------------------------------------------
-- 14. LOGS DE AUDITORÍA
-- ----------------------------------------------------------------------------
INSERT INTO logs_auditoria ("auditLog_id", entidad, entidad_id, accion, usuario_id, detalle) VALUES
('e0000000-0000-0000-0000-000000000001', 'ObjetoEnCustodia', '80000000-0000-0000-0000-000000000001',
 'CREAR', '40000000-0000-0000-0000-000000000001', 'Objeto registrado desde publicación encontrada aprobada'),
('e0000000-0000-0000-0000-000000000002', 'Reclamo', 'a0000000-0000-0000-0000-000000000002',
 'CAMBIO_ESTADO', '40000000-0000-0000-0000-000000000002', 'Estado cambiado a RECLAMADO tras firmar acta de entrega'),
('e0000000-0000-0000-0000-000000000003', 'ReportePerdida', '60000000-0000-0000-0000-000000000001',
 'APROBAR', '40000000-0000-0000-0000-000000000001', 'Publicación aprobada tras revisión');
