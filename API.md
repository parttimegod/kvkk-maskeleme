# Local masking API

An optional HTTP adapter for the default pattern detector. It takes one
document per request and does not use a database or Ollama.

## Run and request

From a checkout with Python 3.11+ and [uv](https://docs.astral.sh/uv/):

```bash
uv run --locked --extra api uvicorn kvkk_maskeleme.api:app --host 127.0.0.1 --port 8000 --no-access-log
```

In another terminal:

```bash
curl -sS http://127.0.0.1:8000/mask \
  -H 'Content-Type: application/json' \
  -d '{"text":"Sağlık raporu için telefon: 0532 000 00 00; e-posta: kisi@example.test"}'
```

```json
{
  "masked_text": "Sağlık raporu için telefon: <TELEFON_1>; e-posta: <EPOSTA_1>",
  "counts": {"TELEFON": 1, "EPOSTA": 1},
  "special_categories": ["SAGLIK"],
  "manual_review_required": true
}
```

Interactive documentation is at `http://127.0.0.1:8000/docs`.

## Contract

The body is JSON with exactly one nonblank Unicode string field, `text`.
Its limit is 100,000 characters. The whole request is limited to 1,048,576
bytes before JSON parsing, using actual received bytes rather than
`Content-Length`. The byte limit also applies to streamed bodies.

| Outcome | HTTP status | Response |
| --- | ---: | --- |
| Masked result | 200 | Response fields shown above |
| Body too large | 413 | `{"error":"Request body too large"}` |
| Invalid fields or malformed JSON | 422 | `{"error":"Invalid request body"}` |
| Invalid JSON byte encoding | 400 | Framework parse error; no masked document |
| Remaining recognised pattern | 500 | `{"error":"Masking verification failed"}` |

Masking and handled validation/verification responses use
`Cache-Control: no-store`. Validation and verification errors omit submitted
text. The success response omits the restore map.

`counts` counts occurrences, not distinct values. Identical type/value
pairs share placeholders within a request. Numbering restarts per request
and skips tokens already in its input.

## Scope

Names, free-text addresses and unsupported formats remain.
`special_categories` flags some sensitive context without removing it;
the health phrase in the example stays visible. Every result sets
`manual_review_required` to true.

The adapter does not write document files or log request bodies. Raw text
and a temporary restore map exist in memory during processing. The command
binds to localhost and disables access logs; it has no authentication for a
shared deployment. Use generated input when demonstrating it.

## Tests

```bash
uv sync --locked --all-extras
uv run --locked --extra api pytest
uv run --locked --extra api ruff check .
```

HTTP tests cover supported and unsupported text, repeated values,
validation errors, Unicode, exact request limits, misleading length headers,
streamed input and verification failures.
