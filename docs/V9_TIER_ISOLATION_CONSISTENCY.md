# V9.4 三层套餐隔离一致性

V9.4 是三层套餐隔离一致性版本。

V9.0 建立 SaaS 企业级一致性底座，V9.1 固定仓库结构，V9.2 固定后端主流程，V9.3 固定前端模块边界。V9.4 开始把基础版、专业版、企业版的能力边界固定为系统级契约。

## 1. V9.4 目标

```text
不是只在前端隐藏按钮。
不是只写商业报价。
而是把套餐、RAG、数据、权重算法、部署模式、审计深度统一隔离。
```

## 2. 三层套餐

### 基础版 / Starter

```text
计费：月费
部署：共享 SaaS
RAG：共享脱敏 RAG
能力：基础报表整理、商品问题识别、商品任务生成
限制：不开放商品权重、店铺权重、运营权重
```

### 专业版 / Professional

```text
计费：年费
部署：多租户 SaaS
RAG：租户隔离 RAG
能力：商品权重、店铺权重、平台趋势、活动趋势、Agent 证据链增强
增值：RAG 数据、模板、行业规则按次维护
限制：不开放私有部署、private RAG、受托运维、高层授权配置链路
```

### 企业版 / Enterprise

```text
计费：部署费 + 年费 + 运维服务
部署：客户服务器或客户云
RAG：客户侧 private RAG
能力：完整权重系统、审批流、执行回写、复盘、审计留痕、受托运维
边界：受托运维只维护系统与留痕，不参与客户经营决策
```

## 3. 隔离维度

```text
Feature Flags：决定能力是否可调用
RAG Namespace：决定经验库隔离边界
Data Scope：决定租户、组织、店铺、角色可见范围
Audit Depth：决定日志和审计深度
Deployment Mode：决定共享、多租户、私有化部署模式
```

## 4. 禁止跨层

```text
Starter 不能访问商品权重和店铺权重算法。
Starter 不能访问租户私有 RAG。
Professional 不能访问客户 private RAG。
Professional 不能访问私有部署控制。
Enterprise 受托运维不能参与经营决策。
前端隐藏不等于隔离，后端能力开关必须同步控制。
```

## 5. 架构可视入口

```text
/api/architecture/v9/tier-isolation
```

主要文件：

```text
src/services/v94_tier_isolation_contract_service.py
src/api/routes/architecture.py
```

这个接口只输出套餐隔离契约，不执行开通、不做计费、不改客户权限。

## 6. 与前端模块的关系

```text
同一套前端主模块。
不同套餐展示不同深度。
Starter 是 basic depth。
Professional 是 weighted operation depth。
Enterprise 是 private governance depth。
```

## 7. Definition of Done

```text
Current Version = v9.4.0。
FastAPI API_VERSION = 9.4.0。
Health API_VERSION = 9.4.0。
Agent registry version = 9.4.0。
新增 docs/V9_TIER_ISOLATION_CONSISTENCY.md。
新增 src/services/v94_tier_isolation_contract_service.py。
新增 /api/architecture/v9/tier-isolation。
新增 scripts/check_tier_isolation_consistency.py。
GitHub Actions 跑 tier isolation consistency check。
README、VERSION、CHANGELOG、前端缓存全部对齐 V9.4。
```
