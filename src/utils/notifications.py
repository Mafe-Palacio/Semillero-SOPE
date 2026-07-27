"""
Notification Dispatcher — servicio interno que centraliza el envío de
todos los correos transaccionales del sistema (Nivel 3 C4: componente
Notification Dispatcher).

Usa SMTP directo (smtplib + STARTTLS), configurado vía variables de
entorno (SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM) — mismos
valores que ya usa el proyecto Blazor del profesor (Gmail SMTP, puerto 587).

IMPORTANTE: los métodos de esta clase hacen una llamada de red bloqueante
(smtplib es síncrono). Para no bloquear el event loop de FastAPI, se deben
invocar desde los endpoints usando BackgroundTasks, no con `await` directo:

    from fastapi import BackgroundTasks
    ...
    background_tasks.add_task(
        dispatcher.enviar_otp_registro, correo=correo, codigo=codigo
    )

Si el envío falla (credenciales inválidas, sin conexión, etc.), el error
se registra pero NO se relanza — un correo que no salió no debe tumbar
el flujo de negocio que lo originó (ej. el registro del usuario ya se
guardó en base de datos aunque el correo falle).
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.core.config import Settings, get_settings

logger = logging.getLogger("notification_dispatcher")


class NotificationDispatcher:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def _enviar_correo(self, destinatario: str, asunto: str, cuerpo_html: str) -> bool:
        """Envío de bajo nivel. Retorna True/False en vez de propagar la
        excepción, para que un fallo de correo no interrumpa el flujo
        de negocio que lo disparó."""
        if not self.settings.smtp_user or not self.settings.smtp_pass:
            logger.warning(
                "SMTP no configurado (SMTP_USER/SMTP_PASS vacíos); "
                "correo NO enviado a %s: [%s]",
                destinatario,
                asunto,
            )
            return False

        mensaje = MIMEMultipart("alternative")
        mensaje["Subject"] = asunto
        mensaje["From"] = self.settings.smtp_from or self.settings.smtp_user
        mensaje["To"] = destinatario
        mensaje.attach(MIMEText(cuerpo_html, "html", "utf-8"))

        try:
            with smtplib.SMTP(
                self.settings.smtp_host, self.settings.smtp_port
            ) as server:
                server.starttls()
                server.login(self.settings.smtp_user, self.settings.smtp_pass)
                server.sendmail(
                    self.settings.smtp_from or self.settings.smtp_user,
                    destinatario,
                    mensaje.as_string(),
                )
            return True

        except Exception:
            logger.exception("Error al enviar correo a %s: [%s]", destinatario, asunto)
            return False

    # ------------------------------------------------------------------
    # Autenticación (HU28, HU29)
    # ------------------------------------------------------------------

    def enviar_otp_registro(self, correo: str, codigo: str) -> bool:
        cuerpo = f"""
        <p>¡Bienvenido/a al Sistema de Objetos Perdidos y Encontrados del ITM!</p>
        <p>Tu código de verificación es:</p>
        <h2>{codigo}</h2>
        <p>Este código vence en 15 minutos. Si no solicitaste este registro, ignora este mensaje.</p>
        """
        return self._enviar_correo(
            correo, "Verifica tu cuenta — Sistema OPE ITM", cuerpo
        )

    def enviar_recuperacion_password(self, correo: str, codigo: str) -> bool:
        cuerpo = f"""
        <p>Recibimos una solicitud para restablecer tu contraseña.</p>
        <p>Tu código de recuperación es:</p>
        <h2>{codigo}</h2>
        <p>Este código vence en 15 minutos. Si no solicitaste esto, ignora este mensaje.</p>
        """
        return self._enviar_correo(
            correo, "Recuperación de contraseña — Sistema OPE ITM", cuerpo
        )

    # ------------------------------------------------------------------
    # Reclamos y Smart Match (HU16, HU24, HU25, HU27)
    # ------------------------------------------------------------------

    def enviar_alerta_match(self, correo: str, descripcion_objeto: str) -> bool:
        cuerpo = f"""
        <p>Encontramos un objeto en custodia que podría coincidir con algo que reportaste como perdido:</p>
        <p><strong>{descripcion_objeto}</strong></p>
        <p>Ingresa a la plataforma para responder las preguntas de seguridad y confirmar si es tuyo.</p>
        """
        return self._enviar_correo(
            correo,
            "Posible coincidencia con tu objeto perdido — Sistema OPE ITM",
            cuerpo,
        )

    def enviar_cita_presencial(
        self, correo: str, fecha_hora: str, sede_nombre: str, punto_entrega_nombre: str
    ) -> bool:
        cuerpo = f"""
        <p>Tu reclamo fue aprobado. Puedes acercarte a recoger tu objeto:</p>
        <ul>
            <li><strong>Fecha y hora:</strong> {fecha_hora}</li>
            <li><strong>Sede:</strong> {sede_nombre}</li>
            <li><strong>Lugar:</strong> {punto_entrega_nombre}</li>
        </ul>
        <p>Recuerda llevar tu documento de identidad y el carné institucional.</p>
        """
        return self._enviar_correo(
            correo, "Tu objeto está listo para recoger — Sistema OPE ITM", cuerpo
        )

        def enviar_correo_acta_entrega(self, correo: str, firma_url: str) -> bool:
            cuerpo = f"""
            <p>Se registró el acta de entrega de tu objeto.</p>
            <  >Puedes consultar la firma/soporte aquí:</p>
            <p><a href="{firma_url}">{firma_url}</a></p>
            <p>Gracias por usar el Sistema de Objetos Perdidos y Encontrados del ITM.</p>"""

        return self._enviar_correo(
            correo, "Acta de entrega registrada — Sistema OPE ITM", cuerpo
        )

    def enviar_cierre_exitoso_reclamante(
        self, correo: str, descripcion_objeto: str
    ) -> bool:
        cuerpo = f"""
        <p>¡Felicitaciones! Tu objeto <strong>{descripcion_objeto}</strong> fue recuperado exitosamente.</p>
        <p>Esperamos haberte sido de ayuda.</p>
        """
        return self._enviar_correo(
            correo, "Objeto recuperado con éxito — Sistema OPE ITM", cuerpo
        )

    def enviar_cierre_exitoso_encontrador(
        self, correo: str, descripcion_objeto: str
    ) -> bool:
        cuerpo = f"""
        <p>El objeto que reportaste como encontrado (<strong>{descripcion_objeto}</strong>)
        fue devuelto exitosamente a su dueño. ¡Gracias por tu aporte a la comunidad ITM!</p>
        """
        return self._enviar_correo(
            correo, "Tu aporte ayudó a alguien — Sistema OPE ITM", cuerpo
        )

    def enviar_cambio_estado_reclamo(
        self, correo: str, nuevo_estado: str, motivo: str | None = None
    ) -> bool:
        detalle = f"<p>Motivo: {motivo}</p>" if motivo else ""
        cuerpo = f"""
        <p>El estado de tu reclamo cambió a: <strong>{nuevo_estado}</strong>.</p>
        {detalle}
        <p>Consulta el detalle completo en la sección "Mis reclamos" de la plataforma.</p>
        """
        return self._enviar_correo(
            correo, "Actualización de tu reclamo — Sistema OPE ITM", cuerpo
        )

    # ------------------------------------------------------------------
    # Administración (HU06)
    # ------------------------------------------------------------------

    def enviar_notificacion_bloqueo(self, correo: str, motivo: str) -> bool:
        cuerpo = f"""
        <p>Tu cuenta en el Sistema de Objetos Perdidos y Encontrados del ITM fue bloqueada.</p>
        <p><strong>Motivo:</strong> {motivo}</p>
        <p>Si consideras que esto es un error, contacta a la oficina de objetos perdidos.</p>
        """
        return self._enviar_correo(
            correo, "Tu cuenta fue bloqueada — Sistema OPE ITM", cuerpo
        )
