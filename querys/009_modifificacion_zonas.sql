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
        RAISE EXCEPTION 'No se encontró la sede Fraternidad';
    END IF;

    -- 1) "Bloque 5" -> "Baños" (reactivado, ya no es un bloque)
    UPDATE ubicaciones
    SET nombre = 'Baños', tipo = 'ZONA_COMUN'::tipoubicacion, activa = TRUE
    WHERE nombre = 'Bloque 5'
      AND NOT EXISTS (SELECT 1 FROM ubicaciones WHERE sede_id = v_sede AND lower(nombre) = 'baños');

    -- 2) Si "Bloque 5" se había borrado del todo, crea "Baños" igualmente
    INSERT INTO ubicaciones (sede_id, nombre, tipo, activa)
    SELECT v_sede, 'Baños', 'ZONA_COMUN'::tipoubicacion, TRUE
    WHERE NOT EXISTS (SELECT 1 FROM ubicaciones WHERE sede_id = v_sede AND lower(nombre) = 'baños');

    -- 3) "Vestieres"
    INSERT INTO ubicaciones (sede_id, nombre, tipo, activa)
    SELECT v_sede, 'Vestieres', 'ZONA_COMUN'::tipoubicacion, TRUE
    WHERE NOT EXISTS (SELECT 1 FROM ubicaciones WHERE sede_id = v_sede AND lower(nombre) = 'vestieres');
END $$;

-- Verificación
SELECT nombre, tipo, activa FROM ubicaciones
WHERE nombre IN ('Baños', 'Vestieres', 'Bloque 5');