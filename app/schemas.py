from pydantic import BaseModel, ConfigDict, Field, field_validator

from .prompts import DEFAULT_PROMPT


class SearchRequest(BaseModel):
    prompt: str = Field(default=DEFAULT_PROMPT)
    model: str | None = None
    shouldNotify: bool = True


class JobOffer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cargo: str
    empresa: str
    ubicacion: str
    modalidad: str
    score: int = Field(ge=0, le=100)
    url: str
    rango_salarial: str
    email_contacto: str
    email_recomendado: str
    justificacion: str

    @field_validator("score")
    @classmethod
    def score_must_pass_threshold(cls, value: int) -> int:
        if value <= 70:
            raise ValueError("Solo se aceptan ofertas con Score superior a 70")
        return value
