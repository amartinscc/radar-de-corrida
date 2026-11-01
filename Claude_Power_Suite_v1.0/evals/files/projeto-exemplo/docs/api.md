# API

## POST /shorten

Corpo: `{"url": "..."}`. Resposta 201: `{"short_url": "..."}`.

## GET /{codigo}

Redireciona (302) para a URL original.

```bash
curl -i localhost:8080/abc1234
