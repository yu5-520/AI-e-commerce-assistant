"""V14.7 full product bundle contract service.

Full product bundle here means one product's complete operating package, not all
products. The station collects the product profile layer, metric layer and
snapshot/trend layer into one Agent input contract. Metric changes, profile
changes and cross-report facts are evidence inside the bundle; they are not
separate task triggers.
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from statistics import mean
from typing import Any, Dict, List

from src.repositories.sqlite_repository import connect, dumps, ensure_columns, loads
from src.services.system_product_snapshot_service import get_product_snapshot, materialize_system_product_snapshot, product_snapshot_history

PRODUCT_SIGNAL_SNAPSHOT_VERSION = "14.7.0"
COMPARE_FIELDS = {
    "inventory": "product_inventory_changed",
    "paymentAmount": "product_payment_changed",
    "grossMargin": "product_margin_changed",
    "roas": "product_roas_changed",
    "roi": "product_roi_changed",
    "clickRate": "product_click_changed",
    "conversionRate": "product_conversion_changed",
    "refundRate": "product_refund_changed",
    "adSpend": "product_ad_spend_changed",
    "organicVisitors": "product_organic_changed",
    "paidVisitors": "product_paid_changed",
}
WINDOWS = {"previous": 1, "7d": 7, "30d": 30, "90d": 90}


def now_iso() -> str:
    return datetime.now().isoformat()


def ensure_product_signal_tables() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS product_signal_snapshots_v14 (
                signal_snapshot_id TEXT PRIMARY KEY,
                data_version TEXT,
                product_snapshot_id TEXT,
                previous_snapshot_id TEXT,
                signal_count INTEGER DEFAULT 0,
                payload TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        ensure_columns(conn, "product_signal_snapshots_v14", {"data_version": "TEXT", "product_snapshot_id": "TEXT", "previous_snapshot_id": "TEXT", "signal_count": "INTEGER DEFAULT 0", "updated_at": "TEXT"})
        conn.execute("CREATE INDEX IF NOT EXISTS idx_product_signal_snapshot_v14_version ON product_signal_snapshots_v14(data_version, created_at)")
        conn.commit()


def signal_snapshot_id_for(data_version: str | None) -> str:
    return f"PRODUCT-SIGNAL-SNAPSHOT-{data_version or 'latest'}"


def _text(value: Any) -> str:
    return str(value or "").strip()


def _num(value: Any) -> float | None:
    if value in {None, "", "—", "未识别"}:
        return None
    try:
        return float(str(value).replace("¥", "").replace(",", "").replace("%", "").strip())
    except Exception:
        return None


def _change(old: Any, new: Any) -> float | None:
    old_num = _num(old)
    new_num = _num(new)
    if old_num is None or new_num is None or abs(old_num) < 1e-9:
        return None
    return (new_num - old_num) / abs(old_num)


def _hash(seed: str, size: int = 14) -> str:
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:size].upper()


def _signal_id(seed: str) -> str:
    return "PSIG-" + _hash(seed)


def _bundle_id(seed: str) -> str:
    return "FPB-" + _hash(seed, 16)


def _index_products(snapshot: Dict[str, Any] | None) -> Dict[str, Dict[str, Any]]:
    products = (snapshot or {}).get("products") or []
    return {str(item.get("objectId") or f"{item.get('storeId') or 'GLOBAL'}::{item.get('productId')}"): item for item in products if item.get("productId") or item.get("objectId")}


def _metric(item: Dict[str, Any] | None, field: str) -> Any:
    if not item:
        return None
    metric = item.get("metricSnapshot") if isinstance(item.get("metricSnapshot"), dict) else {}
    if field == "roas" and metric.get("roas") in {None, "", "—", "未识别"}:
        return metric.get("roi") or item.get("roi")
    return metric.get(field) if field in metric else item.get(field)


def _history_values(history: List[Dict[str, Any]], key: str, field: str, limit: int) -> List[float]:
    values: List[float] = []
    for snapshot in history[:limit]:
        item = _index_products(snapshot).get(key)
        value = _num(_metric(item, field))
        if value is not None:
            values.append(value)
    return values


def _trend_windows(key: str, item: Dict[str, Any], history: List[Dict[str, Any]]) -> Dict[str, Any]:
    trend: Dict[str, Any] = {"historyWindowCount": len(history), "windows": {}}
    for field in COMPARE_FIELDS:
        latest = _num(_metric(item, field))
        metric_windows: Dict[str, Any] = {"latest": latest}
        for name, size in WINDOWS.items():
            values = _history_values(history, key, field, size)
            avg_value = mean(values) if values else None
            metric_windows[name] = {"avg": avg_value, "count": len(values), "changeVsAvg": _change(avg_value, latest) if avg_value is not None else None}
        trend["windows"][field] = metric_windows
    return trend


def _strength(field: str, latest: Any, previous: Any, trend_windows: Dict[str, Any]) -> str:
    latest_num = _num(latest)
    previous_change = _change(previous, latest)
    if field == "inventory" and latest_num is not None and latest_num <= 0:
        return "high"
    if field == "refundRate" and latest_num is not None and latest_num >= 12:
        return "high"
    windows = ((trend_windows.get("windows") or {}).get(field) or {})
    changes = [previous_change]
    for item in windows.values():
        if isinstance(item, dict):
            changes.append(item.get("changeVsAvg"))
    if any(value is not None and abs(float(value)) >= 0.25 for value in changes):
        return "medium"
    if any(value is not None and abs(float(value)) >= 0.08 for value in changes):
        return "low"
    if _text(latest) != _text(previous):
        return "low"
    return "normal"


def _field_signal(field: str, item: Dict[str, Any], old: Dict[str, Any] | None, trend_windows: Dict[str, Any]) -> Dict[str, Any]:
    latest = _metric(item, field)
    previous = _metric(old, field) if old else None
    strength = _strength(field, latest, previous, trend_windows)
    windows = ((trend_windows.get("windows") or {}).get(field) or {})
    evidence = {
        "metricCode": field,
        "signalType": COMPARE_FIELDS[field],
        "signalStrength": strength,
        "latest": _num(latest),
        "previous": _num(previous),
        "changeVsPrevious": _change(previous, latest),
        "windows": windows,
    }
    return evidence


def _source_versions(item: Dict[str, Any], history_items: List[Dict[str, Any]]) -> List[str]:
    versions: List[str] = []
    for candidate in [item, *history_items]:
        metric = candidate.get("metricSnapshot") if isinstance(candidate.get("metricSnapshot"), dict) else {}
        for value in [*(candidate.get("sourceDataVersions") or []), *(metric.get("sourceDataVersions") or [])]:
            if value:
                versions.append(str(value))
    return list(dict.fromkeys(versions))


def _cross_validation(item: Dict[str, Any], history_items: List[Dict[str, Any]], field_signals: List[Dict[str, Any]]) -> Dict[str, Any]:
    metric = item.get("metricSnapshot") if isinstance(item.get("metricSnapshot"), dict) else {}
    source_versions = _source_versions(item, history_items)
    source_datasets = list(dict.fromkeys(str(value) for value in [*(item.get("sourceDatasets") or []), *(metric.get("sourceDatasets") or [])] if value))
    abnormal = [sig for sig in field_signals if sig.get("signalStrength") in {"high", "medium"}]
    changed = [sig for sig in field_signals if sig.get("signalStrength") in {"high", "medium", "low"}]
    return {
        "sourceDataVersions": source_versions,
        "sourceDatasets": source_datasets,
        "sourceVersionCount": len(source_versions),
        "sourceDatasetCount": len(source_datasets),
        "changedMetricCount": len(changed),
        "abnormalMetricCount": len(abnormal),
        "topAbnormalMetrics": abnormal[:5],
        "rule": "V14.7 cross validation is evidence inside one product bundle, not multiple task triggers.",
    }


def _primary_signal(field_signals: List[Dict[str, Any]], old: Dict[str, Any] | None) -> tuple[str, str, str | None]:
    if not old:
        return "product_newly_seen", "low", "product_snapshot"
    best = ("normal_state", "normal", None)
    rank = {"high": 3, "medium": 2, "low": 1, "normal": 0}
    for signal in field_signals:
        strength = str(signal.get("signalStrength") or "normal")
        if rank.get(strength, 0) > rank.get(best[1], 0):
            best = (str(signal.get("signalType")), strength, str(signal.get("metricCode")))
    return best


def _build_full_product_bundle(data_version: str | None, key: str, item: Dict[str, Any], old: Dict[str, Any] | None, history: List[Dict[str, Any]]) -> Dict[str, Any]:
    history_items = [candidate for snapshot in history for k, candidate in _index_products(snapshot).items() if k == key]
    trend = _trend_windows(key, item, history)
    field_signals = [_field_signal(field, item, old, trend) for field in COMPARE_FIELDS]
    signal_type, strength, metric_code = _primary_signal(field_signals, old)
    profile = item.get("profileSnapshot") if isinstance(item.get("profileSnapshot"), dict) else {}
    metric = item.get("metricSnapshot") if isinstance(item.get("metricSnapshot"), dict) else {}
    cross_validation = _cross_validation(item, history_items, field_signals)
    source_versions = cross_validation.get("sourceDataVersions") or []
    digest_seed = dumps({"key": key, "metric": metric, "sources": source_versions, "fieldSignals": field_signals[:5]})
    bundle_seed = f"full_product_bundle|{key}|{_hash(digest_seed, 16)}"
    bundle_id = _bundle_id(bundle_seed)
    signal_id = _signal_id(bundle_seed)
    evidence_refs = [{"type": "metric_signal", "metricCode": sig.get("metricCode"), "signalStrength": sig.get("signalStrength"), "signalType": sig.get("signalType")} for sig in field_signals if sig.get("signalStrength") != "normal"]
    return {
        "signalId": signal_id,
        "packageId": bundle_id.replace("FPB-", "PKG-"),
        "bundleId": bundle_id,
        "version": PRODUCT_SIGNAL_SNAPSHOT_VERSION,
        "dataVersion": data_version,
        "entityType": "product",
        "entityId": item.get("objectId") or key,
        "productId": item.get("productId"),
        "storeId": item.get("storeId"),
        "platform": profile.get("platform") or item.get("platform"),
        "verticalCategory": profile.get("verticalCategory") or item.get("verticalCategory") or "未归类",
        "signalType": "full_product_bundle",
        "primarySignalType": signal_type,
        "signalStrength": strength,
        "metricCode": metric_code or "all_metrics",
        "profileLayer": profile,
        "metricLayer": metric,
        "snapshotLayer": {"trendWindows": trend, "fieldSignals": field_signals, "previousProductMetricSnapshot": old.get("metricSnapshot") if isinstance(old, dict) else None},
        "crossValidation": cross_validation,
        "evidenceRefs": evidence_refs,
        "productProfileSnapshot": profile,
        "productMetricSnapshot": metric,
        "trendWindows": trend,
        "previousProductMetricSnapshot": old.get("metricSnapshot") if isinstance(old, dict) else None,
        "agentProductSnapshotPackage": {
            "contract": "fullProductBundle",
            "bundleId": bundle_id,
            "profileLayer": profile,
            "metricLayer": metric,
            "snapshotLayer": {"trendWindows": trend, "fieldSignals": field_signals},
            "crossValidation": cross_validation,
            "signalSummary": {"signalType": "full_product_bundle", "primarySignalType": signal_type, "signalStrength": strength, "metricCode": metric_code or "all_metrics"},
            "ragRequest": {"verticalCategory": profile.get("verticalCategory") or "未归类", "platform": profile.get("platform"), "taskValueLayer": "volatility_boundary_soft_routing"},
        },
        "status": "pending_agent_judgment",
        "rule": "V14.7 fullProductBundle: profile/data/snapshot layers are collected into one product Agent input. Signals are evidence, not task entry points.",
    }


def _build_signal_packages(current: Dict[str, Any], history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    data_version = current.get("dataVersion")
    current_products = _index_products(current)
    previous_products = _index_products(history[0] if history else None)
    packages: List[Dict[str, Any]] = []
    for key, item in current_products.items():
        packages.append(_build_full_product_bundle(data_version, key, item, previous_products.get(key), history))
    for key, old in previous_products.items():
        if key in current_products:
            continue
        profile = old.get("profileSnapshot") if isinstance(old.get("profileSnapshot"), dict) else {}
        bundle_seed = f"full_product_bundle|missing|{key}|{data_version or 'latest'}"
        signal_id = _signal_id(bundle_seed)
        bundle_id = _bundle_id(bundle_seed)
        packages.append({"signalId": signal_id, "packageId": bundle_id.replace("FPB-", "PKG-"), "bundleId": bundle_id, "version": PRODUCT_SIGNAL_SNAPSHOT_VERSION, "dataVersion": data_version, "entityType": "product", "entityId": old.get("objectId") or key, "productId": old.get("productId"), "storeId": old.get("storeId"), "platform": profile.get("platform"), "verticalCategory": profile.get("verticalCategory") or "未归类", "signalType": "full_product_bundle", "primarySignalType": "product_missing_from_latest", "signalStrength": "medium", "metricCode": "product_presence", "profileLayer": profile, "metricLayer": {}, "snapshotLayer": {"trendWindows": {"historyWindowCount": len(history), "windows": {}}}, "crossValidation": {"sourceDataVersions": [], "sourceDatasetCount": 0, "changedMetricCount": 1}, "evidenceRefs": [{"type": "product_presence", "signalType": "product_missing_from_latest"}], "productProfileSnapshot": profile, "productMetricSnapshot": None, "previousProductMetricSnapshot": old.get("metricSnapshot"), "trendWindows": {"historyWindowCount": len(history), "windows": {}}, "agentProductSnapshotPackage": {"contract": "fullProductBundle", "bundleId": bundle_id, "profileLayer": profile, "metricLayer": {}, "snapshotLayer": {}, "crossValidation": {}, "signalSummary": {"signalType": "full_product_bundle", "primarySignalType": "product_missing_from_latest", "signalStrength": "medium"}}, "status": "pending_agent_judgment", "rule": "V14.7 missing product is one bundle-level evidence item, not a metric task trigger."})
    return packages


def row_to_signal_snapshot(row: Any) -> Dict[str, Any]:
    payload = loads(row["payload"])
    return {**payload, "signalSnapshotId": row["signal_snapshot_id"], "dataVersion": row["data_version"], "productSnapshotId": row["product_snapshot_id"], "previousSnapshotId": row["previous_snapshot_id"], "signalCount": int(row["signal_count"] or 0), "createdAt": row["created_at"], "updatedAt": row["updated_at"]}


def get_product_signal_snapshot(data_version: str | None = None) -> Dict[str, Any] | None:
    ensure_product_signal_tables()
    with connect() as conn:
        if data_version:
            row = conn.execute("SELECT * FROM product_signal_snapshots_v14 WHERE data_version = ? ORDER BY created_at DESC LIMIT 1", (data_version,)).fetchone()
        else:
            row = conn.execute("SELECT * FROM product_signal_snapshots_v14 ORDER BY created_at DESC LIMIT 1").fetchone()
    return row_to_signal_snapshot(row) if row else None


def materialize_product_signal_snapshot(data_version: str | None = None, *, user_id: str | None = None, force: bool = True) -> Dict[str, Any]:
    ensure_product_signal_tables()
    current = get_product_snapshot(data_version) or materialize_system_product_snapshot(data_version=data_version, user_id=user_id, force=force)
    history = product_snapshot_history(data_version, limit=90)
    previous = history[0] if history else None
    packages = _build_signal_packages(current, history)
    snapshot_id = signal_snapshot_id_for(data_version)
    payload = {"version": PRODUCT_SIGNAL_SNAPSHOT_VERSION, "signalSnapshotId": snapshot_id, "dataVersion": data_version, "stationId": "product_signal_snapshot_station", "contract": "fullProductBundle", "productSnapshotId": current.get("snapshotId"), "previousSnapshotId": previous.get("snapshotId") if previous else None, "productSnapshotCount": current.get("productCount") or len(current.get("products") or []), "productSignalPackageCount": len(packages), "productSignalCount": len(packages), "signals": packages, "productSignalPackages": packages, "windowPolicy": {"historyLimit": 90, "windows": WINDOWS}, "rule": "V14.7 product signal snapshot outputs one fullProductBundle per product. Profile/data/snapshot layers are bundled before Agent judgment."}
    now = now_iso()
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO product_signal_snapshots_v14 (signal_snapshot_id, data_version, product_snapshot_id, previous_snapshot_id, signal_count, payload, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM product_signal_snapshots_v14 WHERE signal_snapshot_id = ?), ?), ?)
            """,
            (snapshot_id, data_version, payload["productSnapshotId"], payload["previousSnapshotId"], len(packages), dumps(payload), snapshot_id, now, now),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM product_signal_snapshots_v14 WHERE signal_snapshot_id = ?", (snapshot_id,)).fetchone()
    return {**row_to_signal_snapshot(row), "outputRef": f"product_signal_snapshot:{snapshot_id}", "productSignalSnapshotRef": f"product_signal_snapshot:{snapshot_id}"}


def product_signal_snapshot_summary(limit: int = 20) -> Dict[str, Any]:
    ensure_product_signal_tables()
    with connect() as conn:
        rows = conn.execute("SELECT * FROM product_signal_snapshots_v14 ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    items = [row_to_signal_snapshot(row) for row in rows]
    return {"version": PRODUCT_SIGNAL_SNAPSHOT_VERSION, "snapshotCount": len(items), "latest": items[0] if items else None, "items": items}
