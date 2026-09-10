"""Özel nitelikli veri tespitinin sentetik.py'den bağımsız ölçümü.

olcum.py'nin bildirdiği özel nitelikli recall, sentetik.py'nin ürettiği
cümlelere karşı ölçülüyor. Ama o cümleler zaten sözlükteki köklerle
aynı kelimeleri kullanıyor -- ceza_dosyasi() "mahkûmiyeti", "ilaç
kullandığı" diyor; sözlükte "mahkumiyet" ve "ilac" kökleri var.
saglik_raporu() "DNA incelemesi" diyor; sözlükte "dna" kökü var. Yani
ölçüm, sözlüğü kendi kelime dağarcığına karşı sınıyor. %100 rakamı bu
yüzden bir üst sınırdır, bağımsız bir doğrulama değildir.

Bu dosya sentetik.py'nin cümlelerinden habersiz, benim yazdığım sekiz
gerçekçi adliye cümlesiyle aynı ölçümü tekrarlıyor. Sonuç: sekizden
yalnızca biri (Alevi mensubiyeti) doğru kategoriyle yakalandı. Geri
kalan yedisi ya hiç yakalanmadı ya da yanlış kategoriyle yakalandı
(bkz. test_biyometrik_yuz_karsilastirma -- "teşhis" kelimesi hem
"tanı" hem "kimlik tespiti" anlamına geliyor, sözlük ikisini
ayıramıyor).

Bu, sözlüğün hatalı olduğu anlamına gelmiyor; sözlük kelime köküyle
çalışıyor, eş anlamlı ya da dolaylı anlatımı tanıyamaz. Asıl önemli
olan, bu sınırın README/SONRA.md'de açıkça yazılı olması ve %100
rakamının olduğundan iyi görünmemesi. Kaçan cümleler burada
xfail(strict=True) ile işaretli: iddia zayıflatılmadı, yalnızca bilinen
bir eksiklik olarak kayda geçti. Biri bu kökleri genişletip cümleyi
yakalarsa strict=True bunu XPASS olarak yakalar ve işaretin
kaldırılması gerektiğini hatırlatır.
"""

import pytest

from kvkk_maskeleme.ozel_nitelikli import sozlukle_bul


def _kategoriler(metin: str) -> set[str]:
    return {b.kategori for b in sozlukle_bul(metin)}


@pytest.mark.xfail(
    reason=(
        "'görme yetisini kaybettiği' engelliliği anlatıyor ama sözlükte "
        "yok; sözlük 'engelli'/'malul' gibi kelimenin kendisini arıyor, "
        "hangi işlevin kaybedildiğini betimleyen ifadeyi tanımıyor."
    ),
    strict=True,
)
def test_saglik_gorme_kaybi():
    metin = (
        "Müvekkilin görme yetisini büyük ölçüde kaybettiği ve bu nedenle "
        "günlük işlerini tek başına yürütemediği tıbbi belgelerle "
        "desteklenmektedir."
    )
    assert "SAGLIK" in _kategoriler(metin)


@pytest.mark.xfail(
    reason=(
        "'böbrek yetmezliği', 'diyaliz' sözlükte yok; sözlük yalnızca "
        "kendi köklerini (hastalik, tedavi, ilac...) tanıyor."
    ),
    strict=True,
)
def test_saglik_bobrek_yetmezligi():
    metin = (
        "Davacının uzun süredir böbrek yetmezliği çektiği ve düzenli "
        "diyalize girdiği dosyaya sunulan belgelerden anlaşılmaktadır."
    )
    assert "SAGLIK" in _kategoriler(metin)


@pytest.mark.xfail(
    reason=(
        "'hapis yattığı' günlük dildeki en yaygın ifadelerden biri ama "
        "sözlükte yok; sözlük 'cezaevi'/'hukumlu' gibi resmi terimleri "
        "arıyor."
    ),
    strict=True,
)
def test_ceza_hapis_yattigi():
    metin = (
        "Sanığın gençlik yıllarında işlediği bir suç nedeniyle bir dönem "
        "hapis yattığı kayıtlarda yer almaktadır."
    )
    assert "CEZA_MAHKUMIYETI" in _kategoriler(metin)


@pytest.mark.xfail(
    reason=(
        "'adli para cezasına çarptırıldığı' bir mahkûmiyet anlatıyor ama "
        "sözlükte bağımsız bir 'ceza' kökü yok -- bilerek yok, çünkü "
        "'ceza' tek başına neredeyse her adliye cümlesinde geçer ve "
        "eklenirse yanlış pozitif patlar."
    ),
    strict=True,
)
def test_ceza_adli_para_cezasi():
    metin = (
        "Müvekkilin trafik kazası sonrası adli para cezasına çarptırıldığı "
        "öğrenilmiştir."
    )
    assert "CEZA_MAHKUMIYETI" in _kategoriler(metin)


def test_din_alevi_mensubiyeti():
    """Bu geçiyor: 'Alevi' sözlükte doğrudan bir kök."""
    metin = (
        "Tanığın Alevi olduğu gerekçesiyle ifadesine itibar edilmediği "
        "öne sürülmüştür."
    )
    assert "DIN_MEZHEP" in _kategoriler(metin)


@pytest.mark.xfail(
    reason=(
        "'işçi örgütü' sendikanın günlük dildeki eş anlamlısı ama "
        "sözlükte yalnızca 'sendika' kelimesinin kendisi var."
    ),
    strict=True,
)
def test_dernek_isci_orgutu():
    metin = (
        "Davacının bir işçi örgütüne kayıtlı olduğu ve toplu iş sözleşmesi "
        "görüşmelerine katıldığı belirtilmiştir."
    )
    assert "DERNEK_VAKIF_SENDIKA" in _kategoriler(metin)


@pytest.mark.xfail(
    reason=(
        "'soybağının bilimsel olarak tespit edildiği' bir babalık/DNA "
        "testini dolaylı anlatıyor; sözlük yalnızca 'dna', 'genetik', "
        "'babalik testi' kelimelerinin kendisini arıyor."
    ),
    strict=True,
)
def test_genetik_soybagi_tespiti():
    metin = (
        "Baba olduğu iddia edilen kişiden alınan örnekle soybağının "
        "bilimsel olarak tespit edildiği rapor edilmiştir."
    )
    assert "GENETIK" in _kategoriler(metin)


@pytest.mark.xfail(
    reason=(
        "'yüzünün karşılaştırılarak teşhis edildiği' yüz tanımayı "
        "anlatıyor ama sözlükteki 'teshis' kökü SAGLIK kategorisinde -- "
        "kelime Türkçede hem 'tıbbi tanı' hem 'kimlik tespiti' anlamına "
        "geliyor, sözlük ikisini ayırt edemiyor. Sonuç: cümle "
        "işaretleniyor ama yanlış kategoriyle (BIYOMETRIK değil SAGLIK)."
    ),
    strict=True,
)
def test_biyometrik_yuz_karsilastirma():
    metin = (
        "Şüphelinin güvenlik kamerası görüntülerinden yüzünün "
        "karşılaştırılarak teşhis edildiği belirtilmiştir."
    )
    assert "BIYOMETRIK" in _kategoriler(metin)
