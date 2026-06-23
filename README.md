# AI ERP 企业级电商经营 SaaS 底座

> 当前版本：V9.5.0。V9.5 是 RAG namespace 隔离版本。

## 当前主链路

```text
/api/modules
/api/accounts
/api/data
/api/architecture
/api/system
```

## V9 主线

```text
V9.1 Repository Guard
V9.2 Backend Flow Guard
V9.3 Frontend Module Guard
V9.4 Tier Isolation Guard
V9.5 RAG Isolation Guard
```

## V9.5 RAG 隔离

```text
shared_desensitized_rag
- 共享脱敏经验
- 对应基础版

tenant_isolated_rag
- 租户隔离经验库
- 对应专业版

private_customer_rag
- 客户私有经验库
- 对应企业版
```

入口：

```text
/api/architecture/v9/rag-isolation
```

## 演示入口

```text
/api/health
/api/modules/dashboard
/api/modules/operating-unit
/api/modules/product
/api/modules/todo
/api/accounts
/api/architecture/v9/backend-flow
/api/architecture/v9/frontend-modules
/api/architecture/v9/tier-isolation
/api/architecture/v9/rag-isolation
```

## 文档入口

```text
docs/V9_BACKEND_FLOW_CONSISTENCY.md
docs/V9_FRONTEND_MODULE_CONSISTENCY.md
docs/V9_TIER_ISOLATION_CONSISTENCY.md
docs/V9_RAG_NAMESPACE_ISOLATION.md
versioning/VERSION.md
```

## 当前真实状态

```text
已完成：V9.5 RAG namespace 隔离契约、架构入口和 CI 检查入口。
仍待完成：真实向量数据库 ACL、生产 JWT / Session、RAG namespace 强制执行、三层 smoke test。
```
