"""Publish one immutable set of templates for a media lifecycle."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .infrai_client import InfraiClient
from .models import (
    LifecycleStage,
    PublishedTemplate,
    TemplateReleaseRequest,
    TemplateReleaseResult,
)


@dataclass(frozen=True)
class TemplateSpec:
    subject: str
    html: str


TEMPLATES: dict[LifecycleStage, TemplateSpec] = {
    LifecycleStage.ASSET_INGESTED: TemplateSpec(
        subject="We received {{asset_title}}",
        html="<p>Hi {{creator_name}}, your asset <strong>{{asset_title}}</strong> is queued.</p>",
    ),
    LifecycleStage.PROCESSING_FINISHED: TemplateSpec(
        subject="Processing finished for {{asset_title}}",
        html="<p>{{asset_title}} is ready. Job status: {{job_status}}.</p>",
    ),
    LifecycleStage.CREATOR_DELIVERY: TemplateSpec(
        subject="Your media delivery is ready",
        html="<p>Hi {{creator_name}}, open your delivery: <a href=\"{{delivery_link}}\">view asset</a>.</p>",
    ),
}


class TemplateReleaseService:
    def __init__(self, client: InfraiClient) -> None:
        self._client = client

    def publish(self, request: TemplateReleaseRequest) -> TemplateReleaseResult:
        template_vars = {
            "creator_name": request.creator_name,
            "asset_title": request.asset_title,
            "job_status": request.job_status,
            "delivery_link": request.delivery_link,
        }
        published: list[PublishedTemplate] = []
        for stage, spec in TEMPLATES.items():
            name = f"{request.product}-{stage.value}-{request.release_id}"
            operation_key = hashlib.sha256(name.encode("utf-8")).hexdigest()
            created = self._client.create_template(
                {"name": name, "subject": spec.subject, "html": spec.html},
                f"template-create-{operation_key}",
            )
            template_id = str(created["template_id"])
            preview = self._client.preview_template(
                template_id,
                template_vars,
                f"template-preview-{operation_key}",
            )
            published.append(
                PublishedTemplate(
                    stage=stage,
                    name=name,
                    template_id=template_id,
                    preview=preview,
                )
            )
        return TemplateReleaseResult(
            release_id=request.release_id, templates=published
        )
