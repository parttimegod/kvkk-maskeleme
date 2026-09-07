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
    from kvkk_maskeleme.olcum import CIPALI

    rapor = calistir(5)

    assert not (set(rapor.turler) & MODELE_BAGLI)
    assert set(rapor.turler) <= YAPISAL | CIPALI


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
    assert rapor.belge_sayisi == 49  # yedi belge türü


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


def test_ozel_nitelikli_recall_olculuyor():
    rapor = calistir(5)

    assert rapor.ozel
    for kategori, s in rapor.ozel.items():
        assert s.recall == 1.0, f"{kategori} kaçırdı"


def test_temiz_metinde_yanlis_pozitif_yok():
    """Sözlük cömert ama gürültülü olmamalı.

    Temiz cümleler bilinen tuzakları içeriyor: "tanık dinlenmesi",
    "Aydın ili", "dinlenme salonu".
    """
    rapor = calistir(3)

    assert rapor.temiz_belge_sayisi > 0
    assert rapor.yanlis_pozitifler == [], [
        (y.kategori, y.kanit) for y in rapor.yanlis_pozitifler
    ]
    assert rapor.yanlis_pozitif_orani == 0.0


def test_yanlis_pozitif_kaydediliyor():
    """Ölçüm gerçekten sayıyor mu -- kirli bir metni temiz diye verelim."""
    from kvkk_maskeleme.sentetik import Belge

    rapor = olc([], temizler=[Belge("Sanığın sabıka kaydı vardır.")])

    assert rapor.yanlis_pozitifler
    assert rapor.yanlis_pozitifler[0].kategori == "CEZA_MAHKUMIYETI"
    assert rapor.yanlis_pozitif_orani == 1.0


def test_tabloda_iki_blok_var():
    tablo = calistir(3).tablo()

    assert "TANIMLAYICILAR" in tablo
    assert "ÖZEL NİTELİKLİ" in tablo
    assert "yanlış pozitif" in tablo


def test_ozel_nitelikli_tanimlayici_olcumune_karismiyor():
    """Özel nitelikli etiketler maskeleme recall'ına girmemeli."""
    rapor = calistir(3)

    assert not (set(rapor.turler) & set(rapor.ozel))


def test_butun_tanimlayici_turleri_kapsaniyor():
    """Bir tür hiçbir belgede geçmiyorsa tablo tam görünür ama eksik olur.

    Bu test o sessiz boşluğa karşı: EPOSTA, KART, PASAPORT, SGK_SICIL
    ve DOGUM_TARIHI uzun süre etiketlenmemişti ve ölçümde hiç yoktu.
    """
    from kvkk_maskeleme.olcum import CIPALI
    from kvkk_maskeleme.sentetik import ornekler

    etiketli = set()
    for belge in ornekler(2):
        etiketli |= {e.tur for e in belge.etiketler}

    eksik = (YAPISAL | CIPALI | MODELE_BAGLI) - etiketli
    assert not eksik, f"hiçbir sentetik belgede geçmeyen tür: {sorted(eksik)}"


def test_cipali_turler_saglayicisiz_olculuyor():
    """Bağlam çıpalı türler model gerektirmiyor, tabloda olmalılar."""
    from kvkk_maskeleme.olcum import CIPALI

    rapor = calistir(3)
    assert set(rapor.turler) >= CIPALI


def test_yedi_belge_turu():
    assert calistir(3).belge_sayisi == 21
