"""Worker runtime configuration.

V5.2.2 adds the Redis / ARQ configuration layer while keeping SQLite worker_jobs
as the fallback queue for Demo and low-cost ECS deployments.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from typing import Any, Dict

WORKER_RUNTIME_VERSION = "5.2.2"


@dataclass(frozen=True)
class WorkerRuntimeConfig:
    mode: str
    redis_url: str
    queue_name: str
    max_jobs: int
    job_timeout_seconds: int
    keep_result_seconds: int
    fallback_to_sqlite: bool

    @property
    def redis_enabled(self) -> bool:
        return self.mode in {"redis", "arq"} and bool(self.redis_url)


def worker_runtime_config() -> WorkerRuntimeConfig:
    mode = (os.getenv("WORKER_RUNTIME") or os.getenv("WORKER_MODE") or "sqlite").strip().lower()
    redis_url = (os.getenv("REDIS_URL") or os.getenv("ARQ_REDIS_URL") or "redis://127.0.0.1:6379/0").strip()
    return WorkerRuntimeConfig(
        mode=mode,
        redis_url=redis_url,
        queue_name=os.getenv("WORKER_QUEUE_NAME", "default"),
        max_jobs=int(os.getenv("WORKER_MAX_JOBS", "4")),
        job_timeout_seconds=int(os.getenv("WORKER_JOB_TIMEOUT_SECONDS", "300")),
        keep_result_seconds=int(os.getenv("WORKER_KEEP_RESULT_SECONDS", "3600")),
        fallback_to_sqlite=(os.getenv("WORKER_FALLBACK_SQLITE", "true").lower() != "false"),
    )


def worker_runtime_summary() -> Dict[str, Any]:
    config = worker_runtime_config()
    return {
        "version": WORKER_RUNTIME_VERSION,
        "runtime": asdict(config),
        "activeBackend": "redis_arq" if config.redis_enabled else "sqlite_fallback",
        "rule": "WORKER_RUNTIME=redis/arq 时使用 Redis / ARQ；未配置或不可用时保留 SQLite worker_jobs 队列表。",
        "env": {
            "WORKER_RUNTIME": "sqlite | redis | arq",
            "REDIS_URL": "redis://127.0.0.1:6379/0",
            "WORKER_QUEUE_NAME": "default",
            "WORKER_MAX_JOBS": "4",
            "WORKER_JOB_TIMEOUT_SECONDS": "300",
            "WORKER_FALLBACK_SQLITE": "true",
        },
    }
