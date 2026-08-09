CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Creación de ENUMS
CREATE TYPE RolUsuario AS ENUM ('ADMIN', 'USER');
CREATE TYPE TipoVinculacion AS ENUM ('ESTUDIANTE', 'PROFESOR', 'ADMINISTRATIVO', 'OFICIOS_VARIOS');
CREATE TYPE TipoCodigoVerificacion AS ENUM ('REGISTRO', 'RECUPERACION_PASSWORD');
CREATE TYPE CategoriaObjeto AS ENUM ('ELECTRONICOS', 'DOCUMENTOS', 'ROPA_Y_ACCESORIOS', 'BOLSOS_Y_MALETAS', 'LLAVES', 'LIBROS_Y_UTILES', 'OTROS');
CREATE TYPE EstadoPublicacion AS ENUM ('PENDIENTE', 'APROBADA', 'RECHAZADA', 'ELIMINACION_PENDIENTE', 'CERRADA');
CREATE TYPE TipoUbicacion AS ENUM ('BLOQUE', 'PORTERIA', 'ZONA_COMUN', 'OTRO');
CREATE TYPE TipoPuntoEntrega AS ENUM ('OFICINA', 'PORTERIA');
CREATE TYPE EstadoCustodia AS ENUM ('EN_CUSTODIA', 'POR_VENCER', 'SIN_DUENO_DEFINITIVO', 'RECLAMADO');
CREATE TYPE EstadoReclamo AS ENUM ('ENVIADO', 'EN_REVISION', 'APROBADO', 'RECHAZADO', 'LISTO_PARA_RECOGER', 'CANCELADO_POR_USUARIO', 'RECLAMADO');
CREATE TYPE AccionAuditoria AS ENUM ('CREAR', 'EDITAR', 'APROBAR', 'RECHAZAR', 'ELIMINAR', 'BLOQUEAR', 'DESBLOQUEAR', 'CAMBIO_ESTADO');

-- SEDES Y UBICACIONES

CREATE TABLE sedes (
    sede_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre VARCHAR(100) NOT NULL,
    codigo VARCHAR(50) NOT NULL,
    activa BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_edicion TIMESTAMP NULL,
    usuario_crea_id UUID NULL,
    usuario_edita_id UUID NULL
);

CREATE TABLE ubicaciones (
    ubicacion_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sede_id UUID NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    tipo TipoUbicacion NOT NULL,
    activa BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_edicion TIMESTAMP NULL,
    usuario_crea_id UUID NULL,
    usuario_edita_id UUID NULL,
    CONSTRAINT fk_ubicacion_sede FOREIGN KEY (sede_id) REFERENCES sedes(sede_id) ON DELETE RESTRICT
);

CREATE TABLE puntos_entrega (
    puntoEntrega_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sede_id UUID NOT NULL,
    nombre VARCHAR(150) NOT NULL,
    tipo TipoPuntoEntrega NOT NULL,
    activa BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_edicion TIMESTAMP NULL,
    usuario_crea_id UUID NULL,
    usuario_edita_id UUID NULL,
    CONSTRAINT fk_puntoentrega_sede FOREIGN KEY (sede_id) REFERENCES sedes(sede_id) ON DELETE RESTRICT
);

-- AUTENTICACIÓN Y USUARIOS

CREATE TABLE usuarios (
    usuario_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre_completo VARCHAR(150) NOT NULL,
    cedula VARCHAR(50) NOT NULL UNIQUE,
    carnet VARCHAR(100) NULL UNIQUE,
    celular VARCHAR(20) NULL,
    correo VARCHAR(150) NOT NULL UNIQUE,
    hashed_password VARCHAR(200) NOT NULL,
    rol RolUsuario NOT NULL,
    tipo_vinculacion TipoVinculacion NOT NULL,
    sede_id UUID NULL,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_blocked BOOLEAN NOT NULL DEFAULT FALSE,
    motivo_bloqueo VARCHAR(500) NULL,
    fecha_registro TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_edicion TIMESTAMP NULL,
    usuario_edita_id UUID NULL,
    CONSTRAINT fk_usuario_sede FOREIGN KEY (sede_id) REFERENCES sedes(sede_id) ON DELETE SET NULL
);

