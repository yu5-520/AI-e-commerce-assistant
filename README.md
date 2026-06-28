# AI ERP 企业级电商经营 SaaS 底座

当前基线：**V12.8.0 任务生命周期闭环系统**。

V12.8 把任务系统从“任务列表 + 复盘候选 + RAG草案”升级为一条完整生命周期：生成任务 → 接收任务 → 提交处理材料 → 主管复核 → 生成自动复盘周期 → 复盘结束进入RAG候选 → 人工审核后写入RAG → RAG增强下一次任务生成。运营只提交事实和处理材料，系统负责复盘周期、后续指标读取、效果判断和RAG候选生成。

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
→ action_authorization_gate_service 判断账号权限、动作风险和审批路径
→ task_cluster_service 生成真实后端聚合任务
→ /api/modules/todo 返回带 taskLifecycle 的任务池
→ 运营接收任务
→ 运营提交处理材料 / evidence
→ 主管复核材料
→ task_lifecycle_orchestrator_service 生成自动复盘周期
→ task_recap_scheduler_service 按 T+1 / T+3 / T+7 完成复盘
→ rag_feedback_loop_service 生成RAG候选
→ RAG审核通过后，下一次任务生成自动召回经验卡
```

## V12.8 硬规则

```text
同一个 task_id 必须贯穿生成、接收、提交材料、复核、复盘和RAG候选。
运营不做ROI/GMV/销量预测，只提交客观材料。
系统按任务类型生成复盘周期：活动、素材/标题/主图、库存、投放、售后分别有不同回看窗口。
复盘必须读取后续事实表/报表指标，不让运营手填结果。
只有复盘完成、指标变化明确、人工审核通过的经验卡，才允许增强下一次任务生成。
pending_review 的RAG草案不能直接影响任务生成。
经营表现不等于权限权重，高ROI/高GMV不能触发高权重审批。
重复商品任务必须聚合成真实后端任务。
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
