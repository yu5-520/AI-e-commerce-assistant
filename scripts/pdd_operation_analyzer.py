#!/usr/bin/env python3
import argparse,json,re
FIELDS=['商品名称','商品类目','成本价','售价','物流成本','库存','SKU','商品卖点','竞品信息','运营目标','当前数据']
SENSITIVE=['医药','药','保健','医疗','器械','减肥','功效','成人']

def pick(body,key):
    m=re.search(rf'{key}[：:]\s*(.*)',body)
    return m.group(1).strip() if m else ''

def report(event):
    issue=event.get('issue',{})
    title=issue.get('title','')
    body=issue.get('body','') or ''
    data={k:pick