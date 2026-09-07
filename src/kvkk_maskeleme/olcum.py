"""Ölçüm.

Bu alanda beş açık kaynak proje var ve hiçbiri ne kadar iyi çalıştığını
söylemiyor. "Kişisel verileri maskeler" cümlesi ölçülmeden bir şey ifade
etmiyor; bir aracın yüzde 60 recall'la çalışması, çalışmaması demektir.

Sentetik belgeler etiketli olduğu için burada gerçek recall ve precision
hesaplanabiliyor. Model katmanı olmadan da çalışır: yapısal türlerde
desen katmanının performansını verir.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .maskeleme import maskele
from .model import Saglayici
from .sentetik import Belge, ornekler

YAPISAL = {"TC", "VKN", "IBAN", "TELEFON", "PLAKA", "EPOSTA", "KART"}
MODELE_BAGLI = {"AD", "ADRES", "KURUM"}


@dataclass
class TurSonucu:
    beklenen: int = 0
    bulunan: int = 0
    kacan: list[str] = field(default_factory=list)

    @property
    def recall(self) -> float:
        return self.bulunan / self.beklenen if self.beklenen else 0.0


@dataclass
class Rapor:
    turler: dict[str, TurSonucu] = field(default_factory=dict)
    belge_sayisi: int = 0
    uydurma: list[str] = field(default_factory=list)
    bicim_hatasi: int = 0

    def tablo(self) -> str:
        satirlar = [f"{'tür':<10} {'beklenen':>9} {'bulunan':>8} {'recall':>8}"]
        satirlar.append("-" * 38)
        for tur in sorted(self.turler):
            s = self.turler[tur]
            satirlar.append(
                f"{tur:<10} {s.beklenen:>9} {s.bulunan:>8} {s.recall:>7.1%}"
            )
        satirlar.append("")
        satirlar.append(f"belge: {self.belge_sayisi}")
        if self.uydurma:
            satirlar.append(f"model uydurması: {len(self.uydurma)}")
        if self.bicim_hatasi:
            satirlar.append(f"bozuk JSON cevabı: {self.bicim_hatasi}")
        return "\n".join(satirlar)


def olc(belgeler: list[Belge], saglayici: Saglayici | None = None) -> Rapor:
    """Etiketli belgelerde tespit oranını ölçer.

    saglayici verilmezse yalnızca yapısal türler değerlendirilir; isim
    ve adresi desen katmanının bulması zaten beklenmiyor, onları
    ölçüme katmak sonucu haksız yere düşürür.
    """
    rapor = Rapor(belge_sayisi=len(belgeler))
    kapsam = YAPISAL | MODELE_BAGLI if saglayici else YAPISAL

    for belge in belgeler:
        sonuc = maskele(belge.metin, dogrula=False, saglayici=saglayici)
        bulunan = {(b.tur, b.deger) for b in sonuc.bulgular}
        rapor.uydurma.extend(sonuc.uydurma)
        rapor.bicim_hatasi += int(sonuc.model_bicim_hatasi)

        for e in belge.etiketler:
            if e.tur not in kapsam:
                continue
            s = rapor.turler.setdefault(e.tur, TurSonucu())
            s.beklenen += 1
            if (e.tur, e.deger) in bulunan:
                s.bulunan += 1
            else:
                s.kacan.append(e.deger)

    return rapor


def calistir(adet: int = 20, saglayici: Saglayici | None = None) -> Rapor:
    return olc(ornekler(adet), saglayici)
