# Detection and replacement

The pattern layer proposes spans, then validates TC, VKN, IBAN and card
candidates with their check digits. Other types use patterns or field
labels. Longer overlapping spans win; the type priority breaks length
ties. This avoids treating part of an IBAN as a separate identifier.

The optional model receives the document and returns type/value pairs.
The parser finds every occurrence of each value in the original text.
This keeps character positions under code control and makes absent values
easy to discard. It can also mark an ordinary use of a word that happens
to match a returned name.

Pattern findings take precedence over overlapping model findings. A
model address that overlaps a pattern finding can therefore be discarded
as a whole. Remaining model findings are accepted in response order when
they overlap one another.

## Heuristics

`soyadi_yay` takes the final word of a full-name finding and searches other
occurrences in a diacritic-folded copy of the document. The fold preserves
length and case so positions still address the original text. Some
province/district suffixes are excluded. This reduces missed bare surnames,
but does not resolve whether every matching word denotes that person.

`adresi_genislet` extends an address through an immediately following
numbered street, door, floor or apartment chain. Named streets, different
punctuation and other address forms can fall outside that pattern.

## Replacement and restore

A dictionary keyed by type and exact value assigns consistent placeholders.
Existing placeholder tokens are reserved before numbering begins.
Replacements run from right to left to preserve the original span offsets.

`geri_al` replaces map keys in one pass. Restored values are not processed
again, even if they contain another placeholder. This round trip applies
to an unmodified result and its matching map; editing or combining masked
documents needs its own handling.

Output verification calls the same pattern detector without a model.
It checks for recognisable remaining patterns, not for all personal data.
A second model call would still need evaluation rather than providing an
independent safety guarantee.
