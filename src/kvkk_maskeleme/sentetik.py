"""Sentetik Türkçe belge üreteci.

Bu araç gerçek belgeyle test edilemez. Kişisel veri içeren bir metni
geliştirme sırasında kullanmak, aracın önlemeye çalıştığı ihlalin ta
kendisi olur. O yüzden test verisini üretiyoruz.

İkinci işlevi ölçüm: nerede hangi kişisel verinin olduğunu bildiğimiz
için tespit oranını (recall) hesaplayabiliyoruz. Etiketli veri olmadan
"bu araç ne kadar iyi" sorusunun cevabı yok.

Üretilen kimlik numaraları kontrol hanesi bakımından geçerli, yani
tespit mantığını gerçekten sınıyorlar. Geçerli olmaları gerçek bir
kişiye ait olmadıkları anlamına gelmez -- bu numaralar yalnızca tespit
testi içindir, kimseyi temsil etmezler.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass, field

from .kimlik import tc_kontrol_haneleri, vkn_kontrol_hanesi

ADLAR = [
    "Ahmet", "Mehmet", "Mustafa", "Ayşe", "Fatma", "Emine", "Hüseyin",
    "Hatice", "İbrahim", "Zeynep", "Elif", "Ali", "Murat", "Özlem",
    # Günlük kelimeyle çakışan adlar: tespitin zor kısmı bunlar.
    "Deniz", "Umut", "Şafak", "Barış", "Güneş", "Sevgi", "Nur",
]

SOYADLAR = [
    "Yılmaz", "Kaya", "Demir", "Şahin", "Çelik", "Yıldız", "Yıldırım",
    "Öztürk", "Aydın", "Özdemir", "Arslan", "Doğan", "Kılıç", "Aslan",
]

ILLER = ["Antalya", "İstanbul", "Ankara", "İzmir", "Bursa", "Konya", "Adana"]

MAHALLELER = ["Cumhuriyet", "Fatih", "Yeni", "Bahçelievler", "Kızılay", "Merkez"]

# İlçe ile il tutarlı olmalı: "İzmir ili Muratpaşa ilçesi" diye bir yer
# yok ve Türkçe okuyan biri bunu hemen görür. Sentetik belge gerçekçi
# değilse ölçüm de gerçekçi değildir.
ILCELER = {
    "Antalya": "Muratpaşa", "İstanbul": "Kadıköy", "Ankara": "Çankaya",
    "İzmir": "Konak", "Bursa": "Osmangazi", "Konya": "Selçuklu",
    "Adana": "Seyhan",
}


def _rakam_dizisi(r: random.Random, n: int, ilk_sifir_olmasin: bool = False) -> str:
    ilk = r.randint(1 if ilk_sifir_olmasin else 0, 9)
    return str(ilk) + "".join(str(r.randint(0, 9)) for _ in range(n - 1))


def rastgele_tc(r: random.Random) -> str:
    ilk = _rakam_dizisi(r, 9, ilk_sifir_olmasin=True)
    return ilk + tc_kontrol_haneleri(ilk)


def rastgele_vkn(r: random.Random) -> str:
    ilk = _rakam_dizisi(r, 9)
    return ilk + vkn_kontrol_hanesi(ilk)


def rastgele_iban(r: random.Random) -> str:
    """Kontrol hanesi mod-97 ile hesaplanmış TR IBAN'ı."""
    govde = "".join(str(r.randint(0, 9)) for _ in range(22))
    # TR = 2927, kontrol hanesi 00 varsayılıp mod alınıyor.
    sayi = int(govde + "292700")
    kontrol = 98 - sayi % 97
    return f"TR{kontrol:02d}{govde}"


def rastgele_telefon(r: random.Random) -> str:
    return f"0{r.choice(['530', '532', '541', '505', '555'])} {r.randint(100, 999)} " \
           f"{r.randint(10, 99)} {r.randint(10, 99)}"


def rastgele_plaka(r: random.Random) -> str:
    harfler = "".join(r.choice("ABCDEFGHJKLMNPRSTUVYZ") for _ in range(3))
    return f"{r.randint(1, 81):02d} {harfler} {r.randint(100, 999)}"


def rastgele_ad(r: random.Random) -> str:
    return f"{r.choice(ADLAR)} {r.choice(SOYADLAR)}"


def rastgele_adres(r: random.Random) -> str:
    return (
        f"{r.choice(MAHALLELER)} Mahallesi {r.randint(1, 90)}. Sokak "
        f"No: {r.randint(1, 60)}/{r.randint(1, 20)} {r.choice(ILLER)}"
    )


@dataclass
class Etiket:
    """Metinde bir kişisel verinin nerede olduğu."""

    tur: str
    baslangic: int
    bitis: int
    deger: str


@dataclass
class Belge:
    metin: str
    etiketler: list[Etiket] = field(default_factory=list)

    def turler(self) -> set[str]:
        return {e.tur for e in self.etiketler}


