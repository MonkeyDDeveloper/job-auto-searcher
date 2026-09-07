import smtplib
from email.message import EmailMessage
from email.utils import parseaddr

from .config import Settings
from .schemas import JobOffer


class NotificationError(RuntimeError):
    pass


def _validate_smtp(settings: Settings) -> None:
    if not settings.smtp_host or not settings.smtp_from:
        raise NotificationError("Faltan SMTP_HOST o SMTP_FROM.")
    if not settings.smtp_user or not settings.smtp_password:
        raise NotificationError("Faltan SMTP_USER o SMTP_PASSWORD.")


def _send_messages(settings: Settings, messages: list[EmailMessage]) -> None:
    _validate_smtp(settings)
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as smtp:
        smtp.starttls()
        smtp.login(settings.smtp_user, settings.smtp_password)
        for message in messages:
            smtp.send_message(message)


def _summary(results: dict[str, list[JobOffer]], keys: tuple[str, ...]) -> str:
    labels = {
        "javier_automatizacion": "Javier - Automatización e IoT",
        "javier_software": "Javier - Software Remoto",
        "mayra_petroleras": "Mayra - Oportunidades Petroleras",
    }
    lines: list[str] = []
    for key in keys:
        offers = results.get(key, [])
        lines.extend([f"{labels[key]}: {len(offers)} oportunidades", ""])
        for offer in offers:
            lines.extend(
                [
                    f"{offer.score}/100 - {offer.cargo} en {offer.empresa}",
                    f"Contacto: {offer.email_contacto}",
                    offer.url,
                    "",
                ]
            )
    return "\n".join(lines)


def notify_recipients(
    settings: Settings, results: dict[str, list[JobOffer]]
) -> int:
    recipients = list(
        dict.fromkeys([*settings.email_recipients, settings.mayra_email])
    )
    recipients = [recipient for recipient in recipients if recipient]
    if not recipients:
        raise NotificationError("No hay destinatarios de notificación configurados.")

    message = EmailMessage()
    message["Subject"] = "Búsqueda de empleo: resultados para Javier y Mayra"
    message["From"] = settings.smtp_from or ""
    message["To"] = ", ".join(recipients)
    message.set_content(
        _summary(
            results,
            ("javier_automatizacion", "javier_software", "mayra_petroleras"),
        )
    )
    _send_messages(settings, [message])
    return len(recipients)


def notify_error(settings: Settings, error_message: str) -> int:
    recipients = list(
        dict.fromkeys([*settings.email_recipients, settings.mayra_email])
    )
    recipients = [recipient for recipient in recipients if recipient]
    if not recipients:
        raise NotificationError("No hay destinatarios para la alerta de error.")

    message = EmailMessage()
    message["Subject"] = "Error en Employ Auto Search"
    message["From"] = settings.smtp_from or ""
    message["To"] = ", ".join(recipients)
    message.set_content(
        "La búsqueda de empleo no pudo completarse correctamente.\n\n"
        f"Detalle del error:\n{error_message}\n"
    )
    _send_messages(settings, [message])
    return len(recipients)


def notify_contacts(
    settings: Settings, results: dict[str, list[JobOffer]]
) -> int:
    messages: list[EmailMessage] = []
    for key in ("javier_automatizacion", "javier_software"):
        for offer in results.get(key, []):
            address = parseaddr(offer.email_contacto)[1]
            if not address or offer.email_recomendado.strip().lower() == "no aplica":
                continue
            message = EmailMessage()
            message["Subject"] = f"Presentación profesional - {offer.cargo}"
            message["From"] = settings.smtp_from or ""
            message["To"] = address
            message.set_content(offer.email_recomendado)
            messages.append(message)

    if messages:
        _send_messages(settings, messages)
    return len(messages)
