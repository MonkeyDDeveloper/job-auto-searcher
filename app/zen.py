import json
import socket
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .schemas import JobOffer


API_URL = "https://opencode.ai/zen/v1/chat/completions"


class OpenCodeError(RuntimeError):
    pass


def _parse_json(content: str) -> object:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as error:
        raise OpenCodeError("OpenCode no devolvió JSON válido.") from error


def search_jobs(
    prompt: str,
    model: str,
    api_key: str,
    timeout_seconds: int = 300,
    retries: int = 2,
) -> dict[str, list[JobOffer]]:
    if not api_key:
        raise OpenCodeError("Falta OPENCODE_API_KEY.")
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
    }
    request = Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "employ-auto-search/1.0",
        },
        method="POST",
    )
    last_error: Exception | None = None
    for attempt in range(max(0, retries) + 1):
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                body = json.load(response)
            break
        except HTTPError as error:
            details = error.read().decode("utf-8", errors="replace")
            last_error = error
            retryable = error.code == 429 or error.code >= 500
            if not retryable or attempt >= retries:
                raise OpenCodeError(
                    f"OpenCode devolvió HTTP {error.code}: {details}"
                ) from error
        except (TimeoutError, socket.timeout, URLError) as error:
            last_error = error
            if attempt >= retries:
                reason = getattr(error, "reason", error)
                raise OpenCodeError(
                    f"OpenCode agotó el tiempo de espera o no está disponible: {reason}"
                ) from error
        time.sleep(min(2**attempt, 8))
    else:
        raise OpenCodeError(f"OpenCode no respondió: {last_error}")

    try:
        content = body["choices"][0]["message"]["content"]
        parsed = _parse_json(content)
        if not isinstance(parsed, dict):
            raise TypeError("La respuesta no es un objeto con tres listas")
        result: dict[str, list[JobOffer]] = {}
        for key in ("javier_automatizacion", "javier_software", "mayra_petroleras"):
            raw_offers = parsed.get(key, [])
            if not isinstance(raw_offers, list):
                raise TypeError(f"{key} no es una lista")
            result[key] = [JobOffer.model_validate(offer) for offer in raw_offers]
        return result
    except (KeyError, IndexError, TypeError, ValueError) as error:
        raise OpenCodeError(f"Respuesta inesperada de OpenCode: {body}") from error
