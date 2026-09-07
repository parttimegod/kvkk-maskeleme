"""Ölçüm harness'ının testleri.

Harness'ın kendisi doğru saymazsa bütün rakamlar anlamsız olur, o
yüzden kaçırma ve uydurma senaryolarını elle kuruyoruz.
"""

import json

from kvkk_maskeleme.model import SahteSaglayici
from kvkk_maskeleme.olcum import MODELE_BAGLI, YAPISAL, calistir, olc
from kvkk_maskeleme.sentetik import dilekce, ornekler


def test_yapisal_recall_tam():
    rapor = calistir(10)

    assert rapor.turler
    for tur, s in rapor.turler.items():
        assert s.recall == 1.0, f"{tur} kaçırdı: {s.kacan[:3]}"


def test_saglayicisiz_ad_olculmuyor():
    """Desen katmanının ad bulması beklenmiyor; ölçüme katmak haksız."""
    rapor = calistir(5)

    assert not (set(rapor.turler) & MODELE_BAGLI)
    assert set(rapor.turler) <= YAPISAL


def test_saglayiciyla_ad_olcume_giriyor():
    rapor = olc(ornekler(3), saglayici=SahteSaglayici(cevap="[]"))

    assert "AD" in rapor.turler
    assert rapor.turler["AD"].recall == 0.0  # boş cevap, hepsi kaçtı


def test_dogru_cevap_recalli_yukseltiyor():
    belge = dilekce(0)
    adlar = [e.deger for e in belge.etiketler if e.tur == "AD"]
    cevap = json.dumps([{"tur": "AD", "deger": a} for a in set(adlar)])

    rapor = olc([belge], saglayici=SahteSaglayici(cevap=cevap))

    assert rapor.turler["AD"].recall == 1.0


def test_kacanlar_kaydediliyor():
    rapor = olc(ornekler(2), saglayici=SahteSaglayici(cevap="[]"))

    assert rapor.turler["AD"].kacan
    assert all(isinstance(k, str) for k in rapor.turler["AD"].kacan)


def test_uydurma_rapora_giriyor():
    cevap = '[{"tur": "AD", "deger": "Bu Metinde Yok"}]'
    rapor = olc(ornekler(2), saglayici=SahteSaglayici(cevap=cevap))

    assert rapor.uydurma
    assert "Bu Metinde Yok" in rapor.uydurma


def test_bozuk_cevap_sayiliyor():
    rapor = olc(ornekler(2), saglayici=SahteSaglayici(cevap="çöp"))

    assert rapor.bicim_hatasi == rapor.belge_sayisi


def test_belge_sayisi_dogru():
    rapor = calistir(7)
    assert rapor.belge_sayisi == 14  # tür başına bir belge


def test_tablo_basiliyor():
    tablo = calistir(3).tablo()

    assert "recall" in tablo
    assert "TC" in tablo
    assert "belge:" in tablo


def test_bos_kume():
    rapor = olc([])

    assert rapor.belge_sayisi == 0
    assert rapor.turler == {}
    assert "belge: 0" in rapor.tablo()
