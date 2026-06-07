from pathlib import Path
import os,sys
out=sys.argv[1] if len(sys.argv)>1 else 'analysis-result.md'
t=os.getenv('ISSUE_TITLE','')+' '+os.getenv('ISSUE_BODY','')
mode='natural'
if '[强付费]' in t: mode='paid'
if '[爆品]' in t: mode='hot'
cards={
'natural':('# 自然流测试结果卡','当前适合先测标题、主图和基础流通性，不建议一开始强付费。','先做2-3组标题/主图测试，看曝光、点击、成交。','如需进一步判断活动或投放，请补充成本、库存、点击、成交。'),
'paid':