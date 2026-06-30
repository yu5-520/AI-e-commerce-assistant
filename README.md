# AI ERP 企业级电商经营 SaaS 底座

当前基线：**V14.8.1 商品事实恢复与数据缺口任务流修复版**。

V14.8.1 保留 V14.8 的“前端读模型 / 后台计算隔离”设计，但修复两处实测断点：商品详情页只读到少量摘要、指标事实为空；Agent 判断完成后没有稳定转换为任务快照和任务池。现在商品页会合并 `frontend_product_view` 与运行态商品投影，恢复 SKU、商品定位、指标事实、流量事实和数据缺口摘要；Agent 对关键字段缺失不再硬拦截，而是生成正式“商品数据核验任务”。

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
→ system_product_snapshot_station 生成商品分层快照
→ product_signal_snapshot_station 生成商品全量包 fullProductBundle
→ task_signal_station 将全量包进入队列
→ rag_context_station 给出波动边界
→ agent_judgment_station_v1481_service 逐商品判断
→ 成熟经营判断直接生成 V11.8 SOP task snapshot
→ 数据缺口判断直接生成 商品数据核验 task snapshot
→ task_pool_station 进入任务池
→ /api/view/tasks 与 /api/modules/todo 读取任务池 / 生命周期投影
→ task_lifecycle_state_machine_service 自动接收权限内任务
→ 前端任务卡显示 提交 + 详情
→ 运营提交材料
→ 需复核任务进入总管复核；无需复核任务进入等待自动复盘
→ task_report_service 从同一生命周期投影生成中文详情报告
→ task_state_machine_service 镜像任务、事件、日志到 SQLite
```

## V14.8.1 硬规则

```text
前端页面切换只能读 /api/view/* 或产品桥接读模型，不得触发后台计算。
商品页必须展示商品是谁、在哪个店铺、SKU/ERP/系统编码、指标事实、流量事实、任务摘要。
顶部 KPI 有数据时，指标事实区不得整块显示“未入库”。
Agent 判断中的缺字段不得阻断任务流水线。
关键字段缺失必须生成“商品数据核验任务”，进入 task_snapshot 和 task_pool。
成熟经营判断必须逐条流式入池，不等待整个 worker 批次结束。
任务生成 0 个时必须保留原因，不能只显示“已同步”。
正式任务仍使用 V11.8 SOP 包，生命周期仍由任务状态机处理。
```

## 当前主 API

```text
/                                      web_demo 前端入口
/api/health                            健康检查
/api/view/products                     前端商品读模型
/api/modules/product                   商品页桥接读模型：frontend_product_view + product projection
/api/view/tasks                        前端任务读模型
/api/modules/todo                      带生命周期和单动作的任务队列来源
/api/modules/todo/lifecycle/summary    任务生命周期统计
/api/modules/todo/{id}/accept          幂等接收：已处理则返回当前投影
/api/modules/todo/{id}/submit          提交材料：进入待复核或等待自动复盘
/api/modules/todo/{id}/review          复核：通过后生成自动复盘周期，退回后补充材料
/api/modules/todo/{id}/recap/complete  完成复盘并生成RAG候选
/api/modules/task-reports/tasks/{id}   Repository-aware 生命周期详情报告
/api/system/runtime-diagnostics        运行态诊断
/api/system/reset-runtime-data          清空演示运行态
```

## 部署入口

```bash
bash scripts/deploy_fast.sh
```
