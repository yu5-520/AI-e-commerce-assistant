# docs/archive

这里存放历史归档文档。

## 归档规则

```text
历史归档，不作为当前架构依据。
旧版本 PRD、阶段复盘、V1-V11 过程说明、废弃部署说明、旧 UI 方案都必须放在这里或从仓库删除。
当前 AI 修改仓库时，不允许引用本目录内容作为当前执行链路。
```

## 当前执行文档

当前执行文档只允许使用：

```text
README.md
VERSION.md
versioning/VERSION.md
docs/API_CONTRACT.md
docs/MODULE_CHAIN.md
docs/PRODUCT_ARCHITECTURE.md
docs/DATA_TASK_LIFECYCLE.md
docs/V12_REPORT_GATEWAY.md
docs/DEPLOYMENT_RUNBOOK.md
docs/POSTGRESQL_CUTOVER.md
scripts/verify_release.py
scripts/check_repo_hygiene.py
```

## V12.3 边界

```text
如果文档描述的是旧前端、旧路由、旧部署、旧任务链或旧商品档案阶段，只能归档，不能放在 docs 根目录影响当前链路。
如果文档需要继续作为当前依据，必须明确写入 V12.3 当前事实链路：Sheet → Block → Fact → Gap → Staging → EvidenceGate。
```
