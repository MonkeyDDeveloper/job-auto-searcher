from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    searcher_apikey: str
    opencode_api_key: str
    default_model: str
    fallback_model: str
    opencode_timeout_seconds: int
    opencode_retries: int
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
        opencode_api_key=os.getenv("OPENCODE_API_KEY", ""),
        default_model=os.getenv("OPENCODE_DEFAULT_MODEL", "deepseek-v4-pro"),
        fallback_model=os.getenv(
            "OPENCODE_FALLBACK_MODEL", "deepseek-v4-flash-free"
        ),
        opencode_timeout_seconds=int(os.getenv("OPENCODE_TIMEOUT_SECONDS", "300")),
        opencode_retries=int(os.getenv("OPENCODE_RETRIES", "2")),
        email_recipients=recipients,
        mayra_email=os.getenv("MAYRA_EMAIL", "masachemayra@gmail.com"),
        smtp_host=os.getenv("SMTP_HOST"),
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        smtp_user=os.getenv("SMTP_USER"),
        smtp_password=os.getenv("SMTP_PASSWORD"),
        smtp_from=os.getenv("SMTP_FROM"),
    )
