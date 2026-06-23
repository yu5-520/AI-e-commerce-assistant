# V9.5 RAG Namespace 强制隔离一致性

V9.5 是 RAG namespace 强制隔离一致性版本。

V9.4 固定三层套餐隔离后，V9.5 把隔离继续压到 RAG 数据层：不同套餐、不同租户、不同部署模式必须使用不同的 RAG namespace、读写门禁和审计规则。

## 1. V9.5 目标

```text
shared_desensitized_rag 只能存放共享脱敏经验。
tenant_isolated_rag 只能被同租户授权角色读写。
private_customer_rag 属于企业客户侧存储和客户授权。
前端隐藏不等于 RAG 隔离。
RAG 检索、写入、模板维护和删除都必须有审计。
```

## 2. 三类 RAG Namespace

### shared_desensitized_rag

```text
对应：基础版 / Starter
归属：平台
内容：脱敏案例、通用模板、公开经营模式
禁止：租户原始数据、客户私有数据、员工隐私、价格机密
写入：平台管理员复核后写入
```

### tenant_isolated_rag

```text
对应：专业版 / Professional
归属：租户
内容：租户案例、租户模板、租户平台趋势、活动趋势
禁止：跨租户原始案例、其他租户数据、企业 private RAG
写入：同租户管理者复核或付费 RAG 维护后写入
```

### private_customer_rag

```text
对应：企业版 / Enterprise
归属：客户
内容：客户私有案例、私有模板、权重复盘、审计记忆
禁止：未经合同复用到平台训练、受托运维参与经营决策、静默删除
写入：客户高层授权或受托运维维护授权后写入
```

## 3. 访问门禁

```text
namespaceResolver：tier、tenant_id、org_id、store_scope、role_scope
 ingestionGate：source_type、desensitization_status、review_status、target_namespace
 retrievalGate：namespace、tenant_scope、role_scope、feature_flag、audit_context
 writeGate：human_review、quality_score、metrics_change、approval_status、namespace_policy
 templateMaintenanceGate：paid_maintenance_or_enterprise_ops、change_reason、before_after_diff、approval_trace
 deletionGate：no_silent_delete、executive_or_owner_approval、tombstone_log、recoverability_note
```

## 4. 禁止行为

```text
Starter 把租户原始数据写入 shared_desensitized_rag。
Professional 读取其他租户 namespace。
Professional 读取 private_customer_rag。
Enterprise private RAG 未经合同复用到平台训练。
受托运维静默删除或改写 RAG 记忆。
只靠前端隐藏来做 RAG 隔离。
```

## 5. 架构可视入口

```text
/api/architecture/v9/rag-isolation
```

主要文件：

```text
src/services/v95_rag_namespace_isolation_service.py
src/api/routes/architecture.py
```

这个接口只输出 RAG 隔离契约，不迁移客户向量库、不做真实向量数据库 ACL。

## 6. Definition of Done

```text
Current Version = v9.5.0。
FastAPI API_VERSION = 9.5.0。
Health API_VERSION = 9.5.0。
Agent registry version = 9.5.0。
新增 docs/V9_RAG_NAMESPACE_ISOLATION.md。
新增 src/services/v95_rag_namespace_isolation_service.py。
新增 /api/architecture/v9/rag-isolation。
新增 scripts/check_rag_namespace_isolation.py。
GitHub Actions 跑 RAG namespace isolation check。
README、VERSION、CHANGELOG、前端缓存全部对齐 V9.5。
```
