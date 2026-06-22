# Product Changelog

## v5.0.9 - 2026-06-22

### Product Decision
- Demo 阶段允许删除单条导入记录，避免反复测试上传后记录一直叠加。
- 删除记录是测试清理，不是正式业务回滚；正式留痕仍用回滚功能。
- 删除一条导入记录后，总览、报表、商品、预警和任务池会跟随刷新。

### Changed
- `src/services/data_version_service.py` 新增 `delete_data_version()`，清理 data_snapshots、metric_snapshots、alert_events、imported_report_rows、data_version_rollbacks，并归档关联活跃任务。
- `src/api/routes/data_import.py` 新增 `DELETE /api/data/versions/{data_version}?confirm=true`。
- `web_demo/modules/report/report-runtime.js` 在导入记录行和数据版本详情页新增“删除 / 删除记录”按钮。
- `src/api/main.py` 允许 `DELETE` 请求，并升级到 `5.0.9`。
- `web_demo/index.html` 前端缓存升级到 `5.0.9`。

### Product Boundary
- 删除用于 Demo 测试清理，避免旧导入版本影响测试。
- 回滚用于正式留痕和任务策略处理。
- 删除记录会移除该版本预警和导入行，关联任务会从活跃队列归档。

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
