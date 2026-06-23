# AI ERP 企业级电商经营 SaaS 底座

> 当前版本：V9.2.0。V9.2 是后端主流程一致性版本：在 V9.0 SaaS 企业级一致性底座和 V9.1 仓库结构一致性上，固定 ImportJob → DataVersion → RawRows → ModuleProjection → AlertEvent → WeightSignal → DecisionTask → AgentReport → ApprovalFlow → ExecutionFeedback → ReviewLog → RagMemoryCandidate 的后端契约。

## 项目定位

AI ERP 企业级电商经营 SaaS 底座是一个面向货架电商运营的 AI 经营系统。系统以报表导入、经营预警、任务流转、Agent 证据链、店铺 / 商品权重、RAG 经验沉淀、审计留痕和企业级部署治理为主线。

V8 完成权重数据波动任务系统：商品权重、店铺权重、周期比较、RAG 标准线、联动比对、交叉验证、审批、执行回写和复盘沉淀。

V9 的目标不是继续堆功能，而是把这些能力稳定接入现有产品模块，形成可商业化、可租户隔离、可私有化部署、可审计、可运维、可长期迭代的 SaaS 企业级架构底座。

核心规则：**前端模块保持稳定；后端能力统一整合；套餐能力按层隔离；RAG 与数据按命名空间隔离；关键动作必须审批、留痕、可追溯；仓库入口、文档、脚本、CI 和后端主流程必须指向同一主线。**

## 当前主链路

```text
Browser / Client
↓
Nginx / FastAPI
↓
/api/modules       经营前端模块：总览、经营单元、商品、报表、待办、日志、详情页
/api/accounts      账号、角色、店铺归属和可见范围
/api/data          报表导入、DataVersion、预警、回滚、Demo 删除
/api/architecture  P0 / V7 / V8 / V9 架构状态与权重能力接口
/api/system        系统状态、Repository、PostgreSQL cutover check、运行态清理
/api/worker/jobs   Worker 队列脚手架和异步任务状态
↓
SQLite Demo Runtime：核心演示写路径先稳定
↓
PostgreSQL Mirror / Cutover Check：生产主写切换前只读检查，不自动切换
↓
V8 Weight Runtime：店铺 / 商品 / 运营权重计算、交叉验证、审批、执行回写、复盘
↓
V9 Consistency Baseline：套餐隔离、RAG 隔离、权限审计、部署模式、测试验收统一
↓
V9.1 Repository Guard：目录、文档、脚本、workflow、前端缓存版本统一检查
↓
V9.2 Backend Flow Guard：导入、投影、权重、任务、Agent、审批、执行、复盘、RAG 候选主流程检查
```

## V9.2 后端主流程

```text
ImportJob
↓
DataVersion
↓
RawRows
↓
ModuleProjection
↓
AlertEvent
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

V9.2 新增架构可视入口：

```text
/api/architecture/v9/backend-flow
```

## 三层交付模型

```text
基础版 / Starter
- 月费
- 基础报表整理
- 商品问题分析
- 商品任务生成
- 共享脱敏 RAG
- 不开放商品 / 店铺权重波动算法

专业版 / Professional
- 年费
- 租户隔离数据与 RAG
- 商品权重算法
- 店铺权重算法
- 平台趋势 / 活动趋势
- Agent 任务证据链增强
- RAG 数据与模板按次维护

企业版 / Enterprise
- 私有化部署 + 一次性部署费 + 年费 + 运维服务
- 部署到客户公司服务器或客户云环境
- RAG 与业务数据库放在客户侧存储库
- 完整权重系统、审批流、执行回写、审计日志
- 受托运维人员只维护系统与留痕，不参与经营决策
- 后端关键检查和更改只走高层授权
```

## V9 一致性目标

```text
仓库一致性：README / VERSION / CHANGELOG / docs / scripts / workflow 指向同一主线。
前端一致性：不新增主模块，用套餐深度补强现有模块。
后端一致性：V8 权重能力接入报表、经营单元、商品、任务、Agent、复盘主链路。
三层隔离一致性：基础版、专业版、企业版按后端能力、RAG、算法、部署模式同时隔离。
RAG 隔离一致性：shared_rag / tenant_rag / private_rag 分层治理。
权限审计一致性：业务执行、管理审批、受托运维、审计观察职责分离。
测试验收一致性：基础版、专业版、企业版各有 smoke test 主链路。
```

## 演示入口

```text
/                                      前端 Demo
/api/health                            健康检查
/api/modules/dashboard                 总览
/api/modules/operating-unit            经营单元
/api/modules/product                   商品模块
/api/modules/todo                      待办任务
/api/accounts                          账号与角色
/api/system/security                   系统安全状态
/api/system/repositories               Repository / Mirror 运行态
/api/system/postgres-cutover-check     PostgreSQL 主写切换前检查
/api/architecture/p0                   P0 架构状态
/api/architecture/v8/weight-snapshots  V8 权重快照
/api/architecture/v8/weight-executions V8.9 执行回写
/api/architecture/v9/backend-flow      V9.2 后端主流程契约
```

## 文档入口

```text
docs/V9_SAAS_CONSISTENCY_BASE.md   V9 SaaS 企业级一致性底座
docs/V9_REPOSITORY_CONSISTENCY.md  V9.1 仓库结构一致性
docs/V9_BACKEND_FLOW_CONSISTENCY.md V9.2 后端主流程一致性
docs/V8_WEIGHT_SYSTEM.md           V8 权重数据波动任务系统
docs/P0_SAAS_ARCHITECTURE.md       SaaS P0 架构拆解
docs/POSTGRESQL_ALEMBIC.md         PostgreSQL / Alembic / Repository 迁移说明
docs/CHANGELOG.md                  版本更新记录
docs/product/CHANGELOG.md          产品更新记录
versioning/VERSION.md              当前唯一版本源
```

## 当前真实状态

```text
已完成：V8.9 权重执行回写与复盘记录层。
已完成：SQLite Demo Runtime 主链路。
已完成：PostgreSQL mirror / cutover check 文档与接口。
已完成：/api/modules、/api/accounts、/api/data、/api/architecture、/api/system 主入口。
已完成：V9.0 SaaS 企业级一致性底座文档和治理口径。
已完成：V9.1 仓库结构一致性文档、脚本和 GitHub Actions 检查入口。
已完成：V9.2 后端主流程契约、架构可视入口和 CI 检查入口。
仍待完成：生产 JWT / Session、套餐 Feature Flags、RAG namespace 强制隔离、V9 三层 smoke test、PostgreSQL 主写正式切换。
```
