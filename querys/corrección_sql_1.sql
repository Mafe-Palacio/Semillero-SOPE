-- Renombrar PK y FK a formato camelCase estricto

-- Tabla puntos_entrega
ALTER TABLE puntos_entrega RENAME COLUMN puntoentrega_id TO "puntoEntrega_id";

-- Tabla codigos_verificacion
ALTER TABLE codigos_verificacion RENAME COLUMN codigoverificacion_id TO "codigoVerificacion_id";

-- Tabla reportes_perdida
ALTER TABLE reportes_perdida RENAME COLUMN reporteperdida_id TO "reportePerdida_id";

-- Tabla publicaciones_encontradas
ALTER TABLE publicaciones_encontradas RENAME COLUMN publicacionencontrado_id TO "publicacionEncontrado_id";

-- Tabla objetos_en_custodia
ALTER TABLE objetos_en_custodia RENAME COLUMN objetoencustodia_id TO "objetoEnCustodia_id";
ALTER TABLE objetos_en_custodia RENAME COLUMN publicacionencontrado_id TO "publicacionEncontrado_id";

-- Tabla preguntas_seguridad
ALTER TABLE preguntas_seguridad RENAME COLUMN preguntaseguridad_id TO "preguntaSeguridad_id";
ALTER TABLE preguntas_seguridad RENAME COLUMN objetoencustodia_id TO "objetoEnCustodia_id";

-- Tabla reclamos
ALTER TABLE reclamos RENAME COLUMN objetoencustodia_id TO "objetoEnCustodia_id";

-- Tabla respuestas_seguridad
ALTER TABLE respuestas_seguridad RENAME COLUMN respuestaseguridad_id TO "respuestaSeguridad_id";
ALTER TABLE respuestas_seguridad RENAME COLUMN preguntaseguridad_id TO "preguntaSeguridad_id";

-- Tabla posibles_coincidencias
ALTER TABLE posibles_coincidencias RENAME COLUMN posiblecoincidencia_id TO "posibleCoincidencia_id";
ALTER TABLE posibles_coincidencias RENAME COLUMN objetoencustodia_id TO "objetoEnCustodia_id";
ALTER TABLE posibles_coincidencias RENAME COLUMN reporteperdida_id TO "reportePerdida_id";

-- Tabla actas_entrega
ALTER TABLE actas_entrega RENAME COLUMN actaentrega_id TO "actaEntrega_id";

-- Tabla logs_auditoria
ALTER TABLE logs_auditoria RENAME COLUMN auditlog_id TO "auditLog_id";