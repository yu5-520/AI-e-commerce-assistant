"""Security header middleware for the public HTTP boundary."""

from __future__ import annotations

import os
from typing import Any

SECURITY_HEADERS_VERSION = "5.2.9"

DEFAULT_CSP = "default-src 'self'; img-src 'self' data: https:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self' http://127.0.0.1:* http://localhost:*; frame-ancestors 'none'"


def security_headers_enabled() -> bool:
    return os.getenv("SECURITY_HEADERS_ENABLED", "true").lower() != "false"


def security_header_values() -> dict[str, str]:
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "no-referrer",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=(), payment=()",
        "Content-Security-Policy": os.getenv("CONTENT_SECURITY_POLICY", DEFAULT_CSP),
        "X-Permitted-Cross-Domain-Policies": "none",
    }


async def security_headers_middleware(request: Any, call_next: Any) -> Any:
    response = await call_next(request)
    if not security_headers_enabled():
        return response
    for header, value in security_header_values().items():
        response.headers.setdefault(header, value)
    return response


def security_headers_summary() -> dict[str, Any]:
    return {"version": SECURITY_HEADERS_VERSION, "enabled": security_headers_enabled(), "headers": security_header_values(), "rule": "Security headers are added by FastAPI and should also be mirrored at Nginx."}
