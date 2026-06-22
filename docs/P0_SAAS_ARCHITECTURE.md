# P0 SaaS 架构拆解：从电商运营 Demo 到互联网大厂 SaaS 底座

> 版本：V5.1.0  
> 目标：不继续堆页面，先补齐 SaaS P0 工程底座：多租户隔离、任务落库、导入事务链、Worker、LLM Gateway 降级、Audit、Nginx 前后端分离。

## 1. 当前定位

当前产品已经具备业务主链路：

```text
报表导入
→ 字段映射 / 校验
→ DataVersion
→ imported_report_rows
→ ModuleProjection
→ DashboardSummary
→ AlertEvent
→ DecisionTaskDraft / AgentReport
→ 任务池
→ 总管复核
→ RAG Memory
```

但当前仍是 Demo 单体：

```text
FastAPI 单体
+ web_demo 静态前端
+ Mock 账号权限
+ SQLite / 运行态存储
+ 内存任务池
```

P0 的目标不是微服务化，而是先升级为：

```text
模块化 FastAPI 单体
+ UserContext 依赖注入
+ ScopedRepository 强制过滤
+ PostgreSQL 生产数据模型
+ 持久化任务状态机
+ ImportJob 事务链
+ Redis / Worker 异步任务
+ LLM Gateway 熔断降级
+ AuditLog / JSON TechLog
+ Nginx 前后端分离
```

---

## 2. P0-1 多租户数据隔离

### 必须规则

所有接口必须通过 FastAPI Depends 注入 `UserContext`，禁止 Handler 手动解析 tenant_id / user_id / role / store scope。

```python
@router.get("/tasks")
async def list_tasks(ctx: UserContext = Depends(get_current_context)):
    return await task_service.list_visible(ctx)
```

### UserContext 标准字段

```text
tenant_id
org_id
user_id
role_id
role_name
permissions
store_group_ids
store_ids
visible_modules
```

### 查询规则

所有业务查询默认追加：

```sql
tenant_id = :ctx.tenant_id
AND deleted_at IS NULL
```

然后按角色追加 Data Scope：

```text
owner      -> 全租户可见
manager    -> store_group_id IN ctx.store_group_ids
operator   -> store_id IN ctx.store_ids
finance    -> 财务域 + 授权店铺
observer   -> 只读摘要 / 授权数据
```

### 当前落地文件

```text
src/core/context.py
src/repositories/scoped_repository.py
src/api/routes/architecture.py
```

---

## 3. P0-2 软删除全局机制

### 所有核心表必须包含

```text
deleted_at
deleted_by
delete_reason
```

### Demo 与生产分流

```text
Demo Hard Delete：允许删除导入记录，方便测试
Production Soft Delete：只标记 deleted_at，保留审计链
```

### 影响范围

```text
data_versions
imported_report_rows
module_projections
alert_events
tasks
task_events
task_logs
task_evidence
rag_memory_cases
audit_logs
```

### 唯一索引策略

PostgreSQL：

```sql
CREATE UNIQUE INDEX uniq_active_task_dedupe
ON tasks (tenant_id, dedupe_key)
WHERE deleted_at IS NULL;
```

SQLite Demo：使用组合字段或应用层校验变通。

---

## 4. P0-3 任务系统持久化与状态机

当前 `TASKS / LOGS / TASK_EVENTS` 仍是内存运行态，这是最核心 P0 缺口。

### 必建表

```text
tasks
task_events
task_logs
task_evidence
task_reviews
task_assignments
task_recap_links
```

### 状态机

```text
draft
→ assigned
→ accepted
→ processing
→ submitted
→ reviewing
→ approved / returned
→ completed
→ archived / written_to_recap
```

### 严禁非法跃迁

```text
draft       不能直接 completed
assigned    不能直接 reviewing
completed   不能重新 submitted
archived    不能重新 processing
```

### 事务要求

任务状态变更与 TaskEvent 写入必须在同一事务内：

```python
async with session.begin():
    task.status = next_status
    session.add(TaskEvent(...))
```

---

## 5. P0-4 报表导入事务链与 ImportJob

### 目标链路

```text
ImportJob created
→ file received
→ rows parsed
→ schema validated
→ DataVersion created
→ ImportedRows written
→ ProjectionJob queued
→ AlertJob queued
→ TaskDraft created
→ ready / failed
```

### 必建表

```text
import_jobs
data_versions
imported_report_rows
projection_jobs
module_projections
alert_events
alert_task_links
```

### 关键字段

```text
trace_id
import_job_id
data_version
projection_status: pending / computing / ready / failed
processed_rows
total_rows
error_message
```

### 验收问题

系统必须能回答：

