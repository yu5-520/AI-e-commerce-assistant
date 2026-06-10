from __future__ import annotations

import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

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


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_dirs() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)


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


def extract_numbers(text: str) -> tuple[float | None, float | None, float | None]:
    def pick(keys):
        for key in keys:
            m = re.search(key + r"\D{0,6}(\d+(?:\.\d+)?)", text)
            if m:
                return float(m.group(1))
        return None

    return pick(["成本", "进价"]), pick(["售价", "卖", "价格"]), pick(["库存"])


def clean_string(value, fallback: str = "") -> str:
    text = str(value or fallback).strip()
    blocked = ["result_id", "backflow", "llm_status", "deterministic", "fallback", "api", "POST", "debug"]
    for word in blocked:
        text = text.replace(word, "")
    return re.sub(r"\s+", " ", text).strip()


def build_product_result(mode_name: str, product: str, detail: str, cost: float | None, price: float | None, stock: float | None) -> dict:
    safe_product = product.strip() or "未填写商品"
    title_tags = ["搜索词覆盖", "价格感", "场景词", "轻薄卖点", "清库存", "户外人群", "学生人群", "低价点击", "长尾词", "活动承接"]
    titles = [
        {"text": f"{safe_product}夏季轻薄透气防晒外套", "tag": title_tags[0], "use_case": "自然搜索曝光测试"},
        {"text": f"{safe_product}户外骑行防晒服男女同款", "tag": title_tags[2], "use_case": "场景词点击测试"},
        {"text": f"{safe_product}冰丝透气轻薄防晒衣", "tag": title_tags[3], "use_case": "卖点词测试"},
        {"text": f"{safe_product}夏季新款高性价比外套", "tag": title_tags[1], "use_case": "价格感点击测试"},
        {"text": f"{safe_product}清仓特价轻薄防晒服", "tag": title_tags[4], "use_case": "库存消化测试"},
        {"text": f"{safe_product}户外防晒透气速干外套", "tag": title_tags[5], "use_case": "户外人群测试"},
        {"text": f"{safe_product}学生党夏季防晒外套", "tag": title_tags[6], "use_case": "低价人群测试"},
        {"text": f"{safe_product}低价好穿透气防晒衣", "tag": title_tags[7], "use_case": "低价承接测试"},
        {"text": f"{safe_product}女夏季薄款防晒服外套", "tag": title_tags[8], "use_case": "长尾搜索测试"},
        {"text": f"{safe_product}活动价夏季防晒外套", "tag": title_tags[9], "use_case": "活动报名承接"},
    ]

    image_directions = [
        {
            "name": "价格利益型",
            "main_text": "券后到手价突出",
            "sub_text": "轻薄透气｜夏季防晒｜多场景可穿",
            "structure": "左侧放商品主体，右侧放大价格利益点，下方用 3 个卖点标签承接点击。",
            "use_case": "低价点击测试 / 自然流测款",
        },
        {
            "name": "功能卖点型",
            "main_text": "轻薄透气不闷热",
            "sub_text": "户外通勤都能穿",
            "structure": "上方用场景图，下方列防晒、透气、轻薄三项核心卖点。",
            "use_case": "提升主图点击率",
        },
        {
            "name": "对比承接型",
            "main_text": "比普通外套更适合夏天",
            "sub_text": "薄、透气、防晒、好收纳",
            "structure": "左侧痛点对比，右侧展示商品卖点，底部放适用场景。",
            "use_case": "解决有点击无成交问题",
        },
    ]

    sku_plans = [
        {"type": "引流 SKU", "example": "单件基础款 / 基础颜色", "purpose": "拉点击、测价格感、承接自然流"},
        {"type": "利润 SKU", "example": "升级面料款 / 热卖颜色", "purpose": "提高单件毛利，承接高意向用户"},
        {"type": "组合 SKU", "example": "两件装 / 多色组合", "purpose": "提高客单价，适合活动或清库存"},
    ]

    price_advice = []
    if cost is not None and price is not None:
        profit = price - cost
        margin = profit / price * 100 if price else 0
        price_advice.append({"label": "当前价格", "value": f"售价 {price:.2f}，成本 {cost:.2f}，毛利 {profit:.2f}，毛利率 {margin:.1f}%"})
        price_advice.append({"label": "A 档测试", "value": f"{price:.2f} 元，先观察自然流曝光和点击"})
        price_advice.append({"label": "B 档测试", "value": f"{max(price - 2, cost):.2f} 元，用于测试转化提升"})
        price_advice.append({"label": "止损提醒", "value": "如果点击低，先改标题和主图；不要直接连续降价。"})
    else:
        price_advice.append({"label": "价格建议", "value": "先补成本和售价，再计算毛利、活动价和止损线。"})

    if mode_name == "强付费":
        activity = ["先小预算测素材点击率", "ROI 连续低于预期时先停素材，不直接放大预算", "退款率异常时暂停放量"]
        next_actions = ["先选择 3 条标题做曝光测试", "用价格利益型主图测点击", "用小预算验证转化与 ROI", "第二天回填点击率、转化率、ROI"]
    elif mode_name == "爆品打造":
        activity = ["拆参考爆品的价格带、卖点和 SKU 结构", "先用小库存测流通性", "确认点击与转化后再备货"]
        next_actions = ["先确定参考爆品", "测试低价承接 SKU", "用差异化主图突出卖点", "3 天后回填曝光、点击、成交、库存变化"]
    else:
        activity = ["先测标题和主图，不急着放大预算", "曝光低先换标题词", "点击低先换主图结构", "有点击无成交再看价格和 SKU"]
        next_actions = ["复制 3 条标题上架测试", "优先做价格利益型主图", "保留一个引流 SKU 和一个利润 SKU", "3 天后回填曝光、点击、成交数据"]

    precision_tips = ["竞品价格与销量", "当前曝光 / 点击 / 成交 / 退款", "主图素材和商品核心卖点"]
    if stock is not None:
        next_actions.append(f"当前库存约 {stock:.0f}，建议按库存压力决定是否加入清仓词")

    return {
        "title": f"{mode_name}执行包｜{safe_product}",
        "summary": "已清洗为可直接复制、可执行、可回流的运营结果。",
        "titles": titles,
        "image_directions": image_directions,
        "sku_plans": sku_plans,
        "price_advice": price_advice,
        "activity_suggestions": activity,
        "next_actions": next_actions,
        "precision_tips": precision_tips,
    }