def _yerlestir(parcalar: list[tuple[str, str | None]]) -> Belge:
    """Metni birleştirirken her kişisel verinin konumunu kaydeder."""
    metin, etiketler = "", []
    for deger, tur in parcalar:
        if tur is not None:
            etiketler.append(Etiket(tur, len(metin), len(metin) + len(deger), deger))
        metin += deger
    return Belge(metin, etiketler)


def dilekce(tohum: int = 0) -> Belge:
    """Adliye diline yakın bir dilekçe metni."""
    r = random.Random(tohum)
    ad, tc = rastgele_ad(r), rastgele_tc(r)
    adres, tel = rastgele_adres(r), rastgele_telefon(r)
    karsi_ad, karsi_tc = rastgele_ad(r), rastgele_tc(r)
    iban = rastgele_iban(r)

    return _yerlestir([
        ("ANTALYA ", None), (f"{r.randint(1, 12)}. ASLİYE HUKUK MAHKEMESİ", None),
        ("\n\nDAVACI     : ", None), (ad, "AD"),
        (" (T.C. Kimlik No: ", None), (tc, "TC"), (")", None),
        ("\nADRES      : ", None), (adres, "ADRES"),
        ("\nTELEFON    : ", None), (tel, "TELEFON"),
        ("\n\nDAVALI     : ", None), (karsi_ad, "AD"),
        (" (T.C. Kimlik No: ", None), (karsi_tc, "TC"), (")", None),
        ("\n\nKONU       : Alacak davası.\n\n", None),
        ("AÇIKLAMALAR: Müvekkilim ", None), (ad, "AD"),
        (", davalıdan olan alacağını ", None), (iban, "IBAN"),
        (" numaralı hesabına havale yoluyla talep etmiş, ancak ödeme "
         "yapılmamıştır. Bu nedenle işbu davanın açılması zorunluluğu "
         "doğmuştur.\n\nSaygılarımla,\n", None),
        (ad, "AD"),
    ])


def bilirkisi_raporu(tohum: int = 0) -> Belge:
    r = random.Random(tohum + 1000)
    ad, vkn = rastgele_ad(r), rastgele_vkn(r)
    plaka, tel = rastgele_plaka(r), rastgele_telefon(r)

    return _yerlestir([
        ("BİLİRKİŞİ RAPORU\n\n", None),
        ("Rapor Sahibi : ", None), (ad, "AD"),
        ("\nİletişim     : ", None), (tel, "TELEFON"),
        (f"\nDosya No     : 2026/{r.randint(100, 9999)}\n\n", None),
        ("İnceleme konusu araç ", None), (plaka, "PLAKA"),
        (" plakalı araçtır. Aracın kayıtlı olduğu firmanın vergi kimlik "
         "numarası ", None), (vkn, "VKN"),
        ("'dir. Yapılan inceleme sonucunda hasar tespiti tamamlanmıştır.\n", None),
    ])


KURUMLAR = [
    "Yıldız İnşaat Ltd. Şti.", "Deniz Turizm A.Ş.", "Akdeniz Lojistik Ltd. Şti.",
    "Ege Gıda Sanayi A.Ş.", "Anadolu Tekstil Ltd. Şti.",
]

AYLAR = [
    "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
]


def rastgele_eposta(r: random.Random) -> str:
    ad = _kucuk_ascii(r.choice(ADLAR))
    soyad = _kucuk_ascii(r.choice(SOYADLAR))
    return f"{ad}.{soyad}@{r.choice(['ornekfirma', 'hukukburosu', 'posta'])}.com.tr"


def _kucuk_ascii(s: str) -> str:
    katlama = str.maketrans(
        {"ı": "i", "İ": "i", "ğ": "g", "Ğ": "g", "ü": "u", "Ü": "u",
         "ş": "s", "Ş": "s", "ö": "o", "Ö": "o", "ç": "c", "Ç": "c"}
    )
    return s.translate(katlama).lower()


def rastgele_kart(r: random.Random) -> str:
    """Luhn kontrolünden geçen kart numarası."""
    govde = "4" + "".join(str(r.randint(0, 9)) for _ in range(14))
    toplam = 0
    for i, c in enumerate(reversed(govde)):
        d = int(c)
        if i % 2 == 0:
            d *= 2
            if d > 9:
                d -= 9
        toplam += d
    son = (10 - toplam % 10) % 10
    tam = govde + str(son)
    return " ".join(tam[i : i + 4] for i in range(0, 16, 4))


def rastgele_pasaport(r: random.Random) -> str:
    return f"{r.choice('USZ')}{r.randint(1000000, 9999999)}"


def rastgele_sgk_sicil(r: random.Random) -> str:
    parcalar = [
        str(r.randint(1, 2)), f"{r.randint(1000, 9999)}",
        f"{r.randint(1, 99):02d}", f"{r.randint(1, 99):02d}",
        f"{r.randint(1000000, 9999999)}", f"{r.randint(1, 999):03d}",
        f"{r.randint(1, 99):02d}", f"{r.randint(1, 81):02d}", "000",
    ]
    return " ".join(parcalar)


