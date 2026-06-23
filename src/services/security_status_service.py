"""Deployment and HTTP security status service."""

from __future__ import annotations

import os
from typing import Any, Dict

from src.middleware.api_rate_limit import api_rate_limit_summary
from src.middleware.security_headers import security_headers_summary
from src.services.llm_gateway_service import llm_gateway_control_summary
from src.services.tech_log_service import tech_log_summary
from src.services.worker_runtime_config_service import worker_runtime_summary
from src.core.context import UserContext

SECURITY_STATUS_VERSION = "5.2.9"


def security_status(ctx: UserContext) -> Dict[str, Any]:
    cors_origins = os.getenv("CORS_ALLOW_ORIGINS", "http://127.0.0.1:3000,http://localhost:3000")
    return {
        "version": SECURITY_STATUS_VERSION,
        "apiVersion": "5.2.9",
        "securityHeaders": security_headers_summary(),
        "apiRateLimit": api_rate_limit_summary(),
        "cors": {
            "allowOrigins": [item.strip() for item in cors_origins.split(",") if item.strip()],
            "rule": "Avoid wildcard CORS in production; set CORS_ALLOW_ORIGINS to the deployed frontend domain.",
        },
        "workerRuntime": worker_runtime_summary(),
        "llmGateway": llm_gateway_control_summary(ctx),
        "techLog": tech_log_summary(),
        "nginx": {
            "recommended": True,
            "configPath": "deploy/nginx/ai-erp.conf",
            "rule": "Production traffic should enter through Nginx HTTPS, static frontend, /api reverse proxy, security headers, and coarse rate limit.",
        },
        "deploymentMode": os.getenv("DEPLOYMENT_MODE", "demo"),
    }
