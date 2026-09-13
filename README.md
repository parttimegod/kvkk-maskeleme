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

Both layers work. The pattern layer finds identifiers that carry a check
digit or a context label. The model layer finds names, addresses and
institutions, which no pattern can find.

| Type | Status | Method | Recall |
|---|---|---|---|
| TC identity number | ✓ | pattern + check digit | 100% |
| Tax identification number | ✓ | pattern + check digit | 100% |
| IBAN | ✓ | pattern + mod-97 | 100% |
| Card number | ✓ | pattern + Luhn | 100% |
| Phone | ✓ | pattern | 100% |
| Number plate | ✓ | pattern | 100% |
| Email | ✓ | pattern | 100% |
| Passport number | ✓ | context anchor | 100% |
| Date of birth | ✓ | context anchor | 100% |
| SGK registration number | ✓ | context anchor | 100% |
| **Name** | ✓ | model + surname propagation + diacritic folding | 99.6% |
| **Address** | ✓ | model + address extension | 100% |
| **Institution** | ✓ | model | 100% |

Measured over 220 generated documents, with 0 false positives on 30
clean control sentences. Address recall is now measured against
addresses written in unlabelled prose, not only in a predictable
labelled slot — see [Measurement](#measurement) for what that took. The
model layer is optional: without a provider, only the pattern layer
runs and the last three rows are not attempted. Read
[Measurement](#measurement) before trusting these numbers — it says
what they do and do not cover.

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

Recall is scored by exact `(type, value)` match against the labelled
span, not by whether a finding merely overlaps it. The difference is
not academic: a model that returns only "Kızılay Mahallesi" out of a
longer labelled address *does* overlap the label, so a span-overlap
metric would count it as found, while the masked output still leaks the
street and door number in the clear. Exact-match scoring counts that as
a miss, which is what it actually is. See [Address
extension](#address-extension-adresi_genislet) below for the case that
made the difference concrete.

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
TC                           100      100  100.0%
TELEFON                       40       40  100.0%
VKN                           60       60  100.0%

ÖZEL NİTELİKLİ (işaretleniyor)
tür                     beklenen  bulunan   recall
--------------------------------------------------
CEZA_MAHKUMIYETI              20       20  100.0%
DERNEK_VAKIF_SENDIKA          20       20  100.0%
GENETIK                       20       20  100.0%
SAGLIK                        40       40  100.0%

belge: 220
temiz metin: 30, yanlış pozitif: 0 (0.0% belgede)
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

Passing a provider adds AD, ADRES and KURUM to the measured scope. Final
run, 220 documents (11 types × 20), `gemma-4-abliterated:12b-qat`,
thinking disabled, context window 8192:

```
AD                             520      518   99.6%
ADRES                          160      160  100.0%
KURUM                           60       60  100.0%
TC                              100     100  100.0%

CEZA_MAHKUMIYETI                 20       20  100.0%
DERNEK_VAKIF_SENDIKA             20       20  100.0%
GENETIK                          20       20  100.0%
SAGLIK                           40       40  100.0%

belge: 220
temiz metin: 30, yanlış pozitif: 0 (0.0% belgede)
model uydurması: 5
sure: 327.2s (1.5s/belge)
```

TC and every other pattern-based identifier type also held at 100%,
unchanged from the pattern layer — the rows above are the ones that
depend on the model, or, for ADRES, on `zor_adres` and
`adresi_genislet` being wired into the sample for the first time (see
[Address extension](#address-extension-adresi_genislet), below).

`model uydurması` counts expressions the model returned that do not
occur in the document. Five model-found items were invented this run.
They are discarded rather than masked, because an expression that is not
in the text cannot be a position in it — but the count is reported, so
the fabrication rate of a given model is visible instead of hidden.

**This measurement is not bit-reproducible.** At temperature 0, repeated
runs over the same documents still differ by a couple of names — well
under one percent, but not zero. Recall is therefore quoted to one
decimal place at most; a second decimal would be false precision.

**The 100% in 0.2.0 was an upper bound, and here is what closing it
took.** The generator originally placed every name in a predictable
labelled slot — *"Davacı Ahmet Yılmaz"* — drawn from a fixed list. That
is a fair test of "can the model pick a name out of a labelled slot",
and no test at all of a name appearing mid-sentence without a label, a
name that is also an everyday word, or a misspelled name. Making the
generator harder (`zor_metin`: names in unlabelled prose, case-inflected
names, bare surnames, names that double as everyday words) dropped AD
recall to 96.7%. Every miss had the same shape: a person named once in
full and then referred to later by surname alone — *"Güneş Yıldız'ın
beyanı alınmış... dinlenen Yıldız, beyanında..."* — concentrated on
surnames that are also ordinary Turkish words (Aydın, Kaya, Yıldız,
Aslan, Arslan, Öztürk, Yıldırım). Surname propagation (`soyadi_yay`, see
below) closed that specific gap deterministically, bringing recall to
99.5%.

ADRES carried the exact same weakness going into this release: every
address in the generator sat in a predictable labelled slot, so its
100% was the same kind of upper bound AD's had been. This release
closes that gap the same way — `zor_adres` puts addresses in unlabelled
prose (address-word after the address, a full administrative chain, a
bare neighbourhood name, no address-word anywhere nearby) — and the
progression looks the same shape as AD's did:

| generator | ADRES recall |
|---|---|
| labelled slots only | 100% |
| with `zor_adres` (unlabelled prose) | 96.4% |
| + `adresi_genislet` | 100% |

Closing it took a second piece, `adresi_genislet` — see [Address
extension](#address-extension-adresi_genislet), below, for what the
drop actually looked like and why it was worse than a plain miss.

OCR-damaged names and addresses are now covered too — see [OCR
damage](#ocr-damage-bozuk_metin), below. What remains open: glyph-confusion
damage inside a bare surname (a later reference reading "K1llc", say) —
diacritic folding does not repair this, because there is no diacritic
there to fold back, only a confused glyph — and entity resolution: the
same person appearing as "Deniz Çelik" in one place and "Çelik" in
another gets two different placeholders. That is a readability cost,
not a leak; both spans are still masked. This is also the same class of
limitation the special-category measurement has, recorded in
[SONRA.md](SONRA.md): where a measurement shares vocabulary or
structure with the generator, it measures the generator as much as the
tool.

### Surname propagation (`soyadi_yay`)

A Turkish court document typically names a person once in full and then
refers back to them by surname alone: *"Güneş Yıldız'ın beyanı
alınmış... aynı celsede dinlenen Yıldız, beyanında..."*. The model
reliably finds the first mention and just as reliably misses the bare
surname later — in the 180-document measurement, every single AD miss
had exactly this shape.

This is handled deterministically instead of by asking the model to try
harder: once a full name (`Ad Soyad`) has been found somewhere in the
document, every other bare occurrence of that surname in the same
document is masked too, carrying `kaynak="soyad"` so it stays
distinguishable from a direct model finding (`kaynak="model"`). A bare
`Yıldız` could be a surname or could be weather; asking the model to
guess would reintroduce exactly the kind of unverified guess the
identifier layer avoids by using check digits. Once the full name has
already been confirmed once in the same document, propagating it to its
bare occurrences is a deterministic fact about that document, not a
guess.

The one guard needed: `Aydın` is both a common surname and a province
name, and adliye metni is full of place references — *"Aydın ili"*,
*"Aydın ilinde bulunan taşınmaz"*. `soyadi_yay` skips a candidate
immediately followed by `ili`, `ilinde`, `iline`, `ilinden`, `ilçesi` or
`ilçesinde`, so "Aydın ili" is not masked as if Aydın were a person.

### Address extension (`adresi_genislet`)

The five ADRES misses `zor_adres` turned up were not misses. They were
**half-masked**. Given *"Tebligat Kızılay Mahallesi 28. Cadde No: 20
numarasına yapılmıştır"* — an address with no address-word ("adresinde",
"adres") anywhere near it — the model returned only the neighbourhood,
`"Kızılay Mahallesi"`, out of the full address. Masking that finding as-is
produces:

```
Tebligat <ADRES_1> 28. Cadde No: 20 numarasına yapılmıştır.
```

The street and the door number are still sitting there in the clear.
All five misses had the same shape: no address-word nearby to tell the
model where the address ended, so it stopped at the first thing that
looked complete on its own.

This is worse than a plain miss, because the output *looks* masked.
It is why `olcum.py` scores recall by exact `(type, value)` match
instead of asking "does a finding overlap the labelled span?" — the
overlap question would have scored `"Kızılay Mahallesi"` as found,
because it does overlap the labelled address. The exact-match metric is
stricter, and the strictness is what caught this: a lenient span-overlap
metric would have hidden a live leak behind a passing number.

`adresi_genislet` runs after the model layer and extends an ADRES
finding through whatever street/number/floor chain immediately follows
it — `N. Cadde`, `N. Sokak`, `No: N`, `Kat`/`Daire`/`Blok N` — and
leaves the finding untouched when what follows is not such a chain, so
*"Bahçelievler Mahallesi'nde ikamet etmektedir"* is not over-extended
into the next sentence.

### OCR damage (`bozuk_metin`)

The first OCR measurement read AD 99.6%, and that number was worthless.
The generator gave the model two free cues: the document's own prose
explained the damage — *"tarama sırasında Türkçe karakterlerin düştüğü
tespit edilmiştir"* ("the scan is found to have dropped Turkish
characters") — and a real scan does not narrate its own damage; and
only the names were damaged while the surrounding text stayed clean, so
the damage itself became the signal that a name was there. A real scan
damages everything uniformly.

Removing both cues dropped AD to 91.9% — 40 misses out of 160 damaged
labels. All 40 were exactly two values: "Sahin" and "Öztürk", 20 each.
These are the mixed-damage anaphora cases: a full name appears clean
and the later bare surname is damaged, or the reverse. `soyadi_yay`
matched substrings exactly, so it could not connect "Şahin" to "Sahin".
The model itself found every damaged name it was asked to find —
"Ayse Yildirim", "Mustafa K1llc", "IBRAHIM SAHIN", and the damaged
address. The failure was in the code around the model, not the model.

`soyadi_yay` now searches a diacritic-folded copy of the text. Case is
deliberately not folded: a person surnamed Aslan can appear in a
document that also says "aslan gibi" ("like a lion"), and case-folding
would mask the common noun. The fold is length-preserving so positions
stay valid in the original text, and the recorded value is the string
as it appears in the document, not the folded form.

Final: AD back to 99.6% — the same number as the first measurement, now
meaning something.

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
