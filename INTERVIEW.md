# Project interview practice

Amaç: Bu projeyi kısa ve anlaşılır İngilizceyle anlatmak ve tasarım
kararlarını kod üzerinde açıklamak. Bir oturumda yalnızca bir soruyu çalış.
Örnek cevapları kendi sözlerinle kullan; gösteremediğin bir davranışı veya
profesyonel iş deneyimini sahip olduğun bir yetkinlik gibi sunma.

## Around 90 seconds

In this project, I built a REST API around a library that masks supported
identifiers in Turkish text. A client sends a document to `POST /mask`. The
API returns masked text, occurrence counts, and category flags. It leaves
out the mapping used to restore identifiers.

The library uses patterns, check digits, and context labels. The HTTP layer
validates the input and limits the body before JSON parsing, including when
it arrives in chunks.

I kept the endpoint independent of a database and a language model because
the operation does not need stored state or model inference. The library's
optional model layer is separate.

The main limitation is that names, addresses, and unsupported formats can
remain. Every response requires human review. Synthetic tests cover
supported formats, errors, and boundary conditions. The tests passed locally
and in GitHub Actions. This demonstrates the tested behavior; it does not
prove that all personal data has been removed.

Hız hedefi zorunlu değil. Önce anlaşılır söyle; sonra yaklaşık 90 saniyeye
indir. Bu metin bir portföy projesi anlatımıdır.

## Six questions to explain from the code

### 1. Why are patterns alone not enough?

A pattern can find an eleven-digit number that is actually a file number.
For supported identifier types, check digits filter invalid candidates.
Other types use patterns or context labels. A valid check digit does not
prove that a number has been issued to a real person.

Show `_DESENLER`, `_DOGRULAYICI` and `_desenle_bul` in
[tespit.py](src/kvkk_maskeleme/tespit.py). The checksum validators apply to
TC, VKN, IBAN and cards; do not say that every type has a checksum.

### 2. Why do you have both a text limit and a body limit?

They measure different things: characters in the text and bytes in the
whole JSON body. I check actual body bytes before JSON parsing because a
Content-Length header can be inaccurate or absent. The same limit applies
when the body arrives in chunks.

Show `MAX_TEXT_LENGTH`, `MAX_BODY_BYTES`, `MaskRequest` and
`RequestBodyLimitMiddleware` in [api.py](src/kvkk_maskeleme/api.py).
The limits are 100,000 characters and 1,048,576 bytes. This bounds the
accepted payload; it is not a complete server memory or denial-of-service
guarantee.

### 3. How do you keep placeholders consistent?

Within one request, the library keeps a dictionary keyed by identifier type
and the exact matched text. Repeated identical values receive the same
placeholder. It replaces matches from right to left so earlier character
positions do not move.

Show `yer_tutucu` and the replacement loop in
[maskeleme.py](src/kvkk_maskeleme/maskeleme.py). Numbering restarts on the
next request. Different spellings of the same number are not normalised
into a single identity by this dictionary.

### 4. Why can personal data still remain after a successful response?

The endpoint only uses the pattern layer. Names, addresses and unsupported
formats can remain. The output is rescanned with the same detector, so
verification can catch remaining recognised patterns, but it shares the
detector's blind spots. Special-category content is flagged, not removed.

Show `dogrula_temiz` in [maskeleme.py](src/kvkk_maskeleme/maskeleme.py) and
`manual_review_required=True` in [api.py](src/kvkk_maskeleme/api.py).
Do not present masking as complete anonymisation or legal compliance.

### 5. How do you avoid exposing the input through errors?

The validation handler returns a generic error without the submitted
input. A masking verification failure also returns a generic error and
no document. The successful response omits the restore mapping, and
masking and validation responses carry Cache-Control: no-store.

Show `invalid_request`, `incomplete_masking` and `MaskResponse` in
[api.py](src/kvkk_maskeleme/api.py). A request that is too large gets 413;
field validation gets 422; a masking verification failure gets 500.
Malformed JSON or encoding can return 400 or 422. These are the handled
paths; do not claim that every unexpected exception is covered.

### 6. Why did you leave out a database and an LLM?

The operation does not need stored state: it takes text and returns a
result. A database would add storage and maintenance without serving this
feature. The library has an optional model layer for names and addresses,
but the HTTP demo deliberately uses the deterministic layer.

Show `mask` in [api.py](src/kvkk_maskeleme/api.py): it calls `maskele`
without a model provider and returns only the selected response fields.
This endpoint is not evidence of SQL experience; use a separate relevant
SQL project to demonstrate that skill.

## Evidence you can demonstrate

Snapshot: 30 September 2026, API implementation commit
`9333641f781ac427c551e8bdd571cbb200a01082`. The suite recorded 257 passing
cases, 1 skipped case and 7 existing expected failures; 48 cases cover HTTP
behavior. These are synthetic test results, not field accuracy or real
customer usage. Recheck the numbers before quoting them after code changes.

| Claim | Code or test to open |
| --- | --- |
| Supported types and clean/unsupported text | [test_api.py](tests/test_api.py) |
| Actual body boundary, including a misleading header | `test_actual_body_size_boundary`, `test_body_limit_precedes_processing_and_ignores_content_length` in [test_api_limits.py](tests/test_api_limits.py) |
| Streamed input and Unicode | `test_chunked_body_limit_and_unicode`, `test_invalid_text_does_not_echo_input` in [test_api_limits.py](tests/test_api_limits.py) |
| Generic verification error without original text | `test_verification_failure_returns_generic_error` in [test_api.py](tests/test_api.py) |
| No document file created in the tested working directory | `test_synthetic_document_preserves_lines_without_writing_files` in [test_api_limits.py](tests/test_api_limits.py) |
| Repeated placeholders and separate requests | `test_repeated_value_uses_same_placeholder` in [test_api.py](tests/test_api.py), `test_placeholder_numbering_is_independent_between_requests` in [test_api_limits.py](tests/test_api_limits.py) |

Run the demonstrated HTTP cases:

```bash
uv run --locked --extra api pytest tests/test_api.py tests/test_api_limits.py
```

Use [API.md](API.md) for the live request and two-minute demo.

## A 15-minute practice block

1. **3 minutes:** Read the short explanation aloud once, then say it without
   reading. Record yourself.
2. **5 minutes:** Choose one question. Open the referenced function and
   point to the lines that support your answer.
3. **4 minutes:** Answer it in 3–4 English sentences without looking at
   the suggested wording. Use “I haven't measured that yet” when appropriate.
4. **3 minutes:** Replay the recording. Fix one technical mistake and one
   unclear sentence; record the answer again.

First prompt: **What does this API do, and what does it leave unmasked?**

If asked about AI assistance, describe the work actually done with it.
A useful answer format is: “I used AI assistance for [the specific task].
I checked the result by [the concrete review, test or comparison I performed].”
Fill those parts with actions you can demonstrate.
