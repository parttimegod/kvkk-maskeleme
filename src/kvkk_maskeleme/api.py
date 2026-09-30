"""Small, local HTTP adapter for the deterministic masking layer.

This adapter writes no raw text or reversible mapping to persistent storage
and does not log request bodies.
The response deliberately requires manual review: names, addresses, and
contextual identifiers are outside this endpoint's masking scope.
"""

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .maskeleme import SizintiHatasi, maskele
from .ozel_nitelikli import incele

MAX_TEXT_LENGTH = 100_000
MAX_BODY_BYTES = 1_048_576


class RequestBodyLimitMiddleware:
    """Bound the actual body before JSON parsing, including streamed input."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["method"] != "POST":
            await self.app(scope, receive, send)
            return

        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            if len(body) + len(chunk) > MAX_BODY_BYTES:
                response = JSONResponse(
                    status_code=413,
                    content={"error": "Request body too large"},
                    headers={"Cache-Control": "no-store"},
                )
                await response(scope, receive, send)
                return
            body.extend(chunk)
            if not message.get("more_body", False):
                break

        consumed = False

        async def replay() -> Message:
            nonlocal consumed
            if not consumed:
                consumed = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        await self.app(scope, replay, send)


app = FastAPI(title="Turkish document masking demo")
app.add_middleware(RequestBodyLimitMiddleware)


class MaskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: StrictStr = Field(min_length=1, max_length=MAX_TEXT_LENGTH)

    @field_validator("text")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("text must not be blank")
        try:
            value.encode("utf-8")
        except UnicodeEncodeError:
            raise ValueError("text must be valid Unicode") from None
        return value


class MaskResponse(BaseModel):
    masked_text: str
    counts: dict[str, int]
    special_categories: list[str]
    manual_review_required: bool


@app.exception_handler(RequestValidationError)
async def invalid_request(
    _request: Request, _error: RequestValidationError
) -> JSONResponse:
    # FastAPI's default validation details may echo the submitted document.
    return JSONResponse(
        status_code=422,
        content={"error": "Invalid request body"},
        headers={"Cache-Control": "no-store"},
    )


@app.exception_handler(SizintiHatasi)
async def incomplete_masking(_request: Request, _error: SizintiHatasi) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"error": "Masking verification failed"},
        headers={"Cache-Control": "no-store"},
    )


@app.post("/mask", response_model=MaskResponse)
def mask(request: MaskRequest, response: Response) -> MaskResponse:
    response.headers["Cache-Control"] = "no-store"
    result = maskele(request.text)
    categories = sorted(incele(request.text).kategoriler())
    return MaskResponse(
        masked_text=result.metin,
        counts=result.ozet(),
        special_categories=categories,
        manual_review_required=True,
    )