def rastgele_dogum_tarihi(r: random.Random) -> str:
    return f"{r.randint(1, 28):02d}.{r.randint(1, 12):02d}.{r.randint(1950, 2005)}"


def tebligat(tohum: int = 0) -> Belge:
    """Tebligat mazbatası. E-posta, adres ve doğum tarihi taşıyor."""
    r = random.Random(tohum + 5000)
    ad, tc = rastgele_ad(r), rastgele_tc(r)
    adres, eposta = rastgele_adres(r), rastgele_eposta(r)
    dogum, kurum = rastgele_dogum_tarihi(r), r.choice(KURUMLAR)

    return _yerlestir([
        ("TEBLİGAT MAZBATASI\n\n", None),
        ("MUHATAP      : ", None), (ad, "AD"),
        ("\nT.C. Kimlik  : ", None), (tc, "TC"),
        ("\nDoğum Tarihi : ", None), (dogum, "DOGUM_TARIHI"),
        ("\nADRES        : ", None), (adres, "ADRES"),
        ("\nE-POSTA      : ", None), (eposta, "EPOSTA"),
        ("\nİLGİLİ KURUM : ", None), (kurum, "KURUM"),
        (f"\n\nTebliğ edilecek evrak: 2026/{r.randint(100, 999)} sayılı karar. "
         "Muhatabın adreste bulunamaması hâlinde durum şerh edilerek "
         "iade edilecektir.\n", None),
    ])


def ihtarname(tohum: int = 0) -> Belge:
    """İhtarname. Pasaport ve SGK sicili taşıyor."""
    r = random.Random(tohum + 6000)
    ad, pasaport = rastgele_ad(r), rastgele_pasaport(r)
    sgk, vkn = rastgele_sgk_sicil(r), rastgele_vkn(r)
    kurum = r.choice(KURUMLAR)

    return _yerlestir([
        ("İHTARNAME\n\n", None),
        ("KEŞİDECİ     : ", None), (kurum, "KURUM"),
        ("\nVergi No     : ", None), (vkn, "VKN"),
        ("\nSGK Sicil No : ", None), (sgk, "SGK_SICIL"),
        ("\n\nMUHATAP      : ", None), (ad, "AD"),
        ("\nPasaport No  : ", None), (pasaport, "PASAPORT"),
        ("\n\nİş sözleşmesinden doğan yükümlülüklerin yerine getirilmesi "
         "aksi hâlde yasal yollara başvurulacağı ihtar olunur.\n", None),
    ])


def fatura(tohum: int = 0) -> Belge:
    """Fatura. Kart numarası ve e-posta taşıyor."""
    r = random.Random(tohum + 7000)
    kurum, vkn = r.choice(KURUMLAR), rastgele_vkn(r)
    ad, eposta = rastgele_ad(r), rastgele_eposta(r)
    kart, iban = rastgele_kart(r), rastgele_iban(r)

    return _yerlestir([
        ("FATURA\n\n", None),
        ("SATICI       : ", None), (kurum, "KURUM"),
        ("\nVergi No     : ", None), (vkn, "VKN"),
        ("\nIBAN         : ", None), (iban, "IBAN"),
        ("\n\nALICI        : ", None), (ad, "AD"),
        ("\nE-POSTA      : ", None), (eposta, "EPOSTA"),
        ("\nÖdeme Kartı  : ", None), (kart, "KART"),
        (f"\n\nTutar: {r.randint(1000, 90000)} TL. Ödeme tahsil edilmiştir.\n", None),
    ])


