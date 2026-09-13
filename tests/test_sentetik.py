"""zor_metin ve yeni temiz-cümle tuzaklarının testleri.

zor_metin, AD/ADRES recall ölçümünün üreteci değil aracı ölçmesi için
var: adlar burada "DAVACI :" gibi öngörülebilir bir etiketin hemen
ardından gelmiyor. Buradaki testler iki şeyi garanti ediyor: etiketlerin
_yerlestir tarafından doğru konuma yerleştirildiğini (off-by-one
kontrolü) ve yeni tuzak cümlelerin ne desen katmanını ne de özel
nitelikli sözlüğü tetiklemediğini.
"""

import random

import pytest

from kvkk_maskeleme.model import soyadi_yay
from kvkk_maskeleme.ozel_nitelikli import incele
from kvkk_maskeleme.sentetik import (
    TEMIZ_CUMLELER,
    bozuk_metin,
    ocr_hasari_uygula,
    zor_adres,
    zor_metin,
)
from kvkk_maskeleme.tespit import Bulgu, bul

YENI_TUZAKLAR = (
    "Olay deniz kenarında meydana gelmiştir.",
    "Davacının umut ettiği sonuç doğmamıştır.",
    "Taraflar barış içinde ayrılmıştır.",
    "Keşif şafak vakti yapılmıştır.",
    "Güneş açtıktan sonra keşfe devam edilmiştir.",
    "Dilekçe sevgi ve saygı ifadeleriyle sona ermektedir.",
)

ADRES_TUZAKLARI = (
    "Duruşma Antalya Adliye Sarayı'nda görülmüştür.",
    "Dosya yetkisizlik nedeniyle Ankara'ya gönderilmiştir.",
    "Keşif mahallinde gerekli inceleme yapılmıştır.",
    "Tapu kaydı ilgili tapu müdürlüğünden celp edilmiştir.",
)

# Etiketlenen bir ADRES değeri bu son eklerden biriyle bitiyorsa, hâl eki
# yanlışlıkla etiketin içine sızmış demektir -- _yerlestir'in sınırı adrese
# değil ekin başladığı yere çekilmiş olmalı.
_HAL_EKI_PARCALARI = ("'nde", "'ndeki", "'taki", "'deki", "'ye", "'na")


def test_yeni_tuzaklar_temiz_cumleler_icinde():
    for cumle in YENI_TUZAKLAR:
        assert cumle in TEMIZ_CUMLELER


@pytest.mark.parametrize("cumle", YENI_TUZAKLAR)
def test_tuzak_desen_katmaninda_yanlis_pozitif_degil(cumle):
    assert bul(cumle) == []


@pytest.mark.parametrize("cumle", YENI_TUZAKLAR)
def test_tuzak_ozel_nitelikli_sozlukte_yanlis_pozitif_degil(cumle):
    assert incele(cumle).bulgular == []


def test_zor_metin_en_az_alti_ad_etiketi_iceriyor():
    belge = zor_metin(0)
    ad_sayisi = sum(1 for e in belge.etiketler if e.tur == "AD")
    assert ad_sayisi >= 6


def test_zor_metin_etiket_konumlari_dogru():
    """_yerlestir'in off-by-one hatası yapmadığının kontrolü."""
    belge = zor_metin(1)
    assert belge.etiketler
    for e in belge.etiketler:
        assert belge.metin[e.baslangic : e.bitis] == e.deger


def test_adres_tuzaklari_temiz_cumleler_icinde():
    for cumle in ADRES_TUZAKLARI:
        assert cumle in TEMIZ_CUMLELER


@pytest.mark.parametrize("cumle", ADRES_TUZAKLARI)
def test_adres_tuzagi_desen_katmaninda_yanlis_pozitif_degil(cumle):
    assert bul(cumle) == []


@pytest.mark.parametrize("cumle", ADRES_TUZAKLARI)
def test_adres_tuzagi_ozel_nitelikli_sozlukte_yanlis_pozitif_degil(cumle):
    assert incele(cumle).bulgular == []


def test_zor_adres_en_az_bes_adres_etiketi_iceriyor():
    belge = zor_adres(0)
    adres_sayisi = sum(1 for e in belge.etiketler if e.tur == "ADRES")
    assert adres_sayisi >= 5


def test_zor_adres_etiket_konumlari_dogru():
    """_yerlestir'in off-by-one hatası yapmadığının kontrolü."""
    belge = zor_adres(1)
    assert belge.etiketler
    for e in belge.etiketler:
        assert belge.metin[e.baslangic : e.bitis] == e.deger


def test_zor_adres_etiketleri_hal_ekiyle_bitmiyor():
    """Hâl eki cümleye aittir, etiketlenen adrese değil (zor_metin'deki
    ad etiketleri için izlenen ilkenin aynısı)."""
    belge = zor_adres(2)
    for e in belge.etiketler:
        if e.tur != "ADRES":
            continue
        for ek in _HAL_EKI_PARCALARI:
            assert not e.deger.endswith(ek), f"{e.deger!r} ek ile bitiyor: {ek!r}"


OCR_TUZAKLARI = (
    "Olay denız kenarında meydana gelmıstır.",
    "Taraflar barıs ıcınde ayrılmıstır.",
    "Dosya ıcerıgı incelenmistir.",
)


