"""V11 MVP governance layer.

This layer separates analysis results from executable tasks:
- product identity is decided per product runtime id, not per report upload count;
- first-seen products only get baseline checks and tags unless a hard baseline is broken;
- low/medium priority alerts are persisted as product/store tags and observation signals;
- only high-risk and time-sensitive alerts are allowed into the front-end task queue;
- store metrics are aggregated from imported product rows and converted into store weight tags.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4

from src.repositories.sqlite_repository import connect, dumps, loads

V11_MVP_VERSION = "11.0.0"
PRODUCT_ID_FIELDS = ("product_id", "商品ID", "商品id", "商品编码", "sku", "SKU", "SKU ID", "sku_id")
STORE_ID_FIELDS = ("store_id", "storeId", "店铺ID", "店铺id", "店铺编号")
STORE_NAME_FIELDS = ("store_name", "store", "店铺", "店铺名称", "店铺名")
PLATFORM_FIELDS = ("platform", "平台", "渠道", "来源平台")
STAT_DATE_FIELDS = ("stat_date", "统计日期", "日期", "date", "biz_date")
REVENUE_FIELDS = ("revenue", "actual_paid", "payment_amount", "支付金额", "销售额", "GMV", "成交金额")
SALES_VOLUME_FIELDS = ("sales_volume", "quantity", "paid_units", "支付件数", "销量", "销售件数", "成交件数")
AD_SPEND_FIELDS = ("ad_spend", "广告消耗", "投放消耗", "推广花费", "广告花费")
ROI_FIELDS = ("roi", "ROI", "投产", "投产比", "投入产出比")
REFUND_AMOUNT_FIELDS = ("refund_amount", "退款金额", "退款额", "售后金额")
REFUND_RATE_FIELDS = ("refund_rate", "退款率", "售后率", "退货率")
VISITOR_FIELDS = ("traffic", "visitors", "访客数", "自然流量访客数", "付费流量访客数")
GROSS_MARGIN_FIELDS = ("gross_margin", "毛利率", "利润率")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}".upper()


def _pick(row: Dict[str, Any], *fields: str, default: Any = None) -> Any:
    for field in fields:
        if row.get(field) not in {None, ""}:
            return row.get(field)
    return default


def _as_float(value: Any, default: float = 0.0) -> float:
    if value in {None, ""}:
        return default
    text = str(value).replace(",", "").replace("¥", "").strip()
    percent = text.endswith("%")
    text = text[:-1] if percent else text
    try:
        number = float(text)
    except (TypeError, ValueError):
        return default
    return number / 100 if percent else number


def _clean(value: Any) -> str:
    return str(value or "").strip()


def product_runtime_id(row: Dict[str, Any]) -> str | None:
    product_id = _clean(_pick(row, *PRODUCT_ID_FIELDS))
    if not product_id:
        return None
    store_id = _clean(_pick(row, *STORE_ID_FIELDS)) or "NO_STORE"
    platform = _clean(_pick(row, *PLATFORM_FIELDS)) or "NO_PLATFORM"
    sku_id = _clean(_pick(row, "sku_id", "SKU ID", "SKU", "sku", default=product_id)) or product_id
    return "PRD::" + "::".join([platform, store_id, product_id, sku_id])


def _store_key(row: Dict[str, Any]) -> str:
    platform = _clean(_pick(row, *PLATFORM_FIELDS)) or "NO_PLATFORM"
    store_id = _clean(_pick(row, *STORE_ID_FIELDS))
    store_name = _clean(_pick(row, *STORE_NAME_FIELDS))
    return f"{platform}::{store_id or store_name or 'NO_STORE'}"


def _stat_date(row: Dict[str, Any], data_version: str) -> str:
    return _clean(_pick(row, *STAT_DATE_FIELDS)) or data_version


def ensure_v11_tables() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS product_runtime_profiles_v11 (
                runtime_id TEXT PRIMARY KEY,
                product_id TEXT NOT NULL,
                sku_id TEXT,
                store_id TEXT,
                store_name TEXT,
                platform TEXT,
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                payload TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS product_metric_snapshots_v11 (
                snapshot_id TEXT PRIMARY KEY,
                runtime_id TEXT NOT NULL,
                product_id TEXT NOT NULL,
                store_id TEXT,
                stat_date TEXT NOT NULL,
                data_version TEXT NOT NULL,
                dataset_name TEXT NOT NULL,
                payload TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS product_tags_v11 (
                tag_id TEXT PRIMARY KEY,
                runtime_id TEXT NOT NULL,
                product_id TEXT NOT NULL,
                store_id TEXT,
                tag_type TEXT NOT NULL,
                tag_label TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                payload TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS store_weight_profiles_v11 (
                store_key TEXT PRIMARY KEY,
                store_id TEXT,
                store_name TEXT,
                platform TEXT,
                weight_level TEXT NOT NULL,
                weight_score REAL NOT NULL,
                payload TEXT,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS store_tags_v11 (
                tag_id TEXT PRIMARY KEY,
                store_key TEXT NOT NULL,
                store_id TEXT,
                tag_label TEXT NOT NULL,
                weight_level TEXT NOT NULL,
                payload TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_product_snapshots_v11 ON product_metric_snapshots_v11(runtime_id, stat_date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_product_tags_v11 ON product_tags_v11(runtime_id, created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_store_tags_v11 ON store_tags_v11(store_key, created_at)")
        conn.commit()


def _prior_period_count(runtime_id: str, stat_date: str) -> int:
    ensure_v11_tables()
    with connect() as conn:
        row = conn.execute(
            "SELECT COUNT(DISTINCT stat_date) AS c FROM product_metric_snapshots_v11 WHERE runtime_id = ? AND stat_date <> ?",
            (runtime_id, stat_date),
        ).fetchone()
    return int(row["c"] or 0) if row else 0


def _analysis_stage(prior_periods: int) -> str:
    if prior_periods <= 0:
        return "new_product"
    if prior_periods == 1:
        return "compare_ready"
    if prior_periods < 6:
        return "trend_ready"
    return "stable_trend"


def _product_tags(row: Dict[str, Any], stage: str) -> List[Dict[str, Any]]:
    tags: List[Dict[str, Any]] = []
    if stage == "new_product":
        tags.append({"tagType": "lifecycle", "tagLabel": "新入库商品", "riskLevel": "低"})
        tags.append({"tagType": "data_depth", "tagLabel": "待建立趋势线", "riskLevel": "低"})
    roi = _as_float(_pick(row, *ROI_FIELDS), 0.0)
    refund_rate = _as_float(_pick(row, *REFUND_RATE_FIELDS), 0.0)
    revenue = _as_float(_pick(row, *REVENUE_FIELDS), 0.0)
    ad_spend = _as_float(_pick(row, *AD_SPEND_FIELDS), 0.0)
    if roi and roi < 1.2:
        tags.append({"tagType": "baseline", "tagLabel": "ROI低于基线", "riskLevel": "中" if roi >= 0.8 else "高"})
    if refund_rate and refund_rate > 0.08:
        tags.append({"tagType": "baseline", "tagLabel": "退款率高于基线", "riskLevel": "中" if refund_rate <= 0.15 else "高"})
    if ad_spend > 0 and revenue / ad_spend < 1.0:
        tags.append({"tagType": "baseline", "tagLabel": "投放产出低于基线", "riskLevel": "高"})
    return tags


def _save_product_profile(row: Dict[str, Any], runtime_id: str, data_version: str, dataset_name: str) -> Dict[str, Any]:
    created_at = now_iso()
    stat_date = _stat_date(row, data_version)
    product_id = _clean(_pick(row, *PRODUCT_ID_FIELDS))
    sku_id = _clean(_pick(row, "sku_id", "SKU ID", "SKU", "sku", default=product_id))
    store_id = _clean(_pick(row, *STORE_ID_FIELDS)) or None
    store_name = _clean(_pick(row, *STORE_NAME_FIELDS)) or None
    platform = _clean(_pick(row, *PLATFORM_FIELDS)) or None
    prior_periods = _prior_period_count(runtime_id, stat_date)
    stage = _analysis_stage(prior_periods)
    payload = {
        "version": V11_MVP_VERSION,
        "runtimeId": runtime_id,
        "productId": product_id,
        "skuId": sku_id,
        "storeId": store_id,
        "storeName": store_name,
        "platform": platform,
        "statDate": stat_date,
        "priorPeriodCount": prior_periods,
        "historyDepth": prior_periods + 1,
        "analysisStage": stage,
        "rule": "按商品入库ID和历史周期数分流；不是按报表上传次数分流。",
    }
    with connect() as conn:
        existing = conn.execute("SELECT * FROM product_runtime_profiles_v11 WHERE runtime_id = ?", (runtime_id,)).fetchone()
        first_seen = loads(existing["payload"]).get("firstSeenAt") if existing else created_at
        payload["firstSeenAt"] = first_seen
        payload["lastSeenAt"] = created_at
        conn.execute(
            "INSERT OR REPLACE INTO product_runtime_profiles_v11 (runtime_id, product_id, sku_id, store_id, store_name, platform, first_seen_at, last_seen_at, payload) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (runtime_id, product_id, sku_id, store_id, store_name, platform, first_seen, created_at, dumps(payload)),
        )
        conn.execute(
            "INSERT OR REPLACE INTO product_metric_snapshots_v11 (snapshot_id, runtime_id, product_id, store_id, stat_date, data_version, dataset_name, payload, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (make_id("PSNAP"), runtime_id, product_id, store_id, stat_date, data_version, dataset_name, dumps({"row": row, "profile": payload}), created_at),
        )
        for tag in _product_tags(row, stage):
            tag_payload = {**tag, "runtimeId": runtime_id, "productId": product_id, "storeId": store_id, "dataVersion": data_version, "analysisStage": stage}
            conn.execute(
                "INSERT OR REPLACE INTO product_tags_v11 (tag_id, runtime_id, product_id, store_id, tag_type, tag_label, risk_level, payload, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (make_id("PTAG"), runtime_id, product_id, store_id, tag["tagType"], tag["tagLabel"], tag["riskLevel"], dumps(tag_payload), created_at),
            )
        conn.commit()
    payload["tags"] = _product_tags(row, stage)
    return payload


def _store_weight_level(score: float) -> str:
    if score >= 80:
        return "高权重店铺"
    if score >= 50:
        return "中权重店铺"
    return "测试/低权重店铺"


def _aggregate_store_tags(rows: List[Dict[str, Any]], data_version: str) -> Dict[str, Any]:
    stores: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"rows": 0, "revenue": 0.0, "salesVolume": 0.0, "adSpend": 0.0, "refundAmount": 0.0, "visitors": 0.0, "roiSamples": [], "storeId": None, "storeName": None, "platform": None})
    for row in rows:
        key = _store_key(row)
        stat = stores[key]
        stat["rows"] += 1
        stat["revenue"] += _as_float(_pick(row, *REVENUE_FIELDS), 0.0)
        stat["salesVolume"] += _as_float(_pick(row, *SALES_VOLUME_FIELDS), 0.0)
        stat["adSpend"] += _as_float(_pick(row, *AD_SPEND_FIELDS), 0.0)
        stat["refundAmount"] += _as_float(_pick(row, *REFUND_AMOUNT_FIELDS), 0.0)
        stat["visitors"] += _as_float(_pick(row, *VISITOR_FIELDS), 0.0)
        roi = _as_float(_pick(row, *ROI_FIELDS), 0.0)
        if roi:
            stat["roiSamples"].append(roi)
        stat["storeId"] = stat["storeId"] or _clean(_pick(row, *STORE_ID_FIELDS)) or None
        stat["storeName"] = stat["storeName"] or _clean(_pick(row, *STORE_NAME_FIELDS)) or None
        stat["platform"] = stat["platform"] or _clean(_pick(row, *PLATFORM_FIELDS)) or None
    created_at = now_iso()
    profiles: Dict[str, Any] = {}
    with connect() as conn:
        for key, stat in stores.items():
            roi = stat["revenue"] / stat["adSpend"] if stat["adSpend"] else (sum(stat["roiSamples"]) / len(stat["roiSamples"]) if stat["roiSamples"] else 0.0)
            refund_rate = stat["refundAmount"] / stat["revenue"] if stat["revenue"] else 0.0
            score = min(100.0, stat["revenue"] / 100 + roi * 15 + stat["visitors"] / 200 - refund_rate * 100)
            level = _store_weight_level(score)
            tags = [level]
            if stat["revenue"] >= 5000:
                tags.append("高销售额店铺")
            if roi >= 2.0:
                tags.append("高ROI店铺")
            if stat["adSpend"] and stat["revenue"]:
                tags.append("高投放依赖店铺" if stat["adSpend"] / max(stat["revenue"], 1) > 0.25 else "投放承接正常")
            if refund_rate >= 0.08:
                tags.append("退款风险店铺")
            payload = {"version": V11_MVP_VERSION, "storeKey": key, "dataVersion": data_version, "weightScore": round(score, 2), "weightLevel": level, "metrics": {"revenue": round(stat["revenue"], 2), "salesVolume": stat["salesVolume"], "adSpend": round(stat["adSpend"], 2), "roi": round(roi, 2), "refundRate": round(refund_rate, 4), "productRowCount": stat["rows"]}, "tags": tags, "rule": "店铺权重由报表商品聚合生成，反向影响商品任务强度。"}
            conn.execute(
                "INSERT OR REPLACE INTO store_weight_profiles_v11 (store_key, store_id, store_name, platform, weight_level, weight_score, payload, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (key, stat["storeId"], stat["storeName"], stat["platform"], level, score, dumps(payload), created_at),
            )
            for label in tags:
                conn.execute(
                    "INSERT OR REPLACE INTO store_tags_v11 (tag_id, store_key, store_id, tag_label, weight_level, payload, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (make_id("STAG"), key, stat["storeId"], label, level, dumps({**payload, "tagLabel": label}), created_at),
                )
            profiles[key] = payload
        conn.commit()
    return profiles


def process_report_import(dataset_name: str, rows: List[Dict[str, Any]], data_version: str) -> Dict[str, Any]:
    ensure_v11_tables()
    product_profiles: Dict[str, Any] = {}
    by_product_id: Dict[str, Any] = {}
    valid_rows: List[Dict[str, Any]] = []
    for row in rows:
        runtime_id = product_runtime_id(row)
        if not runtime_id:
            continue
        valid_rows.append(row)
        profile = _save_product_profile(row, runtime_id, data_version, dataset_name)
        product_profiles[runtime_id] = profile
        by_product_id[str(profile.get("productId"))] = profile
    store_profiles = _aggregate_store_tags(valid_rows, data_version)
    new_count = len([item for item in product_profiles.values() if item.get("analysisStage") == "new_product"])
    return {
        "version": V11_MVP_VERSION,
        "mode": "mvp_governance",
        "dataVersion": data_version,
        "datasetName": dataset_name,
        "productCount": len(product_profiles),
        "newProductCount": new_count,
        "existingProductCount": max(len(product_profiles) - new_count, 0),
        "storeCount": len(store_profiles),
        "productProfiles": product_profiles,
        "productProfilesByProductId": by_product_id,
        "storeProfiles": store_profiles,
        "rule": "报表是批次，商品入库ID才是分析主体；低风险沉淀为标签，高风险高时效才进入任务队列。",
    }


def decide_alert_task_policy(alert: Dict[str, Any], governance: Dict[str, Any]) -> Dict[str, Any]:
    product = (governance.get("productProfilesByProductId") or {}).get(str(alert.get("entityId"))) or {}
    stage = product.get("analysisStage") or "unknown"
    priority = alert.get("priority") or "低"
    risk_domain = alert.get("riskDomain") or "通用"
    baseline_hard = priority == "高" and risk_domain in {"库存", "价格", "利润", "流量"}
    create_task = priority == "高" and (stage != "new_product" or baseline_hard)
    if priority in {"低", "中"}:
        create_task = False
    alert_status = "new" if create_task else "tagged_only" if priority == "低" else "observation_tagged"
    queue_type = "urgent_execution" if create_task and priority == "高" else "store_product_tag"
    return {
        "version": V11_MVP_VERSION,
        "createTask": create_task,
        "alertStatus": alert_status,
        "queueType": queue_type,
        "analysisStage": stage,
        "productHistoryDepth": product.get("historyDepth"),
        "rule": "中低风险不进入前端任务栏，沉淀为商品/店铺标签；新商品只允许强基线异常生成任务。",
    }


def apply_alert_policy(alert: Dict[str, Any], governance: Dict[str, Any]) -> Dict[str, Any]:
    policy = decide_alert_task_policy(alert, governance)
    result = dict(alert)
    result["v11MvpPolicy"] = policy
    result["status"] = policy["alertStatus"]
    result.setdefault("judgmentTags", [])
    result["taskQueueType"] = policy["queueType"]
    result["productHistoryDepth"] = policy.get("productHistoryDepth")
    result["analysisStage"] = policy.get("analysisStage")
    return result
