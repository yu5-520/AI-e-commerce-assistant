"""Lightweight in-memory API rate limit middleware.

This is a FastAPI-side tenant/IP/path guard for Demo and small ECS deployments.
Nginx should still provide the outer coarse limit in production.
"""

from __future__ import annotations

import os
import time
from collections import defaultdict, deque
from typing import Any, Deque

from fastapi.responses import JSONResponse

API_RATE_LIMIT_VERSION = "5.2.9"
_WINDOW_SECONDS = int(os.getenv("API_RATE_LIMIT_WINDOW_SECONDS", "60"))
_MAX_REQUESTS = int(os.getenv("API_RATE_LIMIT_PER_MINUTE", "120"))
_BUCKETS: dict[str, Deque[float]] = defaultdict(deque)
_EXEMPT_PREFIXES = tuple(filter(None, os.getenv("API_RATE_LIMIT_EXEMPT_PREFIXES", "/,/web_demo,/api/health").split(",")))


def api_rate_limit_enabled() -> bool:
    return os.getenv("API_RATE_LIMIT_ENABLED", "true").lower() != "false"


def _client_ip(request: Any) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return getattr(request.client, "host", "unknown")


def _rate_key(request: Any) -> str:
    tenant_id = request.headers.get("x-tenant-id", "tenant_demo")
    return f"{tenant_id}:{_client_ip(request)}:{request.url.path}"


def _is_exempt(path: str) -> bool:
    if path == "/":
        return True
    return any(path.startswith(prefix) and prefix not in {"/"} for prefix in _EXEMPT_PREFIXES)


async def api_rate_limit_middleware(request: Any, call_next: Any) -> Any:
    if not api_rate_limit_enabled() or _is_exempt(request.url.path):
        return await call_next(request)
    now = time.time()
    key = _rate_key(request)
    bucket = _BUCKETS[key]
    while bucket and bucket[0] <= now - _WINDOW_SECONDS:
        bucket.popleft()
    if len(bucket) >= _MAX_REQUESTS:
        return JSONResponse(
            status_code=429,
            content={
                "detail": "API rate limit exceeded",
                "version": API_RATE_LIMIT_VERSION,
                "limit": _MAX_REQUESTS,
                "windowSeconds": _WINDOW_SECONDS,
                "retryAfterSeconds": max(1, int(_WINDOW_SECONDS - (now - bucket[0]))),
            },
            headers={"Retry-After": str(max(1, int(_WINDOW_SECONDS - (now - bucket[0]))))},
        )
    bucket.append(now)
    response = await call_next(request)
    response.headers.setdefault("X-RateLimit-Limit", str(_MAX_REQUESTS))
    response.headers.setdefault("X-RateLimit-Remaining", str(max(_MAX_REQUESTS - len(bucket), 0)))
    response.headers.setdefault("X-RateLimit-Window", str(_WINDOW_SECONDS))
    return response


def api_rate_limit_summary() -> dict[str, Any]:
    return {
        "version": API_RATE_LIMIT_VERSION,
        "enabled": api_rate_limit_enabled(),
        "limit": _MAX_REQUESTS,
        "windowSeconds": _WINDOW_SECONDS,
        "activeBuckets": len(_BUCKETS),
        "exemptPrefixes": list(_EXEMPT_PREFIXES),
        "rule": "FastAPI applies tenant/IP/path limits; Nginx should still apply coarse edge rate limits.",
    }
