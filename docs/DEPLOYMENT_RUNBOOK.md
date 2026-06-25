# V11.11 原子化部署 Runbook

本文件只保留服务器部署和排障命令，不写长篇架构解释。

## 1. 部署原则

```text
GitHub 是唯一代码源。
ECS 只运行已验证 release。
不在运行目录里原地 git pull + reset + restart。
fetch 失败必须停止，不能继续 reset 到旧 origin/main。
前端、后端、health、VERSION 必须同一版本。
```

## 2. 目录结构

```text
/opt/ai-ecommerce-assistant-deploy/
├── releases/
│   ├── 20260626035000_abcd1234/
│   └── 20260626041000_efgh5678/
├── current -> releases/20260626041000_efgh5678
├── shared/
│   ├── .env
│   └── logs/
└── deploy.log
```

systemd 只运行：

```text
/opt/ai-ecommerce-assistant-deploy/current
```

## 3. 一键部署

```bash
cd /opt/ai-ecommerce-assistant || exit 1
bash scripts/deploy_atomic.sh
```

首次迁移时，脚本会创建：

```text
/opt/ai-ecommerce-assistant-deploy/releases
/opt/ai-ecommerce-assistant-deploy/shared/logs
/etc/systemd/system/ai-operating-advisor.service.d/override.conf
```

## 4. 部署闸门

`deploy_atomic.sh` 在切换 current 前必须通过：

```text
1. GitHub main 可访问。
2. clone 到独立 release 目录。
3. requirements 安装成功。
4. versioning/VERSION.md 可读。
5. FastAPI app.version 与 VERSION.md 一致。
6. health.API_VERSION 与 VERSION.md 一致。
7. web_demo/index.html 的资源版本与 VERSION.md 一致。
8. 关键路由已注册：
   /api/health
   /api/modules/dashboard
   /api/modules/operating-unit
   /api/modules/product
   /api/modules/todo
   /api/system/runtime-diagnostics
   /api/system/backfill-operating-objects
```

任一失败：不切换 current。

## 5. 运行时验收

切换 current 后必须通过：

```text
GET /api/health
GET /api/system/runtime-diagnostics
GET /api/modules/operating-unit
```

失败时自动回滚上一版 release。

## 6. 手动检查

```bash
readlink -f /opt/ai-ecommerce-assistant-deploy/current
cat /opt/ai-ecommerce-assistant-deploy/current/versioning/VERSION.md
/opt/ai-ecommerce-assistant-deploy/current/.venv/bin/python /opt/ai-ecommerce-assistant-deploy/current/scripts/verify_release.py
sudo systemctl status ai-operating-advisor --no-pager -l
sudo journalctl -u ai-operating-advisor -n 120 --no-pager
curl -sS http://127.0.0.1:3000/api/health ; echo
curl -sS -H 'X-Mock-User-Id: U004' http://127.0.0.1:3000/api/system/runtime-diagnostics ; echo
```

## 7. 回滚

脚本失败会自动回滚。需要手动回滚时：

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
不要绕过 scripts/verify_release.py 直接重启。
```

## 11. 旧目录用途

`/opt/ai-ecommerce-assistant` 只作为 bootstrap 目录使用。正式运行态以：

```text
/opt/ai-ecommerce-assistant-deploy/current
```

为准。
