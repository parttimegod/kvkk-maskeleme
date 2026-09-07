"""Ölçüm.

Bu alandaki açık kaynak projelerin hiçbiri ne kadar iyi çalıştığını
söylemiyor. "Kişisel verileri maskeler" cümlesi ölçülmeden bir şey ifade
etmiyor; %60 recall'la çalışan bir araç çalışmıyor demektir.

Üç şey ölçülüyor:

1. Tanımlayıcı recall'ı -- maskelenmesi gereken kaç veri maskelendi
2. Özel nitelikli recall'ı -- işaretlenmesi gereken kaç belge işaretlendi
3. Yanlış pozitif -- temiz metinde kaç kez boşuna işaretlendi

Üçüncüsü ayrı duruyor çünkü özel nitelikli katmanı bilerek cömert. Cömert
olmanın bedeli ölçülmezse "cömert" ile "gürültülü" arasındaki fark
kaybolur.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .maskeleme import maskele
from .model import Saglayici
from .ozel_nitelikli import KATEGORILER, incele
from .sentetik import Belge, ornekler, temiz_belgeler

YAPISAL = {"TC", "VKN", "IBAN", "TELEFON", "PLAKA", "EPOSTA", "KART"}
# Kontrol hanesi yok, etiketle yakalanıyorlar. Model gerektirmedikleri
# için sağlayıcı olmadan da ölçülüyorlar.
CIPALI = {"PASAPORT", "DOGUM_TARIHI", "SGK_SICIL"}
MODELE_BAGLI = {"AD", "ADRES", "KURUM"}
OZEL_NITELIKLI = set(KATEGORILER)


@dataclass
class TurSonucu:
    beklenen: int = 0
    bulunan: int = 0
    kacan: list[str] = field(default_factory=list)

    @property
    def recall(self) -> float:
        return self.bulunan / self.beklenen if self.beklenen else 0.0


@dataclass
class YanlisPozitif:
    metin: str
    kategori: str
    kanit: str


@dataclass
class Rapor:
    turler: dict[str, TurSonucu] = field(default_factory=dict)
    ozel: dict[str, TurSonucu] = field(default_factory=dict)
    belge_sayisi: int = 0
    uydurma: list[str] = field(default_factory=list)
    bicim_hatasi: int = 0
    temiz_belge_sayisi: int = 0
    yanlis_pozitifler: list[YanlisPozitif] = field(default_factory=list)

    @property
    def yanlis_pozitif_orani(self) -> float:
        if not self.temiz_belge_sayisi:
            return 0.0
        kirlenen = {y.metin for y in self.yanlis_pozitifler}
        return len(kirlenen) / self.temiz_belge_sayisi

    def _blok(self, baslik: str, veri: dict[str, TurSonucu]) -> list[str]:
        if not veri:
            return []
        satirlar = [baslik, f"{'tür':<22} {'beklenen':>9} {'bulunan':>8} {'recall':>8}"]
        satirlar.append("-" * 50)
        for tur in sorted(veri):
            s = veri[tur]
            satirlar.append(
                f"{tur:<22} {s.beklenen:>9} {s.bulunan:>8} {s.recall:>7.1%}"
            )
        satirlar.append("")
        return satirlar

    def tablo(self) -> str:
        satirlar = self._blok("TANIMLAYICILAR (maskeleniyor)", self.turler)
        satirlar += self._blok("ÖZEL NİTELİKLİ (işaretleniyor)", self.ozel)

        satirlar.append(f"belge: {self.belge_sayisi}")
        if self.temiz_belge_sayisi:
            satirlar.append(
                f"temiz metin: {self.temiz_belge_sayisi}, "
                f"yanlış pozitif: {len(self.yanlis_pozitifler)} "
                f"({self.yanlis_pozitif_orani:.1%} belgede)"
            )
        if self.uydurma:
            satirlar.append(f"model uydurması: {len(self.uydurma)}")
        if self.bicim_hatasi:
            satirlar.append(f"bozuk JSON cevabı: {self.bicim_hatasi}")
        return "\n".join(satirlar)


def _tanimlayici_olc(
    rapor: Rapor, belgeler: list[Belge], saglayici: Saglayici | None
) -> None:
    kapsam = YAPISAL | CIPALI | (MODELE_BAGLI if saglayici else set())

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


def _ozel_olc(rapor: Rapor, belgeler: list[Belge], saglayici: Saglayici | None) -> None:
    """Özel nitelikli veri kategori düzeyinde ölçülüyor.

    Tam metin eşleşmesi aranmıyor: bu katman maskeleme yapmadığı için
    doğru davranış kategoriyi yakalamak, kanıtı kelimesi kelimesine
    bulmak değil.
    """
    for belge in belgeler:
        beklenen = {e.tur for e in belge.etiketler if e.tur in OZEL_NITELIKLI}
        if not beklenen:
            continue
        bulunan = incele(belge.metin, saglayici=saglayici).kategoriler()
        for kategori in beklenen:
            s = rapor.ozel.setdefault(kategori, TurSonucu())
            s.beklenen += 1
            if kategori in bulunan:
                s.bulunan += 1
            else:
                s.kacan.append(belge.metin[:60])


def _yanlis_pozitif_olc(
    rapor: Rapor, temizler: list[Belge], saglayici: Saglayici | None
) -> None:
    rapor.temiz_belge_sayisi = len(temizler)
    for belge in temizler:
        for b in incele(belge.metin, saglayici=saglayici).bulgular:
            rapor.yanlis_pozitifler.append(
                YanlisPozitif(belge.metin, b.kategori, b.kanit)
            )


def olc(
    belgeler: list[Belge],
    saglayici: Saglayici | None = None,
    temizler: list[Belge] | None = None,
) -> Rapor:
    """Etiketli belgelerde tespit oranını, temiz metinde yanlış pozitifi ölçer.

    saglayici verilmezse isim ve adres değerlendirmeye alınmıyor; desen
    katmanının onları bulması zaten beklenmiyor, ölçüme katmak sonucu
    haksız yere düşürür.
    """
    rapor = Rapor(belge_sayisi=len(belgeler))
    _tanimlayici_olc(rapor, belgeler, saglayici)
    _ozel_olc(rapor, belgeler, saglayici)
    if temizler:
        _yanlis_pozitif_olc(rapor, temizler, saglayici)
    return rapor


def calistir(adet: int = 20, saglayici: Saglayici | None = None) -> Rapor:
    return olc(ornekler(adet), saglayici, temizler=temiz_belgeler())
