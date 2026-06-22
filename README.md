# AI ERP 经营单元电商协同系统 MVP

> 当前版本：V5.0.9。Demo 阶段新增单条导入记录删除能力，避免反复上传报表后记录、预警和任务一直叠加影响测试。

## 当前主链路

```text
报表模块导入数据表
↓
字段映射 / 数据校验 / 店铺归属 / 账号权限切片
↓
确认导入后自动入库
↓
DataVersion 数据版本进入后端追溯
↓
完整导入行持久化 imported_report_rows
↓
ModuleProjection：刷新商品、流量、报表、首页、经营单元摘要
↓
DashboardSummary：最新导入 / 报表记录 / 商品数量 / 任务队列
↓
AlertEvent：系统规则生成预警事件
↓
模块 Agent：基于 ModuleProjection 生成只读证据和问题判断
↓
DecisionTaskDraft：补充信息 / 经营路径 / 行动顺序
↓
任务默认进入处理中，待办页提交执行证据和成果
↓
总管复核 / 下一轮数据复盘路径效果
↓
RAG Memory：复核后入库并在下一轮召回
```

Demo 清理链路：**导入记录删除 → 清除该版本 imported_report_rows / data_snapshots / metric_snapshots / alert_events / rollback 记录 → 关联活跃任务归档 → 报表、总览、商品、待办刷新。**

核心规则：**首页展示经营摘要，不展示工程代号；报表确认导入就是自动入库；商品、报表、总览必须随导入同步刷新；当前任务按优先级、截止时间和风险域排序；Demo 阶段可删除单条导入记录。**

## 关键目录

```text
src/api/main.py                              FastAPI 入口，版本 5.0.9
src/services/data_version_service.py          数据版本回滚 / Demo 删除
src/api/routes/data_import.py                 导入记录删除接口
src/services/dashboard_service.py             总览经营摘要 / 任务排序
src/services/module_projection_service.py      导入数据到模块内容投影
src/api/routes/modules/dashboard.py            总览 API
src/api/routes/modules/agents.py               Agent API，路径任务默认进入处理中
src/services/action_plan_service.py            DecisionTaskDraft / ActionPlan 合约
src/services/module_task_service.py            统一任务池
web_demo/index.html                            前端入口，缓存号 v5.0.9
web_demo/modules/report/report-runtime.js      报表导入 / 回滚 / 删除记录
web_demo/modules/dashboard/page.js             产品化总览页
web_demo/decision-task.css                     行动顺序优先路径卡 / 待办路径摘要
web_demo/modules/task-report/decision-runtime.js 详情报告路径选择运行层
web_demo/modules/todo/page.js                  待办执行证据提交页
```

## 常用接口

```text
GET    /api/health
GET    /api/system/db-status
POST   /api/system/reset-runtime-data?confirm=true
POST   /api/data/import/confirm
DELETE /api/data/versions/{data_version}?confirm=true
GET    /api/modules/dashboard
GET    /api/modules/product
GET    /api/modules/todo
GET    /api/modules/agents/{module}/{entity_id}
POST   /api/modules/agents/{module}/{entity_id}/tasks
```
