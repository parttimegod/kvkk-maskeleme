"""Tespit katmanı testleri.

Değerli olanlar sondaki iki tanesi: sentetik belgelerde tespit oranı ve
temiz metinde yanlış pozitif. Tespit bozulursa önce onlar kırılır.
"""

import random
from itertools import pairwise

import pytest

from turkish_anonymizer.sentetik import (
    bilirkisi_raporu,
    dilekce,
    ornekler,
    rastgele_iban,
    rastgele_tc,
    rastgele_vkn,
)
from turkish_anonymizer.tespit import bul, turlere_gore


def test_tc_bulunuyor():
    r = random.Random(0)
    no = rastgele_tc(r)
    (b,) = [x for x in bul(f"Kimlik No: {no} olan kişi") if x.tur == "TC"]
    assert b.deger == no


def test_gecersiz_onbir_haneli_sayi_tc_sayilmiyor():
    """Dosya numaraları, tutarlar, tarih dizileri hep 11 hane olabiliyor."""
    assert not [b for b in bul("Dosya sıra no 12345678901 kaydedildi") if b.tur == "TC"]


def test_vkn_bulunuyor():
    r = random.Random(1)
    no = rastgele_vkn(r)
    assert any(b.deger == no for b in bul(f"Vergi no {no}"))


def test_iban_bulunuyor():
    r = random.Random(2)
    iban = rastgele_iban(r)
    (b,) = [x for x in bul(f"Hesap: {iban}") if x.tur == "IBAN"]
    assert b.deger == iban


@pytest.mark.parametrize(
    "metin, tur",
    [
        ("Telefon: 0532 123 45 67", "TELEFON"),
        ("Tel +90 532 123 45 67 numarasından", "TELEFON"),
        ("E-posta: ornek.kisi@firma.com.tr", "EPOSTA"),
        ("Araç 07 ABC 123 plakalı", "PLAKA"),
    ],
)
def test_diger_turler(metin, tur):
    assert any(b.tur == tur for b in bul(metin))


def test_iban_icindeki_rakamlar_tc_sanilmıyor():
    r = random.Random(3)
    iban = rastgele_iban(r)
    turler = {b.tur for b in bul(f"IBAN: {iban}")}
    assert turler == {"IBAN"}


def test_ayni_deger_her_gecisinde_bulunuyor():
    r = random.Random(4)
    no = rastgele_tc(r)
    bulgular = [b for b in bul(f"{no} ve tekrar {no}") if b.tur == "TC"]
    assert len(bulgular) == 2


def test_bulgular_konum_sirasinda():
    b = bul(dilekce(0).metin)
    assert b == sorted(b, key=lambda x: x.baslangic)


def test_bulgular_cakismiyor():
    b = bul(dilekce(1).metin)
    for onceki, sonraki in pairwise(b):
        assert onceki.bitis <= sonraki.baslangic


def test_temiz_metinde_yanlis_pozitif_yok():
    metin = (
        "Mahkeme 2026 yılında toplandı. Dosya 15 sayfa olup, karar 3 gün "
        "içinde tebliğ edilecektir. Duruşma saat 09:30'da başlayacaktır. "
        "Toplam tutar 1.250.000 TL olarak hesaplanmıştır."
    )
    assert bul(metin) == []


def test_dilekcede_yapisal_veriler_yakalaniyor():
    belge = dilekce(7)
    bulunan = turlere_gore(belge.metin)

    for tur in ("TC", "IBAN", "TELEFON"):
        assert tur in bulunan, f"{tur} bulunamadı"


def test_sentetik_kumede_yapisal_recall_tam():
    """Deterministik katman yapısal kimliklerin tamamını bulmalı.

    İsim ve adres bu katmanın işi değil, o yüzden ölçümden çıkarıldı.
    """
    yapisal = {"TC", "VKN", "IBAN", "TELEFON", "PLAKA"}
    beklenen = kacan = 0

    for belge in ornekler(10):
        bulunan = {(b.tur, b.deger) for b in bul(belge.metin)}
        for e in belge.etiketler:
            if e.tur not in yapisal:
                continue
            beklenen += 1
            if (e.tur, e.deger) not in bulunan:
                kacan += 1

    assert beklenen > 0
    assert kacan == 0, f"{beklenen} yapısal veriden {kacan} tanesi kaçtı"


def test_bilirkisi_raporunda_plaka_ve_vkn():
    bulunan = turlere_gore(bilirkisi_raporu(3).metin)
    assert "PLAKA" in bulunan
    assert "VKN" in bulunan
