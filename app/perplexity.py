import httpx
from perplexity import Perplexity

from .schemas import JobOffer, SearchResults


class PerplexityError(RuntimeError):
    pass


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
) -> dict[str, list[JobOffer]]:
    if not api_key:
        raise PerplexityError("Falta PERPLEXITY_API_KEY.")

    timeout = httpx.Timeout(
        connect=10.0,
        read=float(timeout_seconds),
        write=30.0,
        pool=30.0,
    )
    client = Perplexity(api_key=api_key, max_retries=max(0, retries), timeout=timeout)
    try:
        response = client.responses.create(
            model=model,
            input=prompt,
            instructions=(
                "Search the web extensively before answering. Use web_search and "
                "fetch_url for current job listings. Never invent a job, URL, "
                "email, company, or date. Return only the requested JSON."
            ),
            tools=[
                {"type": "web_search", "search_context_size": "high", "max_results": 20},
                {"type": "fetch_url", "max_urls": 10},
            ],
            response_format=_response_schema(),
            max_output_tokens=16000,
            max_steps=10,
        )
    except Exception as error:
        raise PerplexityError(f"Perplexity no pudo completar la búsqueda: {error}") from error
    finally:
        client.close()

    if response.status != "completed":
        raise PerplexityError(
            f"Perplexity terminó con estado {response.status}: {response.error}"
        )
    try:
        parsed = SearchResults.model_validate_json(response.output_text)
    except (ValueError, TypeError) as error:
        raise PerplexityError("Perplexity no devolvió el JSON esperado.") from error
    return {
        "javier_automatizacion": parsed.javier_automatizacion,
        "javier_software": parsed.javier_software,
        "mayra_petroleras": parsed.mayra_petroleras,
    }
