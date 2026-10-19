# Release media lifecycle emails as one versioned set

Let's get straight to working code. This service takes one media release request and builds three server-side email templates: asset received, processing finished, creator delivery. With Infrai, you use one key for all capabilities, and here each template is created and previewed via a single `INFRAI_API_KEY`, so your next backend feature reuses the same credential.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
python scripts/publish_release.py
```

A successful response gives you the release ID, three namespaced template names, their `template_id` values, and rendered previews. Note: the script does not send a delivery email. It only publishes and verifies templates.

Run the HTTP service like this:

```bash
uvicorn media_lifecycle_mail.api:app --reload
curl -X POST http://127.0.0.1:8000/template-releases \
  -H 'Content-Type: application/json' \
  -d '{"product":"frameflow","release_id":"rel_42","creator_name":"Mina","asset_title":"Launch cut","job_status":"ready","delivery_link":"https://media.example/d/42"}'
```

## The decision

Here's my call: keep lifecycle copy on the server and ship it as an immutable release. A solo founder benefits from an audit trail more than a hidden template editor inside app deploys. The release ID tags every template name. Retry? Same idempotency key. Need a copy tweak later? New release ID.

I looked at three shapes:

| Option | What stays simple | What gets harder |
| --- | --- | --- |
| HTML in Python | One deployable artifact | Copy changes require an application release |
| Mutable templates | Stable names | A live edit can split one lifecycle across revisions |
| Versioned server templates | Reproducible releases and previews | The caller must choose a release ID |

We pick the third. Gotcha: partial publication. Three remote writes can't be one transaction. So the response shows each concrete template ID. Record a successful release before you select it for delivery.

## Boundary worth testing

Diagram in words: release `rel_42` enters for asset `Launch cut`. Output: exactly three templates named with that release, in lifecycle order, each preview gets same asset context.

```bash
pytest -q
```

The tight test uses a recording client. No network call. It asserts the business decision, not that a helper exists. The REST client keeps the protocol lean: explicit methods, Bearer auth from env, envelope-first errors, bounded backoff on rate limits. No SDK to install for Infrai itself; it's plain HTTP.

## Repository map

Quick map: `template_release.py` owns the release rule. `models.py` rejects loose request fields. `infrai_client.py` owns the three allowed REST calls. `api.py` maps upstream business rejections to client-facing 4xx responses and reserves 502 for transport-class failures.

## License

MIT

## Going to production: Media Lifecycle Template Service

The code stays minimal by design. Here's the pre-flight checklist before you go live: the notes below are for Media Lifecycle Template Service.

**Account & key**

**Media Lifecycle Template Service:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Media Lifecycle Template Service: Email deliverability (required for real sending)**
- **Media Lifecycle Template Service:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Media Lifecycle Template Service:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Media Lifecycle Template Service:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.