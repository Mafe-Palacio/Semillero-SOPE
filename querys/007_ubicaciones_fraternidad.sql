-- Lugares donde se puede encontrar/perder un objeto en la sede Fraternidad.
-- Idempotente: no duplica un lugar que ya exista con el mismo nombre en la sede.
-- (La API ya devuelve las ubicaciones ordenadas por nombre; aquí se insertan
--  también en orden alfabético.)
DO $$
DECLARE
    v_sede UUID;
BEGIN
    SELECT sede_id INTO v_sede
    FROM sedes
    WHERE codigo = 'FRAT' OR nombre ILIKE '%Fraternidad%'
    ORDER BY (codigo = 'FRAT') DESC
    LIMIT 1;

    IF v_sede IS NULL THEN
        RAISE EXCEPTION 'No se encontró la sede Fraternidad (codigo FRAT). Revisa la tabla sedes.';
    END IF;

    INSERT INTO ubicaciones (sede_id, nombre, tipo, activa)
    SELECT v_sede, l.nombre, l.tipo::tipoubicacion, TRUE
    FROM (VALUES
        ('Auditorio Menor',                                     'ZONA_COMUN'),
        ('Aula pedagógica infantil',                            'ZONA_COMUN'),
        ('Biblioteca',                                          'ZONA_COMUN'),
        ('Bloque K',                                            'BLOQUE'),
        ('Bloque L',                                            'BLOQUE'),
        ('Bloque M',                                            'BLOQUE'),
        ('Bloque N',                                            'BLOQUE'),
        ('Bloque O',                                            'BLOQUE'),
        ('Cafetería (dentro del campus)',                       'ZONA_COMUN'),
        ('Cafetería (fuera del campus)',                        'OTRO'),
        ('Cancha profesional de fútbol',                        'ZONA_COMUN'),
        ('Centro Cultural Fraternidad (auditorio principal)',   'ZONA_COMUN'),
        ('Enfermería',                                          'ZONA_COMUN'),
        ('Entrada / Salida Miraflores',                         'PORTERIA'),
        ('Entrada / Salida principal',                          'PORTERIA'),
        ('Fuente',                                              'ZONA_COMUN'),
        ('Fuera del campus',                                    'OTRO'),
        ('Gimnasio',                                            'ZONA_COMUN'),
        ('Kioscos',                                             'ZONA_COMUN'),
        ('Laboratorios',                                        'ZONA_COMUN'),
        ('Museo de Ciencias Naturales de La Salle',             'ZONA_COMUN'),
        ('Observatorio Astronómico',                            'ZONA_COMUN'),
        ('Otros',                                               'OTRO'),
        ('Papelería',                                           'ZONA_COMUN'),
        ('Parque i (laboratorios de investigación)',            'ZONA_COMUN'),
        ('Piscina',                                             'ZONA_COMUN'),
        ('Placa cubierta polideportiva',                        'ZONA_COMUN'),
        ('Plaza principal',                                     'ZONA_COMUN'),
        ('Sótanos',                                             'ZONA_COMUN'),
        ('Tiendas',                                             'ZONA_COMUN'),
        ('Zona verde al lado del auditorio',                    'ZONA_COMUN'),
        ('Zonas de parqueadero',                                'ZONA_COMUN')
    ) AS l(nombre, tipo)
    WHERE NOT EXISTS (
        SELECT 1 FROM ubicaciones u
        WHERE u.sede_id = v_sede AND lower(u.nombre) = lower(l.nombre)
    );

    RAISE NOTICE 'Ubicaciones de Fraternidad cargadas (sede %).', v_sede;
END $$;

-- Verificación
SELECT nombre, tipo, activa FROM ubicaciones
WHERE sede_id = (SELECT sede_id FROM sedes WHERE codigo = 'FRAT' OR nombre ILIKE '%Fraternidad%'
                 ORDER BY (codigo = 'FRAT') DESC LIMIT 1)
ORDER BY nombre;
