"""Bağlam çıpalı tespit testleri.

En değerli testler etiketsiz değerin yakalanmadığını gösterenler.
Adliye metni tarih dolu; her tarihi doğum tarihi sayan bir araç
kullanılamaz.
"""

import pytest

from kvkk_maskeleme.baglam import bul, bulgulara_cevir
from kvkk_maskeleme.maskeleme import maskele
from kvkk_maskeleme.tespit import turlere_gore


@pytest.mark.parametrize(
    "metin, tur, deger",
    [
        ("Pasaport No: U1234567", "PASAPORT", "U1234567"),
        ("Pasaport Numarası: S987654", "PASAPORT", "S987654"),
        ("Doğum Tarihi: 12.03.1985", "DOGUM_TARIHI", "12.03.1985"),
        ("Doğum tarihi 01/01/1970", "DOGUM_TARIHI", "01/01/1970"),
        ("Doğum Tarihi: 5 Mart 1990", "DOGUM_TARIHI", "5 Mart 1990"),
    ],
)
def test_etiketli_deger_bulunuyor(metin, tur, deger):
    (b,) = [x for x in bul(metin) if x.tur == tur]
    assert b.deger == deger


def test_sgk_sicili_tam_yakalaniyor():
    metin = "SGK Sicil No: 2 4941 01 01 9999999 034 05 61 000"
    (b,) = [x for x in bul(metin) if x.tur == "SGK_SICIL"]

    assert b.deger.endswith("000")


def test_sgk_deseni_satir_sonunu_gecmiyor():
    metin = "Sicil No: 2 4941 01 01 9999999\nTutar: 15 000 TL"
    (b,) = [x for x in bul(metin) if x.tur == "SGK_SICIL"]

    assert "Tutar" not in b.deger
    assert "\n" not in b.deger


@pytest.mark.parametrize(
    "metin",
    [
        "Sözleşme 01.01.2026 tarihinde imzalanmıştır.",
        "Duruşma 15.02.2026 tarihine ertelenmiştir.",
        "Karar 3 Mart 2026 tarihinde tebliğ edildi.",
    ],
)
def test_etiketsiz_tarih_dogum_tarihi_sayilmiyor(metin):
    """Adliye metni tarih dolu; etiket olmadan hepsini işaretlemek
    çıktıyı kullanılamaz hale getirir."""
    assert not [b for b in bul(metin) if b.tur == "DOGUM_TARIHI"]


def test_etiketsiz_pasaport_benzeri_yakalanmiyor():
    bulgular = bul("Dosya U1234567 numarasıyla kaydedildi.")
    assert not [b for b in bulgular if b.tur == "PASAPORT"]


def test_etiket_bulguya_kaydediliyor():
    (b,) = [x for x in bul("Doğum Tarihi: 12.03.1985") if x.tur == "DOGUM_TARIHI"]
    assert "oğum" in b.etiket


def test_sadece_deger_isaretleniyor_etiket_kaliyor():
    """Etiket maskelenmemeli; 'Doğum Tarihi: <...>' okunabilir kalsın."""
    metin = "Doğum Tarihi: 12.03.1985"
    sonuc = maskele(metin)

    assert sonuc.metin == "Doğum Tarihi: <DOGUM_TARIHI_1>"


def test_bulgulara_cevirme_kaynagi_isaretliyor():
    (b,) = bulgulara_cevir("Pasaport No: U1234567")
    assert b.kaynak == "baglam"


def test_tespit_zincirine_katiliyor():
    metin = "Pasaport No: U1234567\nDoğum Tarihi: 12.03.1985"
    bulunan = turlere_gore(metin)

    assert "PASAPORT" in bulunan
    assert "DOGUM_TARIHI" in bulunan


def test_dogrulanmis_bulgu_cakismada_kazaniyor():
    """Kontrol hanesi olan tür, çıpalı türe üstün gelmeli."""
    import random

    from kvkk_maskeleme.sentetik import rastgele_tc

    no = rastgele_tc(random.Random(0))
    turler = {b.tur for b in __import__(
        "kvkk_maskeleme.tespit", fromlist=["bul"]
    ).bul(f"Sicil No: {no}")}

    assert "TC" in turler
