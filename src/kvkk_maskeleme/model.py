"""Model katmanı — isim, adres ve kurum tespiti.

Desen katmanı yapısal kimlikleri buluyor. İsim ve adres desenle
bulunamıyor: Türkçe adların bir kısmı günlük kelimeyle çakışıyor
(Deniz, Umut, Şafak, Barış, Güneş), yani "büyük harfle başlayan kelime"
kuralı hem kaçırıyor hem yanlış yakalıyor. Bağlam gerekiyor.

Buradaki asıl tasarım kararı: **modelden konum istemiyoruz, metin
istiyoruz.** Modeller karakter saymayı beceremiyor; "45. karakterden
56'ya kadar" dediğinde çoğu zaman yanlış oluyor. Bunun yerine bulduğu
ifadeyi aynen yazmasını istiyoruz, konumu biz buluyoruz. Yan faydası:
metinde geçmeyen bir ifade dönerse uydurma olduğu anlaşılıyor.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Protocol

from .tespit import Bulgu

MODEL_TURLERI = ("AD", "ADRES", "KURUM")

ISTEM = """Aşağıdaki Türkçe belgede geçen kişisel bilgileri bul.

Aradıkların:
- AD: kişi adı ve soyadı
- ADRES: açık adres, mahalle, sokak, kapı numarası
- KURUM: şirket, kurum, firma adı

Aramadıkların: kimlik numarası, telefon, IBAN, plaka. Onlar ayrı bir
adımda zaten bulundu.

Dikkat: Türkçede bazı adlar günlük kelimeyle aynıdır (Deniz, Umut,
Şafak, Barış, Güneş, Nur, Sevgi). Bunları yalnızca kişiye işaret
ediyorsa AD say, "deniz kenarı" gibi kullanımda sayma.

Mahkeme, savcılık gibi resmî makam adlarını KURUM sayma.

Yalnızca JSON dizisi döndür, başka hiçbir şey yazma. Her öğe belgede
geçtiği haliyle yazılmalı:

[{"tur": "AD", "deger": "..."}, {"tur": "ADRES", "deger": "..."}]

Hiçbir şey bulamazsan [] döndür.

