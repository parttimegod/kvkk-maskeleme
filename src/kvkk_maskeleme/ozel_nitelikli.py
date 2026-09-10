"""Özel nitelikli kişisel veri tespiti (KVKK md. 6).

Kategoriler kanundan birebir alındı: ırk ve etnik köken, siyasi düşünce,
felsefi inanç, din ve mezhep, kılık kıyafet, dernek/vakıf/sendika
üyeliği, sağlık, cinsel hayat, ceza mahkûmiyeti ve güvenlik tedbirleri,
biyometrik ve genetik veri. Uyum yapan biri çıktıyı doğrudan maddeye
eşleyebilsin diye kanun terminolojisine sadık kalındı.

Bu katman **maskelemiyor, işaretliyor.** Sebebi şu: özel nitelikli veri
bir alan değil, bağlamdır. "Sanık uyuşturucu kullanmaktan sabıkalıdır"
cümlesinde maskelenecek bir alan yok -- cümlenin kendisi veridir.
Maskelemeye kalkışmak belgeyi anlamsızlaştırır. Doğru davranış, belgenin
özel nitelikli veri taşıdığını söyleyip kararı insana bırakmak.

Hata dengesi de burada terstir. Tanımlayıcı katmanında yanlış pozitif
kötüdür; burada yanlış negatif kötüdür. Boşuna işaretlenen belge bir
insanın birkaç dakikasına mal olur, kaçan belge KVKK ihlaline. Bu yüzden
sözlük katmanı bilerek cömert tutuldu.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from .model import Saglayici

# KVKK md. 6'daki sıralamayla.
KATEGORILER = (
    "IRK_ETNIK",
    "SIYASI_DUSUNCE",
    "FELSEFI_INANC",
    "DIN_MEZHEP",
    "KILIK_KIYAFET",
    "DERNEK_VAKIF_SENDIKA",
    "SAGLIK",
    "CINSEL_HAYAT",
    "CEZA_MAHKUMIYETI",
    "BIYOMETRIK",
    "GENETIK",
)

# Kelime kökleri. Türkçe ekli olduğu için sonuna ek gelebilir; kısa
# köklerin başka kelimeyi yakalamaması için kelime sınırı aranıyor
# ("din" kökü "aydın"ı yakalamamalı).
IPUCLARI: dict[str, tuple[str, ...]] = {
    "CEZA_MAHKUMIYETI": (
        "sabika", "mahkumiyet", "mahkum", "hukumlu", "tutuklu", "gozalti",
        "adli sicil", "denetimli serbestlik", "infaz", "ceza evi", "cezaevi",
        "adli kontrol", "beraat", "hagb", "tekerrur",
    ),
    "SAGLIK": (
        "hastalik", "hastane", "teshis", "tedavi", "ameliyat",
        "engelli", "malul", "psikiyatri", "psikolojik", "recete", "epikriz",
        "kronik", "tesekkullu", "sagliksiz", "rahatsizlik", "ilac",
        "bagimlilik", "uyusturucu", "alkolik", "saglik", "sagligi", "hasta",
    ),
    "DIN_MEZHEP": (
        # "din" tam kelime; ekli hâlleri "dini" ile yakalanıyor. İkisini
        # ayırmak zorundayız çünkü "din" + ek deseni "dinlenme"yi de
        # yakalıyor ve o kelime her duruşma tutanağında geçiyor.
        "din", "dini", "dinsel", "dindar",
        "mezhep", "inanc", "cemaat", "ibadet", "musluman",
        "hristiyan", "musevi", "alevi", "sunni", "tarikat",
    ),
    "SIYASI_DUSUNCE": (
        "parti uyeligi", "siyasi gorus", "siyasi dusunce", "oy verdigi",
        "secim calismasi",
    ),
    "DERNEK_VAKIF_SENDIKA": (
        "sendika", "dernek uyesi", "vakif uyesi", "konfederasyon",
    ),
    "IRK_ETNIK": (
        "etnik", "irk", "kurt kokenli", "roman kokenli", "azinlik",
    ),
    "CINSEL_HAYAT": (
        "cinsel yonelim", "cinsel hayat", "cinsel iliski", "cinsel istismar",
    ),
    "BIYOMETRIK": (
        "parmak izi", "yuz tanima", "retina", "iris taramasi", "avuc izi",
        "ses kaydi analizi",
    ),
    "GENETIK": (
        "dna", "genetik", "kalitim", "babalik testi",
    ),
    "FELSEFI_INANC": (
        "felsefi inanc", "vicdani ret", "dunya gorusu",
    ),
    "KILIK_KIYAFET": (
        "basortu", "turban", "kilik kiyafet",
    ),
}


@dataclass(frozen=True)
class OzelNitelikliBulgu:
    kategori: str
    kanit: str
    baslangic: int
    bitis: int
    kaynak: str  # "sozluk" ya da "model"


@dataclass
class OzelNitelikliRapor:
    bulgular: list[OzelNitelikliBulgu] = field(default_factory=list)

    @property
    def var_mi(self) -> bool:
        return bool(self.bulgular)

    def kategoriler(self) -> set[str]:
        return {b.kategori for b in self.bulgular}

    def uyari(self) -> str:
        if not self.var_mi:
            return "Özel nitelikli kişisel veri işareti bulunmadı."
        k = ", ".join(sorted(self.kategoriler()))
        return (
            f"Bu belge özel nitelikli kişisel veri içeriyor olabilir ({k}). "
            "KVKK md. 6 uyarınca işlenmesi açık rıza veya kanunda öngörülen "
            "bir hâle bağlıdır. Maskeleme bu veriyi kaldırmaz."
        )


def _kucult(metin: str) -> str:
    """Türkçe duyarlı küçük harf ve aksan indirgeme.

    str.lower() Türkçede I/İ'yi yanlış çeviriyor; ayrıca ipucu kökleri
    aksansız yazıldığı için metni de aksansızlaştırıyoruz.
    """
    metin = unicodedata.normalize("NFC", metin)
    metin = metin.replace("İ", "i").replace("I", "ı").lower()
    katlama = str.maketrans({"ı": "i", "ğ": "g", "ü": "u", "ş": "s", "ö": "o", "ç": "c"})
    metin = metin.translate(katlama)
    metin = unicodedata.normalize("NFKD", metin)
    return "".join(k for k in metin if not unicodedata.combining(k))


# Bu köklerde ek aramıyoruz. Kısa oldukları için başka kelimenin başına
# denk geliyorlar ve adliye metninde sık geçen kelimeleri yakalıyorlar:
# "din" kökü "dinlenme"yi buluyor, oysa "tanık dinlenmesi" her duruşma
# tutanağında var. Bu köklerde tam kelime şart.
#
# "saglik" ve "hasta" aynı sebeple burada. "saglik" öneki "sağlıklı"yı
# yakalıyordu; "sözleşme sağlıklı biçimde yürütülmüştür" adliye metninde
# sık geçiyor ve sağlık verisi değil. Ekli hâller ("sağlığı",
# "sağlığının") için ayrı kök gerekiyor, çünkü k/ğ yumuşaması yüzünden
# "saglik" öneki onları zaten tutmuyordu.
TAM_KELIME = frozenset({"din", "irk", "dna", "saglik", "hasta"})


def _desen(kok: str) -> re.Pattern[str]:
    if kok in TAM_KELIME:
        return re.compile(rf"\b{re.escape(kok)}\b", re.I)
    # Türkçe eklemeli; kök kelime başında olsun, sonuna ek gelebilsin.
    return re.compile(rf"\b{re.escape(kok)}\w*", re.I)


_DERLENMIS = {
    kategori: [(kok, _desen(kok)) for kok in kokler]
    for kategori, kokler in IPUCLARI.items()
}


def sozlukle_bul(metin: str) -> list[OzelNitelikliBulgu]:
    """Kelime köklerine göre işaretler.

    Kesin sonuç değil, taban. Kaçırmamak için cömert: "uyuşturucu"
    kelimesi geçen her belge sağlık başlığıyla işaretlenir, doğru olup
    olmadığına insan bakar.
    """
    kucuk = _kucult(metin)
    adaylar = []
    for kategori, kokler in _DERLENMIS.items():
        for _kok, desen in kokler:
            for m in desen.finditer(kucuk):
                adaylar.append(
                    OzelNitelikliBulgu(
                        kategori=kategori,
                        kanit=metin[m.start() : m.end()],
                        baslangic=m.start(),
                        bitis=m.end(),
                        kaynak="sozluk",
                    )
                )

    # "mahkum" ve "mahkumiyet" aynı kelimeyi yakalıyor; aynı kategoride
    # çakışan eşleşmelerden uzun olanı tutuyoruz.
    adaylar.sort(key=lambda b: (-(b.bitis - b.baslangic), b.baslangic))
    secilen: list[OzelNitelikliBulgu] = []
    for aday in adaylar:
        if not any(
            s.kategori == aday.kategori
            and aday.baslangic < s.bitis
            and s.baslangic < aday.bitis
            for s in secilen
        ):
            secilen.append(aday)

    return sorted(secilen, key=lambda b: b.baslangic)


ISTEM = """Aşağıdaki Türkçe belgeyi KVKK madde 6 kapsamındaki özel
nitelikli kişisel veriler açısından incele.

