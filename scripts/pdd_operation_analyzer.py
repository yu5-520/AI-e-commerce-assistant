#!/usr/bin/env python3
import argparse
from pathlib import Path

FIELDS = ['商品名称','商品类目','成本价','售价','物流成本','库存','SKU','商品卖点','竞品信息','运营目标','当前数据']


def get_field(body, key):
    tag = '### ' + key
    if tag not in body:
        return ''
    return body.split(tag, 1)[1].split('\n### ', 1)[0].strip()


def choose_route(data):
    text = ' '.join(data.values())
    if any(w in text for w in ['医