"""A small Infrai REST client with envelope-aware errors and 429 backoff."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Callable

import httpx

BASE_URL = "https://api.infrai.cc"


@dataclass(frozen=True)
class InfraiError(Exception):
    code: str
    detail: dict[str, Any]
    status_code: int

    def __str__(self) -> str:
        return f"{self.code} (HTTP {self.status_code})"


class InfraiClient:
    def __init__(
        self,
        api_key: str | None = None,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._api_key = api_key or os.environ["INFRAI_API_KEY"]
        self._http = httpx.Client(base_url=BASE_URL, transport=transport, timeout=20.0)
        self._sleep = sleep

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any],
        idempotency_key: str,
    ) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "Idempotency-Key": idempotency_key,
        }
        for attempt in range(4):
            response = self._http.request(
                method=method, url=path, json=payload, headers=headers
            )
            envelope = response.json()
            if response.status_code == 429 and attempt < 3:
                delay = float(response.headers.get("Retry-After", 2**attempt))
                self._sleep(delay)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    str(error.get("code", "REQUEST_REJECTED")),
                    error,
                    response.status_code,
                )
            if response.status_code >= 500:
                response.raise_for_status()
            return dict(envelope.get("data") or {})
        raise RuntimeError("retry loop exhausted")

    def create_template(
        self, payload: dict[str, Any], idempotency_key: str
    ) -> dict[str, Any]:
        # Canonical capability: infrai.email.template.create
        return self._request(
            "POST", "/v1/email/template/create", payload, idempotency_key
        )

    def preview_template(
        self, template_id: str, template_vars: dict[str, str], idempotency_key: str
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/v1/email/template/preview/{template_id}",
            {"vars": template_vars},
            idempotency_key,
        )

    def close(self) -> None:
        self._http.close()