Kategoriler:
- IRK_ETNIK: ırk, etnik köken
- SIYASI_DUSUNCE: siyasi görüş, parti üyeliği
- FELSEFI_INANC: felsefi inanç, dünya görüşü
- DIN_MEZHEP: din, mezhep, inanç
- KILIK_KIYAFET: kılık ve kıyafet
- DERNEK_VAKIF_SENDIKA: dernek, vakıf, sendika üyeliği
- SAGLIK: hastalık, teşhis, tedavi, engellilik, bağımlılık
- CINSEL_HAYAT: cinsel hayat, cinsel yönelim
- CEZA_MAHKUMIYETI: mahkûmiyet, sabıka, güvenlik tedbiri, tutukluluk
- BIYOMETRIK: parmak izi, yüz tanıma, retina
- GENETIK: DNA, genetik veri

Önemli: bu veriler bir alan değil, cümledir. Bir kişinin sağlık durumu
ya da mahkûmiyeti anlatılıyorsa, o cümleyi kanıt olarak ver.

Kişi adı, kimlik numarası, adres arama -- onlar ayrı bir adımda ele
alındı.

Emin değilsen işaretle. Kaçırmak, fazladan işaretlemekten kötüdür.

Yalnızca JSON dizisi döndür:
[{"kategori": "SAGLIK", "kanit": "belgede geçen cümle"}]

