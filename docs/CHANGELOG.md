# CHANGELOG

本文件记录版本变化。README 只保留项目入口；V9 起，企业级一致性底座、仓库结构一致性、数据库迁移、P0 架构、V8 权重系统分别进入独立文档。

## V9.1.0

仓库结构一致性：

- `versioning/VERSION.md` 统一当前版本为 `v9.1.0`。
- `src/api/main.py` 升级到 `9.1.0`，描述为 V9.1 repository consistency baseline。
- 新增 `docs/V9_REPOSITORY_CONSISTENCY.md`，定义目录职责、必需入口、禁止旧路径、文档职责、脚本职责和 CI 检查顺序。
- 新增 `scripts/check_repository_consistency.py`，检查 V9.1 必需目录、必需文件、README 入口、workflow 入口、前端缓存版本和旧路径回流。
- `.github/workflows/runtime-smoke-test.yml` 新增 Repository consistency check，并把新脚本加入 Python syntax check。
- `scripts/check_version_governance.py` 扩展 active docs 与 required workflow refs，要求 workflow 跑仓库一致性检查。
- `web_demo/index.html` 前端资源缓存统一升级到 `9.1.0`。
- README 更新为 V9.1 仓库结构一致性入口，并加入 `docs/V9_REPOSITORY_CONSISTENCY.md` 文档入口。

## V9.0.0

SaaS 企业级一致性底座：

- README 从 V5 PostgreSQL mirror 入口升级为 V9 SaaS 企业级一致性底座入口。
- `versioning/VERSION.md` 统一当前版本为 `v9.0.0`。
- `src/api/main.py` 升级到 `9.0.0`，保持 `/api/modules`、`/api/accounts`、`/api/data`、`/api/architecture`、`/api/system` 等主入口。
- 新增 `docs/V9_SAAS_CONSISTENCY_BASE.md`，定义仓库一致性、前端一致性、后端一致性、三层套餐隔离、RAG 隔离、权限审计、受托运维、部署模式和测试验收节奏。
- `scripts/check_version_governance.py` 改为优先识别 `API_VERSION = "X.Y.Z"`，避免版本治理脚本与变量式 FastAPI 版本声明冲突。
- V9 明确规则：不新增前端主模块，不继续扩展 V8 算法；V8 权重能力作为后端增强层补强经营单元、商品、任务、Agent 证据链和复盘日志。

## V5.4.0

文档治理：

- README 精简为项目入口和演示路径。
- 新增 `docs/CHANGELOG.md` 作为版本记录入口。
- PostgreSQL 文档保留数据库、Repository、迁移、主写切换检查。
- P0 架构状态继续由 `/api/architecture/p0` 和 `src/services/p0_architecture_service.py` 输出。

## V5.3.9

PostgreSQL 主写切换前检查清单：

- 新增 `src/services/postgres_cutover_check_service.py`。
- 新增 `GET /api/system/postgres-cutover-check`。
- 系统状态页展示 `pass / warn / blocked`。
- 检查项覆盖连接、Alembic、Mirror、Demo 回退、身份边界和回滚策略。

## V5.3.8

Mirror 公共控制层：

- 新增 `src/services/repository_mirror_base_service.py`。
- 统一 `repository_mode / skipped / failed / run_mirror / mirror_summary`。
- Task、ImportJob、WorkerJob、AuditLog、TechLog、ProjectionJob、DataVersion、AlertEvent mirror 服务接入公共层。

## V5.3.7

前端系统状态页：

- 新增 `web_demo/modules/system-status/page.js`。
- 新增 `web_demo/system-status.css`。
- 系统状态页读取 `/api/system/security`、`/api/system/repositories`、`/api/architecture/p0`。
- 导航中新增“系统状态”。

## V5.3.6

DataVersion / AlertEvent 写路径 mirror：

- 新增 `src/services/data_alert_repository_mirror_service.py`。
- ImportJob 完成后从导入结果收集数据版本和预警事件。
- 返回 `productionMirror.dataAlert`。

## V5.3.5

ProjectionJob mirror + 数据模型补齐：

- 新增 `src/db/projection_repositories.py`。
- 新增 `src/services/projection_repository_mirror_service.py`。
- 新增 DataVersion / AlertEvent 生产模型。
- 新增 Alembic 增量迁移 `20260623_535_data_version_alert_event.py`。

## V5.3.4

AuditLog / TechLog hybrid mirror：

- 新增 `src/services/audit_tech_repository_mirror_service.py`。
- `write_audit_log` 和 `write_tech_log` 返回 `productionMirror`。
- 补齐 `ProductionAuditRepository.upsert` 和 `ProductionTechLogRepository.upsert`。

## V5.3.3

ImportJob / WorkerJob hybrid mirror：

- 新增 `src/services/import_worker_repository_mirror_service.py`。
- ImportJob 创建、完成、失败支持 mirror。
- WorkerJob enqueue、claim、complete、fail、retry 支持 mirror。

## V5.3.2

TaskRepository hybrid mirror：

- 任务创建、流转、重置支持 SQLite-first PostgreSQL mirror。
- 保留 SQLite Demo 主链路。

## V5.3.1

SQLAlchemy Repository 过渡层：

- 新增 Production Repository。
- 新增 `DB_REPOSITORY_MODE=sqlite|hybrid|postgres`。
- 新增 `/api/system/repositories`。

## V5.3.0

PostgreSQL / Alembic 生产数据模型骨架：

- 新增 `src/db/base.py`、`src/db/session.py`、`src/db/models.py`。
- 新增 Alembic 初始迁移。
- 当前 SQLite Demo 运行链路不切换。
