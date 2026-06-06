#!/usr/bin/env python3
import argparse,re
from pathlib import Path

FIELDS=['商品名称','商品类目','成本价','售价','物流成本','库存','SKU','商品卖点','竞品信息','运营目标','当前数据']

def pick(body,k):
    m=re.search(r'###\s*'+re.escape(k)+r'\s*\n+([^#]+)',body,re.S)
    return m.group(1).strip() if m else ''

def to_num(x):
    m=re.search(r'-?\d+(?:\.\d+)?',x or '')
    return float(m.group()) if m else None

def build(title,body):
    d