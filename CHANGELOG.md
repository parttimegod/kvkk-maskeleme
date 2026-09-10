# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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
