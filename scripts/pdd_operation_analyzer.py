#!/usr/bin/env python3
import argparse
import re
from pathlib import Path

FIELDS = ["商品名称", "商品类目", "成本价", "售价", "物流成本", "库存", "SKU", "商品卖点", "竞品信息", "运营目标", "当前数据"]


def pick(body, key):
    m = re.search(r"###\s*" + re.escape(key) + r"\s*\n+([^#]+)", body, re.S)
    if m:
        return m.group(1).strip()
    m = re.search(re.escape(key) + r"[：:]\s*(.+)", body)
    return m.group(1).strip() if m else ""
