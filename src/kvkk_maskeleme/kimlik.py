"""Kimlik numarası doğrulama.

Bu modül olmadan araç regex oyuncağı olur. 11 haneli her sayı TC kimlik
numarası değil; doğrulama yapmadan maskelemek iki yönde de hata üretir:
telefon numarasını kimlik sanıp maskelersin, ya da dosya numarasını
maskeleyip metni bozarsın.

Algoritmalar kontrol hanesi üzerine kurulu, yani rastgele bir sayının
geçerli çıkma olasılığı %1 civarı. Bu, yanlış pozitifi pratikte
sıfırlıyor.
"""

from __future__ import annotations

import re

_SADECE_RAKAM = re.compile(r"\D")

# IBAN'da harfler sayıya çevriliyor: A=10, B=11, ... Z=35
_HARF_DEGERI = {chr(ord("A") + i): str(10 + i) for i in range(26)}


def _rakamlar(metin: str) -> str:
    return _SADECE_RAKAM.sub("", metin)


def tc_kontrol_haneleri(ilk_dokuz: str) -> str:
    """İlk dokuz haneden son iki haneyi hesaplar.

    10. hane: tek konumların toplamı × 7, eksi çift konumların toplamı,
    mod 10. 11. hane: ilk on hanenin toplamı mod 10.
    """
    if len(ilk_dokuz) != 9 or not ilk_dokuz.isdigit():
        raise ValueError("İlk dokuz hane rakam olmalı.")

    d = [int(c) for c in ilk_dokuz]
    tek = d[0] + d[2] + d[4] + d[6] + d[8]
    cift = d[1] + d[3] + d[5] + d[7]
    onuncu = (tek * 7 - cift) % 10
    onbirinci = (sum(d) + onuncu) % 10
    return f"{onuncu}{onbirinci}"


def tc_kimlik_gecerli(no: str) -> bool:
    no = _rakamlar(no)
    if len(no) != 11 or no[0] == "0":
        return False
    return tc_kontrol_haneleri(no[:9]) == no[9:]


def vkn_kontrol_hanesi(ilk_dokuz: str) -> str:
    """Vergi kimlik numarasının 10. hanesi.

    Her hane konumuna göre kaydırılıp ikinin kuvvetiyle çarpılıyor;
    TC kimlikten tamamen farklı bir şema.
    """
    if len(ilk_dokuz) != 9 or not ilk_dokuz.isdigit():
        raise ValueError("İlk dokuz hane rakam olmalı.")

    toplam = 0
    for i, c in enumerate(ilk_dokuz):
        rakam = (int(c) + 9 - i) % 10
        if rakam == 9:
            toplam += rakam
        else:
            toplam += (rakam * 2 ** (9 - i)) % 9
    return str((10 - toplam % 10) % 10)


def vkn_gecerli(no: str) -> bool:
    no = _rakamlar(no)
    if len(no) != 10:
        return False
    return vkn_kontrol_hanesi(no[:9]) == no[9]


def iban_gecerli(iban: str) -> bool:
    """ISO 13616 mod-97 kontrolü.

    Türkiye IBAN'ı 26 karakter ama kontrol ülkeden bağımsız çalışıyor;
    ülke uzunluğunu ayrıca sınırlamıyoruz ki yabancı IBAN da yakalansın.
    """
    iban = re.sub(r"\s", "", iban).upper()
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{10,30}", iban):
        return False

    # İlk dört karakter sona taşınıyor, sonra harfler sayıya çevriliyor.
    tasinmis = iban[4:] + iban[:4]
    sayi = "".join(_HARF_DEGERI.get(c, c) for c in tasinmis)
    if not sayi.isdigit():
        return False
    return int(sayi) % 97 == 1


def luhn_gecerli(no: str) -> bool:
    """Kredi kartı numarası. Kart numarasını asla saklamıyoruz, sadece
    metinde tespit edip maskelemek için."""
    no = _rakamlar(no)
    if not 13 <= len(no) <= 19:
        return False

    toplam = 0
    for i, c in enumerate(reversed(no)):
        d = int(c)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        toplam += d
    return toplam % 10 == 0
