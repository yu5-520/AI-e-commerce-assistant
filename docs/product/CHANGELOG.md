# Product Changelog

## v5.0.5 - 2026-06-21

### Product Decision
- V5.0.5 把详情报告从 Agent 工程报告改成经营路径任务草案。
- 导入数据生成只读证据和 Agent 判断；运营只补充系统不知道的现实变量，并选择主经营路径。
- 问题处理包、方案补充和人工确认不再作为运营端默认模块展示。

### Changed
- `src/services/action_plan_service.py` 输出 `readonlyEvidence`、`commonActions`、`supplementSchema`、`decisionPaths`、`recommendedPathId`、`reviewPlan`。
- `src/api/routes/modules/agents.py` 在创建任务时写入 `selectedPathId`、`operatorSupplement` 和 `reviewPlan`。
- 新增 `web_demo/modules/task-report/decision-runtime.js` 覆盖详情报告前端展示。
- 新增 `web_demo/decision-task.css` 放大任务草案、路径选择和补充信息输入区。
- `src/api/main.py` 和 `web_demo/index.html` 升级到 `5.0.5`。

### Product Boundary
- ActionPlan 仍是 Agent 内部工程包，默认不给运营端阅读。
- 方案路径必须有经营取舍：目标、动作、不做什么、复盘指标都不同。
- 运营补充的是供应链、预算、活动约束、替代 SKU 等现实变量，不重复录入系统已有数据。

## v5.0.4 - 2026-06-21

### Product Decision
- V5.0.4 清理最后一批老板端、总管端、经营单元页的演示盘面。
- 经营单元不再展示店铺权限配置和 Mock 接入状态；只有报表导入产生经营数据后才显示经营摘要。
- 总览页不再重复左侧功能栏，不再展示“模块入口”和工程解释小字。

### Changed
- `src/api/routes/modules/operating_unit.py` 改为读取 ModuleProjection、预警和任务统计；无导入数据时返回空状态。
- `web_demo/modules/operating-unit/page.js` 删除店铺组、Mock 接入、待接入系统等演示内容。
- `web_demo/modules/dashboard/page.js` 删除模块入口卡片和说明小字，只保留空状态或经营摘要。
- `web_demo/modules/manager/page.js` 删除 `baseTasks`、`operators`、`moduleSignals`、`recaps` 等前端硬编码数据，改为读取任务池和模块投影。
- `web_demo/modules/executive/page.js` 删除 `stores`、`people`、`supply`、`traffic`、`finance`、`retrospectives`、`auditIssues`、`nextTasks` 等老板端演示数据，改为读取导入数据和任务池。
- `web_demo/core/api-client.js` 的 `resetRuntimeData()` 会同步清理管理视角 localStorage。
- `src/api/main.py` 和 `web_demo/index.html` 升级到 `5.0.4`。

### Product Boundary
- 清的是托底经营数据，不是账号体系和模块导航。
- 店铺权限配置留在账号/权限体系里；经营单元页只展示导入数据后的经营结果。
- 老板端、总管端、运营端都必须遵循同一个空状态标准。
