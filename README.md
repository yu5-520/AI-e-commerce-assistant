# AI ERP 经营单元电商协同系统 MVP

> 当前版本：V5.0.5。详情报告已升级为经营路径任务草案：系统展示只读证据，运营补充现实变量并选择主路径，任务进入待办后等待下一轮数据复盘。

## 当前主链路

```text
报表模块导入数据表
↓
字段映射 / 数据校验 / 店铺归属 / 账号权限切片
↓
DataVersion 数据版本
↓
完整导入行持久化 imported_report_rows
↓
ModuleProjection：刷新商品、流量、报表、首页、经营单元摘要
↓
AlertEvent：系统规则生成预警事件
↓
模块 Agent：基于 ModuleProjection 生成只读证据和问题判断
↓
DecisionTaskDraft：共同动作 / 补充信息 / 经营路径 / 复盘指标
↓
运营补充现实变量并选择主路径
↓
统一任务池：派发 / 接收 / 提交 / 复核 / 归档
↓
下一轮数据复盘路径效果
↓
RAG Memory：复核后入库并在下一轮召回
```

核心规则：**数据导入能生成的内容不让运营重复填；Agent 能判断的内容不让运营重新分析；运营只补充系统不知道的现实变量；方案路径必须有经营取舍；任务进入待办后用下一轮数据复盘路径是否有效。**

## 关键目录

```text
src/api/main.py                              FastAPI 入口，版本 5.0.5
src/api/routes/modules/agents.py              Agent API，任务创建时写入路径选择和补充信息
src/services/action_plan_service.py           DecisionTaskDraft 合约
src/services/module_projection_service.py     导入数据到模块内容投影
src/services/module_task_service.py           统一任务池
web_demo/index.html                           前端入口，缓存号 v5.0.5
web_demo/decision-task.css                    决策任务草案布局
web_demo/modules/task-report/decision-runtime.js 详情报告决策草案运行层
```

## 常用接口

```text
GET  /api/health
GET  /api/system/db-status
POST /api/system/reset-runtime-data?confirm=true
POST /api/data/import/confirm
GET  /api/modules/product
GET  /api/modules/todo
GET  /api/modules/agents/{module}/{entity_id}
POST /api/modules/agents/{module}/{entity_id}/tasks
```
