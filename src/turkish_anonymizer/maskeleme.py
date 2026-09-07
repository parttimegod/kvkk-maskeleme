"""Maskeleme, geri alma ve sızıntı doğrulaması.

İki tasarım kararı burada:

Yer tutucular tutarlı. Aynı kimlik numarası metinde üç kez geçiyorsa
üçünde de <TC_1> yazıyor. Farklı numaralar farklı numara alıyor. Böylece
maskelenmiş metin hâlâ okunabiliyor ve "aynı kişi mi" sorusu
cevaplanabiliyor -- karalama bunu yapamaz.

Çıktı tekrar taranıyor. Maskeleme bittikten sonra metin yeniden tespit
katmanından geçiyor; bir şey kaldıysa sessizce geçmiyor, hata veriyor.
Sızıntının sessiz olması, sızıntının kendisinden kötü.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .tespit import Bulgu, bul


class SizintiHatasi(Exception):
    """Maskeleme sonrası metinde hâlâ kişisel veri var."""


@dataclass
class Sonuc:
    metin: str
    eslesme: dict[str, str] = field(default_factory=dict)
    bulgular: list[Bulgu] = field(default_factory=list)

    def ozet(self) -> dict[str, int]:
        sayim: dict[str, int] = {}
        for b in self.bulgular:
            sayim[b.tur] = sayim.get(b.tur, 0) + 1
        return sayim


def maskele(metin: str, dogrula: bool = True) -> Sonuc:
    """Yapısal kişisel verileri yer tutucuyla değiştirir.

    dogrula=False yalnızca test içindir. Üretimde kapatma: doğrulama
    kapalıyken sızıntı sessizce geçer.
    """
    bulgular = bul(metin)

    # Aynı değer her yerde aynı yer tutucuyu alsın.
    yer_tutucu: dict[tuple[str, str], str] = {}
    sayac: dict[str, int] = {}
    for b in bulgular:
        anahtar = (b.tur, b.deger)
        if anahtar not in yer_tutucu:
            sayac[b.tur] = sayac.get(b.tur, 0) + 1
            yer_tutucu[anahtar] = f"<{b.tur}_{sayac[b.tur]}>"

    # Sondan başa yürüyoruz ki önceki konumlar kaymasın.
    parcalar = list(metin)
    for b in sorted(bulgular, key=lambda x: -x.baslangic):
        parcalar[b.baslangic : b.bitis] = yer_tutucu[(b.tur, b.deger)]
    yeni = "".join(parcalar)

    eslesme = {v: k[1] for k, v in yer_tutucu.items()}
    sonuc = Sonuc(metin=yeni, eslesme=eslesme, bulgular=bulgular)

    if dogrula:
        dogrula_temiz(yeni)
    return sonuc


def dogrula_temiz(metin: str) -> None:
    """Metinde kişisel veri kalmadığını doğrular, kalmışsa hata verir."""
    kalan = bul(metin)
    if kalan:
        ornek = ", ".join(f"{b.tur}" for b in kalan[:3])
        raise SizintiHatasi(
            f"Maskeleme sonrası {len(kalan)} kişisel veri kaldı ({ornek}). "
            "Metin güvenli değil, sonraki adıma geçirme."
        )


def geri_al(metin: str, eslesme: dict[str, str]) -> str:
    """Yer tutucuları özgün değerlerle değiştirir.

    İşlem zinciri bittikten sonra sonucu okunabilir hale getirmek için.
    Eşleme dosyası kişisel veri içerir; metinle birlikte hiçbir yere
    gönderilmemeli.
    """
    for tutucu, deger in eslesme.items():
        metin = metin.replace(tutucu, deger)
    return metin
