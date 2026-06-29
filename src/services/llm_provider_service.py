"""Unified LLM Provider Gateway for V14.1."""

from __future__ import annotations

import json
import os
import time
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List

import httpx

from src.services.llm_guardrail_service import apply_output_guardrail
from src.services.llm_trace_service import record_llm_trace
from src.services.prompt_template_service import render_prompt

LLM_GATEWAY_VERSION = "14.1.0"
ROOT_DIR = Path(__file__).resolve().parents[2]
PROVIDER_CONFIG_PATH = ROOT_DIR / "config" / "model_providers.json"


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _load_provider_config() -> Dict[str, Any]:
    if not PROVIDER_CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(PROVIDER_CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def current_llm_config() -> Dict[str, Any]:
    providers = _load_provider_config()
    provider_name = os.getenv("LLM_PROVIDER", "deepseek")
    provider = deepcopy(providers.get(provider_name) or providers.get("custom") or {})
    base_url = os.getenv("LLM_BASE_URL") or provider.get("base_url") or os.getenv(provider.get("base_url_env", ""), "")
    api_key_env = provider.get("api_key_env") or "LLM_API_KEY"
    api_key = os.getenv("LLM_API_KEY") or os.getenv(api_key_env, "")
    model = os.getenv("LLM_MODEL") or provider.get("default_model") or os.getenv(provider.get("default_model_env", ""), "") or "mock-model"
    return {"version": LLM_GATEWAY_VERSION, "enabled": _env_bool("LLM_ENABLED", False), "mockMode": _env_bool("LLM_MOCK_MODE", False), "traceEnabled": _env_bool("LLM_TRACE_ENABLED", True), "providerName": provider_name, "providerType": provider.get("type") or "openai_compatible", "baseUrl": base_url.rstrip("/"), "apiKeyEnv": api_key_env, "apiKeyConfigured": bool(api_key), "model": model, "temperature": float(os.getenv("LLM_TEMPERATURE", "0.3") or 0.3), "timeout": float(os.getenv("LLM_TIMEOUT", "60") or 60), "maxTokens": int(os.getenv("LLM_MAX_TOKENS", "1200") or 1200), "boundary": "V14.1 LLM may judge signal routing inside Agent station; code controls station interfaces, permissions and lifecycle."}


def llm_status() -> Dict[str, Any]:
    config = current_llm_config()
    return {**{key: value for key, value in config.items() if key != "baseUrl"}, "baseUrlConfigured": bool(config.get("baseUrl")), "ready": bool(config.get("enabled") and config.get("apiKeyConfigured") and config.get("baseUrl")) or bool(config.get("mockMode")), "recommendedUse": ["task_signal_agent_judgment", "creative_test_package", "feedback_experience_card", "task_action_plan_enrich", "module_report_summary"], "notResponsibleFor": ["station_interface_control", "permission_override", "lifecycle_state_write", "repository_write"]}


def _extract_json(text: str) -> Dict[str, Any]:
    if not text:
        return {}
    clean = text.strip()
    if clean.startswith("```"):
        clean = clean.strip("`")
        if clean.lower().startswith("json"):
            clean = clean[4:].strip()
    try:
        return json.loads(clean)
    except Exception:
        start = clean.find("{")
        end = clean.rfind("}")
        if start >= 0 and end > start:
            return json.loads(clean[start : end + 1])
    return {"rawText": text}


def _mock_task_signal_response(payload: Dict[str, Any]) -> Dict[str, Any]:
    signal = payload.get("signal") or {}
    fallback = payload.get("fallbackDecision") or {}
    signal_type = str(signal.get("signalType") or "")
    decision = fallback.get("decision") or "observe_only"
    if signal_type.startswith("redline_"):
        decision = "manager_review_required"
    elif signal_type.startswith("data_gap_") or signal_type == "metric_large_wave":
        decision = "create_task_snapshot"
    elif signal_type == "normal_wave_candidate":
        decision = "ignore_noise"
    task_plan = fallback.get("taskPlan") or {"title": f"信号判断｜{signal.get('entityId') or 'unknown'}", "taskType": "经营信号复核", "priority": "中", "deadline": "24小时内"}
    return {"decision": decision, "confidence": fallback.get("confidence") or 0.66, "reason": fallback.get("reason") or "mock signal judgment", "taskPlan": task_plan, "evidenceRequirements": fallback.get("evidenceRequirements") or [], "reviewMetrics": fallback.get("reviewMetrics") or [], "riskBoundary": fallback.get("riskBoundary") or ["code controls station boundary"]}


def _mock_creative_response(payload: Dict[str, Any]) -> Dict[str, Any]:
    product = payload.get("productFacts") or {}
    product_name = product.get("shortName") or product.get("title") or payload.get("productId") or "商品"
    return {"llmSummary": f"为{product_name}补充测试表达。", "titleVariants": [{"angle": "搜索关键词型", "title": f"{product_name} 实用款"}], "mainImageDirections": [{"direction": "卖点证据图", "firstImageText": "看得见的卖点", "layout": "商品主体 + 关键细节。"}], "riskCheck": ["避免夸大承诺"]}


def _mock_task_response(payload: Dict[str, Any]) -> Dict[str, Any]:
    action_plan = payload.get("actionPlan") or {}
    package = action_plan.get("recommendedPackage") or {}
    return {"llmSummary": f"当前任务适合执行“{package.get('packageName') or action_plan.get('actionPlanType') or '处理包'}”。", "operatorBrief": "按处理包做小范围验证，再提交指标和证据。", "managerReviewBrief": "复核动作、证据和指标。", "riskCheck": package.get("failureThreshold") or ["证据不足", "变量混杂"]}


def _mock_feedback_response(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {"llmSummary": "该任务可提炼为经验卡草案。", "experienceCardDraft": {"applicableConditions": ["同类目", "同平台", "问题类型相同"], "notApplicableConditions": ["指标组合不同"], "resultSummary": payload.get("managerReview") or "待补充结果。"}, "riskCheck": ["需要复核后入库"]}


def _mock_response(prompt_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    if prompt_name == "task_signal_agent_judgment":
        return _mock_task_signal_response(payload)
    if prompt_name == "creative_test_package":
        return _mock_creative_response(payload)
    if prompt_name == "feedback_experience_card":
        return _mock_feedback_response(payload)
    return _mock_task_response(payload)


def _messages(prompt_name: str, payload: Dict[str, Any]) -> List[Dict[str, str]]:
    system_prompt = render_prompt(prompt_name)
    user_payload = json.dumps(payload, ensure_ascii=False, indent=2)
    return [{"role": "system", "content": system_prompt}, {"role": "user", "content": f"请只输出 JSON。输入如下：\n{user_payload}"}]


def generate_json(*, prompt_name: str, payload: Dict[str, Any], expected_keys: List[str] | None = None, agent_name: str = "LLM Gateway", schema_name: str = "generic_json") -> Dict[str, Any]:
    config = current_llm_config()
    start = time.time()
    fallback_used = False
    status = "skipped"
    error_message = ""
    if not config["enabled"] or config["mockMode"] or not config["apiKeyConfigured"] or not config["baseUrl"]:
        fallback_used = True
        status = "fallback"
        result = _mock_response(prompt_name, payload)
    else:
        try:
            headers = {"Authorization": f"Bearer {os.getenv('LLM_API_KEY') or os.getenv(config['apiKeyEnv'], '')}", "Content-Type": "application/json"}
            body = {"model": config["model"], "messages": _messages(prompt_name, payload), "temperature": config["temperature"], "max_tokens": config["maxTokens"], "response_format": {"type": "json_object"}}
            with httpx.Client(timeout=config["timeout"]) as client:
                response = client.post(f"{config['baseUrl']}/chat/completions", headers=headers, json=body)
                response.raise_for_status()
                data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            result = _extract_json(content)
            status = "success"
        except Exception as exc:
            fallback_used = True
            status = "fallback_error"
            error_message = str(exc)
            result = _mock_response(prompt_name, payload)
    guarded = apply_output_guardrail(result, expected_keys=expected_keys)
    latency_ms = int((time.time() - start) * 1000)
    trace = None
    if config.get("traceEnabled"):
        trace = record_llm_trace(agent_name=agent_name, provider=config["providerName"], model=config["model"], prompt_name=prompt_name, schema_name=schema_name, status=status, fallback_used=fallback_used, latency_ms=latency_ms, request_meta={"expectedKeys": expected_keys or [], "payloadKeys": sorted(payload.keys())}, response_meta={"guardrailValid": guarded.get("llmGuardrail", {}).get("valid"), "responseKeys": sorted(guarded.keys())}, error_message=error_message)
    return {"version": LLM_GATEWAY_VERSION, "enabled": config["enabled"], "provider": config["providerName"], "model": config["model"], "status": status, "fallbackUsed": fallback_used, "latencyMs": latency_ms, "trace": trace, "output": guarded, "boundary": config["boundary"]}
