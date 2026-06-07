from pathlib import Path
import os,sys
out=sys.argv[1] if len(sys.argv)>1 else 'analysis-result.md'
t=(os.getenv('ISSUE_TITLE','')+' '+os.getenv('ISSUE_BODY','')).lower()
if '强付费' in t:
    title='强付费放量结果卡'; conclusion='先确认保本线和转化基础，再决定是否放量。'; action='小预算测素材，ROI低于保本线就停。'; need='补充成本、物流、库存、预算、转化、ROI。'
elif '爆品' in t:
    title='爆品打造结果卡'; conclusion='先拆爆品结构和测试流通性，不建议直接大批量备货。'; action='做标题