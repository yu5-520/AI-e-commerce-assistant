# Product Changelog

## v5.0.8 - 2026-06-22

### Product Decision
- 总览从技术状态页改成经营首页。
- 总览不再把完整 `DV_...` 数据版本号作为主视觉；技术版本只留在后端追溯字段。
- 报表导入后，总览自动展示最新导入、记录数、影响模块、商品数和任务数。
- 当前任务按紧急程度和截止时间排序，并用商品 / 风险 / 信号区分，不再显示三条完全一样的任务。

### Changed
- `src/services/dashboard_service.py` 新增产品化经营摘要：`latestImport`、`metrics`、`taskQueue`。
- `web_demo/modules/dashboard/page.js` 改为读取 `/api/modules/dashboard`，展示最新导入、经营指标和排序后的任务队列。
- `src/services/module_projection_service.py` 允许无店铺字段的导入行刷新当前账号投影，避免上传报表后运营端总览和商品栏不更新。
- `src/api/main.py` 和 `web_demo/index.html` 升级到 `5.0.8`。

### Product Boundary
- DataVersion 是追溯字段，不是首页主内容。
- 首页展示经营摘要，不展示工程代号。
- 当前任务列表按优先级、时限和风险域组织。

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
