from pathlib import Path
import os, sys, re

t=os.getenv('ISSUE_TITLE','')
body=os.getenv('ISSUE_BODY','') or ''
comment=os.getenv('COMMENT_BODY','') or ''
text=body+'\n'+comment
out=sys.argv[1] if len(sys.argv)>1 else 'analysis-result.md'

mode='natural-flow'; name='自然流'
if '强付费' in t:
    mode='paid-growth'; name='强付费'
elif '爆品' in t:
    mode='hot-product'; name='爆品打造'

num=r'(\d+(?:\.\d+)?)'
def pick(keys):
    for k in keys:
        m=re.search(k+r'\D{0,4}'+num,text)
        if m: return float(m.group(1))
    return None
cost=pick(['成本','进价'])
price=pick(['售价','卖','价格'])
finance='## 基础财务模板\n'
if cost is not None and price is not None:
    profit=price-cost
    rate=profit/price*100 if price else 0
    finance+=f'- 成本：{cost:.2f}\n- 售价：{price:.2f}\n- 单件毛利：{profit:.2f}\n- 毛利率：{rate:.1f}%\n'
else:
    finance+='- 成本/售价不足，暂不计算毛利率。\n'
finance+='- 说明：这里仅做确定性计算；标题、主图、竞品、投放判断后续交给 API 大模型。\n'

mod=Path(f'docs/modules/{mode}.md').read_text(encoding='utf-8')
tpl=Path(f'docs/output-templates/{mode}-result.md').read_text(encoding='utf-8')
res=f'{tpl}\n\n---\n\n{finance}\n\n## API 大模型预留位\n- 后续可把本次输入、模块文档、输出模板一起发送给 API 大模型生成深度运营建议。\n\n## 已读取模块\n{mod}\n\n## 本次输入摘要\n{text[:800] if text.strip() else "未填写正文"}\n'
Path(out).write_text(res,encoding='utf-8')
