# Modelos OpenCode Zen

Los modelos se ordenan aquí por capacidad general esperada para este caso, no por precio. El modelo por defecto del servicio es `deepseek-v4-pro`: evita los modelos más caros y también los modelos Flash/Nano orientados a velocidad o coste mínimo.

Los precios son USD por 1 millón de tokens, según la documentación de Zen consultada el 6 de septiembre de 2026. Pueden cambiar.

| Nivel | Modelo | Entrada | Salida | Endpoint |
|---|---|---:|---:|---|
| 1 | `claude-opus-5` | $5.00 | $25.00 | `/zen/v1/messages` |
| 1 | `gpt-5.5-pro` | $30.00 | $180.00 | `/zen/v1/responses` |
| 1 | `gpt-6-astra` | $10.00 | $50.00 | `/zen/v1/responses` |
| 2 | `claude-sonnet-4-6` | $3.00 | $15.00 | `/zen/v1/messages` |
| 2 | `gpt-5.6-sol` | $2.00 | $10.00 | `/zen/v1/responses` |
| 2 | `gpt-5.6-luna` | $0.20 | $1.20 | `/zen/v1/responses` |
| 2 | `gemini-3.1-pro` | $2.00 | $12.00 | `/zen/v1/models/gemini-3.1-pro` |
| 3 | `deepseek-v4-pro` | $1.74 | $3.48 | `/zen/v1/chat/completions` |
| 3 | `qwen3.6-plus` | $0.50 | $3.00 | `/zen/v1/chat/completions` |
| 3 | `glm-5.2` | $1.40 | $4.40 | `/zen/v1/chat/completions` |
| 3 | `kimi-k2.6` | $0.95 | $4.00 | `/zen/v1/chat/completions` |
| 4 | `deepseek-v4-flash` | $0.14 | $0.28 | `/zen/v1/chat/completions` |
| 4 | `gemini-3.8-flash` | $1.50 | $7.50 | `/zen/v1/models/gemini-3.8-flash` |
| 4 | `gpt-5.4-nano` | $0.20 | $1.25 | `/zen/v1/responses` |
| 5 | `deepseek-v4-flash-free` | Gratis | Gratis | `/zen/v1/chat/completions` |
| 5 | `big-pickle` | Gratis | Gratis | `/zen/v1/chat/completions` |

## Catálogo actual

El catálogo completo se puede consultar en tiempo real:

```bash
curl https://opencode.ai/zen/v1/models
```

Incluye también variantes de Claude, GPT, Gemini, Grok, Muse, GLM, MiniMax, Kimi, Qwen y modelos gratuitos. Los modelos `responses` y `messages` no usan exactamente el mismo formato que `chat/completions`; este proyecto fija `deepseek-v4-pro` porque usa el endpoint compatible implementado.

## Fuentes

- [OpenCode Zen](https://opencode.ai/docs/zen/)
- [Modelos disponibles](https://opencode.ai/zen/v1/models)
