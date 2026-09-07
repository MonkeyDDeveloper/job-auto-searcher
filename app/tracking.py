import base64
import hashlib
import hmac
import json
import time

from .schemas import JobOffer


def offer_code(key: str, offer: JobOffer) -> str:
    fingerprint = "|".join(
        [key, offer.cargo, offer.empresa, offer.url, offer.email_contacto]
    )
    return f"JOB-{hashlib.sha256(fingerprint.encode('utf-8')).hexdigest()[:10].upper()}"


def make_application_token(application_id: str, secret: str, ttl_seconds: int = 90 * 86400) -> str:
    payload = {"id": application_id, "exp": int(time.time()) + ttl_seconds}
    encoded = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    ).decode("ascii").rstrip("=")
    signature = hmac.new(secret.encode("utf-8"), encoded.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{encoded}.{signature}"


def read_application_token(token: str, secret: str) -> str | None:
    try:
        encoded, signature = token.split(".", 1)
        expected = hmac.new(
            secret.encode("utf-8"), encoded.encode("ascii"), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return None
        padded = encoded + "=" * (-len(encoded) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))
        if int(payload["exp"]) < int(time.time()):
            return None
        return str(payload["id"])
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return None
