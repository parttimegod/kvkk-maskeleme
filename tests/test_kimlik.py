"""Kimlik numarası doğrulayıcılarının testleri.

Test verileri algoritmayla üretiliyor, sabit listeden değil. Gerçek bir
kimlik numarasını teste yazmak, aracın önlemeye çalıştığı şeyin ta
kendisi olurdu.
"""

import random

import pytest

from turkish_anonymizer.kimlik import (
    iban_gecerli,
    luhn_gecerli,
    tc_kimlik_gecerli,
    tc_kontrol_haneleri,
    vkn_gecerli,
    vkn_kontrol_hanesi,
)
from turkish_anonymizer.sentetik import rastgele_iban, rastgele_tc, rastgele_vkn


def test_uretilen_tc_gecerli():
    r = random.Random(0)
    for _ in range(200):
        assert tc_kimlik_gecerli(rastgele_tc(r))


def test_uretilen_vkn_gecerli():
    r = random.Random(0)
    for _ in range(200):
        assert vkn_gecerli(rastgele_vkn(r))


def test_uretilen_iban_gecerli():
    r = random.Random(0)
    for _ in range(200):
        assert iban_gecerli(rastgele_iban(r))


def test_tek_hane_bozulunca_tc_reddediliyor():
    """Kontrol hanesinin işi bu: rastgele sayılar geçmesin."""
    r = random.Random(1)
    for _ in range(100):
        no = rastgele_tc(r)
        i = r.randrange(11)
        bozuk = no[:i] + str((int(no[i]) + 1) % 10) + no[i + 1 :]
        assert not tc_kimlik_gecerli(bozuk)


def test_tc_sifirla_baslayamaz():
    assert not tc_kimlik_gecerli("01234567890")


@pytest.mark.parametrize("no", ["", "123", "1234567890", "abcdefghijk", "1" * 12])
def test_gecersiz_tc_bicimleri(no):
    assert not tc_kimlik_gecerli(no)


def test_tc_bosluk_ve_noktalama_toleransi():
    r = random.Random(2)
    no = rastgele_tc(r)
    assert tc_kimlik_gecerli(f"{no[:3]} {no[3:6]} {no[6:]}")


def test_kontrol_haneleri_iki_karakter():
    assert len(tc_kontrol_haneleri("123456789")) == 2
    assert len(vkn_kontrol_hanesi("123456789")) == 1


def test_kontrol_hanesi_gecersiz_girdi():
    with pytest.raises(ValueError):
        tc_kontrol_haneleri("12345")
    with pytest.raises(ValueError):
        vkn_kontrol_hanesi("abcdefghi")


def test_iban_bosluklu_yazim():
    r = random.Random(3)
    iban = rastgele_iban(r)
    bosluklu = " ".join(iban[i : i + 4] for i in range(0, len(iban), 4))
    assert iban_gecerli(bosluklu)


def test_bozuk_iban_reddediliyor():
    r = random.Random(4)
    iban = rastgele_iban(r)
    bozuk = iban[:5] + str((int(iban[5]) + 1) % 10) + iban[6:]
    assert not iban_gecerli(bozuk)


@pytest.mark.parametrize("iban", ["", "TR", "XX00", "TR00" + "1" * 40])
def test_gecersiz_iban_bicimleri(iban):
    assert not iban_gecerli(iban)


def test_luhn():
    # Yaygın olarak kullanılan test kartı numarası.
    assert luhn_gecerli("4111 1111 1111 1111")
    assert not luhn_gecerli("4111 1111 1111 1112")


def test_luhn_uzunluk_siniri():
    assert not luhn_gecerli("4111")
    assert not luhn_gecerli("4" * 25)
