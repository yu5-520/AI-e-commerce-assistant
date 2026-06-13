from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol
import uuid


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AgentContext:
    """Shared runtime context passed into an Agent."""

    product: str
    mode_name: str
    market_context: dict[str, Any]
    material_pack: dict[str, Any] = field(default_factory=dict)
    client_id: str | None = None
    source: str = "runtime"


@dataclass
class AgentResult:
    """Normalized Agent output contract."""

    agent_id: str
    agent_name: str
    status: str
    output: dict[str, Any]
    trace: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "status": self.status,
            "output": self.output,
            "trace": {
                "run_id": self.trace.get("run_id") or f"run_{uuid.uuid4().hex[:12]}",
                "created_at": self.trace.get("created_at") or now_iso(),
                **{key: value for key, value in self.trace.items() if key not in {"run_id", "created_at"}},
            },
        }


class RuntimeAgent(Protocol):
    agent_id: str
    agent_name: str

    def run(self, context: AgentContext) -> AgentResult:
        """Run the Agent and return a normalized result."""
        ...
