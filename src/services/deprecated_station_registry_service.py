"""V12.14.3 deprecated station registry.

Deprecated Station is not a business station. It is a storage and governance
station for old files, old hooks, old compatibility routes and legacy services.
The first archive-only services have been physically moved out of src/services
into src/deprecated_stations/archive_services.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from src.services.station_registry_service import list_stations

DEPRECATED_STATION_VERSION = "12.14.3"
ROOT_DIR = Path(__file__).resolve().parents[2]

DEPRECATED_ITEMS: List[Dict[str, Any]] = [
    {
        "legacyId": "v112_task_chain_fix_service",
        "filePath": "src/deprecated_stations/archive_services/v112_task_chain_fix_service.py",
        "originalPath": "src/services/v112_task_chain_fix_service.py",
        "legacyVersion": "11.2",
        "oldPurpose": "task chain hotfix and startup patch",
        "currentStatus": "physically_archived",
        "replacementStation": "task_signal_station",
        "allowedUsage": "archive_only",
        "canImport": False,
        "canRoute": False,
        "canFrontendLoad": False,
        "riskLevel": "medium",
        "deleteAfterVersion": "12.16",
        "note": "Physically moved from src/services to deprecated_stations/archive_services in V12.14.3.",
    },
    {
        "legacyId": "v1211_agent_sop_enhancement_service",
        "filePath": "src/deprecated_stations/archive_services/v1211_agent_sop_enhancement_service.py",
        "originalPath": "src/services/v1211_agent_sop_enhancement_service.py",
        "legacyVersion": "12.11",
        "oldPurpose": "Agent SOP enhancement monkey patch",
        "currentStatus": "physically_archived",
        "replacementStation": "agent_enhance_station",
        "allowedUsage": "archive_only",
        "canImport": False,
        "canRoute": False,
        "canFrontendLoad": False,
        "riskLevel": "high",
        "deleteAfterVersion": "12.16",
        "note": "Archive-only. Useful logic must be migrated into agent_enhance_station adapter, not imported from this file.",
    },
    {
        "legacyId": "v1212_rag_llm_agent_service",
        "filePath": "src/deprecated_stations/archive_services/v1212_rag_llm_agent_service.py",
        "originalPath": "src/services/v1212_rag_llm_agent_service.py",
        "legacyVersion": "12.12",
        "oldPurpose": "RAG/LLM Agent SOP monkey patch",
        "currentStatus": "physically_archived",
        "replacementStation": "agent_enhance_station",
        "allowedUsage": "archive_only",
        "canImport": False,
        "canRoute": False,
        "canFrontendLoad": False,
        "riskLevel": "high",
        "deleteAfterVersion": "12.16",
        "note": "Main station registry now points to src.stations.agent_enhance_station.service instead of this old monkey-patch file.",
    },
    {
        "legacyId": "pipeline_compat_route",
        "filePath": "src/api/routes/pipeline.py",
        "legacyVersion": "12.13",
        "oldPurpose": "old pipeline route surface",
        "currentStatus": "legacy_compat_route",
        "replacementStation": "station_interface",
        "allowedUsage": "compat_route_only",
        "canImport": True,
        "canRoute": True,
        "canFrontendLoad": False,
        "riskLevel": "medium",
        "deleteAfterVersion": "12.18",
        "note": "Allowed only as a wrapper over Station Interface. Must not call business services directly.",
    },
    {
        "legacyId": "risk_task_service_adapter_dependency",
        "filePath": "src/services/risk_task_service.py",
        "legacyVersion": "pre-station",
        "oldPurpose": "risk task generation service",
        "currentStatus": "legacy_service_used_by_adapter",
        "replacementStation": "task_signal_station",
        "allowedUsage": "station_adapter_only",
        "canImport": True,
        "canRoute": False,
        "canFrontendLoad": False,
        "riskLevel": "medium",
        "deleteAfterVersion": "13.0",
        "note": "Still used by task_signal_station adapter. Do not call from old routes directly.",
    },
    {
        "legacyId": "operating_unit_snapshot_service_adapter_dependency",
        "filePath": "src/services/operating_unit_snapshot_service.py",
        "legacyVersion": "12.13",
        "oldPurpose": "operating unit snapshot builder",
        "currentStatus": "legacy_service_used_by_adapter",
        "replacementStation": "operating_snapshot_station",
        "allowedUsage": "station_adapter_only",
        "canImport": True,
        "canRoute": False,
        "canFrontendLoad": False,
        "riskLevel": "low",
        "deleteAfterVersion": "13.0",
        "note": "Still used by operating_snapshot_station adapter while station internals are being extracted.",
    },
    {
        "legacyId": "metric_fact_store_service_adapter_candidate",
        "filePath": "src/services/metric_fact_store_service.py",
        "legacyVersion": "12.1",
        "oldPurpose": "metric fact ingestion service",
        "currentStatus": "legacy_service_used_by_adapter",
        "replacementStation": "metric_fact_station",
        "allowedUsage": "station_adapter_only",
        "canImport": True,
        "canRoute": False,
        "canFrontendLoad": False,
        "riskLevel": "low",
        "deleteAfterVersion": "13.0",
        "note": "Candidate adapter dependency for metric_fact_station. Keep out of route and frontend layers.",
    },
]

BLOCKED_MAINLINE_IDS = {item["legacyId"] for item in DEPRECATED_ITEMS if not item.get("canImport") or item.get("allowedUsage") == "archive_only"}


def list_deprecated_items() -> List[Dict[str, Any]]:
    return [{**item, "version": DEPRECATED_STATION_VERSION} for item in DEPRECATED_ITEMS]


def get_deprecated_item(legacy_id: str) -> Dict[str, Any] | None:
    for item in DEPRECATED_ITEMS:
        if item["legacyId"] == legacy_id:
            return {**item, "version": DEPRECATED_STATION_VERSION}
    return None


def deprecated_summary() -> Dict[str, Any]:
    items = list_deprecated_items()
    high_risk = [item for item in items if item.get("riskLevel") == "high"]
    adapter_whitelist = [item for item in items if item.get("allowedUsage") == "station_adapter_only"]
    archived = [item for item in items if item.get("allowedUsage") == "archive_only"]
    return {
        "version": DEPRECATED_STATION_VERSION,
        "stationId": "deprecated_station_archive",
        "itemCount": len(items),
        "highRiskCount": len(high_risk),
        "adapterWhitelistCount": len(adapter_whitelist),
        "archivedReferenceCount": len(archived),
        "items": items,
        "rule": "废弃站点只登记旧文件和旧接口，不参与业务正线。archive_only 文件已开始物理迁移出 src/services。",
    }


def _read_repo_file(path: str) -> str:
    target = ROOT_DIR / path
    try:
        return target.read_text(encoding="utf-8")
    except Exception:
        return ""


def _module_path(file_path: str) -> str:
    return file_path.replace("/", ".").removesuffix(".py")


def mainline_purity_check() -> Dict[str, Any]:
    violations: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    station_backend_modules = {station.get("stationId"): station.get("backendModule") for station in list_stations()}

    deprecated_modules = {_module_path(item["filePath"]): item for item in DEPRECATED_ITEMS}
    deprecated_modules.update({_module_path(item.get("originalPath", "")): item for item in DEPRECATED_ITEMS if item.get("originalPath")})

    for station_id, backend_module in station_backend_modules.items():
        item = deprecated_modules.get(str(backend_module or ""))
        if item and item["legacyId"] in BLOCKED_MAINLINE_IDS:
            violations.append({
                "type": "station_registry_deprecated_backend",
                "stationId": station_id,
                "legacyId": item["legacyId"],
                "filePath": item["filePath"],
                "replacementStation": item["replacementStation"],
                "message": f"{station_id} still points to deprecated backend {backend_module}.",
            })

    main_text = _read_repo_file("src/api/main.py")
    for pattern in ["apply_v112_task_chain_fix", "apply_v1211_agent_sop_enhancement", "apply_v1212_rag_llm_agent"]:
        if pattern in main_text and "legacyStartupHooks" not in main_text:
            violations.append({"type": "main_startup_hook", "pattern": pattern, "filePath": "src/api/main.py", "message": "main.py must not execute legacy startup hook."})

    pipeline_text = _read_repo_file("src/api/routes/pipeline.py")
    for pattern in ["from src.services.risk_task_service import generate_risk_tasks_for_signals", "from src.services.operating_unit_snapshot_service import materialize_operating_unit_snapshot"]:
        if pattern in pipeline_text:
            violations.append({"type": "pipeline_direct_service_import", "pattern": pattern, "filePath": "src/api/routes/pipeline.py", "message": "pipeline.py must remain a Station Interface compatibility layer."})

    for item in DEPRECATED_ITEMS:
        if item.get("allowedUsage") == "archive_only" and item.get("originalPath") and (ROOT_DIR / item["originalPath"]).exists():
            violations.append({"type": "archive_original_path_still_exists", "legacyId": item["legacyId"], "filePath": item["originalPath"], "message": "archive_only file still exists in original src/services path."})
        if item.get("allowedUsage") == "station_adapter_only":
            warnings.append({"type": "adapter_whitelist_legacy_dependency", "legacyId": item["legacyId"], "filePath": item["filePath"], "replacementStation": item["replacementStation"], "message": "Allowed only behind Station Adapter; migrate into station internals later."})

    status = "clean" if not violations else "blocked"
    return {
        "version": DEPRECATED_STATION_VERSION,
        "status": status,
        "failedStage": "deprecated_mainline_leak" if violations else None,
        "violationCount": len(violations),
        "warningCount": len(warnings),
        "violations": violations,
        "warnings": warnings,
        "rule": "主架构正线不得直接引用 archive_only deprecated 文件；archive_only 原路径必须被删除。",
    }
