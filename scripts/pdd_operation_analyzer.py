#!/usr/bin/env python3
import argparse
from pathlib import Path

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--body-file', default='')
    p.add_argument('--out', default='analysis-result.md')
    a = p.parse_args()
    body = Path(a.body_file).read_text(encoding='utf-8') if a.body_file else ''
    route = 'natural-flow-test'
    low = body.lower()
    if 'brand