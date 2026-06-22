# Product Changelog

## v5.0.7 - 2026-06-22

### Product Decision
- 路径选择卡改为“行动顺序优先”：路径标题和经营目标只是小标签，动作步骤是视觉重点。
- 复盘指标不再展示在路径卡里；待办提交时本来就要提供截图、链接、处理结果和数据支撑，复盘指标保留在后端 `reviewPlan` 和待办证据流。
- 报表上传确认后就是自动入库、自动刷新报表 / 总览 / 商品等模块；Agent 不再生成“确认入库”路径，只生成已入库后的数据质量修正任务。

### Changed
- `web_demo/modules/task-report/decision-runtime.js`：路径卡改为小标签 + 大动作步骤，不显示复盘列。
- `web_demo/decision-task.css`：新增 action-sequence-first 布局，步骤块成为主视觉。
- `src/services/action_plan_service.py`：`ACTION_PLAN_VERSION` 升级到 `5.0.7`；清空前端用 `commonActions`；报表异常路径改为字段补传修正、归属映射修正、版本回滚、异常标记观察。
- `src/api/routes/modules/agents.py`：Agent registry 升级到 `5.0.7`，说明路径标题是小标签，行动顺序是主展示。
- `src/api/main.py` 和 `web_demo/index.html` 升级到 `5.0.7`。

### Product Boundary
- 报表导入是确定性流程，不由 Agent 决定是否入库。
- Agent 负责入库后的数据质量复核、补传、归属修正和回滚建议。
- 运营选择的是行动顺序，不是阅读完整方案报告。

## v5.0.6 - 2026-06-22

### Product Decision
- 路径选择页只负责选择主路径和补充决策变量，不再展示不会随路径变化的小字和共同动作。
- 选择路径并确认加入任务清单后，任务默认进入处理中，不再二次接收。
- 待办页不再重复采集决策变量，改为提交执行证据、截图链接、成果和复盘指标。

### Changed
- `web_demo/modules/task-report/decision-runtime.js` 改为横向紧凑路径行，删除共同动作区和顶部固定说明。
- `web_demo/decision-task.css` 调整路径选择为横向行布局，并新增待办路径摘要样式。
- `src/api/routes/modules/agents.py` 创建路径任务时写入 `status=处理中`、`workflowStatus=处理中`、`autoAccepted=true`。
- `web_demo/modules/todo/page.js` 改为根据 `selectedDecisionPath`、`operatorSupplement` 和 `reviewPlan` 展示执行证据表单。
- `src/api/main.py` 和 `web_demo/index.html` 升级到 `5.0.6`。

### Product Boundary
- 详情页负责决策确认，待办页负责执行证明。
- 运营不需要再次接收自己刚确认的路径任务。
- 截图、链接、处理结果、复盘指标属于任务执行证据，不属于路径选择前置变量。

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
