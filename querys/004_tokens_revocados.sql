-- HU35: tokens invalidados al cerrar sesión (POST /auth/logout).
-- Ejecutar UNA vez en el SQL Editor de Supabase (es idempotente).
CREATE TABLE IF NOT EXISTS tokens_revocados (
    token_hash       VARCHAR(64) PRIMARY KEY,
    usuario_id       UUID        NOT NULL,
    tipo             VARCHAR(10) NOT NULL,
    expira_en        TIMESTAMP   NOT NULL,
    fecha_revocacion TIMESTAMP   NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);
CREATE INDEX IF NOT EXISTS ix_tokens_revocados_usuario ON tokens_revocados (usuario_id);
CREATE INDEX IF NOT EXISTS ix_tokens_revocados_expira  ON tokens_revocados (expira_en);
