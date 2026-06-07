from pathlib import Path
import os, sys

TITLE = os.getenv('ISSUE_TITLE', '')
BODY = os.getenv('ISSUE_BODY', '')
OUT = sys.argv[1] if len(sys.argv) > 1 else 'analysis-result.md'

mode = 'natural-flow'
name = '自然流'
if '强付费' in TITLE:
    mode, name = 'paid-growth', '强付费'
elif '爆品' in TITLE:
    mode, name = 'hot-product', '爆品打造'

module_path = Path(f'docs/modules/{mode}.md')