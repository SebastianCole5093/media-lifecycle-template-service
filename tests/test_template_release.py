from typing import Any

from media_lifecycle_mail.models import LifecycleStage, TemplateReleaseRequest
from media_lifecycle_mail.template_release import TemplateReleaseService


class RecordingClient:
    def __init__(self) -> None:
        self.created: list[tuple[dict[str, Any], str]] = []
        self.previews: list[tuple[str, dict[str, str], str]] = []

    def create_template(
        self, payload: dict[str, Any], idempotency_key: str
    ) -> dict[str, str]:
        self.created.append((payload, idempotency_key))
        return {"template_id": f"tmpl-{len(self.created)}"}

    def preview_template(
        self, template_id: str, template_vars: dict[str, str], idempotency_key: str
    ) -> dict[str, object]:
        self.previews.append((template_id, template_vars, idempotency_key))
        return {"html": f"preview for {template_vars['asset_title']}"}


def test_release_namespaces_each_stage_and_previews_with_asset_context() -> None:
    client = RecordingClient()
    request = TemplateReleaseRequest(
        product="frameflow",
        release_id="rel_42",
        creator_name="Mina",
        asset_title="Launch cut",
        job_status="ready",
        delivery_link="https://media.example/d/42",
    )

    result = TemplateReleaseService(client).publish(request)  # type: ignore[arg-type]

    assert [item.stage for item in result.templates] == list(LifecycleStage)
    assert [call[0]["name"] for call in client.created] == [
        "frameflow-asset_ingested-rel_42",
        "frameflow-processing_finished-rel_42",
        "frameflow-creator_delivery-rel_42",
    ]
    assert all(call[1].startswith("template-create-") for call in client.created)
    assert {call[1]["asset_title"] for call in client.previews} == {"Launch cut"}
    assert [item.template_id for item in result.templates] == [
        "tmpl-1",
        "tmpl-2",
        "tmpl-3",
    ]
