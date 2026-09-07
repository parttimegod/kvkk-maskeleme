"""Tespit katmanı testleri.

Değerli olanlar sondaki iki tanesi: sentetik belgelerde tespit oranı ve
temiz metinde yanlış pozitif. Tespit bozulursa önce onlar kırılır.
"""

import random
from itertools import pairwise

import pytest

from kvkk_maskeleme.sentetik import (
    bilirkisi_raporu,
    dilekce,
    ornekler,
    rastgele_iban,
    rastgele_tc,
    rastgele_vkn,
)
from kvkk_maskeleme.tespit import bul, turlere_gore


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


@pytest.mark.parametrize("bicim", ["{a} {b} {c} {d}", "{a}.{b}.{c}{d}", "{a}-{b}{c}{d}"])
def test_ayracli_tc_bulunuyor(bicim):
    """İnsanlar kimlik numarasını boşlukla, noktayla, tireyle yazıyor."""
    no = rastgele_tc(random.Random(0))
    yazim = bicim.format(a=no[:3], b=no[3:6], c=no[6:9], d=no[9:])
    (b,) = [x for x in bul(f"Kimlik: {yazim}") if x.tur == "TC"]

    assert b.kaynak == "ayrac"


def test_ayracli_iban_bulunuyor():
    iban = rastgele_iban(random.Random(1))
    bosluklu = " ".join(iban[i : i + 4] for i in range(0, len(iban), 4))

    assert any(b.tur == "IBAN" for b in bul(f"Hesap: {bosluklu}"))


@pytest.mark.parametrize("harf, rakam", [("O", "0"), ("l", "1"), ("S", "5"), ("B", "8")])
def test_ocr_bozulmasi_onariliyor(harf, rakam):
    """Taranmış belgede OCR harfle rakamı karıştırıyor."""
    no = rastgele_tc(random.Random(2))
    if rakam not in no:
        pytest.skip(f"örnek numarada {rakam} yok")

    bozuk = no.replace(rakam, harf)
    (b,) = [x for x in bul(f"Kimlik: {bozuk}") if x.tur == "TC"]

    assert b.kaynak == "ocr"
    assert b.deger == bozuk  # özgün, bozuk hâli maskelenmeli


def test_ocr_onarimi_dogrulanmadan_kabul_edilmiyor():
    """Onarım tahmin değil: düzeltilmiş hâl kontrol hanesinden geçmeli."""
    assert not [b for b in bul("Kod: OOOOOOOOOOO") if b.tur == "TC"]
    assert not [b for b in bul("Kod: SSSSSSSSSSS") if b.tur == "TC"]


def test_harf_agirlikli_dizi_kimlik_sanilmiyor():
    """Sıradan kelimeler rakama çevrilip uydurma kimlik üretilmemeli."""
    assert not [b for b in bul("SOSYOLOJIDE") if b.tur == "TC"]


def test_ocr_onarimi_kapatilabiliyor():
    no = rastgele_tc(random.Random(3))
    if "0" not in no:
        pytest.skip("örnek numarada 0 yok")
    bozuk = no.replace("0", "O")

    assert bul(f"Kimlik: {bozuk}")
    assert not bul(f"Kimlik: {bozuk}", ocr_onarimi=False)


def test_temiz_yazim_hala_desen_kaynakli():
    no = rastgele_tc(random.Random(4))
    (b,) = [x for x in bul(f"Kimlik: {no}") if x.tur == "TC"]

    assert b.kaynak == "desen"


def test_ayrac_toleransi_gecersiz_sayiyi_gecirmiyor():
    """Gevşek desen, doğrulamayı zayıflatmamalı."""
    assert not [b for b in bul("Dosya 123 456 789 01 sayılı") if b.tur == "TC"]
