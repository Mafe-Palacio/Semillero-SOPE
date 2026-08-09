-- Migración: ampliar el enum categoriaobjeto en Postgres/Supabase
-- ------------------------------------------------------------------
-- Contexto: se dividió ROPA_Y_ACCESORIOS en ROPA y ACCESORIOS, y se
-- agregaron BILLETERAS_Y_MONEDEROS, TERMOS_Y_CONTENEDORES y CASCOS.
--
-- IMPORTANTE sobre cómo correr esto:
-- Postgres NO permite usar un valor de enum recién agregado (ALTER TYPE
-- ... ADD VALUE) dentro de la MISMA transacción en la que se agregó.
-- Por eso este script está separado en pasos con su propio ";" y debes
-- ejecutarlo en el editor SQL de Supabase tal cual, en orden, SIN
-- envolverlo en un BEGIN/COMMIT manual. Si tu cliente SQL agrupa todo
-- en una sola transacción automáticamente, ejecuta el PASO 1 solo,
-- espera a que confirme, y luego ejecuta el PASO 2 en una consulta aparte.

-- =========================================================
-- PASO 1: agregar los nuevos valores al tipo (no borra nada)
-- =========================================================
ALTER TYPE categoriaobjeto ADD VALUE IF NOT EXISTS 'ROPA';
ALTER TYPE categoriaobjeto ADD VALUE IF NOT EXISTS 'ACCESORIOS';
ALTER TYPE categoriaobjeto ADD VALUE IF NOT EXISTS 'BILLETERAS_Y_MONEDEROS';
ALTER TYPE categoriaobjeto ADD VALUE IF NOT EXISTS 'TERMOS_Y_CONTENEDORES';
ALTER TYPE categoriaobjeto ADD VALUE IF NOT EXISTS 'CASCOS';

-- =========================================================
-- PASO 2 (ejecutar en una consulta APARTE, después del paso 1):
-- reasignar las filas existentes que tenían el valor viejo
-- ROPA_Y_ACCESORIOS. Se migran todas a ROPA por defecto; revisa caso
-- por caso si alguna en realidad debería quedar como ACCESORIOS.
-- =========================================================
UPDATE reportes_perdida
   SET categoria = 'ROPA'
 WHERE categoria = 'ROPA_Y_ACCESORIOS';

UPDATE publicaciones_encontradas
   SET categoria = 'ROPA'
 WHERE categoria = 'ROPA_Y_ACCESORIOS';

UPDATE objetos_en_custodia
   SET categoria = 'ROPA'
 WHERE categoria = 'ROPA_Y_ACCESORIOS';

-- =========================================================
-- PASO 3 (opcional, más delicado): eliminar ROPA_Y_ACCESORIOS del tipo
-- =========================================================
-- Postgres no permite hacer DROP VALUE de un enum directamente. Si en
-- algún momento quieres que ROPA_Y_ACCESORIOS deje de ser un valor
-- válido a nivel de base de datos (ya no se puede insertar), hay que
-- recrear el tipo completo. NO es necesario para que la app funcione
-- -- después del PASO 2 ya no quedan filas usándolo, y a nivel de
-- aplicación (Python/Pydantic) ese valor ya no existe, así que nadie
-- podrá volver a insertarlo desde la API. Déjalo así salvo que tengas
-- una razón puntual para forzarlo también a nivel de base de datos.
--
-- Si de verdad lo quieres hacer, avísame y lo armamos aparte: implica
-- crear un tipo nuevo, migrar la columna en las 3 tablas y borrar el
-- tipo viejo, con más riesgo de bloqueos si hay tráfico en producción.
