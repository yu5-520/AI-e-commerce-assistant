from pathlib import Path
import os, sys, re
from llm_client import chat, llm_enabled, load_provider

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

mod=Path(f'docs/modules/{mode}.md').read_text(encoding='utf-8')
tpl=Path(f'docs/output-templates/{mode}-result.md').read_text(encoding='utf-8')
base=f'{tpl}\n\n---\n\n{finance}\n'

llm_note='## API 大模型状态\n- 未启用 API 大模型，当前输出为确定性模板。\n'
llm_result=None
if llm_enabled():
    p,_,_,m=load_provider()
    system='你是拼多多电商运营产品助手。严格按输出模板生成结果卡，不要编造缺失数据。'
    user=f'模式:{name}\n\n输出模板:\n{tpl}\n\n模块说明:\n{mod}\n\n基础财务:\n{finance}\n\n用户输入:\n{text}'
    try:
        llm_result=chat(system,user)
        llm_note=f'## API 大模型状态\n- 已调用 provider: {p}\n- model: {m}\n'
    except Exception as e:
        llm_note=f'## API 大模型状态\n- 调用失败，已回退确定性模板：{type(e).__name__}\n'

res=(llm_result if llm_result else base)+'\n\n---\n\n'+llm_note+'\n## 已读取模块\n'+mod+'\n\n## 本次输入摘要\n'+(text[:800] if text.strip() else '未填写正文')+'\n'
Path(out).write_text(res,encoding='utf-8')
