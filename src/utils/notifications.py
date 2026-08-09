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
import re
import smtplib
from email.message import EmailMessage
from email.utils import formataddr

from src.core.config import Settings, get_settings

logger = logging.getLogger("notification_dispatcher")


class NotificationDispatcher:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    @staticmethod
    def _html_a_texto_plano(html: str) -> str:
        """Fallback simple de texto plano a partir del HTML (quita tags)."""
        texto = re.sub(r"<br\s*/?>", "\n", html)
        texto = re.sub(r"</(p|h1|h2|h3|div|li)>", "\n\n", texto)
        texto = re.sub(r"<[^>]+>", "", texto)
        return re.sub(r"\n{3,}", "\n\n", texto).strip()

    def _enviar_correo(
        self,
        destinatario: str,
        asunto: str,
        cuerpo_html: str,
        nombre_destinatario: str | None = None,
    ) -> bool:
        """Envío de bajo nivel usando EmailMessage (API moderna de Python),
        que codifica automáticamente encabezados y cuerpo en UTF-8 según
        RFC 2047/6532 — evita el bug de nombres/asuntos con tildes rotos
        que además hace que el filtro antispam marque el correo como
        sospechoso por encabezados mal formados.

        Retorna True/False en vez de propagar la excepción: un correo que
        no salió no debe tumbar el flujo de negocio que lo originó.
        """
        if not self.settings.smtp_user or not self.settings.smtp_pass:
            logger.warning(
                "SMTP no configurado (SMTP_USER/SMTP_PASS vacíos); "
                "correo NO enviado a %s: [%s]",
                destinatario,
                asunto,
            )
            return False

        mensaje = EmailMessage()
        mensaje["Subject"] = asunto  # EmailMessage codifica solo si hace falta
        mensaje["From"] = formataddr(
            ("Sistema OPE - ITM", self.settings.smtp_from or self.settings.smtp_user)
        )
        mensaje["To"] = (
            formataddr((nombre_destinatario, destinatario))
            if nombre_destinatario
            else destinatario
        )

        # multipart/alternative: SIEMPRE incluir texto plano junto al HTML.
        # Un correo solo-HTML es una señal clásica de spam para Gmail/Outlook.
        mensaje.set_content(self._html_a_texto_plano(cuerpo_html))
        mensaje.add_alternative(cuerpo_html, subtype="html")

        try:
            with smtplib.SMTP(
                self.settings.smtp_host, self.settings.smtp_port
            ) as server:
                server.starttls()
                server.login(self.settings.smtp_user, self.settings.smtp_pass)
                server.send_message(mensaje)
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
        <p>Puedes consultar la firma/soporte aquí:</p>
        <p><a href="{firma_url}">{firma_url}</a></p>
        <p>Gracias por usar el Sistema de Objetos Perdidos y Encontrados del ITM.</p>
        """
        return self._enviar_correo(
            correo, "Acta de entrega registrada — Sistema OPE ITM", cuerpo
        )

    def enviar_alerta_objetos_por_vencer(
        self, correo: str, descripciones_objetos: list[str]
    ) -> bool:
        """HU09: avisa a la administradora de una sede que uno o varios
        objetos llevan ~5 meses en custodia y están a punto de vencer."""
        items = "".join(f"<li>{d}</li>" for d in descripciones_objetos)
        cuerpo = f"""
        <p>Los siguientes objetos en custodia de tu sede llevan cerca de 5 meses
        sin ser reclamados y fueron marcados como <strong>POR_VENCER</strong>:</p>
        <ul>{items}</ul>
        <p>Si nadie los reclama, en aproximadamente un mes más quedarán como
        candidatos a archivo definitivo.</p>
        """
        return self._enviar_correo(
            correo, "Objetos próximos a vencer en tu sede — Sistema OPE ITM", cuerpo
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
