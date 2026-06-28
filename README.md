# AI ERP 企业级电商经营 SaaS 底座

当前基线：**V12.7.1 任务聚合队列 + 详情页容错 + 高权重判定重构**。

V12.7.1 保留 V12.7 的高权重判定规则：高 ROI、高 GMV、点击率 / 转化率波动、任务优先级、商品生命周期标签、首份报表基线标签，只能作为经营表现或任务排序依据，不能直接判定为高权重店铺或高权重商品。本版新增任务队列收口：同一店铺、同一动作、同一原因的多商品任务，在前端展示为一个聚合队列任务；完整受影响商品列表进入详情页。任务详情接口增加 fail-closed，字段异常时返回结构化报告，不再让页面 500。

## 当前执行入口

```text
前端唯一入口：web_demo/
后端唯一入口：src/api/main.py
版本主文件：VERSION.md + versioning/VERSION.md
运行态数据库：SQLite Demo runtime
部署脚本：scripts/deploy_fast.sh / scripts/deploy_atomic.sh
```

## 当前主链路

```text
报表 / 接口数据导入
→ 报表布局 Agent / 指标事实表 / 数据缺口池
→ 首份报表 baseline_snapshot，只建基线
→ 两份报表才允许环比经营任务
→ risk_task_service 生成红线任务 + ROI/GMV经营任务
→ rag_business_memory_service 读取公司基线和历史经营记忆
→ action_impact_estimation_service 系统生成保守 / 正常 / 乐观估算
→ operating_weight_policy_service 判断治理权重、来源、置信度
→ action_authorization_gate_service 判断账号权限、动作风险和审批路径
→ AppApi.refreshTaskState() 从 /api/modules/todo 同步后端任务池
→ todo/page.js 按店铺 + 动作 + 原因聚合同类商品任务
→ task_report 路由 fail-closed 返回详情或结构化兜底报告
```

## V12.7.1 硬规则

```text
经营表现不等于权限权重。
高ROI、高GMV、任务优先级、生命周期标签和首份报表标签不能触发高权重审批。
第一份报表只做基线，非红线经营任务必须有至少两份可比报表。
重复商品任务不能刷屏，同类任务必须聚合成队列任务。
任务列表只显示时间、紧急度、状态和详情入口。
完整 SOP、指标、证据链、受影响商品列表进入详情页。
任务详情接口不能 500，异常时返回 failClosed 结构化报告。
经营页店铺卡片永远保留查看商品入口，有任务时追加查看任务。
```

## 当前主 API

```text
/                                      web_demo 前端入口
/api/health                            健康检查
/api/modules/dashboard                 总览
/api/modules/report                    数据 / 报表
/api/modules/operating-unit            经营
/api/modules/product                   商品档案
/api/modules/product?storeId=STORE_ID  店铺商品档案
/api/modules/product/{product_id}      单商品事实详情
/api/modules/todo                      聚合后的任务队列来源
/api/modules/task-reports/tasks/{id}   任务详情报告，fail-closed
/api/modules/log                       日志
/api/accounts                          账号
/api/accounts/switch                   ECS Demo 账号切换验证
/api/data/source-connections           数据源接口契约
/api/data/upload/preview               上传文件预览 + 报表布局画像
/api/data/upload/confirm               上传确认导入 + 经营对象 / block事实 / 缺口 / 诊断 / 任务同步
/api/data/metric-facts/summary         指标事实表统计
/api/data/data-gaps/summary            数据缺口池统计
/api/data/import-diagnostics           Sheet → Block → Fact → Gap → Staging 诊断
/api/system/runtime-diagnostics        运行态诊断
/api/system/reset-runtime-data          清空演示运行态
```

## 部署入口

```bash
bash scripts/deploy_fast.sh
```
