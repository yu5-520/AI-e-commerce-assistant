"""Health routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

from src.services.llm_provider_service import llm_status
from src.services.mcp_adapter_service import mcp_adapter_summary
from src.services.tool_gateway_service import tool_gateway_summary

API_VERSION = "4.5.1"

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health() -> Dict[str, Any]:
    llm = llm_status()
    return {
        "ok": True,
        "version": API_VERSION,
        "product": "AI ERP Operating Advisor",
        "mode": "v451_action_plan_ui",
        "api_entry": "/api/modules/*",
        "account_entry": "/api/accounts",
        "llm_entry": "/api/llm/status",
        "safety": {
            "auto_scheduled_platform_action": False,
            "auto_ad_account_operation": False,
            "auto_product_publish": False,
            "auto_price_change": False,
            "auto_inventory_change": False,
            "auto_refund": False,
            "auto_erp_crm_write": False,
            "auto_customer_message_blast": False,
            "marketplace_api_connected": False,
        },
        "v451_action_plan_ui": True,
        "frontend_action_plan_package_cards": True,
        "frontend_task_draft_cards": True,
        "frontend_hides_engineering_ids": True,
        "frontend_numbered_operator_steps": True,
        "v450_llm_gateway": True,
        "llm_gateway_endpoint": "/api/llm/status",
        "llm_generate_endpoint": "/api/llm/generate",
        "llm_trace_endpoint": "/api/llm/traces",
        "llm_provider_service": "src/services/llm_provider_service.py",
        "llm_guardrail_service": "src/services/llm_guardrail_service.py",
        "llm_trace_service": "src/services/llm_trace_service.py",
        "prompt_template_service": "src/services/prompt_template_service.py",
        "tool_gateway_service": "src/services/tool_gateway_service.py",
        "mcp_adapter_service": "src/services/mcp_adapter_service.py",
        "llm_enabled": llm.get("enabled"),
        "llm_ready": llm.get("ready"),
        "llm_provider": llm.get("providerName"),
        "llm_model": llm.get("model"),
        "llm_api_key_configured": llm.get("apiKeyConfigured"),
        "llm_gateway_rule": "LLM 只做表达增强和草案生成；ActionPlan、权限、任务池、人审和审计链路保持确定性。",
        "llm_priority_modules": ["creative_vertical_agent", "feedback_flywheel", "task_action_plan", "module_report_summary"],
        "v450_tool_gateway": True,
        "tool_gateway": tool_gateway_summary(),
        "v450_mcp_adapter_boundary": True,
        "mcp_adapter": mcp_adapter_summary(),
        "mcp_rule": "MCP 只作为未来外部工具适配层，不替代 LLM Gateway、Tool Gateway、ActionPlan、任务池或权限系统。",
        "v442_problem_type_action_plan": True,
        "action_plan_service": "src/services/action_plan_service.py",
        "action_plan_rule": "模块发现问题，problemType 决定处理包，Agent 不按模块套同一模板。",
        "action_plan_problem_types": ["low_ctr_low_conversion", "detail_page_conversion", "low_roi_high_refund", "low_inventory_activity", "competitor_signal_to_test", "report_data_anomaly"],
        "action_plan_outputs": ["actionPlan", "executionPackages", "executionSteps", "evidenceRequired", "submitMetrics", "acceptanceCriteria", "failureThreshold", "reviewFocus"],
        "v4_module_agent_layer": True,
        "v4_agent_version": API_VERSION,
        "agent_runtime_mode": "advisory_only_with_llm_enrichment",
        "module_agent_endpoint": "/api/modules/agents/{module}/{entity_id}",
        "module_agent_task_endpoint": "/api/modules/agents/{module}/{entity_id}/tasks",
        "cycle_agent_endpoint": "/api/modules/agents/cycle/{target}",
        "v420_task_generation_agent": True,
        "task_generation_endpoint": "/api/modules/agents/tasks/generate",
        "task_playbook_endpoint": "/api/modules/agents/tasks/{task_id}/playbook",
        "v430_creative_vertical_agent": True,
        "v441_creative_test_packages": True,
        "creative_vertical_endpoint": "/api/modules/agents/creative/{product_id}",
        "creative_vertical_task_endpoint": "/api/modules/agents/creative/{product_id}/tasks",
        "creative_vertical_outputs": ["titleVariants", "mainImageDirections", "sellingPointOrder", "testPackages", "selectedPackage", "testPlan", "taskDraft", "llmEnrichment"],
        "v440_feedback_flywheel": True,
        "feedback_flywheel_endpoint": "/api/modules/feedback-flywheel",
        "feedback_cycle_endpoint": "/api/modules/feedback-flywheel/cycle/{target}",
        "feedback_cycle_draft_endpoint": "/api/modules/feedback-flywheel/cycle/{target}/draft",
        "feedback_requires_human_approval": True,
        "agent_outputs": ["analysis", "summary", "taskDrafts", "humanDecision", "forbiddenActions", "ragReferences", "confidence", "creativeTestPackages", "actionPlan", "executionPackages", "llmEnrichment", "feedbackMetrics"],
        "agent_forbidden_actions": ["direct_price_change", "direct_ad_spend_change", "direct_refund", "direct_publish", "direct_erp_crm_write", "exaggerated_claim", "auto_memory_approval"],
        "agent_requires_human_confirmation": True,
        "v410_rag_memory": True,
        "rag_memory_endpoint": "/api/modules/rag-memory",
        "rag_memory_search_endpoint": "/api/modules/rag-memory/search",
        "rag_memory_write_gate": ["manager_review", "quality_score", "metrics_change", "human_approval"],
        "frontend_agent_panel": "task-report",
        "frontend_action_plan_rendering": True,
        "data_version_service_version": "3.1.4",
        "role_scoped_task_flow": True,
        "warning_to_operator_todo": True,
        "cross_account_lifecycle_sync": True,
        "v3_data_snapshot": True,
        "v3_report_alert_event": True,
        "v3_alert_to_task_bridge": True,
        "v3_templates_endpoint": "/api/data/templates",
        "v3_preview_endpoint": "/api/data/preview",
        "v3_confirm_import_endpoint": "/api/data/import/confirm",
        "v3_alerts_endpoint": "/api/data/alerts",
        "v3_versions_endpoint": "/api/data/versions",
        "v3_summary_endpoint": "/api/data/v3-summary",
    }
