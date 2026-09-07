"""Maskeleme, geri alma ve sızıntı doğrulaması testleri."""

import random

import pytest

from turkish_anonymizer.maskeleme import (
    SizintiHatasi,
    dogrula_temiz,
    geri_al,
    maskele,
)
from turkish_anonymizer.sentetik import dilekce, ornekler, rastgele_tc
from turkish_anonymizer.tespit import bul


def test_maskelenen_metinde_veri_kalmiyor():
    for belge in ornekler(10):
        sonuc = maskele(belge.metin)
        assert bul(sonuc.metin) == []


def test_ayni_deger_ayni_yer_tutucu():
    r = random.Random(0)
    no = rastgele_tc(r)
    sonuc = maskele(f"{no} kişisi, yine {no} numaralı")

    assert sonuc.metin.count("<TC_1>") == 2
    assert "<TC_2>" not in sonuc.metin


def test_farkli_degerler_farkli_yer_tutucu():
    r = random.Random(1)
    a, b = rastgele_tc(r), rastgele_tc(r)
    sonuc = maskele(f"{a} ve {b}")

    assert "<TC_1>" in sonuc.metin
    assert "<TC_2>" in sonuc.metin


def test_geri_alinca_ozgun_metne_donuyor():
    for belge in ornekler(5):
        sonuc = maskele(belge.metin)
        assert geri_al(sonuc.metin, sonuc.eslesme) == belge.metin


def test_maskeleme_metnin_geri_kalanini_bozmuyor():
    belge = dilekce(0)
    sonuc = maskele(belge.metin)

    assert "ASLİYE HUKUK MAHKEMESİ" in sonuc.metin
    assert "Alacak davası" in sonuc.metin


def test_ozet_tur_basina_sayiyor():
    ozet = maskele(dilekce(2).metin).ozet()

    assert ozet.get("TC", 0) >= 2
    assert ozet.get("IBAN", 0) == 1


def test_temiz_metin_degismiyor():
    metin = "Duruşma ertelenmiştir. Gerekçe dosyaya eklenmiştir."
    sonuc = maskele(metin)

    assert sonuc.metin == metin
    assert sonuc.eslesme == {}


def test_dogrula_temiz_sizintiyi_yakaliyor():
    """Doğrulama katmanının tek işi bu: kirli metni geçirmemek."""
    r = random.Random(3)
    with pytest.raises(SizintiHatasi, match="kişisel veri kaldı"):
        dogrula_temiz(f"Kimlik {rastgele_tc(r)}")


def test_dogrula_temiz_temiz_metinde_sessiz():
    dogrula_temiz("Duruşma ertelenmiştir.")  # hata vermemeli


def test_maskeleme_dogrulamayi_cagiriyor(monkeypatch):
    """Tespit bozulsa bile maskeleme doğrulamayı atlamamalı."""
    import turkish_anonymizer.maskeleme as m

    cagrildi = []
    monkeypatch.setattr(m, "dogrula_temiz", lambda metin: cagrildi.append(metin))
    m.maskele("herhangi bir metin")

    assert cagrildi, "maskele() doğrulamayı çağırmadı"


def test_dogrulama_kapatilabiliyor(monkeypatch):
    import turkish_anonymizer.maskeleme as m

    def patlat(metin):
        raise AssertionError("doğrulama çağrılmamalıydı")

    monkeypatch.setattr(m, "dogrula_temiz", patlat)
    m.maskele("herhangi bir metin", dogrula=False)


def test_eslesme_kisisel_veri_iceriyor():
    """Eşleme tablosu özgün değerleri tutuyor; testin amacı bunu
    belgelemek, çünkü o dosya metinle birlikte gönderilmemeli."""
    sonuc = maskele(dilekce(5).metin)

    assert sonuc.eslesme
    assert all(t.startswith("<") for t in sonuc.eslesme)
