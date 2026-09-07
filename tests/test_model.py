"""Model katmanı testleri.

Hiçbiri gerçek modele ihtiyaç duymuyor. Model geldiğinde değişecek tek
şey sağlayıcı; aradaki bütün mantık burada sınanmış oluyor.

Test edilen asıl şey modelin doğru cevap vermesi değil -- ona
güvenemeyiz. Test edilen şey, model yanlış cevap verdiğinde ne
olduğu: bozuk JSON, uydurma ifade, yanlış tür, boş cevap.
"""

import pytest

from kvkk_maskeleme.maskeleme import maskele
from kvkk_maskeleme.model import (
    MODEL_TURLERI,
    SahteSaglayici,
    bul,
    cevabi_coz,
    istem_hazirla,
)

METIN = "Davacı Ayşe Yılmaz, Cumhuriyet Mahallesi 5. Sokak No: 3 Antalya adresinde."


def test_duz_json_cozuluyor():
    s = cevabi_coz(METIN, '[{"tur": "AD", "deger": "Ayşe Yılmaz"}]')

    assert len(s.bulgular) == 1
    assert s.bulgular[0].tur == "AD"
    assert s.bulgular[0].deger == "Ayşe Yılmaz"
    assert not s.bicim_hatasi


def test_konum_metinden_hesaplaniyor():
    """Modelden konum istemiyoruz; kendimiz buluyoruz."""
    (b,) = cevabi_coz(METIN, '[{"tur": "AD", "deger": "Ayşe Yılmaz"}]').bulgular

    assert METIN[b.baslangic : b.bitis] == "Ayşe Yılmaz"


def test_markdown_citi_temizleniyor():
    cevap = '```json\n[{"tur": "AD", "deger": "Ayşe Yılmaz"}]\n```'
    assert len(cevabi_coz(METIN, cevap).bulgular) == 1


def test_oncesine_sonrasina_yazi_eklenmis_cevap():
    cevap = (
        "Tabii, işte bulduklarım:\n"
        '[{"tur": "AD", "deger": "Ayşe Yılmaz"}]\n'
        "Umarım yardımcı olur."
    )
    assert len(cevabi_coz(METIN, cevap).bulgular) == 1


def test_uydurma_ifade_ayikliyor():
    """Model metinde olmayan bir şey döndürürse bulgu sayılmamalı."""
    s = cevabi_coz(METIN, '[{"tur": "AD", "deger": "Mehmet Demir"}]')

    assert s.bulgular == []
    assert s.uydurma == ["Mehmet Demir"]
    assert s.uydurma_orani == 1.0


def test_uydurma_orani_karisik_cevapta():
    cevap = '[{"tur":"AD","deger":"Ayşe Yılmaz"},{"tur":"AD","deger":"Yok Böyle Biri"}]'
    s = cevabi_coz(METIN, cevap)

    assert len(s.bulgular) == 1
    assert len(s.uydurma) == 1
    assert s.uydurma_orani == 0.5


@pytest.mark.parametrize("cevap", ["", "bulamadım", "{", "[{bozuk}]", "null"])
def test_bozuk_cevap_bicim_hatasi(cevap):
    s = cevabi_coz(METIN, cevap)

    assert s.bicim_hatasi or s.bulgular == []


def test_bos_dizi_hata_degil():
    s = cevabi_coz(METIN, "[]")

    assert s.bulgular == []
    assert not s.bicim_hatasi


def test_bilinmeyen_tur_atiliyor():
    cevap = '[{"tur": "RENK", "deger": "Ayşe Yılmaz"}]'
    assert cevabi_coz(METIN, cevap).bulgular == []


def test_yapisal_turler_model_katmanindan_kabul_edilmiyor():
    """TC'yi model değil desen katmanı bulmalı; doğrulanmış olan kazanır."""
    assert "TC" not in MODEL_TURLERI
    cevap = '[{"tur": "TC", "deger": "Ayşe Yılmaz"}]'
    assert cevabi_coz(METIN, cevap).bulgular == []


def test_eksik_alanlar_atiliyor():
    cevap = '[{"tur": "AD"}, {"deger": "Ayşe Yılmaz"}, {}, "metin", 5]'
    assert cevabi_coz(METIN, cevap).bulgular == []


def test_ayni_ifade_her_gecisinde_bulunuyor():
    metin = "Ayşe Yılmaz geldi, sonra Ayşe Yılmaz gitti."
    s = cevabi_coz(metin, '[{"tur": "AD", "deger": "Ayşe Yılmaz"}]')

    assert len(s.bulgular) == 2


def test_istem_belgeyi_iceriyor():
    istem = istem_hazirla(METIN)

    assert METIN in istem
    assert "{belge}" not in istem


def test_saglayici_cagriliyor():
    s = SahteSaglayici(cevap='[{"tur": "AD", "deger": "Ayşe Yılmaz"}]')
    sonuc = bul(METIN, s)

    assert s.cagri_sayisi == 1
    assert METIN in s.son_istem
    assert len(sonuc.bulgular) == 1


def test_maskeleme_model_katmaniyla():
    s = SahteSaglayici(cevap='[{"tur": "AD", "deger": "Ayşe Yılmaz"}]')
    sonuc = maskele(METIN, saglayici=s)

    assert "<AD_1>" in sonuc.metin
    assert "Ayşe Yılmaz" not in sonuc.metin


def test_saglayici_verilmezse_model_calismiyor():
    sonuc = maskele(METIN)

    assert "Ayşe Yılmaz" in sonuc.metin  # desen katmanı adı bulmaz
    assert sonuc.uydurma == []


def test_cakismada_desen_kazaniyor():
    """Doğrulanmış kimlik numarası, modelin tahmininden güvenilir."""
    import random

    from kvkk_maskeleme.sentetik import rastgele_tc

    no = rastgele_tc(random.Random(0))
    metin = f"Kimlik {no} numaralı kişi"
    s = SahteSaglayici(cevap=f'[{{"tur": "AD", "deger": "{no}"}}]')
    sonuc = maskele(metin, saglayici=s)

    assert "<TC_1>" in sonuc.metin
    assert "<AD_1>" not in sonuc.metin


def test_model_uydurmasi_sonuca_tasiniyor():
    s = SahteSaglayici(cevap='[{"tur": "AD", "deger": "Olmayan Kişi"}]')
    sonuc = maskele(METIN, saglayici=s)

    assert sonuc.uydurma == ["Olmayan Kişi"]


def test_bozuk_cevap_maskelemeyi_patlatmiyor():
    """Model saçmalarsa desen katmanı yine de çalışmalı."""
    sonuc = maskele(METIN, saglayici=SahteSaglayici(cevap="çöp"))

    assert sonuc.model_bicim_hatasi
    assert sonuc.metin == METIN  # bu metinde yapısal veri yok
