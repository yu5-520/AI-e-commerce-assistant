"""V7.2 SaaS control plane and enterprise architecture baseline."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List

from src.core.context import UserContext
from src.repositories.scoped_repository import query_plan_for_context
from src.repositories.sqlite_repository import connect, dumps, loads
from src.services.v71_tenant_config_service import ensure_v71_tenant_config_tables
from src.services.v72_tenant_config_console_service import tenant_config_console_summary

V7_SAAS_VERSION = "7.2.0"

CONTROL_PLANE_LAYERS: List[Dict[str, Any]] = [
    {"layerId": "V7-L1", "name": "租户与组织控制面", "domain": "Identity", "status": "baseline_ready", "capability": "tenant / org / store / user / role / data-scope", "boundary": "所有业务查询必须先拿 UserContext，再进入 scoped repository。"},
    {"layerId": "V7-L2", "name": "数据接入与契约中心", "domain": "Data Contract", "status": "baseline_ready", "capability": "ERP / CRM / 平台报表统一入口、字段识别、版本记录、数据血缘", "boundary": "前端不再手选报表业务分类；后台识别字段、商品、快照、趋势。"},
    {"layerId": "V7-L3", "name": "经营趋势与信号中心", "domain": "Business Signal", "status": "baseline_ready", "capability": "商品快照、指标趋势、经营信号、平台/类目/店铺趋势", "boundary": "任务不能从单点异常直接生成，必须经过趋势和多信号聚合。"},
    {"layerId": "V7-L4", "name": "RAG 指标与规则中心", "domain": "AI Governance", "status": "baseline_ready", "capability": "库存安全线、ROI、CTR、CVR、毛利、售后红线、案例记忆", "boundary": "中高风险任务不得由 Agent 自造指标；缺规则只能生成复核/补全任务。"},
    {"layerId": "V7-L5", "name": "风险门控与任务编排中心", "domain": "Workflow", "status": "baseline_ready", "capability": "低/中/高风险分级、高风险趋势门控、任务生命周期、执行任务拆分", "boundary": "高风险通过门控后也只是申请/审批，不直接执行业务动作。"},
    {"layerId": "V7-L6", "name": "权限额度与审批中心", "domain": "Approval", "status": "baseline_ready", "capability": "运营申请、总管审批、老板审批、额度校验、审批事件", "boundary": "账号额度决定执行、申请、升级审批或复核；Agent 不允许绕过审批。"},
    {"layerId": "V7-L7", "name": "执行回写与复盘中心", "domain": "Feedback", "status": "baseline_ready", "capability": "执行结果、实际花费、采购金额、证据、复盘案例、RAG 沉淀", "boundary": "执行回写只记录结果和证据，不自动改写经营数据或公司规则。"},
    {"layerId": "V7-L8", "name": "审计、日志与可观测中心", "domain": "Observability", "status": "baseline_ready", "capability": "业务审计、技术日志、worker、LLM gateway、数据版本、回滚记录", "boundary": "所有关键动作必须可追踪：谁、何时、基于什么数据、做了什么决定。"},
    {"layerId": "V7-L9", "name": "SaaS 交付治理中心", "domain": "Delivery", "status": "baseline_ready", "capability": "版本、租户配置、功能开关、灰度、运行模式、SLA 检查", "boundary": "Demo 能跑不等于 SaaS 可交付；V7 以可配置、可审计、可迁移为交付边界。"},
    {"layerId": "V7-L10", "name": "租户配置与功能开关中心", "domain": "Config", "status": "v7_2_ready", "capability": "tenant config / feature flag / rollout / role gating / config audit / console actions", "boundary": "SaaS 能力按租户、角色和灰度规则开放，并可由配置中心前端操作。"},
]

PROCESS_REGISTRY: List[Dict[str, Any]] = [
    {"processId": "V7-P1", "name": "动态经营闭环主流程", "entry": "报表中心 / API / RPA 同步", "stages": ["数据接入", "商品匹配", "快照生成", "趋势计算", "经营信号", "RAG 指标", "风险任务", "审批", "执行", "回写", "复盘沉淀"], "ownerRole": "manager", "status": "standardized"},
    {"processId": "V7-P2", "name": "高风险投产治理流程", "entry": "趋势中心高风险候选", "stages": ["RAG 指标门控", "7/30天趋势门控", "权限额度校验", "审批流", "执行任务", "执行回写", "超预算复盘"], "ownerRole": "owner", "status": "standardized"},
    {"processId": "V7-P3", "name": "数据版本与回滚流程", "entry": "报表导入记录", "stages": ["导入记录", "数据版本", "任务影响", "复核", "回滚/删除", "审计日志"], "ownerRole": "manager", "status": "standardized"},
    {"processId": "V7-P4", "name": "RAG 规则治理流程", "entry": "复盘案例 / 人工规则", "stages": ["案例生成", "规则候选", "人工复核", "启用规则", "任务引用", "效果复盘"], "ownerRole": "owner", "status": "planned_next"},
    {"processId": "V7-P5", "name": "租户灰度发布流程", "entry": "配置中心 / 功能开关", "stages": ["创建功能开关", "绑定租户", "绑定角色", "设置灰度比例", "前端操作", "观察审计", "全量开放或回滚"], "ownerRole": "owner", "status": "v7_2_ready"},
]

GOVERNANCE_CHECKS: List[Dict[str, Any]] = [
    {"checkId": "V7-G1", "name": "租户隔离", "required": True, "status": "scaffolded", "evidence": "UserContext + scoped repository + tenant/org/store scope"},
    {"checkId": "V7-G2", "name": "任务不可越权", "required": True, "status": "scaffolded", "evidence": "visibleRoleIds + permissionBudgetGate + approvalChain"},
    {"checkId": "V7-G3", "name": "高风险不可直执", "required": True, "status": "ready", "evidence": "highRiskTrendGate + approvalLifecycle + executionTask split"},
    {"checkId": "V7-G4", "name": "Agent 指标不可胡编", "required": True, "status": "ready", "evidence": "indicator_rag_service + ragIndicatorConstraints"},
    {"checkId": "V7-G5", "name": "关键动作可审计", "required": True, "status": "scaffolded", "evidence": "approval events + execution results + review cases + audit logs"},
    {"checkId": "V7-G6", "name": "SaaS 可迁移", "required": True, "status": "hybrid", "evidence": "SQLite demo runtime + repository mirror / PostgreSQL cutover docs"},
    {"checkId": "V7-G7", "name": "功能不可无配置开放", "required": True, "status": "v7_2_ready", "evidence": "tenant config console + feature flags + rollout rules + config audit"},
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_v7_saas_control_plane_tables() -> None:
    with connect() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS saas_control_layers_v7 (layer_id TEXT PRIMARY KEY, name TEXT NOT NULL, domain TEXT NOT NULL, status TEXT NOT NULL, payload TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS saas_process_registry_v7 (process_id TEXT PRIMARY KEY, name TEXT NOT NULL, owner_role TEXT, status TEXT NOT NULL, payload TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS saas_governance_checks_v7 (check_id TEXT PRIMARY KEY, name TEXT NOT NULL, required INTEGER DEFAULT 1, status TEXT NOT NULL, payload TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)""")
        now = now_iso()
        for layer in CONTROL_PLANE_LAYERS:
            conn.execute("INSERT OR REPLACE INTO saas_control_layers_v7 (layer_id, name, domain, status, payload, created_at, updated_at) VALUES (?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM saas_control_layers_v7 WHERE layer_id = ?), ?), ?)", (layer["layerId"], layer["name"], layer["domain"], layer["status"], dumps(layer), layer["layerId"], now, now))
        for process in PROCESS_REGISTRY:
            conn.execute("INSERT OR REPLACE INTO saas_process_registry_v7 (process_id, name, owner_role, status, payload, created_at, updated_at) VALUES (?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM saas_process_registry_v7 WHERE process_id = ?), ?), ?)", (process["processId"], process["name"], process["ownerRole"], process["status"], dumps(process), process["processId"], now, now))
        for check in GOVERNANCE_CHECKS:
            conn.execute("INSERT OR REPLACE INTO saas_governance_checks_v7 (check_id, name, required, status, payload, created_at, updated_at) VALUES (?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM saas_governance_checks_v7 WHERE check_id = ?), ?), ?)", (check["checkId"], check["name"], 1 if check.get("required") else 0, check["status"], dumps(check), check["checkId"], now, now))
        conn.commit()
    ensure_v71_tenant_config_tables()


