"""HTTP service for publishing and previewing a template release."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .infrai_client import InfraiClient, InfraiError
from .models import TemplateReleaseRequest, TemplateReleaseResult
from .template_release import TemplateReleaseService

app = FastAPI(title="Media lifecycle template releases")


@app.exception_handler(InfraiError)
async def infrai_error_handler(_: Request, error: InfraiError) -> JSONResponse:
    status = error.status_code if 400 <= error.status_code < 500 else 502
    return JSONResponse(
        status_code=status,
        content={"error": {"code": error.code, "detail": error.detail}},
    )


@app.post("/template-releases", response_model=TemplateReleaseResult)
def publish_template_release(body: TemplateReleaseRequest) -> TemplateReleaseResult:
    client = InfraiClient()
    try:
        return TemplateReleaseService(client).publish(body)
    finally:
        client.close()
