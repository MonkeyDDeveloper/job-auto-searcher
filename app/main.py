import secrets
import logging
import time
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Query, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.responses import HTMLResponse
from html import escape

from .config import load_settings
from .notify import NotificationError, notify_contacts, notify_error, notify_recipients
from .schemas import SearchRequest
from .perplexity import PerplexityError, search_jobs
from .sheets import SheetsError, append_results, filter_new_results, list_rows, mark_applied
from .tracking import read_application_token


app = FastAPI(
    title="Employ Auto Search",
    description="Busca, evalúa y notifica oportunidades de empleo.",
    version="1.0.0",
)
bearer_scheme = HTTPBearer(auto_error=False)
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


def require_api_key(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> None:
    configured_key = load_settings().searcher_apikey
    if not configured_key:
        raise HTTPException(
            status_code=500,
            detail="SEARCHER_APIKEY no está configurada en el servidor.",
        )
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Se requiere Authorization: Bearer <SEARCHER_APIKEY>.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not secrets.compare_digest(credentials.credentials, configured_key):
        raise HTTPException(
            status_code=401,
            detail="SEARCHER_APIKEY inválida.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def _alert_error(settings, error: Exception, warnings: list[str]) -> None:
    try:
        recipients = notify_error(settings, str(error))
        warnings.append(f"Alerta de error enviada a {recipients} destinatario(s).")
    except Exception as alert_error:
        warnings.append(f"No se pudo enviar la alerta de error: {alert_error}")


@app.post("/search")
def search(
    request: SearchRequest,
    _: None = Depends(require_api_key),
) -> dict:
    request_id = uuid4().hex[:12]
    started_at = time.monotonic()
    settings = load_settings()
    logger.info(
        "search_started request_id=%s model=%s should_notify=%s",
        request_id,
        request.model or settings.default_model,
        request.shouldNotify,
    )
    try:
        existing_rows = list_rows(settings)
        logger.info("sheets_history_loaded request_id=%s rows=%s", request_id, len(existing_rows))
    except SheetsError as error:
        logger.exception("sheets_history_failed request_id=%s", request_id)
        warnings: list[str] = []
        _alert_error(settings, error, warnings)
        raise HTTPException(status_code=503, detail=str(error)) from error

    requested_model = request.model or settings.default_model
    models_to_try = [requested_model]
    if settings.fallback_model != requested_model:
        models_to_try.append(settings.fallback_model)

    results = None
    model = requested_model
    last_error: PerplexityError | None = None
    for candidate_model in models_to_try:
        logger.info("model_attempt_started request_id=%s model=%s", request_id, candidate_model)
        try:
            results = search_jobs(
                request.prompt,
                candidate_model,
                settings.perplexity_api_key,
                timeout_seconds=settings.perplexity_timeout_seconds,
                retries=settings.perplexity_retries,
                max_steps=settings.perplexity_max_steps,
                max_output_tokens=settings.perplexity_max_output_tokens,
            )
            model = candidate_model
            break
        except PerplexityError as error:
            logger.warning(
                "model_attempt_failed request_id=%s model=%s error=%s",
                request_id,
                candidate_model,
                error,
            )
            last_error = error

    if results is None:
        logger.error("search_failed request_id=%s", request_id)
        alert_warnings: list[str] = []
        _alert_error(settings, last_error, alert_warnings)
        raise HTTPException(status_code=502, detail=str(last_error)) from last_error

    results = filter_new_results(results, existing_rows)
    logger.info(
        "duplicate_filter_completed request_id=%s result_counts=%s",
        request_id,
        {key: len(offers) for key, offers in results.items()},
    )
    try:
        registered_count = append_results(settings, results)
        logger.info("sheets_new_rows_registered request_id=%s count=%s", request_id, registered_count)
    except SheetsError as error:
        logger.exception("sheets_append_failed request_id=%s", request_id)
        warnings: list[str] = []
        _alert_error(settings, error, warnings)
        raise HTTPException(status_code=503, detail=str(error)) from error

    warnings: list[str] = []
    if model != requested_model:
        warnings.append(
            f"El modelo {requested_model} falló; se utilizó el respaldo gratuito {model}."
        )
    notified_count = 0
    contact_emails_sent = 0
    if request.shouldNotify:
        try:
            notified_count = notify_recipients(settings, results)
            contact_emails_sent = notify_contacts(settings, results)
            logger.info(
                "notifications_completed request_id=%s recipients=%s contacts=%s",
                request_id,
                notified_count,
                contact_emails_sent,
            )
        except NotificationError as error:
            logger.exception("notification_failed request_id=%s", request_id)
            warnings.append(str(error))
            _alert_error(settings, error, warnings)
        except OSError as error:
            logger.exception("notification_os_error request_id=%s", request_id)
            warnings.append(f"No se pudo enviar el email: {error}")
            _alert_error(settings, error, warnings)
        except Exception as error:
            logger.exception("notification_unexpected_error request_id=%s", request_id)
            warnings.append(f"Error inesperado enviando notificaciones: {error}")
            _alert_error(settings, error, warnings)

    logger.info(
        "search_completed request_id=%s model=%s duration_seconds=%.2f",
        request_id,
        model,
        time.monotonic() - started_at,
    )
    return {
        "model": model,
        "results": {
            key: [offer.model_dump(by_alias=True) for offer in offers]
            for key, offers in results.items()
        },
        "registeredCount": registered_count,
        "notifiedRecipients": notified_count,
        "contactEmailsSent": contact_emails_sent,
        "warnings": warnings,
    }


@app.get("/applications/mark-applied", response_class=HTMLResponse)
def mark_application_applied(token: str = Query(...)) -> HTMLResponse:
    settings = load_settings()
    application_id = read_application_token(token, settings.application_link_secret)
    if not application_id:
        logger.warning("application_mark_failed reason=invalid_or_expired_token")
        return HTMLResponse(
            "<h1>Enlace inválido o expirado</h1><p>No se pudo actualizar la postulación.</p>",
            status_code=400,
        )
    try:
        message = mark_applied(settings, application_id)
    except SheetsError as error:
        logger.exception("application_mark_failed id=%s", application_id)
        return HTMLResponse(
            f"<h1>Error al actualizar</h1><p>{escape(str(error))}</p>",
            status_code=502,
        )
    logger.info("application_marked_applied id=%s", application_id)
    return HTMLResponse(
        f"<h1>Postulación actualizada</h1><p>{escape(message)}</p>"
        f"<p>Código: <strong>{escape(application_id)}</strong></p>"
    )
