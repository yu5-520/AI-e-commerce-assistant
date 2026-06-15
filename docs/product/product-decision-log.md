# 产品决策日志

## 2026-06-15：active docs 只描述当前可运行主线

### 背景

v1.0.1 后，代码、脚本和版本治理已经收敛到当前 ERP 经营单元产品主线，但产品文档中仍残留未来多页面蓝图、宽泛领域模型和旧验收命令。这些文档会误导后续 AI 或人工修改，把仓库重新拉回旧页面、旧 route 或旧 demo 结构。

### 决策

从 v1.0.2 开始，active docs 只描述当前可运行产品主线：

```text
src.api.main:app
↓
/api/business/*
↓
web_demo/index.html
↓
web_demo/app-v2.js
```

未来产品地图、未来多页面用户流程、宽泛领域模型不再作为当前 MVP 文档保留。需要规划未来能力时，必须新建明确带 `proposal` 或 `future` 标记的文档，不能混入当前验收文档。

### 删除

```text
docs/product/product-map.md
docs/product/user-flow.md
docs/product/domain-model.md
```

### 保留

```text
docs/product/CHANGELOG.md
docs/product/mvp-scope.md
docs/product/module-boundary.md
docs/product/product-decision-log.md
docs/product/product-structure-cleanup-log.md
```

### 新规则

```text
当前说明看 README.md
当前部署看 docs/server-deploy.md
当前产品边界看 docs/product/mvp-scope.md 和 docs/product/module-boundary.md
当前产品变化看 docs/product/CHANGELOG.md
当前工程变化看 versioning/CHANGELOG.md
```

---

## 2026-06-15：main 分支只保留当前产品主线

### 背景

仓库曾同时存在旧前端模板、旧 demo 接口、旧 CLI 入口、旧测试脚本和当前 ERP 经营单元产品链路。多套入口并存会导致服务器部署、AI 代码更新、README 说明和测试脚本反复拉回旧模板。

### 决策

从 v1.0.0 开始，main 分支只保留当前可运行产品主线：

```text
src/api/main.py
↓
/api/business/*
↓
web_demo/index.html
↓
web_demo/app-v2.js
```

旧版 demo、旧兼容 API、旧前端模板、旧 CLI 入口不再留在当前主分支。需要回看旧实现时，通过 Git commit 历史查看。

### 保留能力

```text
ERP / CRM Mock 数据
经营单元识别
循环频率策略
商品体检
竞品机会
上新建议
流量复盘
待确认动作
经营报告
审批记录
数据校验
系统状态
服务器部署
```

### 停止保留

```text
旧 web_demo/app.js
旧 /api/demo
旧 /api/products
旧 /api/customers
旧 /api/diagnosis
旧 /api/tasks
旧 /api/reports
旧 /api/evals
旧 /api/logs
旧 src.run_demo
旧 standalone eval runner
```

### 新规则

```text
结构级变更必须更新 versioning/CHANGELOG.md
版本号变更必须更新 versioning/VERSION.md
产品主线变化必须更新 docs/product/CHANGELOG.md
重大产品决策补充 docs/product/product-decision-log.md
结构清理补充 docs/product/product-structure-cleanup-log.md
测试脚本必须跟随当前 API 主线同步
```

---

## 2026-06-14：从简历展示仓库切回产品仓库

### 背景

此前仓库中存在较多简历、面试、HR 展示、阶段标记类文档，导致项目更像“求职展示材料”，而不是一个正在完成的产品。

### 决策

从本阶段开始，仓库文档层优先服务产品本体，只保留产品骨架、运行说明、API、日志和必要架构文档。