Hiçbir şey yoksa [] döndür.

BELGE:
---
{belge}
---"""


def istem_hazirla(metin: str) -> str:
    return ISTEM.replace("{belge}", metin)


def modelle_bul(metin: str, saglayici: Saglayici) -> list[OzelNitelikliBulgu]:
    """Model cevabını bulgulara çevirir.

    Tanımlayıcı katmanındaki mantığın aynısı: modelden konum değil metin
    isteniyor, konumu biz buluyoruz, metinde geçmeyen kanıt atılıyor.
    """
    from .model import _json_ayikla

    veri = _json_ayikla(saglayici.sor(istem_hazirla(metin)))
    if veri is None:
        return []

    bulgular = []
    for oge in veri:
        if not isinstance(oge, dict):
            continue
        kategori = str(oge.get("kategori", "")).upper().strip()
        kanit = str(oge.get("kanit", "")).strip()
        if kategori not in KATEGORILER or not kanit:
            continue
        i = metin.find(kanit)
        if i == -1:
            continue  # model uydurmuş
        bulgular.append(
            OzelNitelikliBulgu(kategori, kanit, i, i + len(kanit), "model")
        )
    return bulgular


def incele(metin: str, saglayici: Saglayici | None = None) -> OzelNitelikliRapor:
    """Belgeyi özel nitelikli veri açısından inceler.

    Sözlük katmanı her zaman çalışır; sağlayıcı verilirse model katmanı
    da eklenir. İkisi birleştirilir, aynı yerdeki tekrarlar ayıklanır.
    """
    bulgular = sozlukle_bul(metin)
    if saglayici is not None:
        for m in modelle_bul(metin, saglayici):
            if not any(
                b.kategori == m.kategori
                and b.baslangic < m.bitis
                and m.baslangic < b.bitis
                for b in bulgular
            ):
                bulgular.append(m)

    return OzelNitelikliRapor(sorted(bulgular, key=lambda b: b.baslangic))
