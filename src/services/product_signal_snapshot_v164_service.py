"""V16.4 fullProductBundle fact-layer validation wrapper.

The base product_signal_snapshot_service builds the bundle contract. This wrapper
adds the V16.4 acceptance stamp so Agent input can prove that product metrics,
traffic source child facts and report dates survived the import layer.
"""

from __future__ import annotations

from typing import Any, Dict, List

import src.services.product_signal_snapshot_service as base

PRODUCT_SIGNAL_SNAPSHOT_VERSION = "16.4"
_ORIGINAL_BUILD_FULL_PRODUCT_BUNDLE = base._build_full_product_bundle


def _blank(value: Any) -> bool:
    return value in {None, "", "—", "未识别"}


def _fact_layer_validation(item: Dict[str, Any]) -> Dict[str, Any]:
    metric = item.get("metricSnapshot") if isinstance(item.get("metricSnapshot"), dict) else {}
    product_facts = metric.get("productMetricFacts") if isinstance(metric.get("productMetricFacts"), list) else item.get("productMetricFacts") or []
    traffic_facts = metric.get("trafficSourceFacts") if isinstance(metric.get("trafficSourceFacts"), list) else item.get("trafficSourceFacts") or []
    metric_date = metric.get("metricDate") or item.get("metricDate") or metric.get("reportDate") or item.get("reportDate")
    missing = []
    if _blank(metric.get("roi") or item.get("roi")):
        missing.append("product_roi")
    if _blank(metric_date):
        missing.append("metric_date")
    if not product_facts:
        missing.append("product_metric_facts")
    return {
        "version": PRODUCT_SIGNAL_SNAPSHOT_VERSION,
        "status": "passed" if not missing else "attention",
        "missing": missing,
        "metricDate": metric_date,
        "productMetricFactCount": len(product_facts),
        "trafficSourceFactCount": len(traffic_facts),
        "roiSource": "product_metric_facts.roi",
        "trafficRoiPolicy": "traffic_source_facts.roi is child evidence only and cannot overwrite product ROI",
        "rule": "V16.4 fullProductBundle must carry product metric namespace, child traffic facts and report business date before Agent judgment.",
    }


def _build_full_product_bundle_v164(data_version: str | None, key: str, item: Dict[str, Any], old: Dict[str, Any] | None, history: List[Dict[str, Any]]) -> Dict[str, Any]:
    bundle = _ORIGINAL_BUILD_FULL_PRODUCT_BUNDLE(data_version, key, item, old, history)
    validation = _fact_layer_validation(item)
    metric = bundle.get("metricLayer") if isinstance(bundle.get("metricLayer"), dict) else {}
    profile = bundle.get("profileLayer") if isinstance(bundle.get("profileLayer"), dict) else {}
    metric["metricDate"] = metric.get("metricDate") or validation.get("metricDate")
    metric["factLayerValidation"] = validation
    metric.setdefault("productMetricFacts", (item.get("metricSnapshot") or {}).get("productMetricFacts") or item.get("productMetricFacts") or [])
    metric.setdefault("trafficSourceFacts", (item.get("metricSnapshot") or {}).get("trafficSourceFacts") or item.get("trafficSourceFacts") or [])
    profile["metricDate"] = profile.get("metricDate") or validation.get("metricDate")
    bundle["version"] = PRODUCT_SIGNAL_SNAPSHOT_VERSION
    bundle["metricLayer"] = metric
    bundle["profileLayer"] = profile
    bundle["factLayerValidation"] = validation
    bundle["dataFingerprint"] = f"{data_version or 'latest'}::{key}::{validation.get('metricDate') or 'no-date'}::{metric.get('roi') or 'no-roi'}"
    bundle["agentProductSnapshotPackage"]["metricLayer"] = metric
    bundle["agentProductSnapshotPackage"]["profileLayer"] = profile
    bundle["agentProductSnapshotPackage"]["factLayerValidation"] = validation
    bundle["rule"] = "V16.4 fullProductBundle: product-scope metrics, report dates and child traffic facts are validated before Agent judgment."
    return bundle


base.PRODUCT_SIGNAL_SNAPSHOT_VERSION = PRODUCT_SIGNAL_SNAPSHOT_VERSION
base._build_full_product_bundle = _build_full_product_bundle_v164

ensure_product_signal_tables = base.ensure_product_signal_tables
get_product_signal_snapshot = base.get_product_signal_snapshot
materialize_product_signal_snapshot = base.materialize_product_signal_snapshot
product_signal_snapshot_summary = base.product_signal_snapshot_summary
