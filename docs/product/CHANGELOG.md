# Product Changelog

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

## v5.0.3 - 2026-06-21

### Product Decision
- V5.0.3 解决“前端托底已清，但服务器 SQLite 旧导入数据仍被 ModuleProjection 读取”的残留问题。
- 产品运行态需要一个可控清空能力：清掉导入行、数据版本、预警、任务和日志，但保留产品模块、账号体系和代码骨架。

### Changed
- `src/services/system_service.py` 新增 V5 runtime reset：清空 `imported_report_rows`、`data_snapshots`、`metric_snapshots`、`alert_events`、任务状态、导入记录和运行日志。
- `src/api/main.py` 新增启动时一次性 legacy runtime cleanup；旧服务器数据库只在 V5.0.3 首次启动时自动清空一次，并写入 marker，后续重启不会反复清空新导入数据。
- `src/api/routes/system.py` 新增 `/api/system/reset-runtime-data` 和 `/api/system/reset-legacy-runtime-once`。
- `web_demo/core/api-client.js` 新增 `resetRuntimeData()`，清空后同步清理前端内存态。
- `web_demo/index.html` 资源缓存号升级到 `v=5.0.3`。

### Product Boundary
- 清的是运行态数据，不是模块功能。
- 一次性启动清理只为处理 V5 迁移前旧 SQLite 残留；新导入数据不会在每次重启时被清空。
- 后续手动清空必须调用 reset 接口并带确认参数。
