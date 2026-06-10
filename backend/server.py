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

TRUE_VALUES = {"1", "true", "yes", "on"}

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


def build_fallback_result(mode_name: str, product: str, detail: str, cost: float | None, price: float | None, stock: float | None) -> dict:
    safe_product = product.strip() or "未填写商品"
    title_prefixes = ["夏季", "新款", "轻薄", "高性价比", "家用", "学生", "户外", "官方补贴", "清仓", "热卖"]
    titles = [f"{safe_product}{prefix} 拼多多爆款关键词测试标题" for prefix in title_prefixes]

    image_directions = [
        "价格利益型：大字突出券后价/到手价，搭配商品主体和3个卖点标签。",
        "功能卖点型：突出核心功能、使用场景、痛点解决，例如防晒/透气/耐用。",
        "对比承接型：用竞品价格或旧款痛点做对比，强化点击理由。",
    ]

    sku_suggestions = [
        "设置低价引流 SKU，承接搜索和活动流量。",
        "设置利润 SKU，突出材质/规格/组合升级。",
        "设置组合 SKU，用多件装或颜色组合提高客单价。",
    ]

    if cost is not None and price is not None:
        profit = price - cost
        margin = profit / price * 100 if price else 0
        finance = f"成本 {cost:.2f}，售价 {price:.2f}，单件毛利 {profit:.2f}，毛利率 {margin:.1f}%。"
    else:
        finance = "成本/售价不完整，先输出运营建议；补充成本和售价后可计算毛利与止损线。"

    if mode_name == "强付费":
        strategy = "先用小预算测点击率和转化，再根据 ROI 与退款率决定是否放量。"
    elif mode_name == "爆品打造":
        strategy = "先拆竞品价格带、卖点和 SKU 结构，再用小库存测试流通性。"
    else:
        strategy = "先测标题曝光、主图点击和价格感，确认基础流通性后再进入付费或活动。"

    markdown = f"""## {mode_name}执行包｜{safe_product}

### 1. 标题测试包
"""
    for idx, title in enumerate(titles, 1):
        markdown += f"{idx}. {title}\n"
    markdown += "\n### 2. 主图结构方向\n"
    for item in image_directions:
        markdown += f"- {item}\n"
    markdown += "\n### 3. SKU 组合建议\n"
    for item in sku_suggestions:
        markdown += f"- {item}\n"
    markdown += f"\n### 4. 价格与运营判断\n- {finance}\n- {strategy}\n"
    if stock is not None:
        markdown += f"- 当前库存：{stock:.0f}，建议按 3 天观察曝光/点击/成交变化。\n"
    markdown += "\n### 5. 补充这些信息会更精准\n- 竞品价格与销量\n- 当前曝光/点击/成交/退款数据\n- 主图素材和核心卖点\n"

    return {
        "titles": titles,
        "image_directions": image_directions,
        "sku_suggestions": sku_suggestions,
        "price_plan": [finance, strategy],
        "markdown": markdown,
    }


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
    fallback = build_fallback_result(mode_name, product, detail, cost, price, stock)
    llm_status = {"enabled": llm_enabled(), "provider": None, "model": None, "used_fallback": True}
    markdown = fallback["markdown"]

    if llm_enabled():
        provider, _, _, model = load_provider()
        llm_status.update({"provider": provider, "model": model})
        system = "你是拼多多电商运营产品助手。前端用户第一次提交后就直接输出完整运营执行包。信息不足时先给第一版，不要要求用户输入下一步。"
        user = f"模式:{mode_name}\n商品:{product}\n成本:{cost}\n售价:{price}\n库存:{stock}\n\n用户补充:\n{detail}\n\n模块链上下文:\n{module_context}\n\n必须输出：标题测试包、主图结构、SKU建议、价格/活动建议、观察指标、补充信息会更精准。"
        try:
            llm_text = chat(system, user)
            if llm_text:
                markdown = llm_text
                llm_status["used_fallback"] = False
        except Exception as exc:  # keep frontend usable even when model API fails
            llm_status["error"] = type(exc).__name__

    result_id = "res_" + uuid.uuid4().hex[:12]
    record = {
        "result_id": result_id,
        "created_at": now_iso(),
        "mode": mode_name,
        "mode_key": mode_key,
        "product": product,
        "input": {"detail": detail, "cost": cost, "price": price, "stock": stock},
        "output": {**fallback, "markdown": markdown},
        "llm_status": llm_status,
        "backflow_status": "stored_local_runtime_result",
    }
    (RESULT_DIR / f"{result_id}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "ok": True,
        "result_id": result_id,
        "mode": mode_name,
        "product": product,
        "markdown": markdown,
        "cards": fallback,
        "llm_status": llm_status,
        "backflow_status": record["backflow_status"],
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