def product_result_to_markdown(product_result: dict) -> str:
    lines = [f"## {product_result['title']}", "", "### 标题测试包"]
    for idx, item in enumerate(product_result.get("titles", []), 1):
        lines.append(f"{idx}. {item.get('text')}（{item.get('tag')}）")
    lines.extend(["", "### 主图结构方向"])
    for item in product_result.get("image_directions", []):
        lines.append(f"- {item.get('name')}：{item.get('main_text')}｜{item.get('structure')}")
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


def sanitize_product_result(product_result: dict, fallback: dict) -> dict:
    result = fallback.copy()
    for key in ["title", "summary"]:
        if isinstance(product_result.get(key), str):
            result[key] = clean_string(product_result[key], result.get(key, ""))
    for key in ["titles", "image_directions", "sku_plans", "price_advice", "activity_suggestions", "next_actions", "precision_tips"]:
        value = product_result.get(key)
        if isinstance(value, list) and value:
            result[key] = value
    return result


def generate_operation(payload: dict) -> dict:
    ensure_dirs()
    mode_key, mode_name = mode_from_payload(payload)
    product = str(payload.get("product") or "").strip() or "未填写商品"
    detail = str(payload.get("detail") or "")
    cost = number_or_none(payload.get("cost"))
    price = number_or_none(payload.get("price"))
    stock = number_or_none(payload.get("stock"))
    if cost is None or price is None or stock is None:
        parsed_cost, parsed_price, parsed_stock = extract_numbers(detail)
        cost = cost if cost is not None else parsed_cost
        price = price if price is not None else parsed_price
        stock = stock if stock is not None else parsed_stock

    module_context = load_module_context(mode_key)
    fallback_product_result = build_product_result(mode_name, product, detail, cost, price, stock)
    product_result = fallback_product_result
    raw_markdown = product_result_to_markdown(product_result)
    llm_status = {"enabled": llm_enabled(), "provider": None, "model": None, "used_fallback": True}

    if llm_enabled():
        provider, _, _, model = load_provider()
        llm_status.update({"provider": provider, "model": model})
        system = "你是拼多多电商运营产品助手。只返回 JSON，不要输出 Markdown。内容必须产品化，不能出现工程语言、API、debug、result_id、fallback、backflow、llm_status。"
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
                product_result = sanitize_product_result(parsed, fallback_product_result)
                raw_markdown = product_result_to_markdown(product_result)
                llm_status["used_fallback"] = False
            elif llm_text:
                llm_status["parse_warning"] = "llm_text_not_product_json"
        except Exception as exc:
            llm_status["error"] = type(exc).__name__

    result_id = "res_" + uuid.uuid4().hex[:12]
    debug = {
        "result_id": result_id,
        "llm_status": llm_status,
        "backflow_status": "stored_local_runtime_result",
    }
    record = {
        "result_id": result_id,
        "created_at": now_iso(),
        "mode": mode_name,
        "mode_key": mode_key,
        "product": product,
        "input": {"detail": detail, "cost": cost, "price": price, "stock": stock},
        "product_result": product_result,
        "raw_markdown": raw_markdown,
        "debug": debug,
    }
    (RESULT_DIR / f"{result_id}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "ok": True,
        "result_id": result_id,
        "mode": mode_name,
        "product": product,
        "product_result": product_result,
        "debug": debug,
        "markdown": raw_markdown,
    }


def store_feedback(payload: dict) -> dict:
    ensure_dirs()
    feedback_id = "fb_" + uuid.uuid4().hex[:12]
    record = {
        "feedback_id": feedback_id,
        "created_at": now_iso(),
        "result_id": payload.get("result_id"),
        "action": payload.get("action"),
        "section": payload.get("section"),
        "item_text": payload.get("item_text"),
        "note": payload.get("note"),
        "raw": payload,
    }
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
        parsed = urlparse(self.path).path
        if parsed == "/api/health":
            send_json(self, 200, {"ok": True, "service": "ai-ecommerce-backend", "time": now_iso()})
            return
        if parsed.startswith("/api/results/"):
            result_id = parsed.rsplit("/", 1)[-1]
            p = RESULT_DIR / f"{result_id}.json"
            if not p.exists():
                send_json(self, 404, {"ok": False, "error": "result_not_found"})
                return
            send_json(self, 200, json.loads(p.read_text(encoding="utf-8")))
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
