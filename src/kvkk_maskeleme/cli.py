"""Komut satırı arayüzü.

İki güvenlik kararı burada:

Eşleme tablosu istenmedikçe yazılmıyor. Tablo bütün kişisel veriyi
düz metin olarak içeriyor; maskelenmiş çıktının yanına sessizce
bırakılması, maskelemeyi anlamsız kılar. Yazdırmak için açık bayrak
gerekiyor ve yazıldığında uyarı basılıyor.

Özel nitelikli veri uyarısı stderr'e gidiyor, çıktıya karışmıyor.
Böylece `kvkk-maskeleme dosya.txt > temiz.txt` yazan biri uyarıyı
görüyor ama dosyası kirlenmiyor.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .maskeleme import SizintiHatasi, maskele
from .ozel_nitelikli import incele

# Betiklerin ayırt edebilmesi için.
CIKIS_TEMIZ = 0
CIKIS_HATA = 1
CIKIS_OZEL_NITELIKLI = 2


def _oku(yol: str | None) -> str:
    """Dosyadan ya da stdin'den okur.

    Kodlama açıkça UTF-8: Windows'ta varsayılan cp1254 ve Türkçe
    belgeler sessizce bozuluyor.
    """
    if yol in (None, "-"):
        return sys.stdin.read()
    try:
        return Path(yol).read_text(encoding="utf-8")
    except FileNotFoundError:
        raise SystemExit(f"Dosya bulunamadı: {yol}") from None
    except UnicodeDecodeError:
        raise SystemExit(
            f"{yol} UTF-8 değil. Dosyayı UTF-8'e çevirip tekrar deneyin."
        ) from None


def _ayristirici() -> argparse.ArgumentParser:
    a = argparse.ArgumentParser(
        prog="kvkk-maskeleme",
        description=(
            "Türkçe metinlerde kişisel veriyi maskeler. Maskeleme "
            "anonimleştirme değildir; çıktı KVKK anlamında hâlâ kişisel "
            "veridir."
        ),
    )
    a.add_argument("dosya", nargs="?", help="Girdi dosyası. Verilmezse stdin.")
    a.add_argument("-o", "--cikti", help="Çıktı dosyası. Verilmezse stdout.")
    a.add_argument(
        "--esleme",
        help=(
            "Yer tutucu eşlemesini bu dosyaya yaz. DİKKAT: dosya bütün "
            "kişisel veriyi düz metin içerir."
        ),
    )
    a.add_argument(
        "--sadece-incele",
        action="store_true",
        help="Maskeleme yapma, yalnızca özel nitelikli veri raporu ver.",
    )
    a.add_argument(
        "--kati",
        action="store_true",
        help=(
            "Özel nitelikli veri bulunursa 2 koduyla çık. Belgeyi işleme "
            "sokmadan önce durdurmak isteyen betikler için."
        ),
    )
    a.add_argument("--json", action="store_true", help="Raporu JSON olarak ver.")
    return a


def _rapor_yaz(rapor, json_mu: bool) -> None:
    if json_mu:
        print(
            json.dumps(
                {
                    "ozel_nitelikli": rapor.var_mi,
                    "kategoriler": sorted(rapor.kategoriler()),
                    "bulgular": [
                        {"kategori": b.kategori, "kanit": b.kanit, "kaynak": b.kaynak}
                        for b in rapor.bulgular
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(rapor.uyari())
        for b in rapor.bulgular:
            print(f"  {b.kategori:22s} {b.kanit!r}  [{b.kaynak}]")


def main(argv: list[str] | None = None) -> int:
    args = _ayristirici().parse_args(argv)
    metin = _oku(args.dosya)
    rapor = incele(metin)

    if args.sadece_incele:
        _rapor_yaz(rapor, args.json)
        return CIKIS_OZEL_NITELIKLI if (args.kati and rapor.var_mi) else CIKIS_TEMIZ

    try:
        sonuc = maskele(metin)
    except SizintiHatasi as e:
        print(f"HATA: {e}", file=sys.stderr)
        return CIKIS_HATA

    if args.cikti:
        Path(args.cikti).write_text(sonuc.metin, encoding="utf-8")
    else:
        sys.stdout.write(sonuc.metin)

    if args.esleme:
        Path(args.esleme).write_text(
            json.dumps(sonuc.eslesme, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(
            f"UYARI: {args.esleme} bütün kişisel veriyi düz metin içeriyor. "
            "Maskelenmiş metinle birlikte hiçbir yere göndermeyin.",
            file=sys.stderr,
        )

    ozet = sonuc.ozet()
    if ozet:
        print(
            "Maskelendi: " + ", ".join(f"{t}×{n}" for t, n in sorted(ozet.items())),
            file=sys.stderr,
        )

    if rapor.var_mi:
        print(rapor.uyari(), file=sys.stderr)
        if args.kati:
            return CIKIS_OZEL_NITELIKLI

    return CIKIS_TEMIZ


if __name__ == "__main__":
    raise SystemExit(main())
