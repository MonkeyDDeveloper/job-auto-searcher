import httpx
import logging
from perplexity import Perplexity
from urllib.parse import urlparse

from .schemas import JobOffer, SearchResults


class PerplexityError(RuntimeError):
    pass


logger = logging.getLogger(__name__)


def _is_specific_job_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    path = parsed.path.lower().rstrip("/")
    if not path or path in {"/jobs", "/careers", "/search"}:
        return False
    blocked_fragments = (
        "remote-jobs-in",
        "/search/",
        "/search?",
        "/category/",
        "/categories/",
        "/job-search",
    )
    if any(fragment in f"{path}?{parsed.query}" for fragment in blocked_fragments):
        return False
    if "linkedin.com" in parsed.netloc.lower() and "/jobs/view/" not in path:
        return False
    return True


def _response_schema() -> dict:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "employment_search_results",
            "schema": SearchResults.model_json_schema(),
            "strict": True,
        },
    }


def search_jobs(
    prompt: str,
    model: str,
    api_key: str,
    timeout_seconds: int = 300,
    retries: int = 2,
    max_steps: int = 10,
    max_output_tokens: int = 16000,
) -> dict[str, list[JobOffer]]:
    if not api_key:
        raise PerplexityError("Falta PERPLEXITY_API_KEY.")

    timeout = httpx.Timeout(
        connect=10.0,
        read=float(timeout_seconds),
        write=30.0,
        pool=30.0,
    )
    logger.info(
        "perplexity_search_started model=%s timeout_seconds=%s retries=%s max_steps=%s",
        model,
        timeout_seconds,
        retries,
        max_steps,
    )
    client = Perplexity(api_key=api_key, max_retries=max(0, retries), timeout=timeout)
    try:
        response = client.responses.create(
            model=model,
            input=prompt,
            instructions=(
                "Search the web extensively before answering. Use web_search and "
                "fetch_url for current job listings. Open every candidate URL and "
                "verify it is a live, specific job detail/application page. Reject "
                "search pages, category pages, generic portal pages, closed or "
                "expired jobs, 404/410 pages, and login-only pages. Never invent a "
                "job, URL, email, company, or date. Return only the requested JSON."
            ),
            tools=[
                {"type": "web_search", "search_context_size": "high", "max_results": 20},
                {"type": "fetch_url", "max_urls": 10},
            ],
            response_format=_response_schema(),
            max_output_tokens=max_output_tokens,
            max_steps=max_steps,
        )
    except Exception as error:
        logger.exception("perplexity_search_failed model=%s", model)
        raise PerplexityError(f"Perplexity no pudo completar la búsqueda: {error}") from error
    finally:
        client.close()

    if response.status != "completed":
        logger.error("perplexity_search_incomplete status=%s model=%s", response.status, model)
        raise PerplexityError(
            f"Perplexity terminó con estado {response.status}: {response.error}"
        )
    try:
        parsed = SearchResults.model_validate_json(response.output_text)
    except (ValueError, TypeError) as error:
        logger.exception("perplexity_invalid_json model=%s", model)
        raise PerplexityError("Perplexity no devolvió el JSON esperado.") from error
    results = {
        key: [offer for offer in offers if _is_specific_job_url(offer.url)]
        for key, offers in {
            "javier_automatizacion": parsed.javier_automatizacion,
            "javier_software": parsed.javier_software,
            "mayra_petroleras": parsed.mayra_petroleras,
        }.items()
    }
    logger.info(
        "perplexity_search_completed model=%s result_counts=%s",
        model,
        {key: len(offers) for key, offers in results.items()},
    )
    return results
