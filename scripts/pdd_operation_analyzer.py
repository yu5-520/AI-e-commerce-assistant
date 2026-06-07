from pathlib import Path
import os, sys

t=os.getenv('ISSUE_TITLE','')
b=os.getenv('ISSUE_BODY','').strip()
out=sys.argv[1] if len(sys.argv)>1 else 'analysis-result.md'
mode='natural-flow'
name='自然流'
if '强付费' in t:
    mode='paid-growth'; name='强付费'
elif '爆品' in t:
    mode='hot-product'; name='爆品打造'
mod=Path(f'docs/modules/{mode}.md').read_text(encoding='utf-8')
tpl=Path(f'docs/output-templates/{mode}-result.md').read_text(encoding='utf-8')
res=f'{tpl}\n\n---\n\n## 已读取模块\n{mod}\n\n## 本次输入摘要\n{b[:800] if b else "未填写正文"}\n\n## 工作流说明\nworkflow只负责调度；脚本读取docs/modules与docs/output-templates生成结果。\n'
Path(out).write_text(res,encoding='utf-8')
