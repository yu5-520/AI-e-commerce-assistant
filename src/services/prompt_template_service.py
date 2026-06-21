"""Prompt template service for V4.5 LLM Gateway."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

ROOT_DIR = Path(__file__).resolve().parents[2]
PROMPT_DIR = ROOT_DIR / "prompts"

PROMPT_VERSION = "4.5.0"

DEFAULT_PROMPTS: Dict[str, str] = {
    "creative_test_package": """
你是电商标题主图测试包生成 Agent。请根据商品事实、类目 Profile、平台规则、竞品信号、RAG 经验和 ActionPlan，生成可上架小流量测试的标题 / 主图 / 卖点组合。
要求：只输出 JSON，不要 Markdown；不得建议直接改价、直接投放、直接退款、直接发布商品或回写店铺后台。
""".strip(),
    "task_action_plan_enrich": """
你是电商经营任务说明增强 Agent。请基于确定性的 problemType 与 ActionPlan，把处理包写成更具体、可执行、可复核的任务说明。
要求：只输出 JSON；不得改变 problemType，不得新增越权执行动作。
""".strip(),
    "feedback_experience_card": """
你是电商运营经验卡提炼 Agent。请根据任务提交、总管复核、前后指标和日志，把经验整理成结构化经验卡草案。
要求：只输出 JSON；必须包含适用条件、不适用条件、结果指标和复核状态；不得自动批准入库。
""".strip(),
    "module_report_summary": """
你是经营详情报告摘要 Agent。请将模块数据、证据、ActionPlan 和 RAG 引用整理为运营可读摘要。
要求：只输出 JSON；摘要必须围绕问题类型、执行包、提交证据和复核标准。
""".strip(),
}


def prompt_path(prompt_name: str) -> Path:
    safe = prompt_name.replace("/", "_").replace("..", "_")
    return PROMPT_DIR / f"{safe}.md"


def load_prompt(prompt_name: str) -> str:
    path = prompt_path(prompt_name)
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return DEFAULT_PROMPTS.get(prompt_name, DEFAULT_PROMPTS["module_report_summary"])


def render_prompt(prompt_name: str, variables: Dict[str, Any] | None = None) -> str:
    prompt = load_prompt(prompt_name)
    variables = variables or {}
    for key, value in variables.items():
        prompt = prompt.replace("{{" + key + "}}", str(value))
    return prompt


def prompt_summary() -> Dict[str, Any]:
    existing = []
    if PROMPT_DIR.exists():
        existing = sorted(path.stem for path in PROMPT_DIR.glob("*.md"))
    return {
        "version": PROMPT_VERSION,
        "promptDir": str(PROMPT_DIR.relative_to(ROOT_DIR)),
        "defaultPrompts": sorted(DEFAULT_PROMPTS.keys()),
        "filePrompts": existing,
        "rule": "Prompts define wording tasks only; ActionPlan still owns problemType and execution package contract.",
    }
