import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config import Settings
from .schemas import JobOffer
from .tracking import offer_code


class SheetsError(RuntimeError):
    pass


def _call(settings: Settings, payload: dict) -> dict:
    if not settings.google_apps_script_url or not settings.google_apps_script_token:
        raise SheetsError("Faltan GOOGLE_APPS_SCRIPT_URL o GOOGLE_APPS_SCRIPT_TOKEN.")
    request = Request(
        settings.google_apps_script_url,
        data=json.dumps({**payload, "token": settings.google_apps_script_token}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=30) as response:
            result = json.load(response)
    except (HTTPError, URLError, TimeoutError) as error:
        raise SheetsError(f"Google Sheets no respondió: {error}") from error
    if not result.get("ok"):
        raise SheetsError(result.get("error", "Google Sheets devolvió un error."))
    return result


def list_rows(settings: Settings) -> list[dict]:
    return _call(settings, {"action": "list"}).get("rows", [])


def filter_new_results(
    results: dict[str, list[JobOffer]], rows: list[dict]
) -> dict[str, list[JobOffer]]:
    known_ids = {str(row.get("id", "")) for row in rows}
    known_uris = {str(row.get("uri", "")).rstrip("/") for row in rows}
    filtered: dict[str, list[JobOffer]] = {}
    for key, offers in results.items():
        fresh: list[JobOffer] = []
        for offer in offers:
            application_id = offer_code(key, offer)
            uri = offer.url.rstrip("/")
            if application_id in known_ids or uri in known_uris:
                continue
            fresh.append(offer)
        filtered[key] = fresh
    return filtered


def append_results(settings: Settings, results: dict[str, list[JobOffer]]) -> int:
    rows: list[dict] = []
    for key, offers in results.items():
        for offer in offers:
            rows.append(
                {
                    "id": offer_code(key, offer),
                    "uri": offer.url,
                    "candidato": key,
                    "cargo": offer.cargo,
                    "empresa": offer.empresa,
                    "ubicacion": offer.ubicacion,
                    "modalidad": offer.modalidad,
                    "score": offer.score,
                    "rango_salarial": offer.rango_salarial,
                    "email_contacto": offer.email_contacto,
                    "email_recomendado": offer.email_recomendado,
                    "justificacion": offer.justificacion,
                    "postulada": "no",
                }
            )
    if rows:
        _call(settings, {"action": "append", "rows": rows})
    return len(rows)


def mark_applied(settings: Settings, application_id: str) -> str:
    return _call(settings, {"action": "mark_applied", "id": application_id}).get(
        "message", "Postulación actualizada."
    )
