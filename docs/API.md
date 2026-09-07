# API

## `POST /search`

Busca oportunidades con Perplexity Agent API, las separa por candidato y opcionalmente envía notificaciones.

### Autenticación

Requiere el header:

```http
Authorization: Bearer <SEARCHER_APIKEY>
```

La clave válida se configura en la variable de entorno `SEARCHER_APIKEY`.

`shouldNotify` es `true` por defecto. Las tres listas completas se envían a `EMAILS_TO_NOTIFY` y `MAYRA_EMAIL`. Los emails directos solo se envían para las listas de Javier.

### Request

```json
{
  "prompt": "string opcional",
  "model": "string opcional",
  "shouldNotify": true
}
```

### Response

```json
{
  "model": "deepseek-v4-pro",
  "results": {
    "javier_automatizacion": [],
    "javier_software": [],
    "mayra_petroleras": []
  },
  "notifiedRecipients": 0,
  "contactEmailsSent": 0,
  "warnings": []
}
```

Las ofertas válidas deben tener `score` superior a 70. Cada lista puede contener cero o más objetos. Cuando existe `email_contacto` y `email_recomendado` no es `No aplica`, el servicio envía ese borrador al contacto solo si pertenece a Javier.

### Errores

- `502`: Perplexity no respondió con el modelo principal ni con el modelo de respaldo, agotó los reintentos, la clave falta o ambas respuestas no son JSON válidas. El servicio intenta enviar una alerta por email antes de responder.
- `200` con `warnings`: la búsqueda funcionó, pero SMTP no estaba configurado o falló.
