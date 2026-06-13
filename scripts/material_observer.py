from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.material_observer_agent import (  # noqa: E402
    AGENT_ID,
    AGENT_NAME,
    AGENT_STAGE,
    AGENT_VERSION,
    FUNCTION_WORDS,
    GENERIC_BANNED_WORDS,
    PRICE_WORDS,
    SCENE_WORDS,
    SOURCE_POLICY,
    MaterialObserverAgent,
    agent_contract,
    build_material_observation,
)

__all__ = [
    "AGENT_ID",
    "AGENT_NAME",
    "AGENT_VERSION",
    "AGENT_STAGE",
    "SCENE_WORDS",
    "FUNCTION_WORDS",
    "PRICE_WORDS",
    "GENERIC_BANNED_WORDS",
    "SOURCE_POLICY",
    "MaterialObserverAgent",
    "agent_contract",
    "build_material_observation",
]