```text
这个任务来自哪次报表？
这条预警来自哪一行数据？
这个商品卡片为什么刷新？
删除导入记录影响了哪些任务？
回滚后哪些预警保留审计？
```

---

## 6. P0-5 PostgreSQL 生产数据库模型

SQLite 只允许 Demo。生产必须使用 PostgreSQL。

### 配置

```text
APP_ENV=production
DATABASE_URL=postgresql+asyncpg://...
DEMO_DATABASE_URL=sqlite+aiosqlite:///...
```

生产环境如果检测到 SQLite，应拒绝启动。

### 核心索引

```sql
CREATE INDEX idx_tasks_tenant_store
ON tasks (tenant_id, store_id);

CREATE INDEX idx_imported_rows_tenant_version
ON imported_report_rows (tenant_id, data_version);

CREATE INDEX idx_tasks_assignee_status_created
ON tasks (tenant_id, assignee_id, status, created_at DESC);

CREATE INDEX idx_tasks_open
ON tasks (tenant_id, assignee_id, created_at DESC)
WHERE status IN ('assigned', 'accepted', 'processing', 'submitted', 'reviewing');

CREATE INDEX idx_audit_logs_tenant_time
ON audit_logs (tenant_id, created_at DESC);
```

---

## 7. P0-6 Redis 与 Worker

### Redis 职责拆分

```text
Redis DB 0：缓存
Redis DB 1：队列
Redis DB 2：限流 / 临时锁
```

### 队列拆分

```text
import_queue          大报表导入
projection_queue      模块投影计算
alert_queue           预警生成
agent_queue           LLM 分析
notification_queue    通知与轻量任务
```

### 幂等要求

所有 Worker 任务必须可重复执行，不产生副作用：

```text
tenant_id
import_job_id
data_version
job_type
```

重复执行同一 DataVersion 不得生成重复预警或重复任务。

---

## 8. P0-7 LLM Gateway 生产保护

当前 LLM 边界方向正确：LLM 只增强草案，不执行真实经营动作。

### 必补能力

```text
熔断器
租户配额
模块配额
速率限制
结果缓存
Schema 校验
内容安全过滤
规则模板降级
trace 记录
```

### 降级规则

LLM 不可用时，核心链路继续：

```text
库存不足 -> 规则模板补货建议
退款异常 -> 规则模板售后复查建议
流量异常 -> 规则模板投放复核建议
```

---

## 9. P0-8 Audit / Logs 双层体系

### AuditLog：业务审计

```text
audit_logs
- id
- trace_id
- tenant_id
- user_id
- role_id
- resource_type
- resource_id
- action
- before_snapshot
- after_snapshot
- ip
- user_agent
- created_at
```

### TechLog：技术日志

JSON 输出字段：

```text
trace_id
tenant_id
user_id
request_path
method
status_code
latency_ms
error_code
```

业务审计和技术日志通过 trace_id 关联，但存储策略不同。

---

## 10. P0-9 Nginx 前后端分离

### 目标部署

```text
Nginx
├── /api/      -> FastAPI
├── /assets/   -> 前端静态资源
└── /*         -> index.html
```

### 安全要求

```text
HTTPS
CORS 白名单
limit_req 限流
上传接口 body size 限制
proxy_read_timeout
CSP / X-Frame-Options / HSTS
```

---

## 11. 实施顺序

```text
1. 数据库基础层：Async SQLAlchemy / Alembic / TenantScopedMixin / SoftDeleteMixin
2. UserContext：JWT/Session 解析 tenant_id、user_id、role、store scope
3. ScopedRepository：统一注入 tenant、store、deleted_at 过滤
4. Task 持久化：tasks、task_events、task_logs、task_evidence + 严格状态机
5. ImportJob：报表导入、DataVersion、ImportedRows、ProjectionJob、AlertEvent 串链
6. Worker/Redis：导入、投影、预警、Agent 异步化与幂等重试
7. LLM Gateway：熔断、限流、配额、缓存、Schema 校验、Trace、降级模板
8. Audit/Logs：业务审计表 + JSON 技术日志 + trace_id
9. Nginx：前后端分离、HTTPS、限流、安全头
```

---

## 12. P0 Definition of Done

```text
任何业务查询默认按 tenant_id + deleted_at + Data Scope 过滤。
任务、任务事件、任务证据、任务日志全部落库，状态机拒绝非法跃迁。
报表导入形成 ImportJob / DataVersion / AlertEvent / Task / AuditLog 全链路追踪。
LLM 不可用时核心链路不受影响，AgentReport 使用规则模板降级。
生产环境禁止 SQLite、Mock 密码、全局 fallback 假数据、无审计硬删除。
```