BELGE:
---
{belge}
---"""


class Saglayici(Protocol):
    """Bir dil modeline istem gönderip metin cevabı alan her şey."""

    def sor(self, istem: str) -> str: ...


@dataclass
class ModelSonucu:
    bulgular: list[Bulgu] = field(default_factory=list)
    uydurma: list[str] = field(default_factory=list)
    bicim_hatasi: bool = False

    @property
    def uydurma_orani(self) -> float:
        toplam = len(self.bulgular) + len(self.uydurma)
        return len(self.uydurma) / toplam if toplam else 0.0


def istem_hazirla(metin: str) -> str:
    return ISTEM.replace("{belge}", metin)


def _json_ayikla(cevap: str) -> list[dict] | None:
    """Modelin cevabından JSON dizisini çıkarır.

    Modeller sık sık ```json çitiyle sarıyor, öncesine açıklama
    ekliyor ya da sonuna cümle iliştiriyor. İlk köşeli parantezle son
    köşeli parantez arasını almak bunların hepsini kurtarıyor.
    """
    cevap = re.sub(r"```(?:json)?|```", "", cevap).strip()
    bas, son = cevap.find("["), cevap.rfind("]")
    if bas == -1 or son <= bas:
        return None
    try:
        veri = json.loads(cevap[bas : son + 1])
    except json.JSONDecodeError:
        return None
    return veri if isinstance(veri, list) else None


def _konumlari_bul(metin: str, deger: str) -> list[tuple[int, int]]:
    """İfadenin metinde geçtiği bütün konumlar."""
    konumlar, i = [], metin.find(deger)
    while i != -1:
        konumlar.append((i, i + len(deger)))
        i = metin.find(deger, i + 1)
    return konumlar


def cevabi_coz(metin: str, cevap: str) -> ModelSonucu:
    """Model cevabını bulgulara çevirir, uydurmaları ayıklar."""
    veri = _json_ayikla(cevap)
    if veri is None:
        return ModelSonucu(bicim_hatasi=True)

    sonuc = ModelSonucu()
    for oge in veri:
        if not isinstance(oge, dict):
            continue
        tur = str(oge.get("tur", "")).upper().strip()
        deger = str(oge.get("deger", "")).strip()
        if tur not in MODEL_TURLERI or not deger:
            continue

        konumlar = _konumlari_bul(metin, deger)
        if not konumlar:
            # Model metinde olmayan bir şey döndürdü. Sayıyoruz ki
            # hangi modelin ne kadar uydurduğu ölçülebilsin.
            sonuc.uydurma.append(deger)
            continue

        for bas, son in konumlar:
            sonuc.bulgular.append(Bulgu(tur, bas, son, deger, kaynak="model"))

    return sonuc


# "Aydın ili" bir kişi değil bir yer. Kişinin soyadı da Aydın olabildiği
# için soyad yayarken bu sözcüklerden birinin izlediği geçişi atlıyoruz.
# "ile" bilerek listede yok: "Barış Güneş ile Umut Şafak" geçerli bir
# kullanım ve orada Güneş gerçekten soyad.
_YER_EKLERI = ("ili", "ilinde", "iline", "ilinden", "ilçesi", "ilçesinde")


def soyadi_yay(metin: str, bulgular: list[Bulgu]) -> list[Bulgu]:
    """Tam adı bulunan kişinin yalnız geçen soyadını da işaretler.

    Adliye metninde kişi bir kez tam adıyla anılıp sonrasında yalnızca
    soyadıyla geçiyor: "Güneş Yıldız'ın beyanı alınmış... aynı celsede
    dinlenen Yıldız, beyanında...". Model ikincisini kaçırıyor -- 160
    belgelik ölçümde kaçan adların **tamamı** bu biçimdeydi, ve kaçanlar
    günlük kelimeyle çakışan soyadlarda yoğunlaşıyordu (Aydın, Kaya,
    Yıldız, Aslan).

    Modele "bunu da bul" demek yerine burada arıyoruz: tam adı zaten
    bulduysak soyadın o belgedeki diğer geçişleri aynı kişidir. Kaçan
    isim sızıntı demek olduğu için bu katmanda tahmine yer yok.
    """
    mevcut = [(b.baslangic, b.bitis) for b in bulgular]
    yeni: list[Bulgu] = []

    soyadlar = {
        b.deger.split()[-1]
        for b in bulgular
        if b.tur == "AD" and len(b.deger.split()) > 1
    }
    for soyad in soyadlar:
        if len(soyad) < 3:
            continue
        for m in re.finditer(rf"\b{re.escape(soyad)}\b", metin):
            bas, son = m.start(), m.end()
            if any(a < son and bas < z for a, z in mevcut):
                continue
            devam = metin[son:son + 12].lstrip("'’").lstrip()
            if devam.split(" ")[0].rstrip(",.;:") in _YER_EKLERI:
                continue
            yeni.append(Bulgu("AD", bas, son, soyad, kaynak="soyad"))
            mevcut.append((bas, son))
    return yeni


def bul(metin: str, saglayici: Saglayici) -> ModelSonucu:
    sonuc = cevabi_coz(metin, saglayici.sor(istem_hazirla(metin)))
    sonuc.bulgular.extend(soyadi_yay(metin, sonuc.bulgular))
    return sonuc


@dataclass
class SahteSaglayici:
    """Model olmadan bütün zinciri test etmek için.

    Verilen cevabı olduğu gibi döndürür. Bozuk JSON, uydurma ifade,
    boş cevap gibi durumları da bununla sınıyoruz.
    """

    cevap: str = "[]"
    cagri_sayisi: int = 0
    son_istem: str = ""

    def sor(self, istem: str) -> str:
        self.cagri_sayisi += 1
        self.son_istem = istem
        return self.cevap


@dataclass
class OllamaSaglayici:
    """Yerel Ollama sunucusu.

    Bağımlılık eklememek için standart kütüphaneyle konuşuyor. Model
    ancak ilk çağrıda belleğe yükleniyor; bu nesneyi oluşturmak tek
    başına VRAM tüketmiyor.

    **`dusunme` varsayılan olarak kapalı.** Düşünme modu açık bir model
    bu işte cevaba hiç varmadan pencereyi doldurabiliyor: ölçtüğümüz
    bir modelde 16384 token'lık pencerenin tamamı düşünmeye gitti ve
    cevap boş döndü (`done_reason: length`), aynı istem düşünme
    kapalıyken 1,4 saniyede doğru JSON verdi. Buradaki iş akıl yürütmek
    değil, metinde geçen ifadeyi bulup yazmak; düşünme yalnızca maliyet.
    Boş cevap sessizce kaybolmuyor, `bicim_hatasi` olarak sayılıyor --
    ama sebebi görünmediği için burada varsayılanı kapalı tutuyoruz.

    `baglam` verilmezse Ollama kendi varsayılanını kullanıyor; bu
    makinede 4096 çıkıyor ve uzun belgelerde istem sessizce kırpılır.

    Varsayılan model ölçülerek seçildi. 21 belge, aynı istem, düşünme
    kapalı, tek değişen model (16 GB VRAM):

        model                              AD    KURUM  yanlış poz.  s/belge
        gemma-4-abliterated:12b-qat      %100    %100        0          1,6
        qwen3.5-abliterated:9b-q8_0      %100    %100        6          2,5
        Qwen3.6-abliterated:35b-a3b       %97   %77,8        0          3,8

    Qwen3.5 aynı recall'ı veriyor ama 17 temiz metnin 6'sını yanlışlıkla
    işaretledi; bu araçta temiz metni kirletmek kabul edilemez. Qwen3.6
    hem daha yavaş hem kurum adlarında zayıf. Kart değiştiğinde ölçümü
    tekrarla, bu sıralama donanıma bağlı.
    """

    model: str = "huihui_ai/gemma-4-abliterated:12b-qat"
    adres: str = "http://127.0.0.1:11434"
    sicaklik: float = 0.0
    zaman_asimi: float = 180.0
    dusunme: bool | None = False
    baglam: int | None = None

    def sor(self, istem: str) -> str:
        import urllib.error
        import urllib.request

        secenekler: dict[str, object] = {"temperature": self.sicaklik}
        if self.baglam is not None:
            secenekler["num_ctx"] = self.baglam

        govde_sozlugu: dict[str, object] = {
            "model": self.model,
            "prompt": istem,
            "stream": False,
            "options": secenekler,
        }
        if self.dusunme is not None:
            govde_sozlugu["think"] = self.dusunme

        govde = json.dumps(govde_sozlugu).encode("utf-8")

        istek = urllib.request.Request(
            f"{self.adres}/api/generate",
            data=govde,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(istek, timeout=self.zaman_asimi) as y:
                return json.loads(y.read()).get("response", "")
        except urllib.error.HTTPError as e:
            # HTTPError, URLError'ın alt sınıfı. Önce yakalanmazsa sunucu
            # ayaktayken bile "ulaşılamadı" diyoruz ve kullanıcı servisi
            # kurcalamaya başlıyor; oysa en sık sebep 404, yani modelin
            # kurulu olmaması.
            if e.code == 404:
                raise RuntimeError(
                    f"Ollama ayakta ama '{self.model}' modeli kurulu değil. "
                    "`ollama list` kurulu modelleri gösterir."
                ) from e
            raise RuntimeError(
                f"Ollama {e.code} döndürdü ({e.reason})."
            ) from e
        except urllib.error.URLError as e:
            raise RuntimeError(
                f"Ollama'ya ulaşılamadı ({self.adres}). Servis çalışıyor mu? "
                "OLLAMA_MODELS doğru dizini gösteriyor mu?"
            ) from e