# Kişisel veri de özel nitelikli veri de İÇERMEYEN adliye cümleleri.
# Sözlük katmanı bunlardan herhangi birini işaretlerse yanlış pozitif.
# Cömert bir sözlük kaçınılmaz olarak fazladan işaretler; buradaki amaç
# o fazlalığın ölçülebilir olması.
TEMIZ_CUMLELER = (
    "Tanığın dinlenmesine karar verildi.",
    "Duruşmada tanıklar dinlendi ve beyanları tutanağa geçirildi.",
    "Sözleşme sağlıklı biçimde yürütülmüştür.",
    "Dosya kapsamında sağlıklı bir değerlendirme yapılabilmesi için ek "
    "süre verilmiştir.",
    "Dosyanın incelenmesi için duruşma ertelenmiştir.",
    "Bilirkişi raporuna itiraz süresi içinde beyanda bulunulmamıştır.",
    "Mahkememizce yapılan yargılama sonucunda karar verilmiştir.",
    "Gerekçeli kararın taraflara tebliğine karar verildi.",
    "Dava dilekçesinde belirtilen hususlar değerlendirilmiştir.",
    "Aydın ilinde bulunan taşınmazın kaydı celp edilmiştir.",
    "Keşif yapılmasına ve masrafın davacıdan alınmasına karar verildi.",
    "Yargıtay içtihatları doğrultusunda inceleme yapılmıştır.",
    "Vekaletname dosyaya sunulmuş olup usulüne uygundur.",
    "Harç ve masrafların davalıdan tahsiline karar verilmiştir.",
    "Dinlenme salonunda bekleyen taraflara duyuru yapıldı.",
    "Talebin reddine, kararın taraflara bildirilmesine karar verildi.",
    "Süresi içinde istinaf yoluna başvurulabileceği hatırlatıldı.",
    # zor_metin ile aynı günlük-kelime-adları taşıyan tuzaklar: burada
    # sıradan kelime olarak geçiyorlar, ad olarak değil.
    "Olay deniz kenarında meydana gelmiştir.",
    "Davacının umut ettiği sonuç doğmamıştır.",
    "Taraflar barış içinde ayrılmıştır.",
    "Keşif şafak vakti yapılmıştır.",
    "Güneş açtıktan sonra keşfe devam edilmiştir.",
    "Dilekçe sevgi ve saygı ifadeleriyle sona ermektedir.",
    # zor_adres ile aynı amaç: yer sözcüğü geçiyor ama kişisel adres yok.
    "Duruşma Antalya Adliye Sarayı'nda görülmüştür.",
    "Dosya yetkisizlik nedeniyle Ankara'ya gönderilmiştir.",
    # "mahallinde" (olay yerinde) "mahalle" değildir -- bilinçli yakın-ıskalama.
    "Keşif mahallinde gerekli inceleme yapılmıştır.",
    "Tapu kaydı ilgili tapu müdürlüğünden celp edilmiştir.",
    # bozuk_metin ile aynı amaç: aksanı düşünce ada benziyormuş gibi
    # görünen sıradan kelimeler. Hasar sözlük katmanında yanlış pozitif
    # üretmemeli.
    "Olay denız kenarında meydana gelmıstır.",
    "Taraflar barıs ıcınde ayrılmıstır.",
    "Dosya ıcerıgı incelenmistir.",
)


def temiz_belgeler() -> list[Belge]:
    """Etiketsiz temiz cümleler; yanlış pozitif ölçümü için."""
    return [Belge(c) for c in TEMIZ_CUMLELER]


def ornekler(adet: int = 20) -> list[Belge]:
    """Ölçüm için belge kümesi.

    On bir tür. Hepsi bir arada her tanımlayıcı türünü en az bir kez
    içeriyor; bir tür hiçbir belgede geçmiyorsa ölçüm tablosu tam
    görünüp aslında eksik olur.

    Duruşma tutanağı bilerek temiz ve yanlış pozitif tuzakları taşıyor.
    zor_metin adları etiketsiz, düzyazı içinde taşıyor; zor_adres aynısını
    adresler için yapıyor -- AD/ADRES recall'ının üreteci değil aracı
    ölçmesi için. bozuk_metin aynı ilkeyi OCR/tarama hasarı için yapıyor:
    ad ve adres orada değil burada bozuluyor, araç hasarlı hâliyle
    ölçülüyor.
    """
    belgeler = []
    for i in range(adet):
        belgeler.append(dilekce(i))
        belgeler.append(bilirkisi_raporu(i))
        belgeler.append(ceza_dosyasi(i))
        belgeler.append(durusma_tutanagi(i))
        belgeler.append(tebligat(i))
        belgeler.append(ihtarname(i))
        belgeler.append(fatura(i))
        belgeler.append(saglik_raporu(i))
        belgeler.append(zor_metin(i))
        belgeler.append(zor_adres(i))
        belgeler.append(bozuk_metin(i))
    return belgeler


def ceza_dosyasi(tohum: int = 0) -> Belge:
    """Özel nitelikli veri içeren belge (KVKK md. 6).

    Maskelenecek alan olmayan, cümlenin kendisinin veri olduğu durumu
    sınamak için. Etiketlerde yalnızca tanımlayıcılar var; özel
    nitelikli kısım maskelenmiyor, işaretleniyor.
    """
    r = random.Random(tohum + 2000)
    ad, tc = rastgele_ad(r), rastgele_tc(r)

    return _yerlestir([
        ("ANTALYA CUMHURİYET BAŞSAVCILIĞI\n\n", None),
        ("ŞÜPHELİ   : ", None), (ad, "AD"),
        (" (T.C. Kimlik No: ", None), (tc, "TC"), (")", None),
        (f"\nSORUŞTURMA NO: 2026/{r.randint(1000, 9999)}\n\n", None),
        ("Şüphelinin ", None),
        ("adli sicil kaydında daha önce uyuşturucu madde kullanmaktan "
         "mahkûmiyeti bulunduğu", "CEZA_MAHKUMIYETI"),
        (" tespit edilmiştir. Şüphelinin ", None),
        ("kronik bir rahatsızlığı nedeniyle sürekli ilaç kullandığı",
         "SAGLIK"),
        (", bu nedenle hastane raporu sunduğu anlaşılmıştır. ", None),
        ("Sendika üyeliği bulunduğu", "DERNEK_VAKIF_SENDIKA"),
        (" beyan edilmiştir.\n", None),
    ])


