"""Publish one example release and print its template IDs."""

from media_lifecycle_mail.infrai_client import InfraiClient
from media_lifecycle_mail.models import TemplateReleaseRequest
from media_lifecycle_mail.template_release import TemplateReleaseService


def main() -> None:
    client = InfraiClient()
    try:
        result = TemplateReleaseService(client).publish(
            TemplateReleaseRequest(
                product="frameflow",
                release_id="demo-2026-10-01",
                creator_name="Mina",
                asset_title="Launch cut",
                job_status="ready",
                delivery_link="https://media.example/deliveries/launch-cut",
            )
        )
        print(result.model_dump_json(indent=2))
    finally:
        client.close()


if __name__ == "__main__":
    main()
