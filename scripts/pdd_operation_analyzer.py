#!/usr/bin/env python3
import argparse, json, re
from pathlib import Path

FIELDS=['商品名称','商品类目','成本价','售价','物流成本','库存','SKU','商品卖点','竞品信息','运营目标','当前数据']

def pick(body,k):
    m=re.search(rf'{re.escape(k)}[：:]\s*(.*)',body)
    return m.group(1).strip() if m and m.group(1).strip() else '未填写'

def num(v):
    m=re.search(r'-?\d+(?:\.\d+)?',v or