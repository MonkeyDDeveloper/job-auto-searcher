# Modelos Perplexity Agent API

El servicio usa modelos del Agent API con las herramientas `web_search` y `fetch_url`. Los precios son USD por 1 millón de tokens; las herramientas se cobran aparte y pueden cambiar.

| Nivel | Modelo | Entrada | Salida |
|---|---|---:|---:|
| 1 | `openai/gpt-5.6-sol` | $5.00 | $30.00 |
| 2 | `anthropic/claude-sonnet-4-6` | $3.00 | $15.00 |
| 3 | `openai/gpt-5.6-luna` | $0.20 | $1.20 |
| 3 | `perplexity/sonar` | $0.25 | $2.50 |
| 4 | `google/gemini-3.1-flash-lite` | $0.25 | $1.50 |
| 4 | `perplexity/deepseek-v4-flash-0731` | $0.13 | $0.26 |

Costos de herramientas:

| Herramienta | Precio por llamada |
|---|---:|
| `web_search` | $0.0025 |
| `fetch_url` | $0.0005 |

El servicio usa por defecto `openai/gpt-5.6-luna` y como respaldo `perplexity/sonar`.

Fuentes oficiales:

- [Agent API](https://docs.perplexity.ai/docs/agent-api/quickstart)
- [Modelos y precios](https://docs.perplexity.ai/docs/agent-api/models)
- [Web Search](https://docs.perplexity.ai/docs/agent-api/tools/web-search)
