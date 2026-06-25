# V11.12 轻量原子部署 Runbook

本文件只保留服务器部署和排障命令，不写长篇架构解释。

## 1. 部署原则

```text
GitHub 是唯一代码源。
ECS 只运行已验证 release。
不在运行目录里原地 git pull + reset + restart。
fetch 失败必须停止，不能继续 reset 到旧 origin/main。
前端、后端、health、VERSION 必须同一版本。
低配 ECS 默认使用 shared/.venv，不每次重建虚拟环境。
```

## 2. 目录结构

```text
/opt/ai-ecommerce-assistant-deploy/
├── releases/
│   ├── 20260626035000_abcd1234/
│   └── 20260626041000_efgh5678/
├── current -> releases/20260626041000_efgh5678
├── shared/
│   ├── .venv
│   ├── .env
│   ├── requirements.sha256
│   └── logs/
└── deploy.log
```

systemd 运行：

```text
WorkingDirectory=/opt/ai-ecommerce-assistant-deploy/current
ExecStart=/opt/ai-ecommerce-assistant-deploy/shared/.venv/bin/uvicorn src.api.main:app --host 127.0.0.1 --port 3000
```

## 3. 一键部署

```bash
cd /opt/ai-ecommerce-assistant || exit 1
git fetch --prune origin main
git reset --hard origin/main
bash scripts/deploy_atomic.sh
```

低配 ECS 默认：

```text
LIGHT_DEPLOY=1
ROUTE_GUARD_MODE=warn
RUNTIME_ROUTE_GUARD=warn
```

## 4. 轻量部署行为

```text
1. clone 新代码到 releases 独立目录。
2. 复用 /opt/ai-ecommerce-assistant-deploy/shared/.venv。
3. requirements.txt hash 未变化时跳过 pip install。
4. VERSION / app.version / health / 前端资源版本仍强校验。
5. 路由检查默认 warn，不误杀低配 ECS。
6. /api/health 运行时健康检查仍为硬闸门。
7. 成功后切换 current。
8. 失败时不污染当前运行版本。
```

## 5. 严格部署模式

生产或中配服务器可启用严格模式：

```bash
LIGHT_DEPLOY=0 ROUTE_GUARD_MODE=strict RUNTIME_ROUTE_GUARD=strict bash scripts/deploy_atomic.sh
```

## 6. 手动检查

```bash
readlink -f /opt/ai-ecommerce-assistant-deploy/current
cat /opt/ai-ecommerce-assistant-deploy/current/versioning/VERSION.md
/opt/ai-ecommerce-assistant-deploy/shared/.venv/bin/python /opt/ai-ecommerce-assistant-deploy/current/scripts/verify_release.py
sudo systemctl status ai-operating-advisor --no-pager -l
sudo journalctl -u ai-operating-advisor -n 120 --no-pager
curl -sS http://127.0.0.1:3000/api/health ; echo
curl -sS -H 'X-Mock-User-Id: U004' http://127.0.0.1:3000/api/system/runtime-diagnostics ; echo
```

## 7. 回滚

脚本失败会尽量自动回滚。需要手动回滚时：

```bash
ls -1 /opt/ai-ecommerce-assistant-deploy/releases
sudo ln -sfn /opt/ai-ecommerce-assistant-deploy/releases/<上一版目录> /opt/ai-ecommerce-assistant-deploy/current
sudo systemctl restart ai-operating-advisor
```

## 8. 前端缓存检查

```bash
grep -o "v=[0-9.]*" /opt/ai-ecommerce-assistant-deploy/current/web_demo/index.html | sort -u
curl -sS http://127.0.0.1:3000/api/health ; echo
```

前端资源版本必须与 `/api/health` 版本一致。

## 9. Demo 数据清理

仅在测试阶段使用：

```bash
curl -X POST 'http://127.0.0.1:3000/api/system/reset-runtime-data?confirm=true&include_audit_logs=true'
```

## 10. 禁止事项

```text
不要在运行目录里原地 git pull + reset + restart。
不要 sudo git fetch / sudo git reset。
不要在 ECS 手动 patch src/ 后不提交 GitHub。
不要 fetch 失败后继续 reset。
不要让前端静态文件和后端 app.version 来自不同提交。
不要在低配 ECS 上每次重建 release .venv。
```

## 11. 旧目录用途

`/opt/ai-ecommerce-assistant` 只作为 bootstrap 目录使用。正式运行态以：

```text
/opt/ai-ecommerce-assistant-deploy/current
```

为准。
