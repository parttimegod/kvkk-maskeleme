# kvkk-maskeleme

A Python library and CLI for masking supported identifiers in Turkish
documents. The default path uses patterns, check digits and nearby field
labels. An optional Ollama provider adds names, addresses and organisations.

The CLI leaves names and free-text addresses unchanged. For example:

```text
Input:  Deniz Çelik — telefon: 0532 000 00 00; e-posta: kisi@example.test
Output: Deniz Çelik — telefon: <TELEFON_1>; e-posta: <EPOSTA_1>
```

This is reversible masking. The output still needs review before it is
shared: context and unsupported identifiers can identify someone.

## Run

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/). The core library
and CLI use the standard library.

```bash
uvx --from git+https://github.com/parttimegod/kvkk-maskeleme kvkk-maskeleme demo.txt
```

For a checkout:

```bash
git clone https://github.com/parttimegod/kvkk-maskeleme
cd kvkk-maskeleme
uv sync --locked --all-extras
uv run kvkk-maskeleme demo.txt -o masked.txt
```

Masked text goes to stdout or `-o`; counts and warnings go to stderr.
Files use UTF-8. [demo.txt](demo.txt) is a generated court-document example.
Its name, court and case number remain visible in the default output.

## Detection scope

| Type | Method and supported scope |
| --- | --- |
| TC, VKN | Number patterns and check digits; separator tolerance and limited OCR repair |
| IBAN | Turkish IBAN pattern and mod-97; spaces, dots and hyphens |
| Card | 16-digit pattern and Luhn |
| Phone | Turkish mobile-number formats |
| Plate | Turkish province codes and uppercase plate letters |
| Email | Address pattern |
| Passport, birth date, SGK | Value immediately following a recognised field label |
| Name, address, organisation | Optional model, with surname and address heuristics |

A valid check digit filters candidates; it does not prove that a number
was issued to someone. Invalid checksums and unsupported formats can remain.

Repeated values with the same type and spelling share a placeholder.
Numbering starts per call and skips placeholders already present in the
input. Different spellings and a full name versus a surname are separate
values.

After replacement, the same pattern detector scans the output.
`SizintiHatasi` is raised if it finds a remaining supported pattern.
This catches some replacement failures and shares the detector's blind
spots; it does not recheck the model's name/address findings.

## Library and model

```python
from kvkk_maskeleme import geri_al, maskele

original = "Telefon: 0532 000 00 00"
result = maskele(original)
print(result.metin)
assert geri_al(result.metin, result.eslesme) == original
```

`result.eslesme` contains the original values. The CLI writes that map
only when `--esleme mapping.json` is supplied. Keep it separate from any
shared output.

The model path requires an Ollama server and an installed model:

```python
from kvkk_maskeleme import OllamaSaglayici, maskele

provider = OllamaSaglayici(model="<installed-model-tag>", baglam=8192)
result = maskele(original, saglayici=provider)
print(result.uydurma, result.model_bicim_hatasi)
```

The provider sends the document to its configured address, which defaults
to localhost. It asks for verbatim expressions, then locates them in the
source. Expressions absent from the source are discarded and reported.
Malformed JSON sets `model_bicim_hatasi`; a result can still contain only
pattern findings. Check that flag before relying on the model path.

See [DESIGN.md](DESIGN.md) for overlap rules and the surname/address
heuristics.

## Special-category review

`incele` flags dictionary matches, and optionally model findings, for
health, convictions, religion and other special-category topics. It does
not remove those passages. A category is a review hint, not a legal
determination; no findings does not establish that the document is clear.

```bash
uv run kvkk-maskeleme demo.txt --sadece-incele --json
uv run kvkk-maskeleme demo.txt --kati -o masked.txt
```

Exit codes are `0` for a completed operation, `1` for a masking verification
failure, and `2` when `--kati` finds special-category indicators.
In masking mode, `--kati` writes the masked output before returning `2`.
A script using this flag must check the exit code before using the file.

Deleting the restore map alone does not establish anonymisation; the rest
of the document and other available data still matter. The
[KVKK Authority's explanation](https://www.kvkk.gov.tr/Icerik/8363/Kisisel-Verilerin-Silinmesi-Yok-Edilmesi-Veya-Anonim-Hale-Getirilmesi)
describes anonymisation in terms of whether a person can still be
identified. This tool does not assess that risk.

## Local HTTP API

The optional FastAPI adapter exposes `POST /mask` with the default pattern
layer:

```bash
uv run --locked --extra api uvicorn kvkk_maskeleme.api:app --host 127.0.0.1 --port 8000 --no-access-log
```

It returns masked text, occurrence counts, category flags and
`manual_review_required: true`. It omits the restore map and limits input
to 100,000 characters and a 1 MiB body. [API.md](API.md) has the request
format and error behaviour.

## Evaluation and tests

```bash
uv run --locked --extra api pytest
uv run --locked --extra api ruff check .
uv run python -c 'from kvkk_maskeleme.olcum import calistir; print(calistir(20).tablo())'
```

The generated corpus exercises eleven document templates. Identifier
recall requires an exact type, position and value match. The clean-text
false-positive count covers special-category flags only.

[MEASUREMENT.md](MEASUREMENT.md) records the scope and results. In the
separate eight-sentence special-category test set, seven cases remain
expected failures. Generated-corpus success should be read alongside those
misses. CI uses fake model responses; live Ollama evaluation is separate.

## License

MIT