def saglik_raporu(tohum: int = 0) -> Belge:
    """Sağlık verisi ağırlıklı belge."""
    r = random.Random(tohum + 3000)
    ad, tc = rastgele_ad(r), rastgele_tc(r)

    return _yerlestir([
        ("ADLİ TIP KURUMU RAPORU\n\n", None),
        ("İLGİLİ    : ", None), (ad, "AD"),
        (" (T.C. Kimlik No: ", None), (tc, "TC"), (")", None),
        (f"\nRAPOR NO  : 2026/{r.randint(100, 999)}\n\n", None),
        ("Yapılan muayenede ilgilinin ", None),
        ("kalıcı iş göremezlik durumu bulunduğu, tedavisinin sürdüğü",
         "SAGLIK"),
        (" tespit edilmiştir. Ayrıca ", None),
        ("genetik yatkınlığa dair DNA incelemesi", "GENETIK"),
        (" yapılmıştır.\n", None),
    ])


def _son_unlu(kelime: str) -> str:
    """Kelimenin sonundan geriye doğru ilk ünlüsü (ünlü uyumu için)."""
    for c in reversed(kelime):
        if c in "aeıioöuü":
            return c
        if c in "AEIİOÖUÜ":
            return "ı" if c == "I" else ("i" if c == "İ" else c.lower())
    return "e"


def _iyelik_eki(kelime: str) -> str:
    """Tamlayan eki ("-in" hâli): kalın/ince, düz/yuvarlak uyumuna göre.

    "Demir" -> "'in", "Kaya" -> "'nın" (ünlüyle bitince araya "n" girer).
    """
    ek = {
        "a": "ın", "ı": "ın", "e": "in", "i": "in",
        "o": "un", "u": "un", "ö": "ün", "ü": "ün",
    }[_son_unlu(kelime)]
    if kelime[-1] in "aeıioöuüAEIİOÖUÜ":
        ek = "n" + ek
    return "'" + ek


def _yonelme_eki(kelime: str) -> str:
    """Yönelme eki ("-e" hâli): kalın/ince uyumuna göre.

    Ünlüyle bitiyorsa araya "y" girer: "Kaya" -> "'ya", "Demir" -> "'e".
    """
    ek = "a" if _son_unlu(kelime) in "aıou" else "e"
    if kelime[-1] in "aeıioöuüAEIİOÖUÜ":
        ek = "y" + ek
    return "'" + ek


def zor_metin(tohum: int = 0) -> Belge:
    """Etiketsiz, adliye diline yakın düzyazı: adlar rol etiketi olmadan geçiyor.

    Bugüne dek ölçülen AD/ADRES recall'ı, adın hep "DAVACI :" gibi
    öngörülebilir bir etiketin hemen ardından geldiği belgelere
    dayanıyordu -- bu araç değil üreteci ölçmek demekti. Burada ad; tek
    başına soyadıyla, kesme işaretli hâl ekiyle, günlük kelimeyle
    çakışan bir adla, rol sözcüğünden bağımsız ya da aynı cümlede iki
    adla geçiyor.

    Etiket sınırı: "Ahmet Demir'in" gibi durumlarda etiketlenen alan
    kesme işaretinden ÖNCEKİ ad+soyaddır ("Ahmet Demir"); hâl eki
    etikete dahil değildir, çünkü maskeleme aracının değiştirmesi
    gereken kısım budur -- ek cümlenin kendisine ait kalır.
    """
    r = random.Random(tohum + 8000)
    ad1 = rastgele_ad(r)
    ad1_soyad = ad1.split(" ", 1)[1]
    ad2 = rastgele_ad(r)
    ad2_soyad = ad2.split(" ", 1)[1]
    ad3 = rastgele_ad(r)

    return _yerlestir([
        (f"ANTALYA {r.randint(1, 12)}. ASLİYE HUKUK MAHKEMESİ\n\n", None),
        ("GEREKÇELİ KARAR\n\n", None),
        ("Dosya kapsamında yapılan incelemede, ", None),
        (ad1, "AD"),  # şekil 2: tam ad + kesme + tamlayan eki
        (_iyelik_eki(ad1_soyad), None),
        (" beyanı alınmış, olayın gelişimine dair ayrıntılı bilgi "
         "verilmiştir. Aynı celsede dinlenen ", None),
        (ad1_soyad, "AD"),  # şekil 1: soyadı tek başına, rol etiketi yok
        (", beyanında olayı farklı anlatmıştır. ", None),
        (ad2, "AD"),  # şekil 3: yönelme (dative) hâli
        (_yonelme_eki(ad2_soyad), None),
        (" usulüne uygun tebligat yapılmıştır. Tanıklardan ", None),
        (ad3, "AD"),  # şekil 5: rol sözcüğünden ayrı, yapılandırılmış etiket yok
        (" olayı doğrulamıştır. ", None),
        ("Deniz Çelik", "AD"),  # şekil 4: günlük kelime ad olarak kullanılmış
        (" duruşmaya mazeretsiz katılmamış, beyanı sonradan alınmıştır. ", None),
        ("Barış Güneş", "AD"),  # şekil 6: aynı cümlede iki ad (1/2)
        (" ile ", None),
        ("Umut Şafak", "AD"),  # şekil 6: aynı cümlede iki ad (2/2)
        (" arasında imzalanan protokolün geçerliliği bu davanın konusunu "
         "oluşturmaktadır. Taraf vekillerinin beyanları ve dosyadaki "
         "belgeler birlikte değerlendirilerek aşağıdaki şekilde hüküm "
         "kurulmuştur.\n", None),
    ])


