from __future__ import annotations

import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT / "frontend"
RESULT_DIR = ROOT / "data" / "runtime_results"
FEEDBACK_DIR = ROOT / "data" / "runtime_feedback"

sys.path.insert(0, str(ROOT / "scripts"))
from llm_client import chat, llm_enabled, load_provider  # noqa: E402

MODE_MAP = {
    "自然流": ("natural-flow", "自然流"),
    "natural-flow": ("natural-flow", "自然流"),
    "强付费": ("paid-growth", "强付费"),
    "paid-growth": ("paid-growth", "强付费"),
    "爆品打造": ("hot-product", "爆品打造"),
    "爆品": ("hot-product", "爆品打造"),
    "hot-product": ("hot-product", "爆品打造"),
}

IMAGE_CREDIT_COST = {0: 0, 1: 10, 2: 18, 3: 25, 5: 40}
FREE_LIMITS = {"title_counts": {3, 5}, "image_plan_counts": {1, 2}, "image_generate_counts": {0, 1, 2}}
VIP_LIMITS = {"title_counts": {3, 5, 10, 15}, "image_plan_counts": {1, 2, 3, 5}, "image_generate_counts": {0, 1, 2, 3, 5}}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_dirs() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)


def market_time_context() -> dict:
    now = datetime.now(timezone.utc)
    month = now.month
    if month in (3, 4, 5):
        season = "春季"
    elif month in (6, 7, 8):
        season = "夏季"
    elif month in (9, 10, 11):
        season = "秋季"
    else:
        season = "冬季"
    return {"current_year": now.year, "current_month": month, "current_date": now.date().isoformat(), "season": season}


def remove_stale_years(value: str, current_year: int | None = None) -> str:
    current_year = current_year or market_time_context()["current_year"]

    def replace_year(match: re.Match) -> str:
        year = int(match.group(1))
        return match.group(0) if year >= current_year else ""

    text = re.sub(r"\b(20\d{2})\b年?", replace_year, str(value or ""))
    return re.sub(r"\s+", " ", text).strip()


def clean_client_id(value) -> str:
    text = str(value or "").strip()
    text = re.sub(r"[^a-zA-Z0-9_\-]", "", text)
    return text[:80]


def clean_text_value(value, current_year: int | None = None) -> str:
    text = remove_stale_years(str(value or ""), current_year)
    blocked = ["result_id", "backflow", "llm_status", "deterministic", "fallback", "api", "POST", "debug"]
    for word in blocked:
        text = text.replace(word, "")
    return re.sub(r"\s+", " ", text).strip()


def cleanse_value(value, current_year: int | None = None):
    if isinstance(value, dict):
        return {key: cleanse_value(item, current_year) for key, item in value.items()}
    if isinstance(value, list):
        return [cleanse_value(item, current_year) for item in value]
    if isinstance(value, str):
        return clean_text_value(value, current_year)
    return value


def build_material_pack(raw_material: str, current_year: int) -> dict:
    lines = []
    for line in str(raw_material or "").splitlines():
        cleaned = clean_text_value(line, current_year)
        if cleaned:
            lines.append(cleaned)
        if len(lines) >= 16:
            break
    joined = " ".join(lines)
    terms = []
    banned = {"拼多多", "商品", "标题", "新款", "爆款", "旗舰", "官方", "正品", "包邮", "现货", "2024", "2025"}
    for token in re.findall(r"[\u4e00-\u9fffA-Za-z0-9]{2,}", joined):
        if token in banned or re.fullmatch(r"20\d{2}", token):
            continue
        if token not in terms:
            terms.append(token)
        if len(terms) >= 30:
            break
    return {"samples": lines, "terms": terms}


def read_json_body(handler: SimpleHTTPRequestHandler) -> dict:
    length = int(handler.headers.get("Content-Length", "0") or 0)
    raw = handler.rfile.read(length).decode("utf-8") if length else "{}"
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        obj = {}
    return obj if isinstance(obj, dict) else {}


