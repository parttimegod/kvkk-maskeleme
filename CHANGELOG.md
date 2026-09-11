# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.3.0] - 2026-09-11

AD (name) recall went 100% → 96.7% → 99.5% across this release. The
100% was worse than the 99.5% despite being the higher number, because
it was measured against a generator that only ever placed names in
predictable labelled slots — a fair test of reading a label off a
document, not of finding a name that isn't wearing one.

### Added

- `zor_metin`, a synthetic-document generator that places names in
  unlabelled prose: bare surnames, case-inflected names, names that are
  also everyday Turkish words, and names not anchored to a role label.
  Six new trap sentences in `TEMIZ_CUMLELER` covering the same
  everyday-word names used as ordinary words (deniz, umut, şafak, barış,
  güneş).
- `soyadi_yay`, which deterministically propagates a person's surname to
  its later bare occurrences once their full name has been found
  elsewhere in the same document — with a guard so "Aydın ili" (a
  province) is not masked as if Aydın were a person.
- `test_butun_ureticiler_ornekleme_giriyor`, a guard test asserting
  every synthetic-document generator function is actually wired into
  `ornekler()`, so a generator that is defined but never sampled fails
  the test suite instead of silently going unmeasured.

### Changed

- Model-found records now carry `kaynak="model"` instead of the
  incorrect `kaynak="desen"`; records added by surname propagation carry
  `kaynak="soyad"`.
- `ornekler()` now generates nine document types instead of eight
  (`saglik_raporu` added), 180 documents at the default sample size.

### Fixed

- `saglik_raporu` was defined but never included in `ornekler()`, so the
  GENETIK special category was never exercised by measurement — the
  measurement table looked complete while an entire row was silently
  absent.

## [0.2.0] - 2026-09-11

### Added

- `OllamaSaglayici` gained `dusunme` (thinking on/off, default off) and
  `baglam` (context window size) parameters. A model left thinking can
  consume the entire context window without ever producing an answer —
  measured: 16384 tokens all spent thinking, `done_reason: length`, empty
  response; the same prompt with thinking off answered correctly in 1.4
  seconds. Left unset, Ollama's default context window on the measurement
  machine was 4096, which silently truncates long documents.
- Full measurement of the model layer over 140 synthetic documents: AD
  220/220, ADRES 40/40, KURUM 60/60, all 100% — an upper bound, since the
  generator places names in predictable labelled slots drawn from a fixed
  list.

### Changed

- `OllamaSaglayici`'s default model changed from the non-existent
  `gemma4-abl-16k` to `huihui_ai/gemma-4-abliterated:12b-qat`, picked by
  measuring three models on the same 21 documents and prompt with thinking
  disabled:

  | model | AD | KURUM | false positives (of 17 clean) | s/document |
  |---|---|---|---|---|
  | gemma-4-abliterated:12b-qat | 100% | 100% | 0 | 1.6 |
  | qwen3.5-abliterated:9b-q8_0 | 100% | 100% | 6 | 2.5 |
  | Qwen3.6-abliterated:35b-a3b | 97% | 77.8% | 0 | 3.8 |

### Fixed

- The Ollama 404 path (model not installed) reported "cannot reach
  Ollama", the same message as an unreachable service, sending users to
  check the wrong thing.

## [0.1.1] - 2026-09-10

### Fixed

- The `saglik` stem added in 0.1.0 matched `sağlıklı` ("sound", "properly"),
  which is common in Turkish legal prose — "sözleşme sağlıklı biçimde
  yürütülmüştür" was reported as health data. `saglik` and `hasta` now
  require a whole-word match, following the existing `din` / `dinlenme`
  precedent. A separate `sagligi` stem keeps the inflected forms
  ("sağlığı", "sağlığının") that whole-word matching would otherwise lose
  to k/ğ softening.
- Added the affected phrasings to the clean-sentence guard so the
  regression cannot come back unnoticed.

## [0.1.0] - 2026-09-10

### Added

- Structural identifier detection and masking for TC kimlik no, vergi kimlik
  no (VKN), IBAN, and card number, each validated with its check digit.
- Pattern-based detection for phone number, plate number, and e-mail.
- Context-anchored detection for passport number, date of birth, and SGK
  registry number, which have no check digit and rely on the preceding
  label instead of the pattern alone.
- Separator and OCR tolerance for TC, VKN, and IBAN numbers (e.g.
  `760 487 647 54`, `76O48764754`), with the check digit re-validated after
  repair so a correction is never a guess.
- Reversible masking: consistent placeholders (`<TC_1>`, ...), a local
  mapping table, and `geri_al` to restore the original text.
- Re-scan of masked output (`SizintiHatasi`) so a residual leak fails
  loudly instead of shipping silently.
- Special-category personal data detection (KVKK md. 6): a dictionary
  layer flags health, criminal record, union/association membership,
  religion, ethnicity, biometric, genetic, and other special-category
  content without attempting to mask it, since the sentence itself is the
  data.
- Optional model layer (`Saglayici` protocol, `OllamaSaglayici`) that adds
  name and address detection and contextual special-category findings on
  top of the pattern layer; model output not found verbatim in the source
  text is treated as a hallucination and discarded.
- Synthetic, labeled Turkish court-document generator (`sentetik.py`)
  across seven document types, used to measure recall and false-positive
  rate without using real personal data.
- Recall and false-positive measurement (`olcum.py`) for both identifier
  types and special categories.
- Independent test suite (`test_ozel_nitelikli_bagimsiz.py`) for
  special-category detection, written apart from `sentetik.py`'s
  vocabulary.
- Command-line interface: file or stdin input, `-o` file output,
  `--esleme` mapping export (opt-in, with an explicit warning),
  `--sadece-incele`, `--kati` exit code, `--json` report.
- Zero-install usage via `uvx --from git+...`.
- README walkthrough of the CLI against a realistic court document.

### Fixed

- stdout/stderr were not forced to UTF-8, so redirecting output on Windows
  (`kvkk-maskeleme dosya.txt > cikti.txt`) inherited the console code page
  and corrupted Turkish characters, even though file input and `-o` file
  output were already explicit UTF-8.
- The SAGLIK dictionary was missing the bare "sağlık" stem, so the most
  common Turkish court-document health phrase, "sağlık raporu", was not
  flagged as special-category data.

### Changed

- Renamed the package from `turkish_anonymizer` to `kvkk-maskeleme` to
  match its actual legal scope.
- Documented that measured recall for special-category detection is an
  upper bound: `olcum.py` measures it against `sentetik.py`'s own
  generated sentences, which share vocabulary with the detection
  dictionary rather than being independent of it.
