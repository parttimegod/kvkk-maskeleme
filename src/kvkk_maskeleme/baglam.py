"""Pasaport, doğum tarihi ve SGK sicilini hemen önceki etiketle bulur.

Kontrol hanesi doğrulaması yapılmaz. Etiket olmadan geçen değerler
atlanır; desteklenen yazım biçimleri CIPALAR içinde tanımlıdır.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .tespit import Bulgu

# Etiket ile değer arasında iki nokta, boşluk, tire olabiliyor.
_AYIRAC = r"\s*[:\-]?\s*"

_TARIH = (
    r"\d{1,2}[./-]\d{1,2}[./-]\d{4}"
    r"|\d{1,2}\s+(?:Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|"
    r"Eylül|Ekim|Kasım|Aralık)\s+\d{4}"
)

# (tür, etiket deseni, değer deseni)
CIPALAR: list[tuple[str, str, str]] = [
    (
        "PASAPORT",
        r"pasaport(?:\s*(?:no|numaras[ıi]|seri\s*no))?",
        r"[A-Z]\s?\d{6,8}|\d{9}",
    ),
    (
        "DOGUM_TARIHI",
        r"do[ğg]um\s*tarihi|d\.?\s?t\.?",
        _TARIH,
    ),
    (
        "SGK_SICIL",
        r"sgk\s*(?:sicil|i[şs]yeri)\s*(?:no|numaras[ıi])?|sicil\s*(?:no|numaras[ıi])",
        # İşyeri sicili 26 hane, gruplar boşlukla ayrılıyor. Boşluk için
        # \s değil düz boşluk: \s satır sonunu da yutup sonraki alana
        # taşıyordu.
        r"\d[\d ]{16,38}\d",
    ),
]

_DERLENMIS = [
    (tur, re.compile(rf"({etiket}){_AYIRAC}({deger})", re.I))
    for tur, etiket, deger in CIPALAR
]


@dataclass(frozen=True)
class CipaBulgusu:
    tur: str
    baslangic: int
    bitis: int
    deger: str
    etiket: str


def bul(metin: str) -> list[CipaBulgusu]:
    """Etiketiyle birlikte geçen kişisel verileri döndürür.

    Yalnızca değerin konumu işaretleniyor; etiket metinde kalıyor.
    "Doğum Tarihi: <DOGUM_TARIHI_1>" okunabilir olmaya devam ediyor.
    """
    bulgular = []
    for tur, desen in _DERLENMIS:
        for m in desen.finditer(metin):
            deger = m.group(2).strip()
            if not deger:
                continue
            bas = m.start(2)
            bulgular.append(
                CipaBulgusu(tur, bas, bas + len(deger), deger, m.group(1).strip())
            )
    return sorted(bulgular, key=lambda b: b.baslangic)


def bulgulara_cevir(metin: str) -> list[Bulgu]:
    """Maskeleme zincirinin anlayacağı biçime çevirir."""
    return [
        Bulgu(b.tur, b.baslangic, b.bitis, b.deger, kaynak="baglam")
        for b in bul(metin)
    ]
