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
            sonuc.bulgular.append(Bulgu(tur, bas, son, deger))

    return sonuc


def bul(metin: str, saglayici: Saglayici) -> ModelSonucu:
    return cevabi_coz(metin, saglayici.sor(istem_hazirla(metin)))


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
    """

    model: str = "gemma4-abl-16k"
    adres: str = "http://127.0.0.1:11434"
    sicaklik: float = 0.0
    zaman_asimi: float = 180.0

    def sor(self, istem: str) -> str:
        import urllib.error
        import urllib.request

        govde = json.dumps({
            "model": self.model,
            "prompt": istem,
            "stream": False,
            "options": {"temperature": self.sicaklik},
        }).encode("utf-8")

        istek = urllib.request.Request(
            f"{self.adres}/api/generate",
            data=govde,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(istek, timeout=self.zaman_asimi) as y:
                return json.loads(y.read()).get("response", "")
        except urllib.error.URLError as e:
            raise RuntimeError(
                f"Ollama'ya ulaşılamadı ({self.adres}). Servis çalışıyor mu? "
                "OLLAMA_MODELS doğru dizini gösteriyor mu?"
            ) from e
