from __future__ import annotations

from collections import Counter, defaultdict
from typing import Dict, List

from src.data_loader.load_mock_data import to_int, to_number

HOME_KEYWORDS = ["家居", "日用", "收纳", "厨房", "坐垫", "遮阳伞", "办公室", "护腰"]
SUN_PROTECTION_KEYWORDS = ["防晒", "遮阳", "冰袖", "防晒衣", "防晒口罩", "太阳伞"]
APPAREL_KEYWORDS = ["衣", "服", "裤", "裙", "外套", "女装", "男装"]


def infer_operating_unit(
    products: List[Dict[str, object]],
    orders: List[Dict[str, object]] | None = None,
    inventory: List[Dict[str, object]] | None = None,
) -> Dict[str, object]:
    """Infer the merchant's operating unit from ERP product structure.

    The operating unit is intentionally based on ERP data, not on a hardcoded
    category profile. A profile like `sun_protection_clothing` can still be used
    as a demo, but it should not be the default product logic.
    """
    orders = orders or []
    inventory = inventory or []
    category_counter = Counter(str(item.get("category", "unknown")) for item in products)
    keyword_counter = Counter()
    product_group_counter = Counter()
    product_ids_by_group: Dict[str, List[str]] = defaultdict(list)

    for product in products:
        product_id = str(product.get("product_id", ""))
        text = f"{product.get('product_name', '')} {product.get('category', '')} {product.get('main_selling_points', '')}"
        group = _infer_product_group(text)
        product_group_counter[group] += 1
        product_ids_by_group[group].append(product_id)
        for keyword in HOME_KEYWORDS + SUN_PROTECTION_KEYWORDS + APPAREL_KEYWORDS:
            if keyword in text:
                keyword_counter[keyword] += 1

    order_amount_by_product = _sum_order_amount_by_product(orders)
    stock_by_product = _sum_stock_by_product(inventory, products)
    dominant_group = product_group_counter.most_common(1)[0][0] if product_group_counter else "unknown"

    category_profile_id = _choose_profile_id(category_counter, keyword_counter, dominant_group)
    unit_name = _unit_name_for_profile(category_profile_id)
    cycle_suggestion = _suggest_cycle_type(category_profile_id, products, stock_by_product)

    return {
        "operating_unit_id": category_profile_id,
        "unit_name": unit_name,
        "base_source": "ERP product data",
        "category_profile_id": category_profile_id,
        "dominant_platform_categories": dict(category_counter),
        "dominant_product_group": dominant_group,
        "product_group_summary": dict(product_group_counter),
        "product_ids_by_group": dict(product_ids_by_group),
        "keyword_signals": dict(keyword_counter),
        "order_amount_by_product": order_amount_by_product,
        "stock_by_product": stock_by_product,
        "cycle_suggestion": cycle_suggestion,
        "reason": _build_reason(category_profile_id, category_counter, keyword_counter, dominant_group),
    }


def _infer_product_group(text: str) -> str:
    if any(keyword in text for keyword in ["遮阳伞", "防晒", "遮阳"]):
        return "sun_protection_goods"
    if any(keyword in text for keyword in ["置物架", "收纳", "厨房"]):
        return "home_storage_goods"
    if any(keyword in text for keyword in ["护腰", "坐垫", "久坐"]):
        return "health_home_goods"
    if any(keyword in text for keyword in APPAREL_KEYWORDS):
        return "apparel_goods"
    if any(keyword in text for keyword in HOME_KEYWORDS):
        return "home_living_goods"
    return "general_goods"


def _choose_profile_id(category_counter: Counter[str], keyword_counter: Counter[str], dominant_group: str) -> str:
    category_text = " ".join(category_counter.keys())
    home_score = sum(keyword_counter.get(keyword, 0) for keyword in HOME_KEYWORDS) + category_text.count("家居") * 2
    sun_score = sum(keyword_counter.get(keyword, 0) for keyword in SUN_PROTECTION_KEYWORDS)
    apparel_score = sum(keyword_counter.get(keyword, 0) for keyword in APPAREL_KEYWORDS)

    if home_score >= max(sun_score, apparel_score, 1):
        return "home_living_goods"
    if sun_score >= max(apparel_score, 1):
        return "sun_protection_clothing"
    if dominant_group == "apparel_goods" or apparel_score > 0:
        return "apparel_goods"
    return "home_living_goods"


def _unit_name_for_profile(profile_id: str) -> str:
    names = {
        "home_living_goods": "家居生活商品",
        "sun_protection_clothing": "防晒服 / 防晒商品样板",
        "apparel_goods": "服饰商品",
    }
    return names.get(profile_id, "通用经营单元")


def _suggest_cycle_type(
    profile_id: str,
    products: List[Dict[str, object]],
    stock_by_product: Dict[str, int],
) -> str:
    total_stock = sum(stock_by_product.values())
    average_price = 0
    if products:
        average_price = sum(to_number(item.get("sale_price")) for item in products) / len(products)

    if profile_id in {"home_living_goods", "sun_protection_clothing"} and average_price < 100 and total_stock >= 200:
        return "daily_fast_moving_goods_loop"
    if average_price >= 500:
        return "weekly_bulk_goods_review_loop"
    return "weekly_operation_review_loop"


def _first_number(item: Dict[str, object], keys: List[str]) -> float:
    for key in keys:
        value = to_number(item.get(key))
        if value:
            return value
    return 0


def _first_int(item: Dict[str, object], keys: List[str]) -> int:
    for key in keys:
        value = to_int(item.get(key))
        if value:
            return value
    return 0


def _sum_order_amount_by_product(orders: List[Dict[str, object]]) -> Dict[str, float]:
    result: Dict[str, float] = defaultdict(float)
    for order in orders:
        result[str(order.get("product_id"))] += _first_number(order, ["actual_paid", "order_amount", "pay_amount"])
    return {key: round(value, 2) for key, value in result.items()}


def _sum_stock_by_product(inventory: List[Dict[str, object]], products: List[Dict[str, object]]) -> Dict[str, int]:
    result: Dict[str, int] = defaultdict(int)
    for item in inventory:
        result[str(item.get("product_id"))] += _first_int(item, ["available_stock", "current_stock", "stock"])
    if not any(result.values()):
        result.clear()
        for product in products:
            result[str(product.get("product_id"))] += to_int(product.get("stock"))
    return dict(result)


def _build_reason(
    profile_id: str,
    category_counter: Counter[str],
    keyword_counter: Counter[str],
    dominant_group: str,
) -> str:
    top_categories = "、".join(category for category, _count in category_counter.most_common(3))
    top_keywords = "、".join(keyword for keyword, _count in keyword_counter.most_common(5)) or "无明显关键词"
    return (
        f"根据 ERP 商品类目分布（{top_categories}）、商品关键词（{top_keywords}）"
        f"和商品群信号（{dominant_group}），推断当前经营单元为 {profile_id}。"
    )
