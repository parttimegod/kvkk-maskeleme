"""Özel nitelikli veri tespiti testleri (KVKK md. 6).

Bu katmanda hata dengesi ters: yanlış negatif, yanlış pozitiften kötü.
Testler de buna göre yazıldı -- kaçırmama üzerine kurulu.
"""

import pytest

from kvkk_maskeleme.model import SahteSaglayici
from kvkk_maskeleme.ozel_nitelikli import (
    KATEGORILER,
    OzelNitelikliRapor,
    _kucult,
    incele,
    istem_hazirla,
    modelle_bul,
    sozlukle_bul,
)
from kvkk_maskeleme.sentetik import ceza_dosyasi, dilekce


@pytest.mark.parametrize(
    "metin, kategori",
    [
        ("Sanığın sabıka kaydı bulunmaktadır.", "CEZA_MAHKUMIYETI"),
        ("Hükümlü cezaevinde bulunmaktadır.", "CEZA_MAHKUMIYETI"),
        ("Davacının kronik rahatsızlığı vardır.", "SAGLIK"),
        ("Hastanede tedavi görmüştür.", "SAGLIK"),
        ("Sendika üyeliği bulunmaktadır.", "DERNEK_VAKIF_SENDIKA"),
        ("Parmak izi kayda alınmıştır.", "BIYOMETRIK"),
        ("DNA örneği incelenmiştir.", "GENETIK"),
    ],
)
def test_kategoriler_yakalaniyor(metin, kategori):
    assert kategori in {b.kategori for b in sozlukle_bul(metin)}


def test_turkce_ekler_yakalaniyor():
    """Kök 'sabika' ama metinde 'sabıkalıdır' geçiyor."""
    assert sozlukle_bul("Sanık sabıkalıdır.")
    assert sozlukle_bul("Mahkûmiyetine karar verildi.")


def test_kisa_kok_baska_kelimeyi_yakalamiyor():
    """'din' kökü 'aydın' ya da 'dinlenme' yakalamamalı."""
    kategoriler = {b.kategori for b in sozlukle_bul("Aydın ilinde dinlenme tesisi.")}
    assert "DIN_MEZHEP" not in kategoriler


def test_ayni_kelime_tek_kez_sayiliyor():
    """'mahkum' ve 'mahkumiyet' aynı kelimeyi yakalıyor."""
    bulgular = [
        b for b in sozlukle_bul("Mahkûmiyeti bulunmaktadır.")
        if b.kategori == "CEZA_MAHKUMIYETI"
    ]
    assert len(bulgular) == 1


def test_temiz_belgede_isaret_yok():
    assert not incele(dilekce(0).metin).var_mi


def test_ceza_dosyasi_isaretleniyor():
    rapor = incele(ceza_dosyasi(0).metin)

    assert rapor.var_mi
    assert {"CEZA_MAHKUMIYETI", "SAGLIK", "DERNEK_VAKIF_SENDIKA"} <= rapor.kategoriler()


def test_uyari_metni_maddeyi_aniyor():
    uyari = incele(ceza_dosyasi(1).metin).uyari()

    assert "md. 6" in uyari
    assert "Maskeleme bu veriyi kaldırmaz" in uyari


def test_temiz_uyari_metni():
    assert "bulunmadı" in OzelNitelikliRapor().uyari()


def test_kanit_metinden_alinıyor():
    """Kanıt, küçültülmüş değil özgün metinden gelmeli."""
    metin = "Şüphelinin SABIKA kaydı vardır."
    (b,) = [x for x in sozlukle_bul(metin) if x.kategori == "CEZA_MAHKUMIYETI"]

    assert metin[b.baslangic : b.bitis] == b.kanit
    assert b.kanit == "SABIKA"


def test_kucultme_turkce_duyarli():
    assert _kucult("SABIKA") == "sabika"
    assert _kucult("İLAÇ") == "ilac"
    assert _kucult("MAHKÛMİYET").startswith("mahk")


def test_model_kategorisi_ekleniyor():
    metin = "Bu kişi hakkında bir husus vardır ve durumu özeldir."
    cevap = '[{"kategori": "SAGLIK", "kanit": "durumu özeldir"}]'
    bulgular = modelle_bul(metin, SahteSaglayici(cevap=cevap))

    assert len(bulgular) == 1
    assert bulgular[0].kaynak == "model"


def test_model_uydurmasi_atiliyor():
    cevap = '[{"kategori": "SAGLIK", "kanit": "metinde olmayan cümle"}]'
    assert modelle_bul("Kısa bir metin.", SahteSaglayici(cevap=cevap)) == []


def test_model_bilinmeyen_kategori_atiliyor():
    cevap = '[{"kategori": "HOBI", "kanit": "Kısa"}]'
    assert modelle_bul("Kısa bir metin.", SahteSaglayici(cevap=cevap)) == []


def test_bozuk_model_cevabi_sozlugu_bozmuyor():
    rapor = incele(ceza_dosyasi(2).metin, saglayici=SahteSaglayici(cevap="çöp"))

    assert rapor.var_mi  # sözlük katmanı yine çalıştı


def test_model_ve_sozluk_ayni_yeri_tekrarlamiyor():
    metin = "Sanığın sabıka kaydı bulunmaktadır."
    cevap = '[{"kategori": "CEZA_MAHKUMIYETI", "kanit": "sabıka"}]'
    rapor = incele(metin, saglayici=SahteSaglayici(cevap=cevap))

    ceza = [b for b in rapor.bulgular if b.kategori == "CEZA_MAHKUMIYETI"]
    assert len(ceza) == 1


def test_istem_kategorileri_iceriyor():
    istem = istem_hazirla("metin")

    for k in ("SAGLIK", "CEZA_MAHKUMIYETI", "BIYOMETRIK"):
        assert k in istem
    assert "metin" in istem


def test_kategoriler_kanun_sirasinda():
    """KVKK md. 6'daki sıra korunuyor; uyum eşlemesi kolaylaşsın diye."""
    assert KATEGORILER[0] == "IRK_ETNIK"
    assert KATEGORILER[-1] == "GENETIK"
    assert len(KATEGORILER) == 11


@pytest.mark.parametrize(
    "metin",
    [
        "Tanık dinlenmesine karar verildi.",
        "Duruşmada tanıklar dinlendi.",
        "Aydın ilinde dinlenme tesisi bulunmaktadır.",
    ],
)
def test_tanik_dinlenmesi_din_sanilmiyor(metin):
    """Adliye metninde en sık geçen yanlış pozitif buydu."""
    assert "DIN_MEZHEP" not in {b.kategori for b in sozlukle_bul(metin)}


def test_tanik_kelimesi_saglik_sanilmiyor():
    """'tanı' kökü 'tanık'ı yakalıyordu; kök listeden çıkarıldı."""
    assert "SAGLIK" not in {b.kategori for b in sozlukle_bul("Tanık beyanı alındı.")}


def test_gercek_din_ifadesi_hala_yakalaniyor():
    assert "DIN_MEZHEP" in {b.kategori for b in sozlukle_bul("Davacının dini nedir?")}
    assert "DIN_MEZHEP" in {b.kategori for b in sozlukle_bul("Mezhep farkı gözetildi.")}
