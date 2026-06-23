# V9.6 RAG 写入审批与记忆沉淀一致性

V9.6 固定 RAG 候选记忆进入正式记忆库的主流程。

## 1. 目标

```text
RAG 候选不能自动进入正式记忆库。
写入必须先过 namespace policy。
写入必须有质量检查和人工复核。
正式沉淀必须有 approval、before/after、audit_id。
删除必须留 tombstone，不允许静默删除。
```

## 2. 生命周期

```text
rag_memory_candidate
quality_check
namespace_policy_check
human_review
approval_decision
promoted_memory
audit_record
rollback_tombstone
```

## 3. Namespace 写入规则

```text
shared_desensitized_rag：只允许脱敏通用经验。
tenant_isolated_rag：只允许同租户复核经验。
private_customer_rag：只允许客户授权私有经验。
```

## 4. 审批门禁

```text
candidateGate：source、namespace、tenant_id、store_scope、evidence、metrics_change
qualityGate：quality_score、repeatability、risk_label、desensitization_status
humanGate：reviewer_role、approval_status、comment、timestamp
promotionGate：before_hash、after_hash、memory_id、namespace、audit_id
rollbackGate：rollback_reason、tombstone_log、recoverable_snapshot、owner_approval
```

## 5. 禁止行为

```text
未经人工复核自动沉淀。
没有 namespace 写入记忆。
共享库写入租户原始数据。
客户私有库未授权写入。
删除记忆但不留 tombstone。
```

## 6. 架构入口

```text
/api/architecture/v9/rag-write-memory
```

主要文件：

```text
src/services/v96_rag_write_memory_service.py
src/api/routes/architecture.py
scripts/check_rag_write_memory_consistency.py
```
