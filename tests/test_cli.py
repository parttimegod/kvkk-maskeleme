"""CLI testleri.

Asıl sınananlar iki güvenlik davranışı: eşleme dosyasının istenmedikçe
yazılmaması, ve uyarıların stdout'a değil stderr'e gitmesi. İkincisi
önemli çünkü `kvkk-maskeleme dosya.txt > temiz.txt` yazan biri uyarıyı
görmeli ama dosyası kirlenmemeli.
"""

import json
import subprocess
import sys

import pytest

from kvkk_maskeleme.cli import (
    CIKIS_HATA,
    CIKIS_OZEL_NITELIKLI,
    CIKIS_TEMIZ,
    main,
)
from kvkk_maskeleme.sentetik import ceza_dosyasi, dilekce, durusma_tutanagi


@pytest.fixture
def kirli(tmp_path):
    yol = tmp_path / "kirli.txt"
    yol.write_text(dilekce(0).metin, encoding="utf-8")
    return yol


@pytest.fixture
def ozel(tmp_path):
    yol = tmp_path / "ozel.txt"
    yol.write_text(ceza_dosyasi(0).metin, encoding="utf-8")
    return yol


def test_maskeliyor_ve_stdout_a_yaziyor(kirli, capsys):
    assert main([str(kirli)]) == CIKIS_TEMIZ

    cikti = capsys.readouterr().out
    assert "<TC_1>" in cikti
    assert "T.C. Kimlik No" in cikti  # metnin geri kalanı duruyor


def test_cikti_dosyasina_yaziyor(kirli, tmp_path, capsys):
    hedef = tmp_path / "temiz.txt"
    main([str(kirli), "-o", str(hedef)])

    assert "<TC_1>" in hedef.read_text(encoding="utf-8")
    assert capsys.readouterr().out == ""


def test_esleme_istenmedikce_yazilmiyor(kirli, tmp_path):
    """Eşleme tablosu bütün kişisel veriyi içeriyor; varsayılan yazmamak."""
    main([str(kirli)])
    assert list(tmp_path.glob("*.json")) == []


def test_esleme_istenince_yaziliyor_ve_uyariliyor(kirli, tmp_path, capsys):
    harita = tmp_path / "esleme.json"
    main([str(kirli), "--esleme", str(harita)])

    veri = json.loads(harita.read_text(encoding="utf-8"))
    assert any(k.startswith("<TC_") for k in veri)

    hata = capsys.readouterr().err
    assert "UYARI" in hata
    assert "göndermeyin" in hata


def test_uyarilar_stderr_e_gidiyor(ozel, capsys):
    main([str(ozel)])
    yakalanan = capsys.readouterr()

    assert "md. 6" in yakalanan.err
    assert "md. 6" not in yakalanan.out  # çıktı kirlenmemeli


def test_ozet_stderr_e_gidiyor(kirli, capsys):
    main([str(kirli)])
    assert "Maskelendi" in capsys.readouterr().err


def test_kati_mod_ozel_nitelikli_veride_2_donuyor(ozel):
    assert main([str(ozel)]) == CIKIS_TEMIZ
    assert main([str(ozel), "--kati"]) == CIKIS_OZEL_NITELIKLI


def test_kati_mod_temiz_belgede_0_donuyor(tmp_path):
    yol = tmp_path / "tutanak.txt"
    yol.write_text(durusma_tutanagi(0).metin, encoding="utf-8")

    assert main([str(yol), "--kati"]) == CIKIS_TEMIZ


def test_sadece_incele_maskelemiyor(ozel, capsys):
    main([str(ozel), "--sadece-incele"])
    cikti = capsys.readouterr().out

    assert "<TC_1>" not in cikti
    assert "CEZA_MAHKUMIYETI" in cikti


def test_json_raporu(ozel, capsys):
    main([str(ozel), "--sadece-incele", "--json"])
    veri = json.loads(capsys.readouterr().out)

    assert veri["ozel_nitelikli"] is True
    assert "SAGLIK" in veri["kategoriler"]
    assert veri["bulgular"]


def test_stdin_den_okuyor(monkeypatch, capsys):
    import io

    monkeypatch.setattr("sys.stdin", io.StringIO(dilekce(1).metin))
    assert main([]) == CIKIS_TEMIZ
    assert "<TC_1>" in capsys.readouterr().out


def test_olmayan_dosya_anlamli_hata(tmp_path):
    with pytest.raises(SystemExit, match="bulunamadı"):
        main([str(tmp_path / "yok.txt")])


def test_utf8_olmayan_dosya_anlamli_hata(tmp_path):
    yol = tmp_path / "cp1254.txt"
    yol.write_bytes("Şüpheli sabıkalıdır.".encode("cp1254"))

    with pytest.raises(SystemExit, match="UTF-8"):
        main([str(yol)])


def test_sizinti_hatasi_1_donuyor(kirli, monkeypatch, capsys):
    import kvkk_maskeleme.cli as c
    from kvkk_maskeleme.maskeleme import SizintiHatasi

    def patlat(metin):
        raise SizintiHatasi("test sızıntısı")

    monkeypatch.setattr(c, "maskele", patlat)

    assert main([str(kirli)]) == CIKIS_HATA
    assert "HATA" in capsys.readouterr().err


def test_stdout_boru_hatti_utf8_kaliyor(tmp_path):
    """Windows'ta stdout borulandığında (`> dosya.txt`) konsol kod
    sayfası (genelde cp1254) miras alınıyordu; Türkçe karakterler
    bozuluyordu. `-o` ile dosyaya yazmak zaten UTF-8'di, fark buradaydı.

    Gerçek süreci başlatıp stdout'u boru olarak yakalıyoruz -- capsys
    bu hatayı sergilemez, çünkü pytest'in kendi yakalaması zaten UTF-8
    varsayar. `sys.executable -m kvkk_maskeleme.cli` ile alt süreç
    başlatmak, `kvkk-maskeleme dosya.txt > cikti.txt` komutunun aynısını
    taklit eder.
    """
    girdi = tmp_path / "girdi.txt"
    girdi.write_text(
        "Davacının sağlık raporu ve iş göremezlik durumu şüpheli.",
        encoding="utf-8",
    )

    sonuc = subprocess.run(
        [sys.executable, "-m", "kvkk_maskeleme.cli", str(girdi)],
        capture_output=True,
    )

    cikti = sonuc.stdout.decode("utf-8")

    # Konsol kod sayfasına (cp1254) düşseydi bu satır UnicodeDecodeError
    # ya da yanlış kod noktalarıyla sonuçlanırdı. Kod noktalarını
    # doğrudan sınıyoruz; terminalin kendisi Türkçe karakteri yanlış
    # gösterse bile decode edilmiş str nesnesi burada doğru.
    beklenen = "Davacının sağlık raporu ve iş göremezlik durumu şüpheli."
    assert [hex(ord(k)) for k in cikti.strip()] == [hex(ord(k)) for k in beklenen]

    # Özellikle bozulmaya en açık Türkçe karakterler.
    assert hex(ord("ğ")) == "0x11f"
    assert hex(ord("ş")) == "0x15f"
    assert hex(ord("ı")) == "0x131"
    for harf in "ğşı":
        assert ord(harf) in {ord(c) for c in cikti}
