from pathlib import Path
import os, sys, re, json
from llm_client import chat, llm_enabled, load_provider

t=os.getenv('ISSUE_TITLE','')
body=os.getenv('ISSUE_BODY','') or ''
comment=os.getenv('COMMENT_BODY','') or ''
out=sys.argv[1] if len(sys.argv)>1 else 'analysis-result.md'

mode='natural-flow'; name='自然流'
if '强付费' in t:
    mode='paid-growth'; name='强付费'
elif '爆品' in t:
    mode='hot-product'; name='爆品打造'

product=re.sub(r'^\s*\[[^\]]+\]\s*','',t).strip() or '未识别商品类型'
text=f'商品类型/标题输入：{product}\n\nIssue正文：\n{body}\n\n最新评论：\n{comment}'

chain=json.loads(Path('runtime/module_chain.json').read_text(encoding='utf-8'))
conf=chain.get(mode) or chain['natural-flow']

def read_key(key):
    p=conf.get(key)
    if not p:
        return ''
    path=Path(p)
    return path.read_text(encoding='utf-8') if path.exists() else ''

platform=read_key('platform')
platform_title=read_key('platform_title')
platform_image=read_key('platform_image')
mode_doc=read_key('mode')
input_schema=read_key('input_schema')
prompt_doc=read_key('prompt')
tpl=read_key('template').replace('{product}', product)
frontend_schema=read_key('frontend_schema')

continue_request=('下一步' in comment) or ('执行包' in comment) or ('生成标题' in comment) or ('继续' in comment)
extra='本次必须直接输出完整可执行结果卡。不要把“补充信息”当成阻断条件；信息不足时先按现有信息生成第一版，并在末尾用“补充这些信息会更精准”列出最多3项。用户输入越详细，输出越清晰。'
if mode=='natural-flow':
    extra+=' 自然流模式必须包含：拼多多标题测试包、主图文案方向、价格测试建议、观察指标。'
elif mode=='paid-growth':
    extra+=' 强付费模式必须包含：放量条件检查、预算节奏、素材方向、ROI警戒线、停投条件。'
elif mode=='hot-product':
    extra+=' 爆品打造模式必须包含：爆品结构拆解、流通性测试、差异化承接、备货/清货建议、风险提醒。'
if continue_request:
    extra+=' 用户正在继续补充或要求下一步，请基于 Issue 原始输入和最新评论更新/细化结果，而不是重复空泛提示。'

num=r'(\d+(?:\.\d+)?)'
def pick(keys):
    for k in keys:
        m=re.search(k+r'\D{0,4}'+num,text)
        if m: return float(m.group(1))
    return None
cost=pick(['成本','进价'])
price=pick(['售价','卖','价格'])
finance='## 基础财务模板\n'
finance+=f'- 商品类型：{product}\n'
if cost is not None and price is not None:
    profit=price-cost
    rate=profit/price*100 if price else 0
    finance+=f'- 成本：{cost:.2f}\n- 售价：{price:.2f}\n- 单件毛利：{profit:.2f}\n- 毛利率：{rate:.1f}%\n'
else:
    finance+='- 成本/售价不足，暂不计算毛利率。\n'

module_context='\n\n'.join([x for x in [platform, platform_title, platform_image, mode_doc, input_schema, prompt_doc, frontend_schema] if x])
base=f'{tpl}\n\n---\n\n{finance}\n\n## 输出说明\n- 当前为确定性模板回退结果。接入 API 大模型后，会按现有信息直接生成完整执行包。\n- 补充商品卖点、竞品价格、当前数据，会让输出更精准。\n'

llm_note='## API 大模型状态\n- 未启用 API 大模型，当前输出为确定性模板。\n'
llm_result=None
if llm_enabled():
    p,_,_,m=load_provider()
    system='你是拼多多电商运营产品助手。严格按模块链和输出模板生成可执行结果卡。第一次输入就直接输出完整结果，不要求用户再输入下一步。信息不足时先给第一版，不要卡住。'
    user=f'模式:{name}\n商品类型:{product}\n\n额外指令:{extra}\n\n输出模板:\n{tpl}\n\n模块链上下文:\n{module_context}\n\n基础财务:\n{finance}\n\n用户输入:\n{text}'
    try:
        llm_result=chat(system,user)
        llm_note=f'## API 大模型状态\n- 已调用 provider: {p}\n- model: {m}\n'
    except Exception as e:
        llm_note=f'## API 大模型状态\n- 调用失败，已回退确定性模板：{type(e).__name__}\n'

res=(llm_result if llm_result else base)+'\n\n---\n\n'+llm_note+'\n<details>\n<summary>调试信息</summary>\n\n## 已读取模块\n'+module_context+'\n\n## 本次输入摘要\n'+(text[:900] if text.strip() else '未填写正文')+'\n\n</details>\n'
Path(out).write_text(res,encoding='utf-8')
