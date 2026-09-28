# Local masking API

Small HTTP adapter around the existing deterministic masking layer. It uses
synthetic text for this demo and does not need a database or an Ollama model.

## Run

Install [uv](https://docs.astral.sh/uv/) and use Python 3.11+. From this repo:

```bash
uv run --extra api uvicorn kvkk_maskeleme.api:app --host 127.0.0.1 --port 8000
```

In another terminal, send a synthetic example:

```bash
curl -sS http://127.0.0.1:8000/mask \
  -H 'Content-Type: application/json' \
  -d '{"text":"Sağlık raporu için telefon: 0532 000 00 00; e-posta: kisi@example.test"}'
```

Response:

```json
{
  "masked_text": "Sağlık raporu için telefon: <TELEFON_1>; e-posta: <EPOSTA_1>",
  "counts": {"TELEFON": 1, "EPOSTA": 1},
  "special_categories": ["SAGLIK"],
  "manual_review_required": true
}
```

The input must be JSON with one nonblank string `text` (at most 100,000
characters). Invalid input returns HTTP 422 with a generic error that does
not echo the submitted text. Responses use `Cache-Control: no-store`.
Interactive local API docs are at `http://127.0.0.1:8000/docs`.

## Verify

```bash
uv run --extra api pytest
uv run ruff check .
```

## Two-minute demo

1. **0:00–0:25** — Start the server with the command above; open `/docs`.
2. **0:25–1:05** — Run the curl request. Point out the two placeholders,
   per-type counts, and the health-context flag that remains in the text.
3. **1:05–1:35** — Send `{"text":"Deniz Çelik, Kızılay Mahallesi 28. Sokak"}`.
   Show that names and addresses remain and `manual_review_required` is true.
4. **1:35–2:00** — Run the tests and explain that the API never returns the
   reversible mapping, writes no raw document to persistent storage, and
   binds to localhost in the demo command.

## Scope and limits

This endpoint uses patterns and context labels. It masks supported identity,
tax, IBAN, payment-card, phone, plate, email, passport, birth-date, and SGK
values when the existing detector recognizes them. Names, addresses,
institutions, unlabeled passport/birth-date/SGK values, and other contextual
identifiers can remain. `special_categories` is a limited dictionary-based
flag, not removal of sensitive context. A clean flag does not prove the text
is safe. Every result requires human review; the tool does not certify
anonymization or legal compliance. Keep this unauthenticated demo on localhost
and use only synthetic input.
