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


# Kişisel veri de özel nitelikli veri de İÇERMEYEN adliye cümleleri.
# Sözlük katmanı bunlardan herhangi birini işaretlerse yanlış pozitif.
# Cömert bir sözlük kaçınılmaz olarak fazladan işaretler; buradaki amaç
# o fazlalığın ölçülebilir olması.
TEMIZ_CUMLELER = (
    "Tanığın dinlenmesine karar verildi.",
    "Duruşmada tanıklar dinlendi ve beyanları tutanağa geçirildi.",
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
)


def temiz_belgeler() -> list[Belge]:
    """Etiketsiz temiz cümleler; yanlış pozitif ölçümü için."""
    return [Belge(c) for c in TEMIZ_CUMLELER]


def ornekler(adet: int = 20) -> list[Belge]:
    """Ölçüm için belge kümesi.

    Dört tür: iki tanesi tanımlayıcı ağırlıklı, biri özel nitelikli
    veri içeriyor, biri hiçbiri -- sonuncusu yanlış pozitif tuzaklarını
    barındırıyor.
    """
    belgeler = []
    for i in range(adet):
        belgeler.append(dilekce(i))
        belgeler.append(bilirkisi_raporu(i))
        belgeler.append(ceza_dosyasi(i))
        belgeler.append(durusma_tutanagi(i))
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
