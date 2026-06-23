# 部署说明：AI ERP Operating Advisor

当前部署目标是先形成安全入口层，不强制绑定某个云厂商。

## 推荐拓扑

```text
Browser
↓
Nginx 80/443
├─ /            -> frontend static files
└─ /api/*       -> FastAPI 127.0.0.1:8000
                 ├─ Security Headers middleware
                 ├─ API RateLimit middleware
                 ├─ UserContext / ScopedRepository
                 ├─ ImportJob / WorkerJob / AuditLog / TechLog
                 └─ LLM Gateway controls
```

## 最小启动

```bash
cd /opt/ai-ecommerce-assistant
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.api.main:app --host 127.0.0.1 --port 8000
```

## Nginx

```bash
sudo cp deploy/nginx/ai-erp.conf /etc/nginx/conf.d/ai-erp.conf
sudo nginx -t
sudo systemctl reload nginx
```

生产环境需要把 `server_name example.com` 和 `root /opt/ai-ecommerce-assistant/web_demo` 改为真实域名和目录。

## Redis / ARQ Worker

Demo 默认不需要 Redis：

```bash
export WORKER_RUNTIME=sqlite
```

Redis / ARQ 模式：

```bash
export WORKER_RUNTIME=arq
export REDIS_URL=redis://127.0.0.1:6379/0
arq src.workers.arq_worker.WorkerSettings
```

## 安全检查接口

```text
GET /api/system/security
GET /api/audit/tech-logs/summary
GET /api/llm/gateway
GET /api/worker/jobs/runtime
```

## 生产注意

1. 不要让 FastAPI 直接暴露到公网，公网入口应是 Nginx / SLB / WAF。
2. 不要使用 `*` 作为生产 CORS，使用 `CORS_ALLOW_ORIGINS` 指定域名。
3. LLM API Key 只放环境变量，不写入仓库。
4. TechLog 已做脱敏，但仍不要主动写入明文 Token / Cookie / Password。
5. SQLite 只适合 Demo；生产阶段应迁移 PostgreSQL + Alembic。
6. HTTPS 证书稳定后再启用 HSTS。
