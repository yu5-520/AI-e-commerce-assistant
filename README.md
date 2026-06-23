# AI ERP 经营单元电商协同系统 MVP

> 当前版本：V5.2.9。新增部署安全网关层：Nginx 配置模板、部署说明、Security Headers、FastAPI API RateLimit、`.env.example` 和 `/api/system/security`。当前目标是让系统从“本地工程 Demo”进入“可控部署 MVP”。

## 当前主链路

```text
Browser / Client
↓
Nginx：静态前端、/api 反代、粗限流、安全头、HTTPS 入口预留
↓
FastAPI：Security Headers + API RateLimit + CORS Allowlist
↓
UserContext：tenant / org / user / role / store scope
↓
ImportJob / WorkerJob / ARQ Dispatch / SQLite fallback
↓
TraceId：贯穿 ImportJob / ProjectionJob / WorkerJob / WorkerTaskResult / Task / Evidence / RAG Staging / AuditLog / TechLog / LLM Gateway
↓
TaskRepository：任务创建、流转、重置进入 trace audit
↓
TaskEvidence：运营提交证据、总管复核证据进入 trace audit
↓
LLM Gateway：配额、限流、缓存、熔断、Schema 校验，失败时规则模板降级
↓
AuditLog：按 trace_id 串联导入、投影、队列、任务、证据、RAG 暂存、LLM 调用
↓
TechLog：JSON 技术日志，写入前递归脱敏 token / password / secret / key / cookie
↓
ModuleProjection / DashboardSummary / AlertEvent / Module Agent / DecisionTaskDraft
```

核心规则：**首页展示经营摘要，不展示工程代号；报表确认导入就是自动入库；商品、报表、总览必须随导入同步刷新；当前任务按优先级、截止时间和风险域排序；Demo 阶段可删除单条导入记录。**

## V5.2.x P0 SaaS 架构新增

```text
src/middleware/security_headers.py             FastAPI 安全响应头
src/middleware/api_rate_limit.py               FastAPI 轻量 API 限流
src/services/security_status_service.py        /api/system/security 状态聚合
deploy/nginx/ai-erp.conf                       Nginx 反代 / 静态资源 / 限流模板
deploy/README_DEPLOY.md                        ECS / Nginx / Worker 部署说明
.env.example                                   环境变量样例
src/services/llm_gateway_service.py            LLM 控制层：配额 / 限流 / 缓存 / 熔断 / Schema 校验
src/services/tech_log_service.py               JSON TechLog / tech_logs / 敏感信息递归脱敏
src/services/trace_audit_service.py            trace_id / audit_logs / audit timeline，写入前会脱敏
src/services/worker_queue_service.py           WorkerJob 队列表 / 幂等 / 重试 / 认领，已接 trace_id / audit_logs
src/services/import_job_service.py             ImportJob / ProjectionJob 运行记录服务，已接 trace_id / audit_logs
src/services/task_repository_write_service.py  TaskRepository 写路径过渡服务，已接 trace_id / audit_logs
src/services/task_evidence_audit_service.py    证据提交 / 复核写入 task_evidence 与 task_logs，已接 trace audit
src/workers/arq_worker.py                      ARQ WorkerSettings 启动入口
src/api/routes/system.py                       /api/system/db-status 与 /api/system/security
src/api/routes/audit.py                        /api/audit/traces/{trace_id} 与 /api/audit/tech-logs/*
src/api/routes/llm.py                          /api/llm/generate 已走 LLM Gateway 控制层
```

## 常用接口

```text
GET    /api/health
GET    /api/system/db-status
GET    /api/system/security
GET    /api/architecture/p0
GET    /api/llm/status
GET    /api/llm/gateway
POST   /api/llm/generate
GET    /api/audit/traces/{trace_id}
GET    /api/audit/tech-logs
GET    /api/audit/tech-logs/summary
POST   /api/audit/tech-logs/test-redaction
GET    /api/worker/jobs/runtime
GET    /api/worker/jobs/results
GET    /api/worker/jobs/results?trace_id=<TRACE_ID>
GET    /api/worker/jobs/summary
POST   /api/data/import-jobs/confirm
POST   /api/data/import-jobs/report
POST   /api/data/import-jobs/mock-alerts
POST   /api/data/import-jobs/worker/execute-next
POST   /api/modules/todo/{task_id}/submit-evidence
POST   /api/modules/todo/{task_id}/review-evidence
POST   /api/system/reset-runtime-data?confirm=true
```

## Worker 启动方式

```bash
# Demo 默认：不配置 Redis，API 使用 SQLite worker_jobs fallback
export WORKER_RUNTIME=sqlite

# Redis / ARQ 模式
export WORKER_RUNTIME=arq
export REDIS_URL=redis://127.0.0.1:6379/0
arq src.workers.arq_worker.WorkerSettings
```

## Nginx 部署入口

```bash
sudo cp deploy/nginx/ai-erp.conf /etc/nginx/conf.d/ai-erp.conf
sudo nginx -t
sudo systemctl reload nginx
```

生产时需要替换：

```text
server_name example.com
root /opt/ai-ecommerce-assistant/web_demo
proxy_pass http://127.0.0.1:8000/api/
```

## P0 下一步实施顺序

```text
1. 数据库基础层：Async SQLAlchemy / Alembic / TenantScopedMixin / SoftDeleteMixin
2. UserContext：从 Demo Header 过渡到 JWT / Session
3. ScopedRepository：所有业务查询统一 tenant / store / deleted_at 过滤
4. Task 持久化镜像：task_status、task_events、task_logs、task_evidence + 状态机约束
5. TaskRepository Scoped Reads：通过 UserContext 读取可见任务并支持启动快照恢复
6. TaskRepository 写路径过渡：create / transition / reset repository API
7. 正式任务 API 切换：Agent 入池、待办接收 / 提交 / 复核 / 完成 / 重置
8. 报表任务同步桥：report_task_repository_sync_service 与 /api/data/report-tasks/sync-current
9. ImportJob / ProjectionJob / WorkerJob / ARQ / SQLite fallback
10. Worker 任务扩展：projection_refresh、alert_generation、agent_analysis、rag_memory_write
11. Trace / AuditLog / TechLog / 敏感信息脱敏
12. LLM Gateway：配额、限流、缓存、熔断、Schema 校验
13. 部署安全网关：Nginx 模板、Security Headers、API RateLimit、/api/system/security、.env.example
14. 下一步：PostgreSQL / Alembic 生产数据模型，或前端系统状态页展示架构成熟度
```

## 当前真实状态

```text
已完成：部署安全网关骨架、API 应用层限流、安全响应头、Nginx 模板、环境变量样例、系统安全状态接口。
仍待完成：真实 HTTPS 证书、真实域名、Nginx 实机启用、PostgreSQL / Alembic 迁移、生产 JWT / Session。
```
