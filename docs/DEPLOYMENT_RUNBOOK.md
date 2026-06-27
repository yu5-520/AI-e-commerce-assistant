# V11.13 Demo 快速部署 Runbook

本文件只保留服务器部署和排障命令，不写长篇架构解释。

## 1. 部署分层

```text
Demo 快速部署：scripts/deploy_fast.sh
阶段轻量发布：scripts/deploy_atomic.sh
客户 / 生产发布：LIGHT_DEPLOY=0 的完整原子部署
```

当前 Demo 阶段默认使用快速部署，目标是每次小改 30 秒到 2 分钟内完成验证。

## 2. Demo 快速部署

```bash
cd /opt/ai-ecommerce-assistant || exit 1
bash scripts/deploy_fast.sh
```

快速部署行为：

```text
1. fetch GitHub 最新 main。
2. fetch 失败立即停止，不 reset 到旧缓存。
3. reset bootstrap 仓库到 origin/main。
4. 不创建 release。
5. 不重建 venv。
6. 默认不 pip install。
7. 检查 VERSION / app.version / health.API_VERSION / 前端资源版本。
8. systemd 指回 /opt/ai-ecommerce-assistant。
9. 重启后端。
10. /api/health 版本通过后完成。
```

适合：

```text
前端 UI 调整
按钮跳转
字段文案
普通接口字段
普通 service 逻辑
Demo 高频测试
```

## 3. 强制安装依赖

只有 requirements.txt 变化时使用：

```bash
FORCE_INSTALL_REQUIREMENTS=1 bash scripts/deploy_fast.sh
```

## 4. 轻量原子部署

阶段版本或一整天收口后使用：

```bash
cd /opt/ai-ecommerce-assistant || exit 1
git fetch --prune origin main
git reset --hard origin/main
LIGHT_DEPLOY=1 ROUTE_GUARD_MODE=warn RUNTIME_ROUTE_GUARD=warn bash scripts/deploy_atomic.sh
```

轻量原子部署目录：

```text
/opt/ai-ecommerce-assistant-deploy/
├── releases/
├── current -> releases/<当前版本>
├── shared/.venv
└── deploy.log
```

适合：

```text
导入链路重构
账号隔离重构
系统页重构
阶段版本验收
给别人临时试用
```

## 5. 完整生产部署

客户环境或中配服务器使用：

```bash
LIGHT_DEPLOY=0 ROUTE_GUARD_MODE=strict RUNTIME_ROUTE_GUARD=strict bash scripts/deploy_atomic.sh
```

适合：

```text
客户服务器
私有部署
正式 SaaS 环境
多人使用环境
```

## 6. 快速部署检查

```bash
cat /opt/ai-ecommerce-assistant/versioning/VERSION.md
curl -sS http://127.0.0.1:3000/api/health ; echo
curl -sS -H 'X-Mock-User-Id: U004' http://127.0.0.1:3000/api/system/runtime-diagnostics ; echo
sudo systemctl status ai-operating-advisor --no-pager -l
sudo journalctl -u ai-operating-advisor -n 80 --no-pager
```

## 7. 原子部署检查

```bash
readlink -f /opt/ai-ecommerce-assistant-deploy/current
cat /opt/ai-ecommerce-assistant-deploy/current/versioning/VERSION.md
/opt/ai-ecommerce-assistant-deploy/shared/.venv/bin/python /opt/ai-ecommerce-assistant-deploy/current/scripts/verify_release.py
curl -sS http://127.0.0.1:3000/api/health ; echo
```

## 8. GitHub 网络慢时

快速部署脚本会重试 fetch。手动排查：

```bash
cd /opt/ai-ecommerce-assistant || exit 1
git config --global http.version HTTP/1.1
git config --global http.lowSpeedLimit 0
git config --global http.lowSpeedTime 999999
timeout 300 git fetch --no-tags --depth=1 origin +refs/heads/main:refs/remotes/origin/main
```

如果连续失败，不要 reset，不要部署，等待网络恢复或切换镜像源。

## 9. Demo 数据清理

仅在测试阶段使用：

```bash
curl -X POST 'http://127.0.0.1:3000/api/system/reset-runtime-data?confirm=true&include_audit_logs=true'
```

## 10. 禁止事项

```text
不要 fetch 失败后继续 reset。
不要 sudo git fetch / sudo git reset。
不要在 ECS 手动 patch src/ 后不提交 GitHub。
不要让前端静态文件和后端 app.version 来自不同提交。
Demo 小改不要每次走完整原子部署。
requirements.txt 没变不要 pip install。
```

## 11. 当前推荐节奏

```text
每次小改：bash scripts/deploy_fast.sh
阶段收口：bash scripts/deploy_atomic.sh
客户部署：LIGHT_DEPLOY=0 严格发布
```