def zor_adres(tohum: int = 0) -> Belge:
    """Etiketsiz, adliye diline yakın adresler: ADRES hep "ADRES :" gibi
    öngörülebilir bir etiketin ardından gelmiyor.

    Bugüne dek ölçülen ADRES recall'ı, adresin hep bu tür bir etiketin
    hemen ardından geldiği belgelere dayanıyordu -- bu araç değil
    üreteci ölçmek demekti (zor_metin'in AD için yaptığı düzeltmenin
    aynısı, burada ADRES için). Burada adres; adres sözcüğü kendisinden
    SONRA gelerek, kesme işaretli hâl ekiyle, tam idari zincir olarak,
    sadece mahalle adıyla ya da hiçbir adres sözcüğü olmadan geçiyor.

    Etiket sınırı: Türkçe hâl eki cümleye ait, adrese değil -- zor_metin'in
    ad etiketlerinde izlenen ilkenin aynısı. "Sokak'taki" içinde etiketlenen
    kısım "Sokak"tır, "'taki" değildir; "Mahallesi'nde" içinde etiketlenen
    kısım "Mahallesi"dir, "'nde" değildir.
    """
    r = random.Random(tohum + 9000)

    # şekil 1: adres önce, "adresinde" sözcüğü ondan SONRA (rastgele_adres'i
    # olduğu gibi kullanıyor).
    adres1 = rastgele_adres(r)

    # şekil 2: mahalle + sokak, kesme işaretli hâl ekiyle. "'taki" sabit
    # çünkü "Sokak" hep aynı ünsüz/ünlüyle bitiyor (kalın, ünsüz-son).
    mahalle2 = r.choice(MAHALLELER)
    sokak2 = r.randint(1, 90)
    adres2 = f"{mahalle2} Mahallesi {sokak2}. Sokak"

    # şekil 3: tam idari zincir (il-ilçe-mahalle-sokak-no).
    il3 = r.choice(ILLER)
    mahalle3 = r.choice(MAHALLELER)
    sokak3 = r.randint(1, 90)
    no3 = r.randint(1, 60)
    adres3 = (
        f"{il3} ili {ILCELER[il3]} ilçesi {mahalle3} Mahallesi "
        f"{sokak3}. Sokak No: {no3}"
    )

    # şekil 4: sadece mahalle adı, ikametgah olarak. "'nde" sabit çünkü
    # "Mahallesi" hep aynı ünlüyle bitiyor (ince, ünlü-son).
    mahalle4 = r.choice(MAHALLELER)
    adres4 = f"{mahalle4} Mahallesi"

    # şekil 5: yakınında hiçbir adres sözcüğü yok -- "numarasına" var ama
    # "adres" sözcüğü hiç geçmiyor.
    mahalle5 = r.choice(MAHALLELER)
    cadde5 = r.randint(1, 90)
    no5 = r.randint(1, 60)
    adres5 = f"{mahalle5} Mahallesi {cadde5}. Cadde No: {no5}"

    return _yerlestir([
        (f"ANTALYA {r.randint(1, 12)}. ASLİYE HUKUK MAHKEMESİ\n\n", None),
        ("GEREKÇELİ KARAR\n\n", None),
        ("Dosya kapsamında yapılan incelemede, müvekkilin ", None),
        (adres1, "ADRES"),  # şekil 1
        (" adresinde ikamet ettiği anlaşılmıştır. Yapılan tebligatta "
         "muhatabın ", None),
        (adres2, "ADRES"),  # şekil 2
        ("'taki dairede oturduğu bilgisi edinilmiştir. Taşınmaz ", None),
        (adres3, "ADRES"),  # şekil 3
        (" adresinde kayıtlıdır. Davalı, ", None),
        (adres4, "ADRES"),  # şekil 4
        ("'nde ikamet etmektedir. Tebligat ", None),
        (adres5, "ADRES"),  # şekil 5
        (" numarasına yapılmıştır. Taraf vekillerinin beyanları ve "
         "dosyadaki belgeler birlikte değerlendirilerek aşağıdaki "
         "şekilde hüküm kurulmuştur.\n", None),
    ])


