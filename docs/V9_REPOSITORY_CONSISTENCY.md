# V9.1 仓库结构一致性

V9.1 是仓库结构一致性版本。

V9.0 先统一了 SaaS 企业级一致性底座的产品主线；V9.1 进一步把仓库目录、文档入口、脚本职责、CI 检查和版本治理固定下来，避免后续 AI 或人工更新被旧 Demo 文件、旧文档和旧入口带偏。

## 1. V9.1 目标

```text
仓库像一个长期产品，而不是阶段性补丁集合。
README 是唯一产品入口。
versioning/VERSION.md 是唯一版本源。
docs 按职责分层。
scripts 按治理 / 验收 / 部署分工。
CI 能拦住旧入口、旧路径和版本漂移。
```

## 2. 目录职责

```text
.github/workflows/
  GitHub Actions CI、版本治理、仓库治理、运行 smoke test。

docs/
  产品主线、架构、数据库、部署、版本、V8/V9 专项文档。

docs/product/
  产品决策、产品边界、产品更新记录。

src/api/
  FastAPI 入口、路由注册、产品 API 暴露层。

src/core/
  UserContext、租户、组织、角色和数据范围等核心上下文。

src/services/
  业务服务层：模块投影、任务、权重、RAG、审计、Worker、审批等。

src/repositories/
  Demo Runtime 与 Repository 抽象，承接 SQLite-first / PostgreSQL mirror 过渡。

src/middleware/
  安全头、限流、请求级保护。

web_demo/
  前端 Demo 壳、模块页面、样式和浏览器端 API 客户端。

scripts/
  治理脚本、smoke test、部署检查脚本。

versioning/
  唯一版本源和技术更新记录。
```

## 3. 当前必需入口

```text
README.md
versioning/VERSION.md
versioning/CHANGELOG.md
docs/CHANGELOG.md
docs/product/CHANGELOG.md
docs/V9_SAAS_CONSISTENCY_BASE.md
docs/V9_REPOSITORY_CONSISTENCY.md
docs/V8_WEIGHT_SYSTEM.md
docs/P0_SAAS_ARCHITECTURE.md
docs/POSTGRESQL_ALEMBIC.md
src/api/main.py
web_demo/index.html
.github/workflows/runtime-smoke-test.yml
scripts/check_version_governance.py
scripts/check_repository_consistency.py
scripts/smoke_test_runtime.py
scripts/smoke_test_api.py
```

## 4. 当前稳定 API 主入口

```text
/api/modules       前端产品模块主入口
/api/accounts      账号、角色、店铺归属和可见范围
/api/data          报表导入、DataVersion、预警、回滚、Demo 删除
/api/architecture  P0 / V7 / V8 / V9 架构状态与权重能力接口
/api/system        系统状态、Repository、PostgreSQL cutover check、运行态清理
/api/worker/jobs   Worker 队列脚手架和异步任务状态
/api/audit         审计与技术日志入口
```

V9.1 不重命名这些入口，不迁移业务路由，不新增前端主模块。

## 5. 禁止回流的旧路径

```text
backend/server.py
src/run_demo.py
src/services/workflow_service.py
src/services/eval_service.py
evals/run_evals.py
web_demo/app.js
web_demo/app-v2.js
web_demo/data-import.css
scripts/material_observer.py
agents/material_observer_agent.py
agents/registry.py
runtime/agent_registry.json
runtime/module_chain.json
modules/platforms
modules/operation_modes
modules/frontend
```

这些路径属于旧阶段或旧架构残留。如果未来需要同类能力，必须接入当前 V9 主目录和主流程，而不是恢复旧入口。

## 6. 文档职责边界

```text
README.md
  只写项目定位、当前主链路、三层交付模型、入口和当前状态。

docs/V9_SAAS_CONSISTENCY_BASE.md
  写 SaaS 企业级一致性底座：前端、后端、三层隔离、RAG、权限、部署、测试。

docs/V9_REPOSITORY_CONSISTENCY.md
  写仓库结构、目录职责、必需入口、禁止旧路径、CI 检查规则。

docs/V8_WEIGHT_SYSTEM.md
  写 V8 权重数据波动任务系统。

docs/P0_SAAS_ARCHITECTURE.md
  写 P0 SaaS 架构底线。

docs/POSTGRESQL_ALEMBIC.md
  写数据库、Repository、Alembic、主写切换前检查。

docs/CHANGELOG.md
  写总版本记录。

docs/product/CHANGELOG.md
  写产品决策、产品边界、模块体验变化。

versioning/VERSION.md
  写唯一当前版本与压缩版历史。

versioning/CHANGELOG.md
  写技术更新记录。
```

## 7. 脚本职责边界

```text
scripts/check_version_governance.py
  检查 VERSION、main.py、CHANGELOG、workflow 与旧入口。

scripts/check_repository_consistency.py
  检查 V9.1 仓库结构、必需目录、必需文件、README 入口、workflow 入口和前端缓存版本。

scripts/smoke_test_runtime.py
  检查当前 runtime 工作流、Mock 数据、业务视图和基础闭环。

scripts/smoke_test_api.py
  检查产品 API、LLM Gateway、Agent、任务生命周期和模块接口。
```

## 8. CI 检查顺序

```text
1. Python syntax check
2. Version governance check
3. Repository consistency check
4. Runtime workflow smoke test
5. Product API smoke test
```

V9.1 新增 Repository consistency check，用于防止：

```text
版本源不一致
README 漂移
前端缓存版本不一致
旧 Demo 入口回流
必需文档缺失
必需脚本缺失
workflow 忘记跑治理脚本
```

## 9. 后续 V9.2 接口

V9.1 不强行改业务链路。V9.2 才开始做后端主流程一致性：

```text
报表导入
↓
ModuleProjection
↓
WeightSignal
↓
DecisionTask
↓
AgentReport
↓
ApprovalFlow
↓
ExecutionFeedback
↓
ReviewLog
↓
RagMemoryCandidate
```

V9.1 只保证仓库主线清楚，避免 V9.2 接主流程时踩旧入口和旧文档。

## 10. Definition of Done

```text
Current Version = v9.1.0。
FastAPI API_VERSION = 9.1.0。
README 声明 V9.1 仓库一致性。
web_demo/index.html asset cache = 9.1.0。
新增 docs/V9_REPOSITORY_CONSISTENCY.md。
新增 scripts/check_repository_consistency.py。
GitHub Actions 运行 repository consistency check。
旧路径不会回流。
必需文档和必需脚本被 CI 检查。
```