def test_ocr_tuzaklari_temiz_cumleler_icinde():
    for cumle in OCR_TUZAKLARI:
        assert cumle in TEMIZ_CUMLELER


@pytest.mark.parametrize("cumle", OCR_TUZAKLARI)
def test_ocr_tuzagi_desen_katmaninda_yanlis_pozitif_degil(cumle):
    assert bul(cumle) == []


@pytest.mark.parametrize("cumle", OCR_TUZAKLARI)
def test_ocr_tuzagi_ozel_nitelikli_sozlukte_yanlis_pozitif_degil(cumle):
    assert incele(cumle).bulgular == []


def test_ocr_hasari_uygula_turkce_karakterli_girdiyi_degistirir():
    r = random.Random(0)
    girdi = "Şişli'de oturan Güçlü Öztürk'ün ifadesi alınmıştır."
    assert ocr_hasari_uygula(girdi, r) != girdi


def test_ocr_hasari_uygula_glif_karisikligiyla_da_degistirir():
    r = random.Random(0)
    girdi = "Kılıç'ın beyanı çelişkilidir."
    assert ocr_hasari_uygula(girdi, r, glif_karisikligi=True) != girdi


def test_ocr_hasari_uygula_deterministik():
    """Aynı tohumla üretilmiş random.Random aynı hasarı vermeli --
    ölçümün tekrarlanabilir olması buna dayanıyor."""
    girdi = "Kılıç'ın beyanı çelişkilidir."
    hasar1 = ocr_hasari_uygula(girdi, random.Random(42), glif_karisikligi=True)
    hasar2 = ocr_hasari_uygula(girdi, random.Random(42), glif_karisikligi=True)
    assert hasar1 == hasar2


def test_ocr_hasari_uygula_rn_m_karisikligi_calisabiliyor():
    """rn/m karışıklığı olasılıklı; birkaç tohumdan en az biri tetiklemeli.

    Kod yolunun ölü olmadığını göstermek için -- tek bir tohuma
    bağlanmıyor, aksi hâlde olasılık değişirse test kırılgan olurdu.
    """
    girdi = "kerim demir teslim edilmiştir"
    degisti = any(
        ocr_hasari_uygula(girdi, random.Random(t), rn_m_karisikligi=True) != girdi
        for t in range(30)
    )
    assert degisti


def test_bozuk_metin_en_az_uc_ad_ve_bir_adres_etiketi_iceriyor():
    belge = bozuk_metin(0)
    ad_sayisi = sum(1 for e in belge.etiketler if e.tur == "AD")
    adres_sayisi = sum(1 for e in belge.etiketler if e.tur == "ADRES")
    assert ad_sayisi >= 3
    assert adres_sayisi >= 1


def test_bozuk_metin_etiket_konumlari_dogru():
    """_yerlestir'in off-by-one hatası yapmadığının kontrolü."""
    belge = bozuk_metin(1)
    assert belge.etiketler
    for e in belge.etiketler:
        assert belge.metin[e.baslangic : e.bitis] == e.deger


def test_soyadi_yay_hasarli_anafor_baglantisi_kurulmuyor():
    """Bilinen bir açık, düzeltme değil: bu testin amacı davranışı KAYDETMEK.

    soyadi_yay tam alt dizi eşleşmesiyle çalışıyor (bkz. model.py). Tam
    ad temiz bulunduysa ("Ayşe Yıldırım") ve sonrasında çıplak soyadı
    OCR hasarıyla farklı yazılmışsa ("Yildirim", aksansız), aranan
    dize ile metindeki dize birebir eşleşmediği için bağlantı KURULMUYOR.
    Bu, bozuk_metin'in sınadığı tam senaryo. xfail değil çünkü bu bir
    hata değil -- mevcut tasarımın bilinen sınırı; burada kayıtlı olması
    ileride biri "neden düzeltmiyoruz" diye sorduğunda cevap versin diye.
    """
    metin = (
        "Duruşmada dinlenen Ayşe Yıldırım beyanında bulunmuştur. Taranmış "
        "nüshada yalnızca soyadıyla geçen Yildirim ifadesi de aynı kişiye "
        "aittir."
    )
    tam_ad = "Ayşe Yıldırım"
    bas = metin.index(tam_ad)
    tam_ad_bulgusu = Bulgu("AD", bas, bas + len(tam_ad), tam_ad)

    yeni = soyadi_yay(metin, [tam_ad_bulgusu])

    assert yeni == []
    assert "Yildirim" not in [b.deger for b in yeni]


def test_butun_ureticiler_ornekleme_giriyor():
    """Üretici yazılıp ornekler()'e bağlanmazsa ölçüm sessizce eksik kalır.

    saglik_raporu bir süre tam da bunu yaptı: tanımlıydı ama ornekler()
    içinde yoktu, o yüzden GENETIK satırı ölçüm tablosunda hiç çıkmadı.
    Tablo tam görünüyordu. Yeni bir üretici bağlanmazsa burası patlasın.
    """
    import inspect

    from kvkk_maskeleme import sentetik

    ureticiler = [
        f
        for ad, f in inspect.getmembers(sentetik, inspect.isfunction)
        if not ad.startswith("_")
        and list(inspect.signature(f).parameters) == ["tohum"]
    ]

    assert len(ureticiler) >= 9
    assert len(sentetik.ornekler(1)) == len(ureticiler)
