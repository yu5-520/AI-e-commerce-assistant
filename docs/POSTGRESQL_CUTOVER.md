# POSTGRESQL_CUTOVER

本文件只记录当前生产数据库切换边界。旧迁移解释和版本流水账不进入本文档。

## 1. Repository 模式

```text
DB_REPOSITORY_MODE=sqlite   默认模式：只写 SQLite Demo runtime，保证演示稳定。
DB_REPOSITORY_MODE=hybrid   过渡模式：SQLite 成功后尝试 PostgreSQL mirror，mirror 异常不影响 Demo。
DB_REPOSITORY_MODE=postgres 目标模式：仅在检查和抽样对账通过后使用。
```

## 2. 检查接口

```text
/api/system/repositories
/api/system/repositories?check=true
/api/system/postgres-cutover-check
```

## 3. 切换顺序

```text
1. 保持 sqlite，确认 Demo 稳定。
2. 配置 DATABASE_URL。
3. 执行 Alembic 迁移。
4. 切换 hybrid。
5. 检查 postgres-cutover-check。
6. 消除 blocked 项。
7. 抽样对账任务、导入、预警、日志数据。
8. 写入回滚方案。
9. 再考虑 postgres。
```

## 4. 必须对账的链路

- 报表导入。
- DataVersion。
- AlertEvent。
- DecisionTask。
- TaskEvent。
- WorkerJob。
- AuditLog。
- TechLog。
- LLMGatewayEvent。

## 5. 当前边界

当前主运行仍是 SQLite-first Demo。PostgreSQL 是生产迁移目标，不是当前默认主写。
