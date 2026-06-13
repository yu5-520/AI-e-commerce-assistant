from __future__ import annotations

from .material_observer_agent import MaterialObserverAgent

AGENT_REGISTRY = {
    MaterialObserverAgent.agent_id: MaterialObserverAgent,
}


def get_agent(agent_id: str):
    agent_cls = AGENT_REGISTRY.get(agent_id)
    if not agent_cls:
        raise KeyError(f"Unknown agent_id: {agent_id}")
    return agent_cls()
