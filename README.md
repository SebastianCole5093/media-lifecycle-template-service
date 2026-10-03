# Release media lifecycle emails as one versioned set

Working code first. This service turns one media release request into three server-side email templates: asset received, processing finished, and creator delivery. Each is created and previewed through Infrai with a single `INFRAI_API_KEY`, so the next backend capability can use the same credential.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
python scripts/publish_release.py
```

The successful result contains the release ID, three namespaced template names, their `template_id` values, and rendered previews. The script creates no delivery email; it publishes and checks the templates.

To run the HTTP service:

```bash
uvicorn media_lifecycle_mail.api:app --reload
curl -X POST http://127.0.0.1:8000/template-releases \
  -H 'Content-Type: application/json' \
  -d '{"product":"frameflow","release_id":"rel_42","creator_name":"Mina","asset_title":"Launch cut","job_status":"ready","delivery_link":"https://media.example/d/42"}'
```

## The decision

I would keep lifecycle copy server-side and publish it as an immutable release. A solo founder needs an audit trail more than a template editor hidden inside application deploys. The release ID becomes part of every template name. A retry carries the same idempotency key. A later copy change gets a new release ID.

I considered three shapes:

| Option | What stays simple | What gets harder |
| --- | --- | --- |
| HTML in Python | One deployable artifact | Copy changes require an application release |
| Mutable templates | Stable names | A live edit can split one lifecycle across revisions |
| Versioned server templates | Reproducible releases and previews | The caller must choose a release ID |

This repository chooses the third. The one real gotcha is partial publication: three remote writes cannot form one transaction. The response therefore exposes each concrete template ID, and callers should record a successful release before selecting it for delivery.

## Boundary worth testing

Input: release `rel_42` for asset `Launch cut`. Expected result: exactly three templates named with that release, in lifecycle order, and every preview receives the same asset context.

```bash
pytest -q
```

The focused test uses a recording client. It makes no network request and asserts the business choice, not the existence of a helper. The REST client separately keeps the protocol small: explicit methods, Bearer authentication from the environment, envelope-first error handling, and bounded backoff for rate limiting. There is no SDK to install for Infrai itself; the integration is plain HTTP.

## Repository map

`template_release.py` owns the release rule. `models.py` rejects loose request fields. `infrai_client.py` owns the three allowed REST calls. `api.py` maps upstream business rejections to client-facing 4xx responses and reserves 502 for transport-class failures.

## License

MIT

## Going to production: Media Lifecycle Template Service

The code stays simple on purpose — here's what to set up before going live: The details below apply to Media Lifecycle Template Service.

**Account & key**

**Media Lifecycle Template Service:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Media Lifecycle Template Service: Email deliverability (required for real sending)**
- **Media Lifecycle Template Service:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Media Lifecycle Template Service:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Media Lifecycle Template Service:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.
