# Employ Auto Search

Servicio HTTP que envía un prompt a OpenCode Zen, normaliza las oportunidades encontradas y envía notificaciones por correo tanto al resumen como a los contactos directos extraídos.

## Requisitos

- Python 3.11 o superior.
- Una API key de OpenCode Zen.
- Un servidor SMTP y una contraseña de aplicación.

## Instalación

```bash
cd /Users/javier/employ-auto-search
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Exporta las variables de `.env` en tu shell o usa un gestor de secretos. El servicio no carga `.env` automáticamente para evitar añadir otra dependencia; por ejemplo:

```bash
set -a
source .env
set +a
```

Inicia la API:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Documentación interactiva: `http://localhost:8000/docs`.

## Endpoint

`POST /search`

El endpoint requiere autenticación Bearer. Configura una clave privada en `SEARCHER_APIKEY` y envíala así:

```bash
export SEARCHER_APIKEY="una-clave-larga-y-aleatoria"
```

Body opcional:

```json
{
  "prompt": "Busca vacantes de Python remotas publicadas esta semana.",
  "model": "deepseek-v4-pro",
  "shouldNotify": true
}
```

Todos los campos son opcionales:

- `prompt`: usa por defecto el prompt completo de búsqueda definido en `app/prompts.py`.
- `model`: usa por defecto `OPENCODE_DEFAULT_MODEL`, que es `deepseek-v4-pro`.
- `OPENCODE_FALLBACK_MODEL`: modelo alternativo si falla el principal; por defecto `deepseek-v4-flash-free`.
- `OPENCODE_TIMEOUT_SECONDS`: tiempo máximo por intento contra OpenCode; por defecto `300` segundos.
- `OPENCODE_RETRIES`: reintentos ante timeout, desconexión, HTTP 429 o HTTP 5xx; por defecto `2`.
- `shouldNotify`: `true` por defecto. Envía las tres listas completas a todos los destinatarios de `EMAILS_TO_NOTIFY` y a `MAYRA_EMAIL`, además de los correos directos de Javier.

La respuesta se normaliza en tres listas: `javier_automatizacion`, `javier_software` y `mayra_petroleras`. Cada lista puede contener la cantidad de resultados que OpenCode logre validar, incluso cero; no se exige llegar a cinco.

Si el modelo principal falla después de sus reintentos, el servicio intenta automáticamente el modelo gratuito configurado en `OPENCODE_FALLBACK_MODEL`. Solo genera una alerta de error si también falla el modelo de respaldo.

Ejemplo:

```bash
curl -X POST http://localhost:8000/search \
  -H "Authorization: Bearer $SEARCHER_APIKEY" \
  -H 'Content-Type: application/json' \
  -d '{"shouldNotify":false}'
```

## Email

`shouldNotify` requiere `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD` y `SMTP_FROM`. Gmail normalmente requiere una contraseña de aplicación en `SMTP_PASSWORD`, no la contraseña normal de la cuenta. Los destinatarios del resumen se leen de `EMAILS_TO_NOTIFY` separados por comas.

Cuando OpenCode encuentra un `Email de Contacto` y redacta un `Email Recomendado` para Javier, el servicio envía ese borrador directamente al contacto. Los borradores de Mayra se incluyen en el resumen completo, pero nunca se envían automáticamente a sus contactos. Tanto Javier como Mayra reciben las tres listas.

Si SMTP no está configurado, el endpoint devuelve los resultados y añade el problema a `warnings`.

Si OpenCode o una integración de email falla, el servicio intenta enviar una alerta con el detalle del error a `EMAILS_TO_NOTIFY` y `MAYRA_EMAIL`. Si el propio SMTP está caído, la alerta no podrá enviarse y el error queda en los logs/respuesta cuando sea posible.

## Nota sobre búsqueda web

El endpoint envía el prompt a Zen. La capacidad de encontrar ofertas reales depende de que el modelo/proveedor tenga acceso web. El prompt exige no inventar URLs ni ofertas; para una garantía de búsqueda verificable conviene añadir un proveedor de búsqueda web antes de producción.

## Modelos y precios

Los precios son USD por 1 millón de tokens y pueden cambiar.

| Nivel | Modelo | Entrada | Salida |
|---|---|---:|---:|
| 1 | `claude-opus-5` | $5.00 | $25.00 |
| 1 | `gpt-5.5-pro` | $30.00 | $180.00 |
| 1 | `gpt-6-astra` | $10.00 | $50.00 |
| 2 | `claude-sonnet-4-6` | $3.00 | $15.00 |
| 2 | `gpt-5.6-sol` | $2.00 | $10.00 |
| 2 | `gpt-5.6-luna` | $0.20 | $1.20 |
| 2 | `gemini-3.1-pro` | $2.00 | $12.00 |
| 3 | `deepseek-v4-pro` | $1.74 | $3.48 |
| 3 | `qwen3.6-plus` | $0.50 | $3.00 |
| 3 | `glm-5.2` | $1.40 | $4.40 |
| 3 | `kimi-k2.6` | $0.95 | $4.00 |
| 4 | `deepseek-v4-flash` | $0.14 | $0.28 |
| 4 | `gemini-3.8-flash` | $1.50 | $7.50 |
| 4 | `gpt-5.4-nano` | $0.20 | $1.25 |
| 5 | `deepseek-v4-flash-free` | Gratis | Gratis |
| 5 | `big-pickle` | Gratis | Gratis |

El servicio usa por defecto `deepseek-v4-pro`. Consulta el [catálogo actualizado de OpenCode Zen](https://opencode.ai/docs/zen/) y [`docs/MODELS.md`](docs/MODELS.md) antes de cambiar de modelo.
