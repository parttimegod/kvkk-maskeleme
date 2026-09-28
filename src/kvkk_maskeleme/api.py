"""Small, local HTTP adapter for the deterministic masking layer.

No raw text or reversible placeholder mapping is stored or logged here.
The response deliberately requires manual review: names, addresses, and
contextual identifiers are outside this endpoint's masking scope.
"""

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator

from .maskeleme import SizintiHatasi, maskele
from .ozel_nitelikli import incele

app = FastAPI(title="Turkish document masking demo")


class MaskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: StrictStr = Field(min_length=1, max_length=100_000)

    @field_validator("text")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("text must not be blank")
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
