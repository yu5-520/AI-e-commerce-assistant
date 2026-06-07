from pathlib import Path
import os,sys
t=os.getenv('ISSUE_TITLE','')
m='自然流'
if '强付费' in t: m='强付费'
if '爆品' in t: m='爆品'
out=sys.argv[1] if len(sys.argv)>1 else 'analysis-result.md'
text=f'# {m}结果卡\n\n## 结论\n已进入{m}模式，先按该模式输出执行建议，不再让AI自动选路。\n\n## 先做什么\n- 用当前输入生成第一轮测试动作\n- 缺失信息不强行判断\n- 下一轮再补数据加深分析\n\n## 补充信息\n自然流看标题/主图/点击；强付费看成本/预算/ROI；爆品看竞品/备货/流通性。\n'
Path(out).write_text(text,encoding='utf-8')
