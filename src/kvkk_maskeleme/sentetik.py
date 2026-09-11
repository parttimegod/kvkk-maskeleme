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
)


def temiz_belgeler() -> list[Belge]:
    """Etiketsiz temiz cümleler; yanlış pozitif ölçümü için."""
    return [Belge(c) for c in TEMIZ_CUMLELER]


def ornekler(adet: int = 20) -> list[Belge]:
    """Ölçüm için belge kümesi.

    Sekiz tür. Hepsi bir arada her tanımlayıcı türünü en az bir kez
    içeriyor; bir tür hiçbir belgede geçmiyorsa ölçüm tablosu tam
    görünüp aslında eksik olur.

    Duruşma tutanağı bilerek temiz ve yanlış pozitif tuzakları taşıyor.
    zor_metin ise adları etiketsiz, düzyazı içinde taşıyor -- AD/ADRES
    recall'ının üreteci değil aracı ölçmesi için.
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
        belgeler.append(zor_metin(i))
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
