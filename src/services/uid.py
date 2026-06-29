"""Small UID helper used by task evidence and demo runtime services.

V12.11.4 startup hotfix: recent task evidence services import
`src.services.uid.make_id`, but the helper module was missing in the repository.
Keeping this as a tiny compatibility shim prevents FastAPI startup from failing
on ECS while preserving the existing call sites.
"""

from __future__ import annotations

import uuid
from datetime import datetime

UID_VERSION = "12.11.4"


def make_id(prefix: str = "ID") -> str:
    safe_prefix = "".join(ch for ch in str(prefix or "ID") if ch.isalnum() or ch in {"_", "-"}).strip("_-") or "ID"
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{safe_prefix}-{stamp}-{uuid.uuid4().hex[:8].upper()}"
