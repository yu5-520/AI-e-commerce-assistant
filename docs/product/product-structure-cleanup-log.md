# 产品结构清理日志

## 2026-06-15：v1.0.5 后端接口契约修复

### 修复目标

让产品业务接口、审批接口、系统接口和 smoke test 形成闭环，避免“状态写入了，但产品接口看不到”的断层。

### 本轮修复内容

```text
/api/business/actions
/api/approvals/{task_id}/approve
/api/approvals/{task_id}/reject
/api/health
/api/system/clear-runtime-data
scripts/smoke_test_api.py
```

### 本轮同步修正

```text
src/api/routes/business.py
src/api/routes/health.py
src/api/routes/system.py
src/api/main.py
scripts/smoke_test_api.py
versioning/VERSION.md
versioning/CHANGELOG.md
docs/product/CHANGELOG.md
```

### 新规则

- 审批状态写入后，必须能从 `/api/business/actions` 读回。
- 前端不应该为了知道动作状态，再额外读取低层审批记录。
- `/api/health` 必须返回当前应用版本。
- 当前清理接口优先使用 `/api/system/clear-runtime-data`，旧 `/api/system/clear-demo-data` 只作为兼容别名保留。
- API smoke test 必须覆盖产品接口状态回写，而不是只测试低层写入接口。

---

## 2026-06-15：v1.0.4 前端 UI 主线清理

### 清理目标

将前端从“raw workflow 渲染器”收敛为“产品 API UI”，让页面结构、API 调用和样式组件都服务当前 `/api/business/*` 主线。

### 当前前端主链路

```text
web_demo/index.html
↓
web_demo/app-v2.js
↓
/api/business/today
/api/business/operating-unit
/api/business/data-health
/api/business/products
/api/business/competitors
/api/business/listing
/api/business/traffic
/api/business/actions
/api/business/report
```

### 本轮删除内容

```text
web_demo/data-import.css
```

删除原因：该样式文件主要服务旧的数据导入后台表格组件，当前单页经营工作台已经不再使用这些独立组件。

### 本轮同步修正

```text
web_demo/index.html
web_demo/app-v2.js
src/api/main.py
scripts/check_version_governance.py
versioning/VERSION.md
versioning/CHANGELOG.md
docs/product/CHANGELOG.md
```

### 新规则

- 前端页面优先使用 productized `/api/business/*` 接口。
- raw workflow 只作为 fallback 或调试数据来源，不作为 UI 主契约。
- 未被当前页面使用的独立样式组件应删除。
- 被删除的前端组件必须加入版本治理检查，避免后续回流。

---

## 2026-06-15：v1.0.3 模块链记忆清理

### 清理目标

将仓库模块链从旧的独立模块注册表，收敛到当前真实运行主线。

### 当前保留主链路

```text
src.api.main:app
↓
/api/business/*
↓
src/services/business_view_service.py
↓
src/workflow/mock_workflow.py
↓
operating_unit / scheduler / category / competitor / listing / traffic_test / operating_loop
↓
src/reports/generate_operating_report.py
```

### 本轮删除内容

```text
runtime/module_chain.json
modules/platforms/
modules/operation_modes/
modules/frontend/
src/reports/generate_demo_report.py
```

### 本轮同步修正

```text
src/reports/generate_operating_report.py
src/workflow/mock_workflow.py
src/services/business_view_service.py
src/api/main.py
scripts/check_version_governance.py
versioning/VERSION.md
versioning/CHANGELOG.md
docs/product/CHANGELOG.md
```

### 新规则

- active trunk 不保留旧模块注册表。
- 当前模块链以真实运行入口和 import 链为准。
- 报告输出使用 `operating_report.md`，不再使用旧 demo 报告命名。
- 旧模块实验从 Git 历史查，不放在当前 runtime / modules 目录里。

---

## 2026-06-15：v1.0.2 文档主干清理

### 清理目标

将产品文档从“未来多页面蓝图 / 旧对象模型混杂”收敛为“当前 v1.x 可运行产品主线”。

### 本轮保留文档

```text
README.md
docs/server-deploy.md
versioning/VERSION.md
versioning/CHANGELOG.md
docs/product/README.md
docs/product/CHANGELOG.md
docs/product/mvp-scope.md
docs/product/module-boundary.md
docs/product/product-decision-log.md
docs/product/product-structure-cleanup-log.md
```

### 本轮删除文档

```text
docs/product/product-map.md
docs/product/user-flow.md
docs/product/domain-model.md
```

删除原因：这些文档描述未来多页面产品结构或宽泛领域对象，容易把当前 MVP 拉回已从 active trunk 移除的旧页面 / 旧接口假设。

### 本轮同步修正

```text
README.md
docs/product/README.md
docs/product/mvp-scope.md
docs/product/module-boundary.md
scripts/check_version_governance.py
src/api/main.py
versioning/VERSION.md
versioning/CHANGELOG.md
docs/product/CHANGELOG.md
```

### 新规则

- active docs 只描述当前可运行主线。
- 未来产品地图、未来多页面用户流、未来领域模型不得混入当前 MVP 文档。
- 如需恢复规划，应创建明确带 `proposal` 或 `future` 标记的新文档。
- 版本治理脚本需要检查 active docs 是否重新出现旧 demo 命令、旧 route 验收或旧 Agent 链路。

---

## 2026-06-15：v1.0.0 主分支产品主线清理

### 清理目标

将仓库从“多版本并存 / 旧模板残留”收敛为“当前产品主线唯一可运行”。

### 本轮保留主链路

```text
src/api/main.py
↓
/api/business/*
↓
web_demo/index.html
↓
web_demo/app-v2.js
```

### 本轮删除内容

```text
web_demo/app.js
src/api/routes/demo.py
src/api/routes/products.py
src/api/routes/customers.py
src/api/routes/diagnosis.py
src/api/routes/tasks.py
src/api/routes/reports.py
src/api/routes/evals.py
src/api/routes/logs.py
src/run_demo.py
src/services/workflow_service.py
src/services/eval_service.py
evals/run_evals.py
```

### 本轮同步修正

```text
README.md
versioning/CHANGELOG.md
versioning/VERSION.md
scripts/smoke_test_api.py
.gitignore
```

### 清理原则

- main 分支只保留当前产品主线。
- 旧模板、旧 demo、旧兼容接口不再留在当前主分支。
- 历史版本通过 Git commit 保留，不通过根目录残留保留。
- 后续任何架构级清理必须同步更新 `versioning/` 和 `docs/product/` 日志。

### 风险说明

- 线上服务器需要重新 `git pull` 并执行部署脚本，否则页面仍可能来自旧进程或旧代码。
- 若还有文档引用已删除接口，应视为过期文档，继续更新或删除。