def durusma_tutanagi(tohum: int = 0) -> Belge:
    """Özel nitelikli veri İÇERMEYEN tutanak.

    Yanlış pozitif tuzaklarını bilerek barındırıyor: "tanık dinlenmesi"
    ifadesi sözlükteki "din" kökünü, "tanık" ise "tanı" kökünü tetikleme
    riski taşıyor. Bu belge işaretlenirse araç adliyede kullanılamaz.
    """
    r = random.Random(tohum + 4000)
    ad, tanik = rastgele_ad(r), rastgele_ad(r)

    return _yerlestir([
        (f"DURUŞMA TUTANAĞI\n\nESAS NO: 2026/{r.randint(100, 999)}\n\n", None),
        ("Davacı ", None), (ad, "AD"),
        (" duruşmada hazır. Tanık ", None), (tanik, "AD"),
        (" dinlenmek üzere çağrıldı. Tanığın dinlenmesine karar verildi. "
         "Beyanı alındı ve tutanağa geçirildi. Dosyanın incelenmesi için "
         "duruşma ertelenmiştir.\n", None),
    ])


# Aksan katlaması: ş/ğ/ö/ü/ç ve büyük İ, tarayıcı Türkçe olmayan bir
# profille çalıştığında en yakın düz Latin harfe düşer. "ı" burada YOK
# -- iki farklı hasar biçiminde iki farklı hedefe gidiyor (aşağıya bkz.),
# o yüzden ayrı ele alınıyor.
_AKSAN_KATLAMA = str.maketrans({
    "ş": "s", "Ş": "S",
    "ğ": "g", "Ğ": "G",
    "ö": "o", "Ö": "O",
    "ü": "u", "Ü": "U",
    "ç": "c", "Ç": "C",
    "İ": "I",
})

# "rn" iki harf yan yana taranınca "m"ye, "m" de bazı fontlarda "rn"ye
# benziyor. Büyük harfe bilerek uygulanmıyor: blok harfle yazılan
# başlıklarda (bkz. bozuk_metin şekil 5) bu karışıklık gözlenmiyor.
_RN_M_DESENI = re.compile(r"rn|m")


def ocr_hasari_uygula(
    metin: str,
    r: random.Random,
    *,
    glif_karisikligi: bool = False,
    rn_m_karisikligi: bool = False,
) -> str:
    """Taranmış bir belgede gerçekten görülen OCR/harf-okuma hasarını simüle eder.

    tespit.py'deki OCR onarımı kontrol hanesini yeniden doğrulayarak
    çalışıyor; ad ve adreste kontrol hanesi yok, o yaklaşım buraya
    taşınamaz. Bu fonksiyon onarmıyor, tam tersini yapıyor: hasarı
    üretiyor, araç hasarlı hâliyle -- hiç onarılmadan -- ölçülüyor.

    İki taban davranış var:

    - Varsayılan (`glif_karisikligi=False`): tarayıcı Türkçe olmayan bir
      profille çalıştığında görülen en yaygın hasar. Bütün aksanlar
      sessizce düşer: ş->s, ğ->g, ı->i, İ->I, ö->o, ü->u, ç->c.
    - `glif_karisikligi=True`: "ı" harfi "i" değil, görsel olarak
      karışan "l" ya da "1" olarak okunur -- klasik glif karışıklığı.
      Diğer aksanlar (ş, ğ, İ, ö, ü, ç) yine aynı şekilde düşer; onların
      Latin karşılığı zaten tek ve belirsizliksiz, karışacak ikinci bir
      aday yok.

    `rn_m_karisikligi=True` verilirse küçük harfli "rn"/"m" dizileri
    rastgele yön değiştirir. Varsayılan kapalı: bu değişim harf sayısını
    değiştiriyor, o yüzden yalnızca açıkça istendiğinde uygulanıyor.

    `r` aynı durumdaysa çıktı da birebir aynıdır -- ölçüm tekrarlanabilir
    olsun diye. Türkçe karakter içeren bir girdi için çıktı girdiden HER
    ZAMAN farklıdır; sessizce aynısını döndürmek hasarı gizler.
    """
    hasarli = metin.translate(_AKSAN_KATLAMA)
    if glif_karisikligi:
        hasarli = "".join(r.choice(("l", "1")) if c == "ı" else c for c in hasarli)
    else:
        hasarli = hasarli.replace("ı", "i")

    if rn_m_karisikligi:

        def _degistir(m: re.Match[str]) -> str:
            parca = m.group()
            karsilik = "m" if parca == "rn" else "rn"
            return karsilik if r.random() < 0.6 else parca

        hasarli = _RN_M_DESENI.sub(_degistir, hasarli)

    return hasarli


