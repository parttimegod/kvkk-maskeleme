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

from .model import Saglayici
from .model import bul as model_bul
from .tespit import Bulgu, bul


class SizintiHatasi(Exception):
    """Maskeleme sonrası metinde hâlâ kişisel veri var."""


@dataclass
class Sonuc:
    metin: str
    eslesme: dict[str, str] = field(default_factory=dict)
    bulgular: list[Bulgu] = field(default_factory=list)
    uydurma: list[str] = field(default_factory=list)
    model_bicim_hatasi: bool = False

    def ozet(self) -> dict[str, int]:
        sayim: dict[str, int] = {}
        for b in self.bulgular:
            sayim[b.tur] = sayim.get(b.tur, 0) + 1
        return sayim


def _birlestir(kesin: list[Bulgu], model: list[Bulgu]) -> list[Bulgu]:
    """Desen bulgularıyla model bulgularını birleştirir.

    Çakışmada desen kazanıyor: kontrol hanesiyle doğrulanmış bir kimlik
    numarası, modelin "bu bir ad" tahmininden daha güvenilir.
    """
    sonuc = list(kesin)
    for m in model:
        if not any(m.baslangic < k.bitis and k.baslangic < m.bitis for k in sonuc):
            sonuc.append(m)
    return sorted(sonuc, key=lambda b: b.baslangic)


def maskele(
    metin: str,
    dogrula: bool = True,
    saglayici: Saglayici | None = None,
) -> Sonuc:
    """Kişisel verileri yer tutucuyla değiştirir.

    saglayici verilirse isim, adres ve kurum için model katmanı da
    çalışır. Verilmezse yalnızca yapısal kimlikler maskelenir.

    dogrula=False yalnızca test içindir. Üretimde kapatma: doğrulama
    kapalıyken sızıntı sessizce geçer.
    """
    bulgular = bul(metin)
    uydurma: list[str] = []
    bicim_hatasi = False

    if saglayici is not None:
        ms = model_bul(metin, saglayici)
        bulgular = _birlestir(bulgular, ms.bulgular)
        uydurma, bicim_hatasi = ms.uydurma, ms.bicim_hatasi

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
    sonuc = Sonuc(
        metin=yeni,
        eslesme=eslesme,
        bulgular=bulgular,
        uydurma=uydurma,
        model_bicim_hatasi=bicim_hatasi,
    )

    if dogrula:
        dogrula_temiz(yeni)
    return sonuc


def dogrula_temiz(metin: str) -> None:
    """Metinde yapısal kişisel veri kalmadığını doğrular.

    Yalnızca desen katmanını kapsıyor. İsim ve adres için aynı güvence
    yok: doğrulamak ikinci bir model geçişi gerektirir -- bkz. SONRA.md
    """
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
