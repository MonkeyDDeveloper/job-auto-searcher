import smtplib
from email.message import EmailMessage
from email.utils import parseaddr
from html import escape

from .config import Settings
from .schemas import JobOffer
from .tracking import make_application_token, offer_code


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
    lines: list[str] = ["RESULTADOS DE BÚSQUEDA DE EMPLEO", "=" * 32, ""]
    number = 0
    for key in keys:
        offers = results.get(key, [])
        lines.extend([labels[key].upper(), "-" * len(labels[key]), ""])
        for offer in offers:
            number += 1
            code = offer_code(key, offer)
            lines.extend(
                [
                    f"{number}. [{code}] {offer.cargo} | {offer.empresa}",
                    f"   Score: {offer.score}/100",
                    f"   Ubicación: {offer.ubicacion}",
                    f"   Modalidad: {offer.modalidad}",
                    f"   Salario: {offer.rango_salarial}",
                    f"   Contacto: {offer.email_contacto}",
                    f"   URL: {offer.url}",
                    f"   Razón del match: {offer.justificacion}",
                    f"   Empresa: {offer.empresa}",
                    "   Email sugerido (español e inglés):",
                    f"   {offer.email_recomendado}",
                    "",
                ]
            )
    return "\n".join(lines)


def _summary_html(
    settings: Settings,
    results: dict[str, list[JobOffer]],
    keys: tuple[str, ...],
) -> str:
    labels = {
        "javier_automatizacion": "Javier - Automatización e IoT",
        "javier_software": "Javier - Software Remoto",
        "mayra_petroleras": "Mayra - Oportunidades Petroleras",
    }
    sections: list[str] = []
    for key in keys:
        cards: list[str] = []
        for offer in results.get(key, []):
            code = offer_code(key, offer)
            button = ""
            if settings.public_base_url and settings.application_link_secret:
                token = make_application_token(code, settings.application_link_secret)
                button = (
                    f'<p><a href="{escape(settings.public_base_url)}/applications/mark-applied?token='
                    f'{escape(token, quote=True)}" style="display:inline-block;background:#0f5965;color:#fff;'
                    'padding:10px 14px;border-radius:6px;text-decoration:none;font-weight:bold">'
                    "Marcar como postulada</a></p>"
                )
            cards.append(
                """
                <article style="border:1px solid #d9dee5;border-radius:8px;padding:16px;margin:12px 0">
                  <p style="margin:0 0 6px;color:#0f5965;font-weight:bold">Código: {code}</p>
                  <h3 style="margin:0 0 8px;color:#17324d">{cargo} · {empresa}</h3>
                  <p style="margin:4px 0"><strong>Score:</strong> {score}/100</p>
                  <p style="margin:4px 0"><strong>Ubicación:</strong> {ubicacion}<br>
                  <strong>Modalidad:</strong> {modalidad}<br>
                  <strong>Salario:</strong> {salario}<br>
                  <strong>Contacto:</strong> {contacto}</p>
                  <p style="margin:10px 0"><strong>Razón del match:</strong><br>{justificacion}</p>
                  <p style="margin:10px 0"><strong>Empresa:</strong> {empresa}</p>
                  <p style="margin:10px 0"><strong>Email sugerido (español e inglés):</strong></p>
                  <pre style="white-space:pre-wrap;background:#f5f7fa;border-radius:6px;padding:12px;font-family:Arial,sans-serif">{email_recomendado}</pre>
                  {button}
                  <p style="margin:4px 0"><a href="{url}">Ver oportunidad</a></p>
                </article>
                """.format(
                    cargo=escape(offer.cargo),
                    empresa=escape(offer.empresa),
                    code=escape(code),
                    score=offer.score,
                    ubicacion=escape(offer.ubicacion),
                    modalidad=escape(offer.modalidad),
                    salario=escape(offer.rango_salarial),
                    contacto=escape(offer.email_contacto),
                    justificacion=escape(offer.justificacion),
                    email_recomendado=escape(offer.email_recomendado),
                    button=button,
                    url=escape(offer.url, quote=True),
                )
            )
        sections.append(
            f"<h2 style=\"color:#0f5965;border-bottom:2px solid #0f5965;padding-bottom:6px\">"
            f"{escape(labels[key])}</h2>{''.join(cards) or '<p>No se encontraron oportunidades.</p>'}"
        )
    all_applications = (
        f'<p><a href="{escape(settings.google_sheet_url, quote=True)}" style="display:inline-block;'
        'background:#263238;color:#fff;padding:10px 14px;border-radius:6px;text-decoration:none;'
        'font-weight:bold">Ver todas las postulaciones</a></p>'
    )
    return (
        "<html><body style=\"font-family:Arial,sans-serif;line-height:1.45;color:#263238;max-width:760px\">"
        "<h1>Resultados de búsqueda de empleo</h1>"
        f"{all_applications}{''.join(sections)}"
        "</body></html>"
    )


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
    message.add_alternative(
        _summary_html(
            settings,
            results,
            ("javier_automatizacion", "javier_software", "mayra_petroleras"),
        ),
        subtype="html",
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
            code = offer_code(key, offer)
            message = EmailMessage()
            message["Subject"] = (
                f"[{code}] {offer.empresa} - Presentación profesional - {offer.cargo}"
            )
            message["From"] = settings.smtp_from or ""
            message["To"] = address
            message.set_content(
                f"Código de seguimiento: {code}\n"
                f"Empresa: {offer.empresa}\n\n"
                f"{offer.email_recomendado}"
            )
            messages.append(message)

    if messages:
        _send_messages(settings, messages)
    return len(messages)
