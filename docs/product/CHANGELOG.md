# Product Changelog

## v5.0.1 - 2026-06-21

### Product Decision
- V5.0.1 修复流程链路断点：空系统不能被种子任务撑开；导入后模块内容必须读取完整数据行；报表详情必须走投影数据；报表任务创建不能因路由切换断开。

### Changed
- `src/services/module_task_service.py` 移除运行态 seed tasks / seed logs，系统初始任务池为空。
- 新增 `src/services/import_row_store_service.py`，保存完整 normalizedRows。
- `src/services/report_schema_service.py` 在确认导入后持久化完整数据行。
- `src/services/module_projection_service.py` 优先读取完整导入行，再 fallback 到历史 sampleRows。
- 新增 `src/api/routes/modules/report_v5.py`，报表模块走 projected report groups / details。
- `src/api/routes/modules/__init__.py` 切换到 V5 报表路由。

### Product Boundary
- 示例数据只能通过报表模块显式试跑，不再自动进入运行态。
- 首页、商品、流量、报表、待办都以导入数据和账号权限为准。

## v5.0.0 - 2026-06-21

### Product Decision
- V5 进入产品 Demo 操作系统阶段：保留原模块栏和模块功能，清除前端 MVP 托底业务内容。
- 首页不做导入入口，只作为产品化封面和经营摘要；没有导入数据时只显示暂无数据。
- 报表模块继续作为唯一数据入口；导入数据后，系统同时更新模块内容、生成预警、生成任务，并按账号权限切片。

### Changed
- `src/services/module_data_service.py` 清空运行态商品、竞品、上新、流量和报表详情托底数据，只保留空边界和报表模板。
- 新增 `src/services/module_projection_service.py`，把 DataVersion 快照投影成商品、流量和报表模块内容。
- `src/api/routes/modules/product.py` 改为从导入数据投影读取商品内容，并把任务绑定到商品模块和店铺权限。
- `src/api/routes/modules/traffic.py` 改为从订单导入数据投影读取流量承接内容，并把任务绑定到流量模块和店铺权限。
- `web_demo/modules/dashboard/page.js` 清除老板 / 总管 / 运营首页硬编码经营盘面，改成“暂无数据 / 经营摘要 / 模块入口”。
- `README.md` 和 `versioning/VERSION.md` 更新为 V5 主链路。

### Product Boundary
- 清托底数据，不清模块功能。
- 导入数据不只是生成任务，还要更新对应模块内容。
- 数据表、预警、任务都必须按店铺和账号权限切片。
- Agent 仍只做任务增强、执行说明、复核重点和回流草案，不越权执行真实经营动作。
