# AI ERP 企业级电商经营 SaaS 底座

当前基线：**V12.8.2 后端主架构强制闸门版**。

V12.8.2 保留 V12.8.1 的任务生命周期闭环和前后端契约收口，本版重点修正“主架构服务存在但最终输出被短路”的问题：店铺标签必须经过 store_tag_projection_service，不能因为商品数量、已入库、ROI/GMV 表现默认显示高权重；动作审批必须经过预算权限、系统保守估算、公司基线和已确认治理权重，不能因为 actionType 是投放预算调整就一刀切主管审批；详情页 fallback 改为中文诊断兜底，并明确不能作为正常详情页。

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
→ rag_business_memory_service 读取公司基线 + approved/effective RAG经验卡
→ action_impact_estimation_service 系统生成保守/正常/乐观影响估算
→ operating_weight_policy_service 只信任RAG/主管/老板/多期历史贡献的治理权重
→ action_authorization_gate_service 按预算权限、保守下限、公司基线、治理权重判断审批
→ task_cluster_service 生成真实后端聚合任务
→ /api/modules/todo 返回带 taskLifecycle 的真实任务池
→ task_lifecycle_orchestrator_service 推进接收、提交材料、复核、复盘、RAG候选
→ store_tag_projection_service 输出治理标签 / 数据标签 / 经营标签
→ RAG审核通过后，下一次任务生成自动召回经验卡
```

## V12.8.2 硬规则

```text
店铺标签必须经过 store_tag_projection_service。
没有 RAG/主管/老板/多期历史贡献来源时，只能显示“权重未确认”，不能显示“高权重店铺”。
经营表现不等于权限权重，高ROI、高GMV、商品数量、已入库不能触发高权重审批。
投放预算调整、活动报名、扩流测试不能因 actionType 一刀切主管审批。
预算/活动动作必须读取 operatorActivityBudgetRange。
预算超权限、系统保守估算低于公司基线、或已确认治理高权重对象，才升级主管审批。
同一个 task_id 必须贯穿生成、接收、提交材料、复核、复盘和RAG候选。
前端不得再次聚合同类商品任务；聚合只能由后端 task_cluster_service 完成。
详情页 safe fallback 只能兜底，不能作为正常详情页。
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
/api/modules/todo                      带生命周期的任务队列来源
/api/modules/todo/lifecycle/summary    任务生命周期统计
/api/modules/todo/{id}/recap/complete  完成复盘并生成RAG候选
/api/modules/task-reports/tasks/{id}   任务详情报告，支持 affectedProducts 和 taskLifecycle
/api/modules/log                       日志
/api/modules/recap-candidates          复盘候选
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
