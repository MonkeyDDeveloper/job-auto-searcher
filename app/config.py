from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    searcher_apikey: str
    perplexity_api_key: str
    default_model: str
    fallback_model: str
    perplexity_timeout_seconds: int
    perplexity_retries: int
    email_recipients: tuple[str, ...]
    mayra_email: str
    smtp_host: str | None
    smtp_port: int
    smtp_user: str | None
    smtp_password: str | None
    smtp_from: str | None


def load_settings() -> Settings:
    recipients = tuple(
        email.strip()
        for email in os.getenv(
            "EMAILS_TO_NOTIFY", "fraydeveloper@gmail.com,anotheremail@gmail.com"
        ).split(",")
        if email.strip()
    )
    return Settings(
        searcher_apikey=os.getenv("SEARCHER_APIKEY", ""),
        perplexity_api_key=os.getenv("PERPLEXITY_API_KEY", ""),
        default_model=os.getenv("PERPLEXITY_MODEL", "openai/gpt-5.6-luna"),
        fallback_model=os.getenv(
            "PERPLEXITY_FALLBACK_MODEL", "perplexity/sonar"
        ),
        perplexity_timeout_seconds=int(
            os.getenv("PERPLEXITY_TIMEOUT_SECONDS", "300")
        ),
        perplexity_retries=int(os.getenv("PERPLEXITY_RETRIES", "2")),
        email_recipients=recipients,
        mayra_email=os.getenv("MAYRA_EMAIL", "masachemayra@gmail.com"),
        smtp_host=os.getenv("SMTP_HOST"),
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        smtp_user=os.getenv("SMTP_USER"),
        smtp_password=os.getenv("SMTP_PASSWORD"),
        smtp_from=os.getenv("SMTP_FROM"),
    )
