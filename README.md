# kvkk-maskeleme

Personal data detection and **masking** for Turkish text. Replaces direct
identifiers with placeholders before a document is processed, in
particular before it is sent to a cloud-based model.

> **This tool does not anonymise data.** Because masking is reversible,
> the output is still personal data under Turkey's personal data
> protection law (KVKK, Law No. 6698). See [Scope under
> KVKK](#scope-under-kvkk) for detail.

## Example

Input (`demo.txt`):

```
ANTALYA 3. ASLİYE HUKUK MAHKEMESİ
Dosya No: 2026/1487 E.

Davacı Mehmet Yılmaz (T.C. Kimlik No: 62601815964), Doğum Tarihi: 12.03.1985.
İletişim: 0532 445 67 89 / m.yilmaz@ornek.com
Ödeme TR81 0830 1661 3186 0913 9099 60 numaralı hesaba yapılacaktır.

Dosyanın 12345678901 sayılı dosya ile birleştirilmesine, tanık dinlenmesine ve
davacının sağlık raporunun celbine karar verildi.
```

Command:

```bash
kvkk-maskeleme demo.txt
```

Output (stdout):

```
ANTALYA 3. ASLİYE HUKUK MAHKEMESİ
Dosya No: 2026/1487 E.

Davacı Mehmet Yılmaz (T.C. Kimlik No: <TC_1>), Doğum Tarihi: <DOGUM_TARIHI_1>.
İletişim: <TELEFON_1> / <EPOSTA_1>
Ödeme <IBAN_1> numaralı hesaba yapılacaktır.

Dosyanın 12345678901 sayılı dosya ile birleştirilmesine, tanık dinlenmesine ve
davacının sağlık raporunun celbine karar verildi.
```

Warnings (stderr):

```
Maskelendi: DOGUM_TARIHI×1, EPOSTA×1, IBAN×1, TC×1, TELEFON×1
Bu belge özel nitelikli kişisel veri içeriyor olabilir (SAGLIK). KVKK md. 6 uyarınca işlenmesi açık rıza veya kanunda öngörülen bir hâle bağlıdır. Maskeleme bu veriyi kaldırmaz.
```

Points to note:

- `12345678901` is left untouched — eleven digits, but it fails the TC
  identity number check digit, so it is a file number, not an identity
  number.
- The `Doğum Tarihi:` label stays as it is; only the value is replaced,
  so the document stays readable.
- The IBAN is caught even though it is written with spaces.
- The phrase "tanık dinlenmesine" ("hearing the witness") is not counted
  as religious data, even though it contains the root "din" ("religion").
- The summary goes to stderr, so `> clean.txt` captures only the masked
  document.
- The phrase "sağlık raporu" ("health report") is flagged as a special
  category of personal data (KVKK Article 6); this line is not masked,
  only a warning is appended to stderr — the document stays readable, but
  it is flagged as needing human review.

## Status

The pattern layer works. The model layer's **infrastructure is ready,
but no model is wired in** — the interface, response parsing, merging
and measurement are written and tested; it activates once an
`OllamaSaglayici` is supplied.

| Type | Status | Method |
|---|---|---|
| TC identity number | ✓ | pattern + check digit |
| Tax identification number | ✓ | pattern + check digit |
| IBAN | ✓ | pattern + mod-97 |
| Card number | ✓ | pattern + Luhn |
| Phone | ✓ | pattern |
| Number plate | ✓ | pattern |
| Email | ✓ | pattern |
| Passport number | ✓ | context anchor |
| Date of birth | ✓ | context anchor |
| SGK registration number | ✓ | context anchor |
| **Name** | infrastructure ready | model layer |
| **Address** | infrastructure ready | model layer |
| **Institution** | infrastructure ready | model layer |

## Scope under KVKK

This section exists to make clear what the tool does and does not do.
Misunderstanding it creates a compliance gap.

### Masking is not anonymisation

Under KVKK, anonymisation means that data can no longer be linked to a
person under any circumstances, even when matched against other data.
Anonymised data falls outside the scope of the law.

This tool performs **pseudonymisation / masking**: a `<TC_1>` placeholder
plus a mapping table that stays local. As long as the mapping exists,
the operation is reversible, and therefore:

- The output **is still personal data**
- The duty to inform, and retention and security obligations, **still
  apply**
- The data **does not fall outside the scope of KVKK**

The benefit is this: direct identifiers do not leave the premises when
data is sent to a cloud-based model. This is risk reduction, not
exemption.

If you actually want to anonymise, delete the mapping table and close
off the `geri_al` (restore) path — but even then you still have to
assess the rest of the text for re-identification risk.

### Special categories are out of scope

Under KVKK Article 6, special categories of personal data are: race,
ethnic origin, political opinion, philosophical belief, religion, sect
or other belief, dress and appearance, membership of an association,
foundation or trade union, health, sex life, **criminal conviction and
security measures**, biometric and genetic data.

This data **is not masked, it is flagged.** The reason: special category
data is not a field, it is context. In the sentence "Sanık daha önce
uyuşturucu kullanmaktan sabıkalıdır" ("The defendant has a prior
conviction for drug use") there is no field to mask — the sentence
itself is the data. Attempting to mask it would make the document
meaningless.

```python
from kvkk_maskeleme import incele

rapor = incele(metin)
rapor.var_mi          # True
rapor.kategoriler()   # {"CEZA_MAHKUMIYETI", "SAGLIK"}
print(rapor.uyari())
```

```
Bu belge özel nitelikli kişisel veri içeriyor olabilir
(CEZA_MAHKUMIYETI, DERNEK_VAKIF_SENDIKA, SAGLIK). KVKK md. 6 uyarınca
işlenmesi açık rıza veya kanunda öngörülen bir hâle bağlıdır.
Maskeleme bu veriyi kaldırmaz.
```

The categories are named in the law's order and with the law's
terminology, so that someone doing compliance work can map the output
directly onto the article.

**The error balance is inverted here.** In the identifier layer, a false
positive is bad; here, a false negative is bad. A document flagged
unnecessarily costs a person a few minutes; a document that slips
through costs a KVKK violation. The dictionary layer is deliberately
generous because of this.

If a provider is supplied, the model layer also runs and adds the
contextual expressions the dictionary misses.

### Re-identification

Even with direct identifiers removed, a document can still identify a
person: the case type, date, court and the case's own idiosyncratic
details can combine to reveal identity. KVKK's definition says
"identified **or identifiable**." This tool does not measure the risk of
being identifiable.

## Installation

No installation needed:

```bash
uvx --from git+https://github.com/parttimegod/kvkk-maskeleme kvkk-maskeleme document.txt
```

To install it permanently:

```bash
uv tool install git+https://github.com/parttimegod/kvkk-maskeleme
kvkk-maskeleme document.txt
```

As a library:

```bash
uv add git+https://github.com/parttimegod/kvkk-maskeleme
```

Requirements: Python 3.11+ and [uv](https://docs.astral.sh/uv/). The
package itself has no dependencies, only the standard library.

## Command line

```bash
kvkk-maskeleme document.txt                 # mask, write to stdout
kvkk-maskeleme document.txt -o clean.txt
cat document.txt | kvkk-maskeleme
kvkk-maskeleme document.txt --sadece-incele # special-category report only
kvkk-maskeleme document.txt --json
```

Warnings and the summary go to **stderr**, output goes to stdout. So
someone who writes `kvkk-maskeleme document.txt > clean.txt` still sees the
warning, but their file does not get polluted.

The mapping table **is not written unless asked for** — since it
contains all the personal data in plain text, leaving it silently next
to the masked output would make the masking pointless:

```bash
kvkk-maskeleme document.txt --esleme mapping.json
```

Writing it prints this to stderr:

```
UYARI: mapping.json bütün kişisel veriyi düz metin içeriyor. Maskelenmiş
metinle birlikte hiçbir yere göndermeyin.
```

The warning says the mapping file holds every identifier in plain text, and
must never be sent anywhere together with the masked document.

Exit codes for scripts: `0` clean, `1` error, `2` special category data
found (with `--kati`).

```bash
kvkk-maskeleme document.txt --kati > clean.txt || echo "manual review needed"
```

## Usage

```python
from kvkk_maskeleme import maskele, geri_al

sonuc = maskele(metin)

sonuc.metin      # masked text
sonuc.eslesme    # {"<TC_1>": "12345678901", ...}
sonuc.ozet()     # {"TC": 2, "IBAN": 1}

geri_al(sonuc.metin, sonuc.eslesme)   # original text
```

Example output (synthetic document):

```
DAVACI     : Hatice Özdemir (T.C. Kimlik No: <TC_1>)
ADRES      : Bahçelievler Mahallesi 34. Sokak No: 36/8 İstanbul
TELEFON    : <TELEFON_1>

DAVALI     : Murat Arslan (T.C. Kimlik No: <TC_2>)

AÇIKLAMALAR: Müvekkilim Hatice Özdemir, davalıdan olan alacağını
<IBAN_1> numaralı hesabına havale yoluyla talep etmiş...
```

ID numbers, phone and IBAN were masked. **Names and address remain** —
that is what Phase 2 is for.

The library's own messages, warnings and docstrings are in Turkish,
because the input domain is Turkish text.

## Design

**Real documents are not written cleanly.** People write identity
numbers with spaces, dots, dashes; in scanned documents, OCR confuses
letters with digits. There are two tolerance layers:

```
760 487 647 54     separator tolerance
760.487.64754      separator tolerance
76O48764754        OCR repair (O → 0)
760487647S4        OCR repair (S → 5)
```

OCR repair is **a verified repair, not a guess**: a digit is substituted
for the letter and the check digit is recalculated; if it does not
pass, the candidate is dropped. That is why letter-heavy strings like
`SOSYOLOJIDE` ("in sociology") are not counted as an identity number. A
finding's `kaynak` (source) field says which route found it (`desen`,
`ayrac`, `ocr` — "pattern", "separator", "ocr") — a repaired record may
need human review.

**Types without a check digit use a context anchor.** Passport number,
date of birth and SGK registration number have no check digit to
validate against; the pattern alone produces false positives.
`01.01.2026` could be a date of birth or a contract date — what
distinguishes them is the label next to it.

```
Doğum Tarihi: 12.03.1985     →  caught
Duruşma 15.02.2026 tarihinde →  not caught
```

This is a deliberate gap: a passport number written without a label
slips through. The alternative would be treating every date in a court
text as a date of birth, which would make the output unusable.

The label is not masked, only the value: `Doğum Tarihi: <DOGUM_TARIHI_1>`
stays readable.

**A pattern alone is not enough.** The "11-digit number" pattern also
catches file numbers, amounts, date sequences. TC identity, VKN, IBAN
and card numbers have a check digit; a candidate that does not validate
is discarded. This keeps false positives at practically zero.

**Placeholders are consistent.** If the same number appears three times
in the text, all three get `<TC_1>`; different numbers get different
numbers. The masked text stays readable, and the question "is this the
same person" can still be answered.

**The output is rescanned.** Once masking is done, the text is passed
back through the detection layer. If anything is left, `SizintiHatasi`
(LeakError) is raised. A silent leak is worse than the leak itself:

```python
maskele(metin)                  # raises if the output is not clean
maskele(metin, dogrula=False)   # for tests only
```

**Reversible.** The mapping table stays local, so the text can be
restored to its original form after the processing chain. The mapping
table contains personal data; it must never be sent anywhere together
with the text.

## Model layer

Names and addresses cannot be found with a pattern. Some Turkish first
names overlap with everyday words — *Deniz* ("sea"), *Umut* ("hope"),
*Şafak* ("dawn"), *Barış* ("peace"), *Güneş* ("sun") — so a "capitalised
word" rule both misses names and catches the wrong things.

```python
from kvkk_maskeleme import maskele, OllamaSaglayici

sonuc = maskele(metin, saglayici=OllamaSaglayici())
sonuc.uydurma              # expressions the model invented that are not in the text
sonuc.model_bicim_hatasi   # set if the response is not JSON
```

If no provider is supplied, only the pattern layer runs. The interface
is a single-method protocol, so wiring it up to a different backend is
easy.

### Choosing a model

The default was picked by measurement, not by reputation. Same 21
documents, same prompt, thinking disabled, one variable — the model
(16 GB VRAM):

| Model | AD | KURUM | False positives | s/document |
|---|---|---|---|---|
| `gemma-4-abliterated:12b-qat` | 100% | 100% | 0 | 1.6 |
| `qwen3.5-abliterated:9b-q8_0` | 100% | 100% | 6 | 2.5 |
| `Qwen3.6-abliterated:35b-a3b` | 97% | 77.8% | 0 | 3.8 |

False positives are counted over 17 clean control sentences. Qwen3.5
reaches the same recall but wrongly flags 6 of them; for this tool,
polluting clean text is not an acceptable trade. Repeat the measurement
on your own hardware — the ranking depends on what fits in VRAM.

**Thinking is disabled by default, and this matters more than the model
choice.** A model left to think can fill the whole context window
without ever reaching an answer: one of the models above spent all
16384 tokens thinking and returned an empty response
(`done_reason: length`). The same prompt with thinking off answered
correctly in 1.4 seconds. The empty response is counted as a format
error rather than lost silently, but the cause is not visible from the
counter, so the default is off. The task here is not reasoning; it is
copying out an expression that is already in the text.

The context window is worth setting too. Left unset, Ollama picked 4096
on this machine, which silently truncates long documents:

```python
OllamaSaglayici(model="...", dusunme=False, baglam=8192)
```

**We do not ask the model for a position, we ask it for text.** Models
are bad at counting characters; when one says "from character 45 to 56"
it is wrong most of the time. We ask it to reproduce the expression it
found verbatim, and we locate it ourselves. Side benefit: if it returns
an expression that is not in the text, that is recognisable as a
fabrication, and it gets counted as one.

On conflict, the pattern wins — an identity number verified by its
check digit is more reliable than the model's guess that "this is a
name."

## Measurement

None of the open-source projects in this space state how well they
actually work. The sentence "masks personal data" means nothing without
a measurement; a tool running at 60% recall is a tool that does not
work.

Because synthetic documents are labelled, actual recall can be
calculated. There is also a set of court-text sentences containing no
personal data; if the dictionary layer flags one of them, it counts as
a false positive.

```python
from kvkk_maskeleme.olcum import calistir
print(calistir(20).tablo())
```

```
TANIMLAYICILAR (maskeleniyor)
tür                     beklenen  bulunan   recall
--------------------------------------------------
DOGUM_TARIHI                  20       20  100.0%
EPOSTA                        40       40  100.0%
IBAN                          40       40  100.0%
KART                          20       20  100.0%
PASAPORT                      20       20  100.0%
PLAKA                         20       20  100.0%
SGK_SICIL                     20       20  100.0%
TC                            80       80  100.0%
TELEFON                       40       40  100.0%
VKN                           60       60  100.0%

ÖZEL NİTELİKLİ (işaretleniyor)
tür                     beklenen  bulunan   recall
--------------------------------------------------
CEZA_MAHKUMIYETI              20       20  100.0%
DERNEK_VAKIF_SENDIKA          20       20  100.0%
SAGLIK                        20       20  100.0%

belge: 140
temiz metin: 17, yanlış pozitif: 0 (0.0% belgede)
```

The last line measures the cost of the generous dictionary. The clean
sentences contain known traps: *"tanık dinlenmesi"* ("hearing the
witness"), *"Aydın ili"* ("Aydın province"), *"sözleşme sağlıklı biçimde
yürütülmüştür"* ("the contract was carried out soundly"). If these get
flagged, the tool becomes unusable in a courthouse.

When no provider is supplied, names and addresses are not included in
the measurement; the pattern layer is not expected to find them anyway,
and including them would unfairly lower the result.

### With the model layer

Passing a provider adds AD, ADRES and KURUM to the measured scope. Same
140 documents, `gemma-4-abliterated:12b-qat`, thinking disabled:

```
AD                           220      220  100.0%
ADRES                         40       40  100.0%
KURUM                         60       60  100.0%

belge: 140
temiz metin: 17, yanlış pozitif: 0 (0.0% belgede)
model uydurması: 5
sure: 155.6s (1.1s/belge)
```

`model uydurması` counts expressions the model returned that do not
occur in the document. Five out of 320 model-found items were invented.
They are discarded rather than masked, because an expression that is not
in the text cannot be a position in it — but the count is reported, so
the fabrication rate of a given model is visible instead of hidden.

**Read the 100% narrowly.** The generator places names in predictable
labelled slots — *"Davacı Ahmet Yılmaz"* — and draws them from a fixed
list. That is a fair test of "can the model pick a name out of Turkish
legal prose", and no test at all of a name appearing mid-sentence
without a label, a name that is also an everyday word used as an
everyday word, or a misspelled name. It is an upper bound. This is the
same limitation the special-category measurement has, recorded in
[SONRA.md](SONRA.md): where a measurement shares vocabulary or structure
with the generator, it measures the generator as much as the tool.

## Test data

It cannot be tested with real documents — using a text containing
personal data during development would itself be the violation the tool
is trying to prevent. `sentetik.py` generates labelled documents: which
personal data is where in the text is known, which makes the detection
rate measurable.

```python
from kvkk_maskeleme.sentetik import dilekce

belge = dilekce(tohum=0)
belge.metin        # synthetic petition
belge.etiketler    # [Etiket("TC", 45, 56, "..."), ...]
```

The generated identity numbers are valid with respect to the check
digit, so they genuinely exercise the detection logic. They do not
represent anyone.

## Tests

```bash
uv run pytest
uv run ruff check .
```

## License

MIT
