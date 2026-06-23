# AI ERP 企业级电商经营 SaaS 底座

> 当前版本：V9.4.0。V9.4 是三层套餐隔离一致性版本：在 V9.0-V9.3 的基础上，固定 Starter / Professional / Enterprise 的能力边界、RAG namespace、数据范围、权重算法、部署模式和审计深度。

## 项目定位

AI ERP 企业级电商经营 SaaS 底座是一个面向货架电商运营的 AI 经营系统。系统以报表导入、经营预警、任务流转、Agent 证据链、店铺 / 商品权重、RAG 经验沉淀、审计留痕和企业级部署治理为主线。

核心规则：**前端模块保持稳定；后端能力统一整合；套餐能力按层隔离；RAG 与数据按命名空间隔离；关键动作必须审批、留痕、可追溯；仓库入口、文档、脚本、CI、后端主流程、前端模块边界和套餐隔离必须指向同一主线。**

## 当前主链路

```text
/api/modules       经营前端模块：总览、经营单元、商品、报表、待办、日志、详情页
/api/accounts      账号、角色、店铺归属和可见范围
/api/data          报表导入、DataVersion、预警、回滚、Demo 删除
/api/architecture  P0 / V7 / V8 / V9 架构状态与权重能力接口
/api/system        系统状态、Repository、PostgreSQL cutover check、运行态清理
```

## V9 主线

```text
V9.1 Repository Guard
↓
V9.2 Backend Flow Guard
↓
V9.3 Frontend Module Guard
↓
V9.4 Tier Isolation Guard
```

## V9.4 三层套餐隔离

```text
基础版 / Starter
- 月费
- 共享 SaaS
- 共享脱敏 RAG
- 基础报表整理、商品问题识别、商品任务生成
- 不开放商品权重、店铺权重、运营权重

专业版 / Professional
- 年费
- 多租户 SaaS
- 租户隔离 RAG
- 商品权重、店铺权重、平台趋势、活动趋势、Agent 证据链增强
- RAG 数据、模板、行业规则按次维护

企业版 / Enterprise
- 部署费 + 年费 + 运维服务
- 客户服务器或客户云
- 客户侧 private RAG
- 完整权重系统、审批流、执行回写、复盘、审计留痕、受托运维
- 受托运维只维护系统与留痕，不参与客户经营决策
```

V9.4 新增架构可视入口：

```text
/api/architecture/v9/tier-isolation
```

## 演示入口

```text
/                                       前端 Demo
/api/health                             健康检查
/api/modules/dashboard                  总览
/api/modules/operating-unit             经营单元
/api/modules/product                    商品模块
/api/modules/todo                       待办任务
/api/accounts                           账号与角色
/api/architecture/v9/backend-flow       V9.2 后端主流程契约
/api/architecture/v9/frontend-modules   V9.3 前端模块契约
/api/architecture/v9/tier-isolation     V9.4 三层套餐隔离契约
```

## 文档入口

```text
docs/V9_SAAS_CONSISTENCY_BASE.md        V9 SaaS 企业级一致性底座
docs/V9_REPOSITORY_CONSISTENCY.md       V9.1 仓库结构一致性
docs/V9_BACKEND_FLOW_CONSISTENCY.md     V9.2 后端主流程一致性
docs/V9_FRONTEND_MODULE_CONSISTENCY.md  V9.3 前端模块一致性
docs/V9_TIER_ISOLATION_CONSISTENCY.md   V9.4 三层套餐隔离一致性
docs/V8_WEIGHT_SYSTEM.md                V8 权重数据波动任务系统
docs/P0_SAAS_ARCHITECTURE.md            SaaS P0 架构拆解
docs/POSTGRESQL_ALEMBIC.md              PostgreSQL / Alembic / Repository 迁移说明
versioning/VERSION.md                   当前唯一版本源
```

## 当前真实状态

```text
已完成：V9.0 SaaS 企业级一致性底座。
已完成：V9.1 仓库结构一致性。
已完成：V9.2 后端主流程一致性。
已完成：V9.3 前端模块一致性。
已完成：V9.4 三层套餐隔离一致性契约、架构入口和 CI 检查入口。
仍待完成：生产 JWT / Session、真实 Feature Flags 强制执行、RAG namespace 强制隔离、V9 三层 smoke test、PostgreSQL 主写正式切换。
```