def _read_seeded_rows() -> Dict[str, List[Dict[str, Any]]]:
    ensure_v7_saas_control_plane_tables()
    with connect() as conn:
        layer_rows = conn.execute("SELECT payload FROM saas_control_layers_v7 ORDER BY layer_id ASC").fetchall()
        process_rows = conn.execute("SELECT payload FROM saas_process_registry_v7 ORDER BY process_id ASC").fetchall()
        check_rows = conn.execute("SELECT payload FROM saas_governance_checks_v7 ORDER BY check_id ASC").fetchall()
    return {"layers": [loads(row["payload"]) for row in layer_rows], "processes": [loads(row["payload"]) for row in process_rows], "checks": [loads(row["payload"]) for row in check_rows]}


def v7_saas_architecture_summary(ctx: UserContext) -> Dict[str, Any]:
    rows = _read_seeded_rows()
    config_summary = tenant_config_console_summary(ctx)
    query_plan = query_plan_for_context(ctx, table_alias="resource")
    by_domain: Dict[str, int] = defaultdict(int)
    for layer in rows["layers"]:
        by_domain[layer["domain"]] += 1
    return {
        "version": V7_SAAS_VERSION,
        "title": "V7.2 SaaS 大厂体系架构基底",
        "positioning": "把 V6 经营闭环收束成 SaaS 控制面，并通过 V7.2 配置中心前端完成启用、暂停、灰度和审计。",
        "currentContext": ctx.to_dict(),
        "mandatoryScopePlan": {"where": query_plan.where, "params": query_plan.params, "rule": query_plan.rule},
        "controlPlane": {"layerCount": len(rows["layers"]), "domainCount": dict(by_domain), "layers": rows["layers"]},
        "tenantConfig": config_summary,
        "processRegistry": rows["processes"],
        "governanceChecks": rows["checks"],
        "mainWorkflow": ["报表/API/RPA 数据接入", "字段识别与商品匹配", "商品快照与指标趋势", "经营信号聚合", "RAG 指标约束", "风险分级任务", "权限额度与审批生命周期", "执行任务与结果回写", "执行复盘与 RAG 案例沉淀", "租户配置中心前端操作、功能开关、灰度与交付治理"],
        "definitionOfDone": ["所有业务动作可归属到租户、组织、店铺、角色和数据范围。", "所有关键流程有标准状态机、审计事件和回滚边界。", "所有中高风险任务有 RAG 指标、历史趋势、权限额度和审批链路。", "审批与执行分离，执行结果回写后进入复盘和 RAG 案例记忆。", "老板/总管可在前端配置中心操作功能开关，老板可调整灰度规则。"],
    }
