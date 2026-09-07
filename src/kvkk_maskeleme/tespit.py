"""Deterministik tespit katmanı.

Yapısal kimlikleri bulur: TC kimlik, VKN, IBAN, telefon, plaka, e-posta,
kart numarası. Hepsi desen + doğrulama ikilisiyle çalışıyor.

Doğrulama olmadan desen tek başına işe yaramaz. "11 haneli sayı" deseni
dosya numarasını, tarih dizisini, tutar alanını da yakalar. Kontrol
hanesi bunları eler.

Gerçek belgeler temiz yazılmıyor. İnsanlar kimlik numarasını boşlukla,
noktayla, tireyle yazıyor; taranmış belgelerde OCR harfle rakamı
karıştırıyor. Bu yüzden iki tolerans katmanı var:

- Ayraç toleransı: rakamlar arasındaki tek boşluk/nokta/tire yok sayılır.
- OCR onarımı: harfe benzeyen rakamlar (O/0, l/1, S/5) denenir, ama
  onarılmış hâl kontrol hanesinden geçmezse kabul edilmez. Tahmin değil,
  doğrulanmış onarım.

İsim ve adres burada YOK. Onlar desenle bulunamıyor, model katmanının
işi -- bkz. model.py
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
    kaynak: str = "desen"  # "desen", "ayrac" ya da "ocr"

    def __len__(self) -> int:
        return self.bitis - self.baslangic


# Rakamlar arasında tek ayraca izin veriyoruz. Doğrulayıcı zaten ayraçları
# atıyor, o yüzden desen gevşek olabilir.
_AYRAC = r"[ .\-]?"

_DESENLER: list[tuple[str, re.Pattern[str]]] = [
    ("IBAN", re.compile(
        rf"\bTR{_AYRAC}\d{{2}}(?:{_AYRAC}\d{{4}}){{5}}{_AYRAC}\d{{2}}\b", re.I
    )),
    ("EPOSTA", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]{2,}\b")),
    ("TELEFON", re.compile(
        r"(?:\+90[\s-]?|0)\(?5\d{2}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}\b"
    )),
    ("PLAKA", re.compile(r"\b(?:0[1-9]|[1-7]\d|8[01])[\s-]?[A-Z]{1,3}[\s-]?\d{2,4}\b")),
    ("KART", re.compile(r"\b(?:\d{4}[\s-]?){3}\d{4}\b")),
    ("TC", re.compile(rf"\b[1-9](?:{_AYRAC}\d){{10}}\b")),
    ("VKN", re.compile(rf"\b\d(?:{_AYRAC}\d){{9}}\b")),
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

# Taranmış belgelerde harfe dönüşen rakamlar. Her harf tek bir rakama
# karşılık geliyor, yani onarım belirsiz değil.
_OCR_KARSILIK = {
    "O": "0", "o": "0", "D": "0",
    "l": "1", "I": "1", "i": "1", "|": "1",
    "S": "5", "s": "5",
    "B": "8", "G": "6",
    "Z": "2", "z": "2",
}
_OCR_HARF = "".join(_OCR_KARSILIK)

# OCR adayı: rakam ve karışabilen harflerden oluşan diziler.
_OCR_DESENLER = {
    "TC": re.compile(rf"\b[0-9{_OCR_HARF}]{{11}}\b"),
    "VKN": re.compile(rf"\b[0-9{_OCR_HARF}]{{10}}\b"),
}

# Bir adayın çoğunluğu gerçekten rakam olmalı; yoksa sıradan kelimeleri
# rakama çevirip uydurma kimlik üretiriz.
_ASGARI_RAKAM_ORANI = 0.6


def _ocr_onar(aday: str) -> str:
    return "".join(_OCR_KARSILIK.get(c, c) for c in aday)


def _yeterince_rakam(aday: str) -> bool:
    rakam = sum(c.isdigit() for c in aday)
    return rakam / len(aday) >= _ASGARI_RAKAM_ORANI


def _cakisiyor(a: Bulgu, b: Bulgu) -> bool:
    return a.baslangic < b.bitis and b.baslangic < a.bitis


def _desenle_bul(metin: str) -> list[Bulgu]:
    adaylar: list[Bulgu] = []
    for tur, desen in _DESENLER:
        for m in desen.finditer(metin):
            deger = m.group()
            dogrula = _DOGRULAYICI.get(tur)
            if dogrula and not dogrula(deger):
                continue
            ayracli = bool(re.search(r"[ .\-]", deger)) and tur in _DOGRULAYICI
            kaynak = "ayrac" if ayracli else "desen"
            adaylar.append(Bulgu(tur, m.start(), m.end(), deger, kaynak))
    return adaylar


def _ocr_ile_bul(metin: str) -> list[Bulgu]:
    """Yalnızca onarıldıktan sonra doğrulanan adayları döndürür."""
    adaylar: list[Bulgu] = []
    for tur, desen in _OCR_DESENLER.items():
        dogrula = _DOGRULAYICI[tur]
        for m in desen.finditer(metin):
            ham = m.group()
            if ham.isdigit() or not _yeterince_rakam(ham):
                continue
            onarilmis = _ocr_onar(ham)
            if onarilmis.isdigit() and dogrula(onarilmis):
                adaylar.append(Bulgu(tur, m.start(), m.end(), ham, "ocr"))
    return adaylar


def bul(metin: str, ocr_onarimi: bool = True) -> list[Bulgu]:
    """Metindeki yapısal kişisel verileri konumlarıyla döndürür.

    ocr_onarimi=False ile onarım kapatılabilir; taranmamış, temiz
    kaynaklarda gereksiz iş yapmamak için.
    """
    adaylar = _desenle_bul(metin)
    if ocr_onarimi:
        adaylar += _ocr_ile_bul(metin)

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
