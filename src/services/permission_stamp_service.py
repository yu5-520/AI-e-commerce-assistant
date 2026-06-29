"""V14.5 permission stamp service.

Permission is a stamp that travels with imported rows, operating objects, facts,
snapshots, signals, and tasks. Uploading a report grants the uploader default
operating ownership for rows in that report unless ERP/CRM explicitly provides
another owner.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List
from uuid import uuid4

PERMISSION_STAMP_VERSION = "14.5.0"
ERP_OWNER_KEYS = ["ownerUserId", "owner_user_id", "operatorUserId", "operator_user_id", "assignedOperatorId", "assigned_operator_id", "运营ID", "运营账号", "负责人ID", "负责人"]


def _text(value: Any) -> str | None:
    if value in {None, "", "—", "未识别"}:
        return None
    return str(value).strip() or None


def _as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if item not in {None, ""}]
    if isinstance(value, str):
        if value.startswith("[") and value.endswith("]"):
            return [item.strip().strip("'\"") for item in value.strip("[]").split(",") if item.strip()]
        return [value]
    return [str(value)]


def explicit_erp_owner(row: Dict[str, Any]) -> str | None:
    for key in ERP_OWNER_KEYS:
        value = _text(row.get(key))
        if value:
            return value
    return None


def make_permission_stamp(*, uploaded_by_user_id: str | None, uploader_role_id: str | None = None, data_version: str | None = None, source: str | None = None, import_batch_id: str | None = None, row: Dict[str, Any] | None = None) -> Dict[str, Any]:
    row = row or {}
    erp_owner = explicit_erp_owner(row)
    owner = erp_owner or uploaded_by_user_id or "system"
    source_value = "erp_owner" if erp_owner else "report_uploader"
    stamp_id = f"PMS-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:6].upper()}"
    visible = list(dict.fromkeys([item for item in [owner, uploaded_by_user_id, "U001"] if item]))
    return {"version": PERMISSION_STAMP_VERSION, "permissionStampId": stamp_id, "permissionSource": source_value, "uploadedByUserId": uploaded_by_user_id, "uploaderRoleId": uploader_role_id, "ownerUserId": owner, "assignedOperatorId": owner, "visibleUserIds": visible, "visibleRoleIds": ["owner", "manager", "operator"], "dataVersion": data_version, "importBatchId": import_batch_id or data_version, "source": source, "overrideAllowed": True, "rule": "ERP/CRM explicit owner wins; otherwise report uploader is the default operating owner."}


def apply_permission_stamp(row: Dict[str, Any], stamp: Dict[str, Any]) -> Dict[str, Any]:
    next_row = {str(key): value for key, value in (row or {}).items()}
    row_owner = explicit_erp_owner(next_row)
    effective = dict(stamp)
    if row_owner and row_owner != stamp.get("ownerUserId"):
        visible = list(dict.fromkeys([row_owner, stamp.get("uploadedByUserId"), "U001"]))
        effective.update({"permissionSource": "erp_owner", "ownerUserId": row_owner, "assignedOperatorId": row_owner, "visibleUserIds": [item for item in visible if item]})
    next_row["permissionStamp"] = effective
    next_row["permissionStampId"] = effective.get("permissionStampId")
    next_row["permissionSource"] = effective.get("permissionSource")
    next_row["uploadedByUserId"] = effective.get("uploadedByUserId")
    next_row["ownerUserId"] = effective.get("ownerUserId")
    next_row["assignedOperatorId"] = effective.get("assignedOperatorId")
    next_row["visibleUserIds"] = effective.get("visibleUserIds") or []
    next_row["visibleRoleIds"] = effective.get("visibleRoleIds") or []
    next_row["importBatchId"] = effective.get("importBatchId")
    return next_row


def stamp_rows(rows: List[Dict[str, Any]], stamp: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [apply_permission_stamp(row, stamp) for row in rows if isinstance(row, dict)]


def row_permission_stamp(row: Dict[str, Any]) -> Dict[str, Any]:
    stamp = row.get("permissionStamp") if isinstance(row.get("permissionStamp"), dict) else {}
    if stamp:
        return stamp
    return {"permissionStampId": row.get("permissionStampId"), "permissionSource": row.get("permissionSource"), "uploadedByUserId": row.get("uploadedByUserId"), "ownerUserId": row.get("ownerUserId"), "assignedOperatorId": row.get("assignedOperatorId"), "visibleUserIds": _as_list(row.get("visibleUserIds")), "visibleRoleIds": _as_list(row.get("visibleRoleIds")), "importBatchId": row.get("importBatchId")}


def permission_stamp_allows(row: Dict[str, Any], user_id: str | None, role_id: str | None = None) -> bool:
    if not user_id:
        return True
    if role_id in {"owner", "manager", "finance"}:
        return True
    stamp = row_permission_stamp(row)
    allowed = set(_as_list(stamp.get("visibleUserIds")))
    for key in ["uploadedByUserId", "ownerUserId", "assignedOperatorId"]:
        value = stamp.get(key)
        if value:
            allowed.add(str(value))
    return str(user_id) in allowed
