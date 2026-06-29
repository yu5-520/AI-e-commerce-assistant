# AI ERP 企业级电商经营 SaaS 底座

当前基线：**V12.8.3 任务卡动作与聚合详情收口版**。

V12.8.3 保留 V12.8.2 的后端主架构强制闸门，本版重点收口任务生命周期在产品卡片上的表现：任务列表按左侧时间轴排序，运营任务卡只显示一个当前人工动作和常驻详情；复核只在总管任务视角出现；复盘由系统自动调度，不作为运营按钮。前端任务卡必须读取后端 `primaryTaskAction` / `visibleTaskActions`，不能直接渲染 raw `availableActions`。聚合任务详情必须稳定返回中文报告，展示关联商品、触发原因、证据链、权限判断、生命周期、自动复盘周期和下一步。

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
→ /api/modules/todo 返回带 taskLifecycle 和 primaryTaskAction 的真实任务池
→ web_demo/modules/todo/page.js 只渲染当前动作 + 详情
→ task_report_service 为聚合任务生成中文详情报告
→ task_lifecycle_orchestrator_service 推进接收、提交材料、复核、自动复盘、RAG候选
→ RAG审核通过后，下一次任务生成自动召回经验卡
```

## V12.8.3 硬规则

```text
任务列表必须按时间顺序展示，左侧显示时间轴 / 序号 / 时效等级。
运营任务卡只能显示：接收 → 提交 → 详情。
总管任务卡处理复核；复核不出现在运营卡片。
复盘由系统自动生成周期，不作为运营任务卡按钮。
详情按钮常驻。
前端任务卡禁止直接读取 raw availableActions 渲染按钮。
前端任务卡必须读取 primaryTaskAction / visibleTaskActions。
聚合任务详情必须稳定返回中文报告，不能进入空白或英文 fallback。
详情报告必须包含 affectedProducts / taskLifecycle / actionAuthorization / recapCycles / nextStep。
店铺标签必须经过 store_tag_projection_service。
投放预算调整、活动报名、扩流测试不能因 actionType 一刀切主管审批。
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
/api/modules/todo                      带生命周期和单动作的任务队列来源
/api/modules/todo/lifecycle/summary    任务生命周期统计
/api/modules/todo/{id}/recap/complete  完成复盘并生成RAG候选
/api/modules/task-reports/tasks/{id}   聚合任务详情报告，支持 affectedProducts 和 taskLifecycle
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