def send_json(handler: SimpleHTTPRequestHandler, status: int, payload: dict) -> None:
    body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def mode_from_payload(payload: dict) -> tuple[str, str]:
    raw_mode = str(payload.get("mode") or "自然流")
    return MODE_MAP.get(raw_mode, ("natural-flow", "自然流"))


def load_module_context(mode_key: str) -> str:
    chain_path = ROOT / "runtime" / "module_chain.json"
    if not chain_path.exists():
        return ""
    chain = json.loads(chain_path.read_text(encoding="utf-8"))
    conf = chain.get(mode_key) or chain.get("natural-flow") or {}
    chunks = []
    for key in ["platform", "platform_title", "platform_image", "mode", "input_schema", "prompt", "template", "frontend_schema"]:
        rel = conf.get(key)
        if not rel:
            continue
        p = ROOT / rel
        if p.exists():
            chunks.append(p.read_text(encoding="utf-8"))
    return "\n\n".join(chunks)


def number_or_none(value) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def int_from_payload(payload: dict, key: str, default: int) -> int:
    try:
        return int(payload.get(key, default))
    except (TypeError, ValueError):
        return default


def nearest_allowed(value: int, allowed: set[int]) -> int:
    if value in allowed:
        return value
    return max([item for item in allowed if item <= value] or [min(allowed)])


def generation_config_from_payload(payload: dict) -> dict:
    membership = "vip" if str(payload.get("membership") or "free").lower() == "vip" else "free"
    limits = VIP_LIMITS if membership == "vip" else FREE_LIMITS
    requested = {"title_count": int_from_payload(payload, "title_count", 3), "image_plan_count": int_from_payload(payload, "image_plan_count", 1), "image_generate_count": int_from_payload(payload, "image_generate_count", 0)}
    applied = {"title_count": nearest_allowed(requested["title_count"], limits["title_counts"]), "image_plan_count": nearest_allowed(requested["image_plan_count"], limits["image_plan_counts"]), "image_generate_count": nearest_allowed(requested["image_generate_count"], limits["image_generate_counts"])}
    adjustments = []
    for key, value in requested.items():
        if value != applied[key]:
            adjustments.append({"field": key, "requested": value, "applied": applied[key], "reason": "vip_required_or_invalid_count"})
    credits = IMAGE_CREDIT_COST.get(applied["image_generate_count"], 0)
    return {"membership": membership, "requested": requested, "applied": applied, "adjustments": adjustments, "credit_estimate": {"image_generate_count": applied["image_generate_count"], "credits": credits, "note": "当前版本仅估算图片生成积分；未接入真实图片生成模型。" if applied["image_generate_count"] else "未选择图片生成。"}}


def extract_numbers(text: str) -> tuple[float | None, float | None, float | None]:
    def pick(keys):
        for key in keys:
            m = re.search(key + r"\D{0,6}(\d+(?:\.\d+)?)", text)
            if m:
                return float(m.group(1))
        return None
    return pick(["成本", "进价"]), pick(["售价", "卖", "价格"]), pick(["库存"])


