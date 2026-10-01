"""Additional HTTP boundaries; only generated or invented test data is used."""

import asyncio
import json
import random

import httpx
import pytest
from fastapi.testclient import TestClient

from kvkk_maskeleme import api
from kvkk_maskeleme.sentetik import dilekce, rastgele_iban, rastgele_tc

TC = rastgele_tc(random.Random(0))
IBAN = rastgele_iban(random.Random(2))


@pytest.fixture
def client():
    with TestClient(api.app) as test_client:
        yield test_client


@pytest.mark.parametrize(
    "text, kind, value",
    [
        (
            f"Kimlik: {TC[:3]} {TC[3:6]} {TC[6:9]} {TC[9:]}",
            "TC",
            f"{TC[:3]} {TC[3:6]} {TC[6:9]} {TC[9:]}",
        ),
        (f"Kimlik: {TC[:3]}.{TC[3:6]}.{TC[6:]}", "TC", f"{TC[:3]}.{TC[3:6]}.{TC[6:]}"),
        (f"Kimlik: {TC.replace('0', 'O')}", "TC", TC.replace("0", "O")),
        (
            "Hesap: " + " ".join(IBAN[i : i + 4] for i in range(0, len(IBAN), 4)),
            "IBAN",
            " ".join(IBAN[i : i + 4] for i in range(0, len(IBAN), 4)),
        ),
        ("Tel: +90 532 123 45 67", "TELEFON", "+90 532 123 45 67"),
    ],
)
def test_separator_ocr_and_phone_formats(client, text, kind, value):
    response = client.post("/mask", json={"text": text})
    assert response.status_code == 200
    data = response.json()
    assert data["masked_text"] == text.replace(value, f"<{kind}_1>")
    assert data["counts"] == {kind: 1}
    assert value not in response.text


@pytest.mark.parametrize("text", [True, {"secret": TC}, "\ud800"])
def test_invalid_text_does_not_echo_input(client, text):
    # ASCII JSON encoding lets an unpaired surrogate reach the server.
    response = client.post(
        "/mask",
        content=json.dumps({"text": text}),
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 422
    assert response.json() == {"error": "Invalid request body"}
    assert TC not in response.text
    assert "secret" not in response.text
    assert response.headers["cache-control"] == "no-store"


def test_exact_text_length_limit(client):
    response = client.post("/mask", json={"text": "x" * api.MAX_TEXT_LENGTH})
    assert response.status_code == 200
    assert len(response.json()["masked_text"]) == api.MAX_TEXT_LENGTH


def test_sensitive_extra_field_is_rejected_without_echo(client):
    response = client.post("/mask", json={"text": f"Kimlik: {TC}", "extra": TC})
    assert response.status_code == 422
    assert TC not in response.text
    assert "masked_text" not in response.json()


def test_invalid_utf8_json_is_rejected(client):
    response = client.post(
        "/mask",
        content=b'{"text":"\xff"}',
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 400
    assert "masked_text" not in response.json()


@pytest.mark.parametrize("extra_bytes", [0, 1])
def test_actual_body_size_boundary(client, extra_bytes):
    # Whitespace is valid JSON padding, independent of the text-field limit.
    payload = json.dumps({"text": "sentetik"}).encode()
    body = payload + b" " * (api.MAX_BODY_BYTES - len(payload) + extra_bytes)
    response = client.post(
        "/mask", content=body, headers={"content-type": "application/json"}
    )
    assert response.status_code == (413 if extra_bytes else 200)
    assert response.headers["cache-control"] == "no-store"
    if not extra_bytes:
        assert response.json()["masked_text"] == "sentetik"


def test_body_limit_precedes_processing_and_ignores_content_length(client, monkeypatch):
    def fail(_text):
        pytest.fail("Oversized request must not reach masking")

    monkeypatch.setattr(api, "maskele", fail)
    response = client.post(
        "/mask",
        content=TC.encode() + b"x" * api.MAX_BODY_BYTES,
        headers={"content-type": "application/json", "content-length": "2"},
    )
    assert response.status_code == 413
    assert response.json() == {"error": "Request body too large"}
    assert TC not in response.text


@pytest.mark.parametrize("oversized", [False, True])
def test_chunked_body_limit_and_unicode(oversized):
    async def run():
        text = f"Kimlik: {TC}\nŞüphe üzerine."
        payload = json.dumps({"text": text}, ensure_ascii=False).encode()

        async def chunks():
            if oversized:
                yield b"x" * (api.MAX_BODY_BYTES // 2)
                yield b"x" * (api.MAX_BODY_BYTES // 2 + 1)
            else:
                for index in range(0, len(payload), 3):
                    yield payload[index : index + 3]

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=api.app), base_url="http://test"
        ) as async_client:
            response = await async_client.post(
                "/mask",
                content=chunks(),
                headers={"content-type": "application/json"},
            )
        assert response.status_code == (413 if oversized else 200)
        assert response.headers["cache-control"] == "no-store"
        if not oversized:
            assert response.json()["masked_text"] == "Kimlik: <TC_1>\nŞüphe üzerine."

    asyncio.run(run())


def test_synthetic_document_preserves_lines_without_writing_files(
    client, tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    document = dilekce(2)
    response = client.post("/mask", json={"text": document.metin})
    assert response.status_code == 200
    masked = response.json()["masked_text"]
    assert masked.count("\n") == document.metin.count("\n")
    for label in document.etiketler:
        if label.tur in {"TC", "IBAN", "TELEFON"}:
            assert label.deger not in masked
    assert list(tmp_path.iterdir()) == []


def test_placeholder_numbering_is_independent_between_requests(client):
    first = client.post("/mask", json={"text": TC}).json()
    other_tc = rastgele_tc(random.Random(5))
    second = client.post("/mask", json={"text": other_tc}).json()
    assert first["masked_text"] == second["masked_text"] == "<TC_1>"
    assert TC not in json.dumps(second)


def test_openapi_describes_text_length_and_existing_response(client):
    schema = client.get("/openapi.json").json()
    request_schema = schema["components"]["schemas"]["MaskRequest"]
    assert request_schema["properties"]["text"]["maxLength"] == api.MAX_TEXT_LENGTH
    assert request_schema["additionalProperties"] is False
    assert (
        "manual_review_required"
        in (schema["components"]["schemas"]["MaskResponse"]["properties"])
    )