-- FKs dependen de 'usuarios'
ALTER TABLE sedes ADD CONSTRAINT fk_sede_usuario_crea FOREIGN KEY (usuario_crea_id) REFERENCES usuarios(usuario_id) ON DELETE SET NULL;
ALTER TABLE sedes ADD CONSTRAINT fk_sede_usuario_edita FOREIGN KEY (usuario_edita_id) REFERENCES usuarios(usuario_id) ON DELETE SET NULL;
ALTER TABLE ubicaciones ADD CONSTRAINT fk_ubicacion_usuario_crea FOREIGN KEY (usuario_crea_id) REFERENCES usuarios(usuario_id) ON DELETE SET NULL;
ALTER TABLE ubicaciones ADD CONSTRAINT fk_ubicacion_usuario_edita FOREIGN KEY (usuario_edita_id) REFERENCES usuarios(usuario_id) ON DELETE SET NULL;
ALTER TABLE puntos_entrega ADD CONSTRAINT fk_puntoentrega_usuario_crea FOREIGN KEY (usuario_crea_id) REFERENCES usuarios(usuario_id) ON DELETE SET NULL;
ALTER TABLE puntos_entrega ADD CONSTRAINT fk_puntoentrega_usuario_edita FOREIGN KEY (usuario_edita_id) REFERENCES usuarios(usuario_id) ON DELETE SET NULL;
ALTER TABLE usuarios ADD CONSTRAINT fk_usuario_usuario_edita FOREIGN KEY (usuario_edita_id) REFERENCES usuarios(usuario_id) ON DELETE SET NULL;

CREATE TABLE codigos_verificacion (
    codigoVerificacion_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID NOT NULL,
    codigo VARCHAR(50) NOT NULL,
    tipo TipoCodigoVerificacion NOT NULL,
    expira_en TIMESTAMP NOT NULL,
    usado BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_codigo_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(usuario_id) ON DELETE CASCADE
);

-- PUBLICACIONES

CREATE TABLE reportes_perdida (
    reportePerdida_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID NOT NULL,
    categoria CategoriaObjeto NOT NULL,
    descripcion VARCHAR(500) NOT NULL,
    lugar_perdida_id UUID NOT NULL,
    fecha_perdida DATE NOT NULL,
    hora_aproximada TIME NULL,
    imagen_url VARCHAR(500) NULL,
    estado EstadoPublicacion NOT NULL DEFAULT 'PENDIENTE',
    fecha_publicacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    motivo_rechazo VARCHAR(500) NULL,
    eliminacion_solicitada BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_edicion TIMESTAMP NULL,
    usuario_edita_id UUID NULL,
    CONSTRAINT fk_reporte_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(usuario_id) ON DELETE RESTRICT,
    CONSTRAINT fk_reporte_lugar FOREIGN KEY (lugar_perdida_id) REFERENCES ubicaciones(ubicacion_id) ON DELETE RESTRICT,
    CONSTRAINT fk_reporte_usuario_edita FOREIGN KEY (usuario_edita_id) REFERENCES usuarios(usuario_id) ON DELETE SET NULL
);

CREATE TABLE publicaciones_encontradas (
    publicacionEncontrado_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID NOT NULL,
    categoria CategoriaObjeto NOT NULL,
    descripcion VARCHAR(500) NOT NULL,
    lugar_hallazgo_id UUID NOT NULL,
    lugar_entrega_fisica_id UUID NOT NULL,
    fecha_hallazgo DATE NOT NULL,
    imagen_url VARCHAR(500) NULL,
    estado EstadoPublicacion NOT NULL DEFAULT 'PENDIENTE',
    fecha_publicacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    motivo_rechazo VARCHAR(500) NULL,
    eliminacion_solicitada BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_edicion TIMESTAMP NULL,
    usuario_edita_id UUID NULL,
    CONSTRAINT fk_encontrado_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(usuario_id) ON DELETE RESTRICT,
    CONSTRAINT fk_encontrado_lugar FOREIGN KEY (lugar_hallazgo_id) REFERENCES ubicaciones(ubicacion_id) ON DELETE RESTRICT,
    CONSTRAINT fk_encontrado_entrega FOREIGN KEY (lugar_entrega_fisica_id) REFERENCES puntos_entrega(puntoEntrega_id) ON DELETE RESTRICT,
    CONSTRAINT fk_encontrado_usuario_edita FOREIGN KEY (usuario_edita_id) REFERENCES usuarios(usuario_id) ON DELETE SET NULL
);

-- INVENTARIO Y CUSTODIA

CREATE TABLE objetos_en_custodia (
    objetoEnCustodia_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_id UUID NOT NULL,
    publicacionEncontrado_id UUID NULL,
    categoria CategoriaObjeto NOT NULL,
    descripcion VARCHAR(500) NOT NULL,
    lugar_origen_id UUID NOT NULL,
    fecha_ingreso DATE NOT NULL,
    imagen_url VARCHAR(500) NULL,
    detalles_internos VARCHAR(500) NULL,
    estado EstadoCustodia NOT NULL DEFAULT 'EN_CUSTODIA',
    fecha_vencimiento_alerta DATE NULL,
    en_proceso_validacion BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_edicion TIMESTAMP NULL,
    usuario_edita_id UUID NULL,
    CONSTRAINT fk_custodia_admin FOREIGN KEY (admin_id) REFERENCES usuarios(usuario_id) ON DELETE RESTRICT,
    CONSTRAINT fk_custodia_publicacion FOREIGN KEY (publicacionEncontrado_id) REFERENCES publicaciones_encontradas(publicacionEncontrado_id) ON DELETE SET NULL,
    CONSTRAINT fk_custodia_origen FOREIGN KEY (lugar_origen_id) REFERENCES puntos_entrega(puntoEntrega_id) ON DELETE RESTRICT,
    CONSTRAINT fk_custodia_usuario_edita FOREIGN KEY (usuario_edita_id) REFERENCES usuarios(usuario_id) ON DELETE SET NULL
);

