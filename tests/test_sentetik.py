"""zor_metin ve yeni temiz-cümle tuzaklarının testleri.

zor_metin, AD/ADRES recall ölçümünün üreteci değil aracı ölçmesi için
var: adlar burada "DAVACI :" gibi öngörülebilir bir etiketin hemen
ardından gelmiyor. Buradaki testler iki şeyi garanti ediyor: etiketlerin
_yerlestir tarafından doğru konuma yerleştirildiğini (off-by-one
kontrolü) ve yeni tuzak cümlelerin ne desen katmanını ne de özel
nitelikli sözlüğü tetiklemediğini.
"""

import pytest

from kvkk_maskeleme.ozel_nitelikli import incele
from kvkk_maskeleme.sentetik import TEMIZ_CUMLELER, zor_metin
from kvkk_maskeleme.tespit import bul

YENI_TUZAKLAR = (
    "Olay deniz kenarında meydana gelmiştir.",
    "Davacının umut ettiği sonuç doğmamıştır.",
    "Taraflar barış içinde ayrılmıştır.",
    "Keşif şafak vakti yapılmıştır.",
    "Güneş açtıktan sonra keşfe devam edilmiştir.",
    "Dilekçe sevgi ve saygı ifadeleriyle sona ermektedir.",
)


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
