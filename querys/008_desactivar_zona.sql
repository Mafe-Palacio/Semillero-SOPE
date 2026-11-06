DO $$
DECLARE
    v_id UUID;
BEGIN
    FOR v_id IN SELECT ubicacion_id FROM ubicaciones WHERE nombre = 'Bloque 5' LOOP
        BEGIN
            DELETE FROM ubicaciones WHERE ubicacion_id = v_id;
            RAISE NOTICE 'Bloque 5 (%) eliminado.', v_id;
        EXCEPTION WHEN foreign_key_violation THEN
            UPDATE ubicaciones SET activa = FALSE WHERE ubicacion_id = v_id;
            RAISE NOTICE 'Bloque 5 (%) tiene reportes asociados: se DESACTIVÓ.', v_id;
        END;
    END LOOP;
END $$;

-- Verificación: no debe aparecer activa
SELECT nombre, activa FROM ubicaciones WHERE nombre = 'Bloque 5';