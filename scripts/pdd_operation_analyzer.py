#!/usr/bin/env python3
import argparse
from pathlib import Path

FIELDS = [
    "商品名称", "商品类目", "成本价", "售价", "物流成本", "库存",
    "SKU", "商品卖点", "竞品信息", "运营目标", "当前数据"
]


def read_body(path: str) -> str:
    return Path(path).read_text(encoding="utf-8") if path else ""


def field(body: str, key: str) -> str:
    tag = "### " + key
    if tag not in body:
        return ""
    part = body