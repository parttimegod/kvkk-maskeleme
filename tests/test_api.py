"""HTTP contract tests. All input is generated or written as synthetic text."""

import random

import pytest
from fastapi.testclient import TestClient

from kvkk_maskeleme.api import app
from kvkk_maskeleme.maskeleme import SizintiHatasi
from kvkk_maskeleme.sentetik import (
    dilekce,
    rastgele_dogum_tarihi,
    rastgele_iban,
    rastgele_kart,
    rastgele_pasaport,
    rastgele_plaka,
    rastgele_sgk_sicil,
    rastgele_tc,
    rastgele_telefon,
    rastgele_vkn,
)

client = TestClient(app)


def sample(label, generator, kind):
    value = generator(random.Random(19))
    return f"{label}: {value}", kind, value


@pytest.mark.parametrize(
    "text,kind,value",
    [
        sample("Kimlik No", rastgele_tc, "TC"),
        sample("Vergi No", rastgele_vkn, "VKN"),
        sample("IBAN", rastgele_iban, "IBAN"),
        sample("Telefon", rastgele_telefon, "TELEFON"),
        ("E-posta: kisi@example.test", "EPOSTA", "kisi@example.test"),
        sample("Plaka", rastgele_plaka, "PLAKA"),
        sample("Kart", rastgele_kart, "KART"),
        sample("Pasaport No", rastgele_pasaport, "PASAPORT"),
        sample("Doğum Tarihi", rastgele_dogum_tarihi, "DOGUM_TARIHI"),
        sample("SGK Sicil No", rastgele_sgk_sicil, "SGK_SICIL"),
    ],
    ids=[
        "tc", "vkn", "iban", "phone", "email", "plate", "card", "passport", "dob", "sgk"
    ],
)
def test_supported_identifiers(text, kind, value):
    response = client.post("/mask", json={"text": text})

    assert response.status_code == 200
    body = response.json()
    assert value not in body["masked_text"]
    assert f"<{kind}_1>" in body["masked_text"]
    assert body["counts"][kind] == 1
    assert body["manual_review_required"] is True
    assert "eslesme" not in body and "mapping" not in body
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize(
    "text",
    [
        "Dosya sıra no 12345678901 kaydedildi.",
        "Duruşma 15.02.2026 tarihinde yapılacaktır.",
        "Dosya No: 2026/1487 E.",
        "Aydın ilinde tanık dinlendi.",
        "Deniz Çelik, Kızılay Mahallesi 28. Sokak No: 20 adresinde oturur.",
    ],
)
def test_unsupported_or_clean_text_remains_for_manual_review(text):
    response = client.post("/mask", json={"text": text})

    assert response.status_code == 200
    assert response.json()["masked_text"] == text
    assert response.json()["counts"] == {}
    assert response.json()["manual_review_required"] is True


def test_synthetic_document_masks_known_identifiers_but_not_names():
    document = dilekce(4)
    response = client.post("/mask", json={"text": document.metin})

    assert response.status_code == 200
    masked = response.json()["masked_text"]
    assert all(
        label.deger not in masked for label in document.etiketler if label.tur == "TC"
    )
    assert any(label.deger in masked for label in document.etiketler if label.tur == "AD")


def test_repeated_value_uses_same_placeholder():
    phone = "0532 000 00 00"
    response = client.post("/mask", json={"text": f"{phone} ve tekrar {phone}"})

    assert response.json()["masked_text"] == "<TELEFON_1> ve tekrar <TELEFON_1>"
    assert response.json()["counts"] == {"TELEFON": 2}


def test_special_category_flag_does_not_claim_to_mask_context():
    response = client.post("/mask", json={"text": "Sağlık raporu: 0532 000 00 00"})

    assert response.json()["special_categories"] == ["SAGLIK"]
    assert response.json()["masked_text"] == "Sağlık raporu: <TELEFON_1>"
    assert response.json()["manual_review_required"] is True


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"text": ""},
        {"text": " \n "},
        {"text": None},
        {"text": 123},
        {"text": ["synthetic"]},
        {"text": "safe", "extra": "should be rejected"},
        ["synthetic"],
        {"text": "x" * 100_001},
    ],
)
def test_invalid_input_is_rejected_without_echoing_document(payload):
    response = client.post("/mask", json=payload)

    assert response.status_code == 422
    assert response.json() == {"error": "Invalid request body"}
    assert response.headers["cache-control"] == "no-store"


def test_malformed_json_is_rejected_without_echo():
    response = client.post(
        "/mask",
        content='{"text":"0532 000 00 00",',
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 422
    assert "0532" not in response.text


def test_verification_failure_returns_generic_error(monkeypatch):
    def fail(_text):
        raise SizintiHatasi("unexpected sensitive text")

    monkeypatch.setattr("kvkk_maskeleme.api.maskele", fail)
    response = client.post("/mask", json={"text": "0532 000 00 00"})

    assert response.status_code == 500
    assert response.json() == {"error": "Masking verification failed"}
    assert "0532" not in response.text
    assert response.headers["cache-control"] == "no-store"
