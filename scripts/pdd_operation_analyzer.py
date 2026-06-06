#!/usr/bin/env python3
import argparse, json, re
from pathlib import Path

FIELDS = ["商品名称", "商品类目", "成本价", "售价", "物流成本", "库存", "SKU", "商品卖点", "竞品信息", "运营目标", "当前数据"]

def pick(body, key):
    patterns = [rf"###\s*{re.escape(key)}\s*\n+([^#]+)", rf"{re.escape(key)}[：:]\s*(.+)"]
    for pat in patterns:
        m = re.search(pat, body or "", re.S)
        if