def build_product_result(mode_name: str, product: str, detail: str, cost: float | None, price: float | None, stock: float | None, config: dict, market_context: dict) -> dict:
    current_year = market_context["current_year"]
    safe_product = clean_text_value(product, current_year) or "未填写商品"
    season = market_context["season"]
    applied = config["applied"]
    title_pool = [
        {"text": f"{safe_product}{season}轻薄透气防晒外套", "tag": "搜索词覆盖", "use_case": "自然搜索曝光测试"},
        {"text": f"{safe_product}户外骑行防晒服男女同款", "tag": "场景词", "use_case": "场景词点击测试"},
        {"text": f"{safe_product}冰丝透气轻薄防晒衣", "tag": "轻薄卖点", "use_case": "卖点词测试"},
        {"text": f"{safe_product}{season}高性价比外套", "tag": "价格感", "use_case": "价格感点击测试"},
        {"text": f"{safe_product}清仓特价轻薄防晒服", "tag": "清库存", "use_case": "库存消化测试"},
        {"text": f"{safe_product}户外防晒透气速干外套", "tag": "户外人群", "use_case": "户外人群测试"},
        {"text": f"{safe_product}学生党{season}防晒外套", "tag": "学生人群", "use_case": "低价人群测试"},
        {"text": f"{safe_product}低价好穿透气防晒衣", "tag": "低价点击", "use_case": "低价承接测试"},
        {"text": f"{safe_product}女{season}薄款防晒服外套", "tag": "长尾词", "use_case": "长尾搜索测试"},
        {"text": f"{safe_product}活动价防晒外套", "tag": "活动承接", "use_case": "活动报名承接"},
        {"text": f"{safe_product}通勤户外两用轻薄外套", "tag": "通勤场景", "use_case": "多场景测试"},
        {"text": f"{safe_product}防晒透气不闷热外套", "tag": "痛点词", "use_case": "痛点承接测试"},
        {"text": f"{safe_product}骑车旅游防晒薄款外套", "tag": "场景细分", "use_case": "细分人群测试"},
        {"text": f"{safe_product}防晒服女宽松显瘦", "tag": "人群词", "use_case": "女性人群测试"},
        {"text": f"{safe_product}多色可选轻薄防晒衣", "tag": "SKU 承接", "use_case": "颜色 SKU 测试"},
    ]
    image_pool = [
        {"name": "价格利益型", "main_text": "券后到手价突出", "sub_text": "轻薄透气｜防晒｜多场景可穿", "structure": "左侧放商品主体，右侧放大价格利益点，下方用 3 个卖点标签承接点击。", "use_case": "低价点击测试 / 自然流测款"},
        {"name": "功能卖点型", "main_text": "轻薄透气不闷热", "sub_text": "户外通勤都能穿", "structure": "上方用场景图，下方列防晒、透气、轻薄三项核心卖点。", "use_case": "提升主图点击率"},
        {"name": "场景使用型", "main_text": "通勤骑行都适合", "sub_text": "出门随手穿", "structure": "用真实出行场景做背景，商品主体居中，卖点标签放在底部。", "use_case": "VIP 场景图测试"},
        {"name": "对比痛点型", "main_text": "比普通外套更适合热天", "sub_text": "薄、透气、防晒、好收纳", "structure": "左侧痛点对比，右侧展示商品卖点，底部放适用场景。", "use_case": "VIP 痛点承接测试"},
        {"name": "活动承接型", "main_text": "活动价限时测试", "sub_text": "轻薄防晒｜多色可选｜库存有限", "structure": "顶部活动利益点，中间商品主体，下方放颜色/SKU 和库存提示。", "use_case": "VIP 活动报名承接"},
    ]
    sku_plans = [{"type": "引流 SKU", "example": "单件基础款 / 基础颜色", "purpose": "拉点击、测价格感、承接自然流"}, {"type": "利润 SKU", "example": "升级面料款 / 热卖颜色", "purpose": "提高单件毛利，承接高意向用户"}, {"type": "组合 SKU", "example": "两件装 / 多色组合", "purpose": "提高客单价，适合活动或清库存"}]
    price_advice = []
    if cost is not None and price is not None:
        profit = price - cost
        margin = profit / price * 100 if price else 0
        price_advice.extend([{"label": "当前价格", "value": f"售价 {price:.2f}，成本 {cost:.2f}，毛利 {profit:.2f}，毛利率 {margin:.1f}%"}, {"label": "A 档测试", "value": f"{price:.2f} 元，先观察自然流曝光和点击"}, {"label": "B 档测试", "value": f"{max(price - 2, cost):.2f} 元，用于测试转化提升"}, {"label": "止损提醒", "value": "如果点击低，先改标题和主图；不要直接连续降价。"}])
    else:
        price_advice.append({"label": "价格建议", "value": "先补成本和售价，再计算毛利、活动价和止损线。"})
    if mode_name == "强付费":
        activity = ["先小预算测素材点击率", "ROI 连续低于预期时先停素材，不直接放大预算", "退款率异常时暂停放量"]
        next_actions = ["选择标题做曝光测试", "用价格利益型主图测点击", "用小预算验证转化与 ROI", "第二天回填点击率、转化率、ROI"]
    elif mode_name == "爆品打造":
        activity = ["拆参考爆品的价格带、卖点和 SKU 结构", "先用小库存测流通性", "确认点击与转化后再备货"]
        next_actions = ["先确定参考爆品", "测试低价承接 SKU", "用差异化主图突出卖点", "3 天后回填曝光、点击、成交、库存变化"]
    else:
        activity = ["先测标题和主图，不急着放大预算", "曝光低先换标题词", "点击低先换主图结构", "有点击无成交再看价格和 SKU"]
        next_actions = [f"复制 {min(applied['title_count'], 3)} 条标题上架测试", "优先做价格利益型主图", "保留一个引流 SKU 和一个利润 SKU", "3 天后回填曝光、点击、成交数据"]
    if stock is not None:
        next_actions.append(f"当前库存约 {stock:.0f}，建议按库存压力决定是否加入清仓词")
    product_result = {
        "title": f"{mode_name}执行包｜{safe_product}",
        "summary": f"已按当前{season}语境生成：标题 {applied['title_count']} 条、主图方案 {applied['image_plan_count']} 个。",
        "generation_config": config,
        "market_context": {"current_year": current_year, "season": season},
        "titles": title_pool[:applied["title_count"]],
        "image_directions": image_pool[:applied["image_plan_count"]],
        "image_generation_plan": {"count": applied["image_generate_count"], "credits": config["credit_estimate"]["credits"], "note": config["credit_estimate"]["note"]},
        "sku_plans": sku_plans,
        "price_advice": price_advice,
        "activity_suggestions": activity,
        "next_actions": next_actions,
        "precision_tips": ["竞品价格与销量", "当前曝光 / 点击 / 成交 / 退款", "主图素材和商品核心卖点"],
    }
    return cleanse_value(product_result, current_year)


