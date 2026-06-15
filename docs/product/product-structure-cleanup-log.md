# 产品结构清理日志

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

---

## 2026-06-14：产品仓库结构清理

## 清理目标

将仓库从“求职展示导向”收敛为“产品完成导向”。

## 本轮新增产品骨架文档

```text
docs/product/README.md
docs/product/product-map.md
docs/product/domain-model.md
docs/product/user-flow.md
docs/product/module-boundary.md
docs/product/mvp-scope.md
docs/product/product-decision-log.md
```

## 本轮原则

- 不新增简历、面试、HR、BOSS 类文档。
- 不继续堆解释型包装材料。
- 产品文档只服务用户、场景、模块、对象、流程、边界和 MVP。
- 后续围绕产品结构继续重构 API 和前端。

## 下一步建议

```text
1. 拆分 FastAPI routes
2. 按 product-map 重构前端信息架构
3. 增加 SQLite / JSON 日志持久化
4. 增加 Data Import 页面和 API
5. 从 Demo Workflow 逐步拆成产品级 workflows
```
