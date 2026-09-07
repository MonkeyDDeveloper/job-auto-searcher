# Employ Auto Search

Servicio HTTP que envía un prompt a Perplexity Agent API, busca oportunidades en la web, normaliza los resultados y envía notificaciones por correo.

## Requisitos

- Python 3.11 o superior.
- Una API key de Perplexity API.
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
- `model`: usa por defecto `PERPLEXITY_MODEL`, que es `openai/gpt-5.6-luna`.
- `PERPLEXITY_FALLBACK_MODEL`: modelo alternativo si falla el principal; por defecto `perplexity/sonar`.
- `PERPLEXITY_TIMEOUT_SECONDS`: tiempo máximo por intento; por defecto `300` segundos.
- `PERPLEXITY_RETRIES`: reintentos del SDK ante errores transitorios; por defecto `2`.
- `shouldNotify`: `true` por defecto. Envía las tres listas completas a todos los destinatarios de `EMAILS_TO_NOTIFY` y a `MAYRA_EMAIL`, además de los correos directos de Javier.

La respuesta se normaliza en tres listas: `javier_automatizacion`, `javier_software` y `mayra_petroleras`. Cada lista puede contener la cantidad de resultados que Perplexity logre validar, incluso cero; no se exige llegar a cinco.

Si el modelo principal falla después de sus reintentos, el servicio intenta automáticamente el modelo configurado en `PERPLEXITY_FALLBACK_MODEL`. Solo genera una alerta de error si también falla el modelo de respaldo.

Ejemplo:

```bash
curl -X POST http://localhost:8000/search \
  -H "Authorization: Bearer $SEARCHER_APIKEY" \
  -H 'Content-Type: application/json' \
  -d '{"shouldNotify":false}'
```

## Email

`shouldNotify` requiere `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD` y `SMTP_FROM`. Gmail normalmente requiere una contraseña de aplicación en `SMTP_PASSWORD`, no la contraseña normal de la cuenta. Los destinatarios del resumen se leen de `EMAILS_TO_NOTIFY` separados por comas.

Cuando Perplexity encuentra un `email_contacto` y redacta un `email_recomendado` para Javier, el servicio envía ese borrador directamente al contacto. El borrador debe incluir versiones completas en español e inglés y mencionar la empresa. Los borradores de Mayra se incluyen en el resumen completo, pero nunca se envían automáticamente a sus contactos. Tanto Javier como Mayra reciben las tres listas.

Si SMTP no está configurado, el endpoint devuelve los resultados y añade el problema a `warnings`.

Si Perplexity o una integración de email falla, el servicio intenta enviar una alerta con el detalle del error a `EMAILS_TO_NOTIFY` y `MAYRA_EMAIL`. Si el propio SMTP está caído, la alerta no podrá enviarse y el error queda en los logs/respuesta cuando sea posible.

## Control de postulaciones

El servicio consulta la hoja de Google Sheets antes de cada búsqueda. Si una oportunidad ya existe por `id` o `uri`, no vuelve a aparecer. Cada oportunidad nueva se registra con `postulada = no`.

El archivo [`docs/google-apps-script.js`](docs/google-apps-script.js) contiene el puente de Apps Script. Copia su contenido en **Extensions → Apps Script**, configura `SPREADSHEET_ID`, `SHEET_NAME` y `SECRET`, y despliega como **Web app** ejecutando como tú. Configura la URL y el mismo token en `GOOGLE_APPS_SCRIPT_URL` y `GOOGLE_APPS_SCRIPT_TOKEN`.

Los resúmenes incluyen un botón **Marcar como postulada** para cada oportunidad y un botón **Ver todas las postulaciones**. El primero actualiza la fila a `postulada = si` y muestra una página HTML de confirmación.

## Nota sobre búsqueda web

El endpoint usa Perplexity Agent API con las herramientas `web_search` y `fetch_url`, por lo que la IA puede buscar y verificar páginas antes de generar el JSON. La respuesta sigue validándose para evitar inventar o guardar datos con estructura incorrecta.

Las URLs deben apuntar a la página individual de la vacante y al lugar específico para postular. Se excluyen rutas generales, páginas de búsqueda o categorías, vacantes cerradas/expiradas/eliminadas, errores 404/410 y páginas que solo requieran iniciar sesión sin permitir verificar la oportunidad.

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

El servicio usa por defecto `openai/gpt-5.6-luna`. Consulta el [catálogo actualizado de modelos de Perplexity Agent API](https://docs.perplexity.ai/docs/agent-api/models) y [`docs/MODELS.md`](docs/MODELS.md) antes de cambiar de modelo.
