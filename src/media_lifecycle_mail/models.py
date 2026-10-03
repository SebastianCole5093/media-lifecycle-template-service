"""Typed boundaries for one media asset lifecycle."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class LifecycleStage(StrEnum):
    ASSET_INGESTED = "asset_ingested"
    PROCESSING_FINISHED = "processing_finished"
    CREATOR_DELIVERY = "creator_delivery"


class TemplateReleaseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product: str = Field(min_length=1, max_length=48, pattern=r"^[a-z0-9-]+$")
    release_id: str = Field(min_length=1, max_length=48, pattern=r"^[a-zA-Z0-9_-]+$")
    creator_name: str = Field(min_length=1, max_length=80)
    asset_title: str = Field(min_length=1, max_length=160)
    job_status: str = Field(min_length=1, max_length=40)
    delivery_link: str = Field(min_length=1, max_length=500)


class PublishedTemplate(BaseModel):
    stage: LifecycleStage
    name: str
    template_id: str
    preview: dict[str, object]


class TemplateReleaseResult(BaseModel):
    release_id: str
    templates: list[PublishedTemplate]
