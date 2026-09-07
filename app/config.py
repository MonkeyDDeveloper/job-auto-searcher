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
    google_apps_script_url: str | None
    google_apps_script_token: str | None
    google_sheet_url: str
    application_link_secret: str
    public_base_url: str


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
        google_apps_script_url=os.getenv("GOOGLE_APPS_SCRIPT_URL"),
        google_apps_script_token=os.getenv("GOOGLE_APPS_SCRIPT_TOKEN"),
        google_sheet_url=os.getenv(
            "GOOGLE_SHEET_URL",
            "https://docs.google.com/spreadsheets/d/1I_QuiLT5TQLBcDA3Cc7Ttw7fia9huQ5AL2XrcFQowI0/edit",
        ),
        application_link_secret=os.getenv("APPLICATION_LINK_SECRET", ""),
        public_base_url=os.getenv("PUBLIC_BASE_URL", "").rstrip("/"),
    )
