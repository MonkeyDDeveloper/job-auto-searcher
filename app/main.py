import secrets

from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import load_settings
from .notify import NotificationError, notify_contacts, notify_error, notify_recipients
from .schemas import SearchRequest
from .perplexity import PerplexityError, search_jobs


app = FastAPI(
    title="Employ Auto Search",
    description="Busca, evalúa y notifica oportunidades de empleo.",
    version="1.0.0",
)
bearer_scheme = HTTPBearer(auto_error=False)


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
    settings = load_settings()
    requested_model = request.model or settings.default_model
    models_to_try = [requested_model]
    if settings.fallback_model != requested_model:
        models_to_try.append(settings.fallback_model)

    results = None
    model = requested_model
    last_error: PerplexityError | None = None
    for candidate_model in models_to_try:
        try:
            results = search_jobs(
                request.prompt,
                candidate_model,
                settings.perplexity_api_key,
                timeout_seconds=settings.perplexity_timeout_seconds,
                retries=settings.perplexity_retries,
            )
            model = candidate_model
            break
        except PerplexityError as error:
            last_error = error

    if results is None:
        alert_warnings: list[str] = []
        _alert_error(settings, last_error, alert_warnings)
        raise HTTPException(status_code=502, detail=str(last_error)) from last_error

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
        except NotificationError as error:
            warnings.append(str(error))
            _alert_error(settings, error, warnings)
        except OSError as error:
            warnings.append(f"No se pudo enviar el email: {error}")
            _alert_error(settings, error, warnings)
        except Exception as error:
            warnings.append(f"Error inesperado enviando notificaciones: {error}")
            _alert_error(settings, error, warnings)

    return {
        "model": model,
        "results": {
            key: [offer.model_dump(by_alias=True) for offer in offers]
            for key, offers in results.items()
        },
        "notifiedRecipients": notified_count,
        "contactEmailsSent": contact_emails_sent,
        "warnings": warnings,
    }
