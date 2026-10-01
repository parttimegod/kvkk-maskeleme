# Measurement

Run the deterministic evaluation from a checkout:

```bash
uv run python -c 'from kvkk_maskeleme.olcum import calistir; print(calistir(20).tablo())'
```

`ornekler(20)` creates 220 documents across eleven templates. The content is
generated from fixed vocabularies and structures, including unlabelled
prose and simulated OCR damage. It is not a held-out collection of scanned
court documents.

## Scoring

Identifier recall is the number of labelled occurrences found divided by
the number expected. A finding must match type, start, end and value
exactly. Finding one copy of a repeated value does not count the other
copies. A partial address does not count as a complete address.

AD, ADRES and KURUM are measured only when a provider is supplied; they are
outside the default detector's scope. Their absence from a default report
is not a successful detection result.

Special-category recall uses category presence per document, not exact
spans, because that layer flags context rather than replacing it.
The false-positive count runs this layer on 30 clean control sentences.
It does not measure identifier precision or model name/address false
positives.

## Deterministic run

With 20 samples per template and no provider, the current run found every
labelled occurrence in its supported scope:

| Identifier | Expected | Found |
| --- | ---: | ---: |
| TC | 100 | 100 |
| VKN | 60 | 60 |
| IBAN | 40 | 40 |
| Phone | 40 | 40 |
| Email | 40 | 40 |
| Card | 20 | 20 |
| Plate | 20 | 20 |
| Passport | 20 | 20 |
| Birth date | 20 | 20 |
| SGK | 20 | 20 |

The four generated special-category groups were also found: convictions
20/20, association/union context 20/20, genetic context 20/20, and health
40/40. None of the 30 clean controls received a special-category flag.

These templates often use the same vocabulary as the detector. In
[the separate test set](tests/test_ozel_nitelikli_bagimsiz.py), only one of
eight written sentences receives its expected category. Seven cases use
strict expected-failure markers, including dialysis, indirect conviction
wording and face identification misclassified as health. Those failures
describe real gaps in the dictionary, even when the generated report
shows 100%.

## Model results

Earlier release notes reported AD 518/520, ADRES 160/160 and KURUM 60/60
with a local Gemma model. Those runs used type/value scoring, which could
credit missed repeated occurrences, and were not rerun during this review.
They are historical results, not validation under the current scoring rule.

To evaluate a model now, pass a configured `OllamaSaglayici` to
`calistir` and record the model tag, server version, context size, prompt,
sample size and errors. Temperature zero does not make all model runtimes
repeat identically. The CI suite tests parsing and replacement with fake
responses; it does not run a live model.

Next useful measurements are identifier precision, a larger independent
category set and authorised data representative of the intended workflow.