def product_result_to_markdown(product_result: dict) -> str:
    lines = [f"## {product_result['title']}", "", "### 标题测试包"]
    for idx, item in enumerate(product_result.get("titles", []), 1):
        lines.append(f"{idx}. {item.get('text')}（{item.get('tag')}）")
    lines.extend(["", "### 主图结构方向"])
    for item in product_result.get("image_directions", []):
        lines.append(f"- {item.get('name')}：{item.get('main_text')}｜{item.get('structure')}")
    plan = product_result.get("image_generation_plan") or {}
    if plan.get("count"):
        lines.extend(["", "### 图片生成积分"])
        lines.append(f"- 选择生成 {plan.get('count')} 张图片，预计消耗 {plan.get('credits')} 积分。")
    lines.extend(["", "### SKU 组合建议"])
    for item in product_result.get("sku_plans", []):
        lines.append(f"- {item.get('type')}：{item.get('example')}，{item.get('purpose')}")
    lines.extend(["", "### 价格建议"])
    for item in product_result.get("price_advice", []):
        lines.append(f"- {item.get('label')}：{item.get('value')}")
    lines.extend(["", "### 下一步操作"])
    for item in product_result.get("next_actions", []):
        lines.append(f"- {item}")
    lines.extend(["", "### 补充这些信息会更精准"])
    for item in product_result.get("precision_tips", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def parse_product_result_json(text: str) -> dict | None:
    if not text:
        return None
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    try:
        obj = json.loads(cleaned)
    except json.JSONDecodeError:
        return None
    product_result = obj.get("product_result") if isinstance(obj, dict) else None
    return product_result if isinstance(product_result, dict) else None


def sanitize_product_result(product_result: dict, fallback: dict, config: dict, market_context: dict) -> dict:
    current_year = market_context["current_year"]
    result = fallback.copy()
    for key in ["title", "summary"]:
        if isinstance(product_result.get(key), str):
            result[key] = clean_text_value(product_result[key], current_year) or result.get(key, "")
    for key in ["titles", "image_directions", "sku_plans", "price_advice", "activity_suggestions", "next_actions", "precision_tips"]:
        value = product_result.get(key)
        if isinstance(value, list) and value:
            result[key] = value
    applied = config["applied"]
    result["titles"] = result.get("titles", [])[:applied["title_count"]]
    result["image_directions"] = result.get("image_directions", [])[:applied["image_plan_count"]]
    result["generation_config"] = config
    result["market_context"] = {"current_year": current_year, "season": market_context["season"]}
    result["image_generation_plan"] = {"count": applied["image_generate_count"], "credits": config["credit_estimate"]["credits"], "note": config["credit_estimate"]["note"]}
    return cleanse_value(result, current_year)


def generate_operation(payload: dict) -> dict:
    ensure_dirs()
    market_context = market_time_context()
    current_year = market_context["current_year"]
    mode_key, mode_name = mode_from_payload(payload)
    product = clean_text_value(payload.get("product") or "", current_year) or "未填写商品"
    detail = clean_text_value(payload.get("detail") or "", current_year)
    market_material = str(payload.get("market_material") or payload.get("source_materials") or "")
    material_pack = build_material_pack(market_material, current_year)
    cost = number_or_none(payload.get("cost"))
    price = number_or_none(payload.get("price"))
    stock = number_or_none(payload.get("stock"))
    config = generation_config_from_payload(payload)
    client_id = clean_client_id(payload.get("client_id"))
    if cost is None or price is None or stock is None:
        parsed_cost, parsed_price, parsed_stock = extract_numbers(detail)
        cost = cost if cost is not None else parsed_cost
        price = price if price is not None else parsed_price
        stock = stock if stock is not None else parsed_stock
    module_context = load_module_context(mode_key)
    fallback_product_result = build_product_result(mode_name, product, detail, cost, price, stock, config, market_context)
    product_result = fallback_product_result
    raw_markdown = product_result_to_markdown(product_result)
    llm_status = {"enabled": llm_enabled(), "provider": None, "model": None, "used_fallback": True}
    if llm_enabled():
        provider, _, _, model = load_provider()
        llm_status.update({"provider": provider, "model": model})
        system = f"你是拼多多电商运营产品助手。当前年份是{current_year}，当前季节是{market_context['season']}。只返回 JSON，不要输出 Markdown。标题严禁出现早于{current_year}年的年份词，例如 2024、2025。内容必须产品化，不能出现工程语言、API、debug、result_id、fallback、backflow、llm_status。参考素材只能提取词感和结构，不能直接抄袭。严格按用户选择的数量输出。"
        applied = config["applied"]
        user = f"""
请根据输入生成 product_result。只返回如下 JSON：
{{
  "product_result": {{
    "title": "自然流执行包｜商品名",
    "summary": "一句面向用户的结果说明",
    "titles": [{{"text":"可直接复制的标题", "tag":"搜索词覆盖", "use_case":"用途"}}],
    "image_directions": [{{"name":"价格利益型", "main_text":"主图大字", "sub_text":"副文案", "structure":"画面结构", "use_case":"适用场景"}}],
    "sku_plans": [{{"type":"引流 SKU", "example":"单件基础款", "purpose":"作用"}}],
    "price_advice": [{{"label":"A 档测试", "value":"具体价格动作"}}],
    "activity_suggestions": ["活动或投放建议"],
    "next_actions": ["下一步动作"],
    "precision_tips": ["补充信息项"]
  }}
}}

当前时间语境：{json.dumps(market_context, ensure_ascii=False)}
素材参考包：{json.dumps(material_pack, ensure_ascii=False)}
标题禁用规则：不要出现早于 {current_year} 年的年份词，不要为了显得新而硬写过去年份。
数量要求：标题 {applied['title_count']} 条，主图方案 {applied['image_plan_count']} 个。图片生成选择 {applied['image_generate_count']} 张，预计积分 {config['credit_estimate']['credits']}。
模式:{mode_name}
商品:{product}
成本:{cost}
售价:{price}
库存:{stock}
用户补充:{detail}
模块链上下文:{module_context[:3000]}
"""
        try:
            llm_text = chat(system, user)
            parsed = parse_product_result_json(llm_text or "")
            if parsed:
                product_result = sanitize_product_result(parsed, fallback_product_result, config, market_context)
                raw_markdown = product_result_to_markdown(product_result)
                llm_status["used_fallback"] = False
            elif llm_text:
                llm_status["parse_warning"] = "llm_text_not_product_json"
        except Exception as exc:
            llm_status["error"] = type(exc).__name__
    product_result = cleanse_value(product_result, current_year)
    raw_markdown = product_result_to_markdown(product_result)
    result_id = "res_" + uuid.uuid4().hex[:12]
    client_id = client_id or f"single_{result_id}"
    debug = {"result_id": result_id, "llm_status": llm_status, "backflow_status": "stored_local_runtime_result", "generation_config": config, "market_context": market_context}
    record = {"result_id": result_id, "client_id": client_id, "created_at": now_iso(), "mode": mode_name, "mode_key": mode_key, "product": product, "input": {"detail": detail, "cost": cost, "price": price, "stock": stock, "market_material": market_material}, "material_pack": material_pack, "product_result": product_result, "raw_markdown": raw_markdown, "debug": debug}
    (RESULT_DIR / f"{result_id}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "result_id": result_id, "client_id": client_id, "mode": mode_name, "product": product, "product_result": product_result, "debug": debug, "markdown": raw_markdown}


def list_recent_results(client_id: str, limit: int = 20) -> list[dict]:
    ensure_dirs()
    client_id = clean_client_id(client_id)
    if not client_id:
        return []
    items = []
    for path in RESULT_DIR.glob("res_*.json"):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if record.get("client_id") != client_id:
            continue
        product_result = record.get("product_result") or {}
        config = product_result.get("generation_config") or {}
        items.append({"result_id": record.get("result_id"), "created_at": record.get("created_at"), "mode": record.get("mode"), "product": record.get("product"), "title": product_result.get("title"), "generation_config": config.get("applied") or {}})
    items.sort(key=lambda item: item.get("created_at") or "", reverse=True)
    return items[:limit]


def store_feedback(payload: dict) -> dict:
    ensure_dirs()
    feedback_id = "fb_" + uuid.uuid4().hex[:12]
    record = {"feedback_id": feedback_id, "client_id": clean_client_id(payload.get("client_id")), "created_at": now_iso(), "result_id": payload.get("result_id"), "action": payload.get("action"), "section": payload.get("section"), "item_text": payload.get("item_text"), "note": payload.get("note"), "raw": payload}
    (FEEDBACK_DIR / f"{feedback_id}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "feedback_id": feedback_id, "stored": True}


class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path: str) -> str:
        parsed = urlparse(path).path
        if parsed == "/":
            return str(FRONTEND_DIR / "index.html")
        if parsed.startswith("/frontend/"):
            return str(ROOT / parsed.lstrip("/"))
        return str(FRONTEND_DIR / parsed.lstrip("/"))

    def do_OPTIONS(self) -> None:
        send_json(self, 200, {"ok": True})

    def do_GET(self) -> None:
        parsed_url = urlparse(self.path)
        parsed = parsed_url.path
        query = parse_qs(parsed_url.query)
        if parsed == "/api/health":
            send_json(self, 200, {"ok": True, "service": "ai-ecommerce-backend", "time": now_iso()})
            return
        if parsed == "/api/results":
            client_id = clean_client_id((query.get("client_id") or [""])[0])
            send_json(self, 200, {"ok": True, "results": list_recent_results(client_id)})
            return
        if parsed.startswith("/api/results/"):
            result_id = parsed.rsplit("/", 1)[-1]
            client_id = clean_client_id((query.get("client_id") or [""])[0])
            p = RESULT_DIR / f"{result_id}.json"
            if not p.exists():
                send_json(self, 404, {"ok": False, "error": "result_not_found"})
                return
            record = json.loads(p.read_text(encoding="utf-8"))
            if client_id and record.get("client_id") != client_id:
                send_json(self, 404, {"ok": False, "error": "result_not_found"})
                return
            send_json(self, 200, {"ok": True, **record})
            return
        return super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path).path
        payload = read_json_body(self)
        if parsed == "/api/generate":
            send_json(self, 200, generate_operation(payload))
            return
        if parsed == "/api/feedback":
            send_json(self, 200, store_feedback(payload))
            return
        send_json(self, 404, {"ok": False, "error": "not_found"})


def main() -> None:
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "3000"))
    ensure_dirs()
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"AI ecommerce backend running at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
