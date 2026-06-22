# AI ERP 经营单元电商协同系统 MVP

> 当前版本：V5.0.7。详情页路径卡改为行动顺序优先：路径标题和经营目标只是小标签，行动步骤是主视觉；复盘指标留在待办提交和后端复盘链路。报表确认导入后自动入库并刷新报表、总览和商品等模块，Agent 只处理入库后的数据质量修正任务。

## 当前主链路

```text
报表模块导入数据表
↓
字段映射 / 数据校验 / 店铺归属 / 账号权限切片
↓
确认导入后自动入库
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
DecisionTaskDraft：补充信息 / 经营路径 / 行动顺序
↓
运营补充现实变量并选择行动顺序
↓
任务默认进入处理中
↓
待办页提交执行证据、截图链接和成果
↓
总管复核 / 下一轮数据复盘路径效果
↓
RAG Memory：复核后入库并在下一轮召回
```

核心规则：**数据导入能生成的内容不让运营重复填；报表确认导入就是自动入库，不由 Agent 决定是否入库；路径卡只展示行动顺序，不展示复盘报告；待办只提交执行证据和成果。**

## 关键目录

```text
src/api/main.py                              FastAPI 入口，版本 5.0.7
src/api/routes/modules/agents.py              Agent API，路径任务默认进入处理中
src/services/action_plan_service.py           DecisionTaskDraft / ActionPlan 合约
src/services/module_projection_service.py     导入数据到模块内容投影
src/services/module_task_service.py           统一任务池
web_demo/index.html                           前端入口，缓存号 v5.0.7
web_demo/decision-task.css                    行动顺序优先路径卡 / 待办路径摘要
web_demo/modules/task-report/decision-runtime.js 详情报告路径选择运行层
web_demo/modules/todo/page.js                 待办执行证据提交页
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
