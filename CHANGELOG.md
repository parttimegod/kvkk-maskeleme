# Changelog

## Unreleased

- Added the optional local HTTP adapter with character and body limits,
  category flags, generic handled errors and no restore map in responses.
- Identifier recall now requires exact type, position and value matches.
  The previous type/value rule could credit missed repeated occurrences.
  Historical model scores below were not rerun under this rule.
- Placeholder allocation reserves tokens already present in the input.
  Restore replaces keys in one pass to avoid processing restored values.
- Rewrote usage, design and measurement notes around the detector's tested
  scope and known misses.

## [0.5.0] - 2026-09-13

- Added document-wide simulated OCR damage, including diacritic loss and
  some glyph confusions, without prose announcing the damage.
- Surname propagation now searches a length-preserving diacritic fold
  while retaining case. This connects `Şahin` and `Sahin` without also
  matching lowercase common nouns.
- Added OCR control sentences. Bare-surname glyph confusion remains open.

## [0.4.0] - 2026-09-13

- Added addresses in unlabelled prose to the generator, including
  administrative chains and neighbourhood-only mentions.
- Added address extension through a following street/door/floor chain
  when a model returns only the neighbourhood.
- Corrected province/district pairings in generated addresses.

## [0.3.0] - 2026-09-11

- Added unlabelled names, inflections, bare surnames and everyday-word
  name controls.
- Added surname propagation with exclusions for some place suffixes.
- Findings distinguish model, surname and pattern sources.
- Included the previously omitted health-report generator in sampling.

## [0.2.0] - 2026-09-11

- Added Ollama thinking and context-window options.
- Changed the default tag to `huihui_ai/gemma-4-abliterated:12b-qat`.
- Distinguished an installed-server/missing-model HTTP 404 from a
  connection failure.

Earlier development notes reported local model comparisons and successive
recall figures, ending at AD 518/520, ADRES 160/160 and KURUM 60/60.
Those used generated templates and the older type/value scoring rule.
See [MEASUREMENT.md](MEASUREMENT.md) for how the current evaluation differs;
the old runs are not an independent accuracy estimate.

## [0.1.1] - 2026-09-10

- Required whole-word matches for `saglik` and `hasta` to avoid flagging
  ordinary phrases such as `sağlıklı biçimde`.
- Added separate inflected health stems and clean-sentence regression cases.

## [0.1.0] - 2026-09-10

- Added pattern/check-digit detection for TC, VKN, IBAN and cards;
  patterns for mobile phone, plate and email; field-label detection for
  passport, birth date and SGK.
- Added separator tolerance and limited check-digit-tested OCR repair.
- Added reversible placeholders, pattern rescanning and optional mapping
  export.
- Added dictionary category flags and an optional model provider for
  names, addresses, organisations and contextual flags.
- Added labelled generated court-document templates and a measurement
  report. Clean-control false positives cover category flags only.
- Added independent category examples, including known misses.
- Added the CLI with UTF-8 file and stream handling.
- Renamed the package from `turkish_anonymizer` to `kvkk-maskeleme`.
