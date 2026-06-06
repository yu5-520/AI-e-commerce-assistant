#!/usr/bin/env python3
"""Stable rule-based analyzer for PDD operation issues.

Reads a GitHub issue event JSON and writes a Markdown report.
No external AI API is required, so the workflow can run without secrets.
"""

import argparse
import json
import re
from pathlib import Path

FIELDS = ["商品名称", "商品类目", "成本价", "售价", "物流成本", "库存", "SKU", "商品卖点",