def bozuk_metin(tohum: int = 0) -> Belge:
    """OCR/tarama hasarı görmüş adliye metni: ad ve adres orijinal değil,
    taranmış belgede gerçekten çıkan bozuk hâlleriyle geçiyor.

    zor_metin ve zor_adres'in yaptığını burada OCR hasarı için yapıyoruz:
    etiket değeri metinde GEÇTİĞİ HÂLİYLEDİR -- maskelenmesi gereken
    hasarlı ad/adrestir, temiz hâli değil. tespit.py'deki OCR onarımı
    kontrol hanesi olan alanlar (TC, VKN...) için var; burada kontrol
    hanesi yok, o onarım aktarılamıyor. Bu üretici onarmıyor, aracın
    hasarlı hâliyle -- çıplak -- nasıl başa çıktığını ölçüyor.

    Beş durum:

    1. Tüm aksanları düşmüş tam ad.
    2. Klasik glif karışıklığı: "ı" -> "l" ya da "1".
    3. Aksanları düşmüş adres.
    4. Anafor hasar altında, iki yönde: bir yerde tam ad temiz, sonraki
       çıplak soyadı hasarlı; başka bir yerde tam ad hasarlı, sonraki
       çıplak soyadı temiz. Bu ikisi model.soyadi_yay'ı tam alt dizi
       eşleşmesi yaptığı için kırıyordu -- 160 hasarlı etiketten kaçan
       40'ın tamamı buydu. soyadi_yay artık aksan katlanmış metinde
       arıyor; bu iki durum onun regresyon testidir.
    5. BÜYÜK HARF ad, Türkçe I/İ ayrımının kaybolmasıyla.
    """
    r = random.Random(tohum + 10000)

    # 1. tam aksan düşmesi.
    ad1 = "Ayşe Yıldırım"
    ad1_hasarli = ocr_hasari_uygula(ad1, r)

    # 2. glif karışıklığı (ı -> l/1).
    ad2 = "Mustafa Kılıç"
    ad2_hasarli = ocr_hasari_uygula(ad2, r, glif_karisikligi=True)

    # 3. adres, aksan düşmesi.
    adres1 = "Bahçelievler Mahallesi 12. Sokak No: 5"
    adres1_hasarli = ocr_hasari_uygula(adres1, r)

    # 4a. anafor: tam ad temiz, sonraki çıplak soyadı hasarlı.
    ad3 = "Elif Şahin"
    ad3_soyad_hasarli = ocr_hasari_uygula("Şahin", r)

    # 4b. anafor: tam ad hasarlı, sonraki çıplak soyadı temiz.
    ad4 = "Zeynep Öztürk"
    ad4_hasarli = ocr_hasari_uygula(ad4, r)
    ad4_soyad_temiz = ad4.split(" ", 1)[1]

    # 5. büyük harf, I/İ ayrımının kaybolması.
    ad5 = "İBRAHİM ŞAHİN"
    ad5_hasarli = ocr_hasari_uygula(ad5, r)

    # Belgenin TAMAMI hasarlı: çevre metin de aksansız. İlk hâlinde
    # yalnızca adlar bozuktu ve metin "taramada Türkçe karakterler düştü"
    # diye açıkça yazıyordu -- ikisi de modele bedava ipucu veriyordu.
    # Temiz bir cümlenin ortasındaki tek bozuk kelime zaten "burada ad
    # var" demektir; gerçek taramada böyle bir kontrast olmaz, her şey
    # aynı ölçüde bozulur. Açıklayıcı cümleler de kaldırıldı: taranmış
    # belge kendi hasarını anlatmaz.
    return _yerlestir([
        (f"ANTALYA {r.randint(1, 12)}. ASLIYE HUKUK MAHKEMESI\n\n", None),
        ("GEREKCELI KARAR\n\n", None),
        ("DAVACI  : ", None),
        (ad1_hasarli, "AD"),
        ("\nADRES   : ", None),
        (adres1_hasarli, "ADRES"),
        ("\nDAVALI  : ", None),
        (ad2_hasarli, "AD"),
        ("\n\nDurusmada dinlenen ", None),
        (ad3, "AD"),
        (" beyanda bulunmus, olayin gelisimini ayrintili bicimde "
         "anlatmistir. ", None),
        (ad3_soyad_hasarli, "AD"),
        (", ifadesinde onceki beyanini tekrar etmistir. ", None),
        (ad4_hasarli, "AD"),
        (" adina duzenlenen belge dosyaya sunulmus, sozlesme ", None),
        (ad4_soyad_temiz, "AD"),
        (" tarafindan imzalanmistir. Tanik ", None),
        (ad5_hasarli, "AD"),
        (" dinlenmis, beyani tutanaga gecirilmistir. Taraf vekillerinin "
         "beyanlari ve dosyadaki belgeler birlikte degerlendirilerek "
         "asagidaki sekilde hukum kurulmustur.\n", None),
    ])
