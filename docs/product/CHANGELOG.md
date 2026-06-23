# Product Changelog

## v9.2.0 - 2026-06-24

### Product Decision
- V9.2 定位为后端主流程一致性版本，不新增前端主模块。
- 本次更新固定导入、数据版本、模块投影、预警、权重、任务、Agent、审批、回写、复盘和 RAG 候选之间的后端契约。
- V8 权重能力继续作为后端增强层补强经营单元、商品、任务详情、Agent 报告和日志复盘。

### Changed
- `README.md` 当前版本升级为 `V9.2.0`，加入 V9.2 Backend Flow Guard 主链路。
- `versioning/VERSION.md` 当前版本升级为 `v9.2.0`。
- `src/api/main.py`、`src/api/routes/health.py`、`src/api/routes/modules/agents.py` 统一升级到 `9.2.0`。
- 新增 `docs/V9_BACKEND_FLOW_CONSISTENCY.md`。
- 新增 `src/services/v92_backend_flow_service.py`。
- 新增 `/api/architecture/v9/backend-flow`。
- 新增 `scripts/check_backend_flow_consistency.py`，并接入 GitHub Actions。
- `web_demo/index.html` 前端资源缓存统一升级到 `9.2.0`。

### Product Boundary
- V9.2 只治理后端主流程契约，不新增前端主模块。
- `/api/modules` 仍是前端产品模块主入口；`/api/accounts` 仍是账号、角色、店铺归属和可见范围入口。
- `/api/architecture/v9/backend-flow` 只输出主流程契约，不处理具体经营动作。
- V9.3 才进入前端模块一致性，把权重摘要按套餐深度补强到原模块展示。

## v9.1.0 - 2026-06-24

### Product Decision
- V9.1 定位为仓库结构一致性版本，不新增前端主模块，不改变业务链路。
- 本次更新把仓库目录、文档入口、脚本职责、CI 检查和前端缓存统一到 V9.1，避免后续更新被旧 Demo 文件、旧入口和旧文档带偏。
- V9.1 为 V9.2 后端主流程一致性做准备：先让仓库主线清楚，再把 V8 权重能力接进导入、投影、任务、Agent 和复盘主链路。

### Changed
- `README.md` 当前版本升级为 `V9.1.0`，加入 V9.1 Repository Guard 主链路和 `docs/V9_REPOSITORY_CONSISTENCY.md` 文档入口。
- `versioning/VERSION.md` 当前版本升级为 `v9.1.0`。
- `src/api/main.py` 升级到 `9.1.0`。
- 新增 `docs/V9_REPOSITORY_CONSISTENCY.md`，明确目录职责、必需入口、禁止旧路径、文档职责、脚本职责和 CI 检查顺序。
- 新增 `scripts/check_repository_consistency.py`。
- `.github/workflows/runtime-smoke-test.yml` 新增 Repository consistency check。
- `web_demo/index.html` 前端资源缓存统一升级到 `9.1.0`。

### Product Boundary
- V9.1 只治理仓库结构，不引入新业务功能。
- 旧阶段入口不得回流到当前主干。
- `/api/modules` 仍是前端产品模块主入口；`/api/accounts` 仍是账号、角色、店铺归属和可见范围入口。
- V9.2 才进入后端主流程一致性，把权重能力更深接入报表导入后的自动链路。

## v9.0.0 - 2026-06-24

### Product Decision
- V9 定位为 SaaS 企业级一致性底座版本，不新增前端主模块，不继续扩展 V8 权重算法。
- V8 权重系统沉入后端能力层，用来补强经营单元、商品、任务详情、Agent 报告和复盘日志，而不是在前端堆新的“权重中心”主模块。
- 基础版、专业版、企业版按能力、RAG、算法、部署模式和审计深度做系统级隔离。

### Changed
- `README.md` 改为 V9 SaaS 企业级一致性底座入口。
- `versioning/VERSION.md` 当前版本升级为 `v9.0.0`。
- `src/api/main.py` 升级到 `9.0.0`，保留 `/api/modules` 与 `/api/accounts` 作为稳定产品入口。
- `scripts/check_version_governance.py` 改为优先读取 `API_VERSION`，避免版本治理脚本与 FastAPI 变量式版本声明冲突。
- 新增 `docs/V9_SAAS_CONSISTENCY_BASE.md`，定义仓库一致性、前端一致性、后端一致性、三层隔离一致性、RAG 隔离、权限审计、受托运维和测试验收节奏。

### Product Boundary
- 基础版只开放报表分析、商品问题识别、商品任务生成和共享脱敏 RAG。
- 专业版开放租户隔离 RAG、商品权重、店铺权重、平台趋势、活动趋势和 Agent 证据链增强。
- 企业版开放私有化部署、客户侧 RAG / 数据库、完整权重系统、受托运维、高层审批门控和审计留痕。
- `/api/modules` 保持前端产品主入口；`/api/accounts` 保持账号、角色、店铺归属和可见范围入口。

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
