"""Deterministik tespit katmanı.

Yapısal kimlikleri bulur: TC kimlik, VKN, IBAN, telefon, plaka, e-posta,
kart numarası. Hepsi desen + doğrulama ikilisiyle çalışıyor.

Doğrulama olmadan desen tek başına işe yaramaz. "11 haneli sayı" deseni
dosya numarasını, tarih dizisini, tutar alanını da yakalar. Kontrol
hanesi bunları eler.

İsim ve adres burada YOK. Onlar desenle bulunamıyor, model katmanının
işi -- bkz. SONRA.md
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .kimlik import iban_gecerli, luhn_gecerli, tc_kimlik_gecerli, vkn_gecerli


@dataclass(frozen=True)
class Bulgu:
    tur: str
    baslangic: int
    bitis: int
    deger: str

    def __len__(self) -> int:
        return self.bitis - self.baslangic


# Aday desenler geniş tutuluyor; eleme işini doğrulayıcılar yapıyor.
_DESENLER: list[tuple[str, re.Pattern[str]]] = [
    ("IBAN", re.compile(r"\bTR\d{2}[\s]?(?:\d{4}[\s]?){5}\d{2}\b", re.I)),
    ("EPOSTA", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]{2,}\b")),
    ("TELEFON", re.compile(
        r"(?:\+90[\s-]?|0)\(?5\d{2}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}\b"
    )),
    ("PLAKA", re.compile(r"\b(?:0[1-9]|[1-7]\d|8[01])[\s-]?[A-Z]{1,3}[\s-]?\d{2,4}\b")),
    ("KART", re.compile(r"\b(?:\d{4}[\s-]?){3}\d{4}\b")),
    ("TC", re.compile(r"\b[1-9]\d{10}\b")),
    ("VKN", re.compile(r"\b\d{10}\b")),
]

_DOGRULAYICI = {
    "TC": tc_kimlik_gecerli,
    "VKN": vkn_gecerli,
    "IBAN": iban_gecerli,
    "KART": luhn_gecerli,
}

# Çakışmada hangisi kazanır. IBAN içinde TC gibi görünen diziler olabiliyor.
_ONCELIK = {
    "IBAN": 0, "EPOSTA": 1, "KART": 2, "TELEFON": 3,
    "TC": 4, "VKN": 5, "PLAKA": 6,
}


def _cakisiyor(a: Bulgu, b: Bulgu) -> bool:
    return a.baslangic < b.bitis and b.baslangic < a.bitis


def bul(metin: str) -> list[Bulgu]:
    """Metindeki yapısal kişisel verileri konumlarıyla döndürür."""
    adaylar: list[Bulgu] = []
    for tur, desen in _DESENLER:
        for m in desen.finditer(metin):
            deger = m.group()
            dogrula = _DOGRULAYICI.get(tur)
            if dogrula and not dogrula(deger):
                continue
            adaylar.append(Bulgu(tur, m.start(), m.end(), deger))

    # Uzun ve yüksek öncelikli olan kazanıyor; kalanlar eleniyor.
    adaylar.sort(key=lambda b: (-len(b), _ONCELIK[b.tur], b.baslangic))
    secilen: list[Bulgu] = []
    for aday in adaylar:
        if not any(_cakisiyor(aday, s) for s in secilen):
            secilen.append(aday)

    return sorted(secilen, key=lambda b: b.baslangic)


def turlere_gore(metin: str) -> dict[str, list[str]]:
    """Tespit özetini tür başına gruplar. Hata ayıklama için."""
    sonuc: dict[str, list[str]] = {}
    for b in bul(metin):
        sonuc.setdefault(b.tur, []).append(b.deger)
    return sonuc