CREATE TABLE preguntas_seguridad (
    preguntaSeguridad_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    objetoEnCustodia_id UUID NOT NULL,
    pregunta VARCHAR(250) NOT NULL,
    respuesta_correcta VARCHAR(500) NOT NULL,
    orden INT NOT NULL,
    CONSTRAINT fk_pregunta_objeto FOREIGN KEY (objetoEnCustodia_id) REFERENCES objetos_en_custodia(objetoEnCustodia_id) ON DELETE CASCADE
);

-- RECLAMOS

CREATE TABLE reclamos (
    reclamo_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    objetoEnCustodia_id UUID NOT NULL,
    usuario_id UUID NOT NULL,
    estado EstadoReclamo NOT NULL DEFAULT 'ENVIADO',
    evidencia_url VARCHAR(500) NULL,
    fecha_envio TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_revision TIMESTAMP NULL,
    motivo_rechazo VARCHAR(500) NULL,
    fecha_cita TIMESTAMP NULL,
    horario_cita VARCHAR(150) NULL,
    es_presencial BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_reclamo_objeto FOREIGN KEY (objetoEnCustodia_id) REFERENCES objetos_en_custodia(objetoEnCustodia_id) ON DELETE RESTRICT,
    CONSTRAINT fk_reclamo_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(usuario_id) ON DELETE RESTRICT
);

-- Índice único parcial: un solo reclamo activo por objeto (HU08 - concurrencia)
CREATE UNIQUE INDEX ux_reclamo_objeto_activo
ON reclamos (objetoEnCustodia_id)
WHERE estado IN ('ENVIADO', 'EN_REVISION');

CREATE TABLE respuestas_seguridad (
    respuestaSeguridad_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reclamo_id UUID NOT NULL,
    preguntaSeguridad_id UUID NOT NULL,
    respuesta_usuario VARCHAR(500) NOT NULL,
    CONSTRAINT fk_respuesta_reclamo FOREIGN KEY (reclamo_id) REFERENCES reclamos(reclamo_id) ON DELETE CASCADE,
    CONSTRAINT fk_respuesta_pregunta FOREIGN KEY (preguntaSeguridad_id) REFERENCES preguntas_seguridad(preguntaSeguridad_id) ON DELETE RESTRICT
);

CREATE TABLE posibles_coincidencias (
    posibleCoincidencia_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    objetoEnCustodia_id UUID NOT NULL,
    reportePerdida_id UUID NOT NULL,
    usuario_id UUID NOT NULL,
    score INT NOT NULL,
    notificado BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_deteccion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_coincidencia_objeto FOREIGN KEY (objetoEnCustodia_id) REFERENCES objetos_en_custodia(objetoEnCustodia_id) ON DELETE CASCADE,
    CONSTRAINT fk_coincidencia_reporte FOREIGN KEY (reportePerdida_id) REFERENCES reportes_perdida(reportePerdida_id) ON DELETE CASCADE,
    CONSTRAINT fk_coincidencia_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(usuario_id) ON DELETE RESTRICT
);

-- ENTREGA Y ACTA DIGITAL

CREATE TABLE actas_entrega (
    actaEntrega_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reclamo_id UUID NOT NULL UNIQUE,
    nombre_reclamante VARCHAR(150) NOT NULL,
    cedula_reclamante VARCHAR(50) NOT NULL,
    correo_reclamante VARCHAR(150) NOT NULL,
    celular_reclamante VARCHAR(20) NOT NULL,
    carnet_reclamante VARCHAR(100) NOT NULL,
    firma_url VARCHAR(500) NOT NULL,
    fecha_hora_entrega TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    procesada_por_admin_id UUID NOT NULL,
    validacion_verbal BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_acta_reclamo FOREIGN KEY (reclamo_id) REFERENCES reclamos(reclamo_id) ON DELETE RESTRICT,
    CONSTRAINT fk_acta_admin FOREIGN KEY (procesada_por_admin_id) REFERENCES usuarios(usuario_id) ON DELETE RESTRICT
);

-- AUDITORÍA

CREATE TABLE logs_auditoria (
    auditLog_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entidad VARCHAR(500) NOT NULL,
    entidad_id UUID NOT NULL,
    accion AccionAuditoria NOT NULL,
    usuario_id UUID NOT NULL,
    detalle VARCHAR(500) NULL,
    fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_audit_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(usuario_id) ON DELETE RESTRICT
);
