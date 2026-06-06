#!/usr/bin/env python3
import argparse, json, os, re
from pathlib import Path

FIELDS = ["商品名称","商品类目","成本价","售价","物流成本","库存","SKU","商品卖点","竞品信息","运营目标","当前数据"]
SENSITIVE = ["医药","药","保健","医疗","器械","减肥","功效","成人"]

def load_event(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def parse_body(body):
    data = {k: "" for k in F