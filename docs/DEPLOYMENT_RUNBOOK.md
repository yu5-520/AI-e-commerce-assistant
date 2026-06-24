# DEPLOYMENT_RUNBOOK

本文件只保留服务器部署和排障命令，不写架构解释。

## 1. 拉取最新代码

```bash
cd /opt/ai-ecommerce-assistant || exit 1
git fetch origin main
git reset --hard origin/main
git log -1 --oneline
```

## 2. 安装依赖

```bash
cd /opt/ai-ecommerce-assistant || exit 1
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## 3. FastAPI import 检查

```bash
cd /opt/ai-ecommerce-assistant || exit 1
source .venv/bin/activate
python - <<'PY'
from src.api.main import app
print('APP_VERSION =', app.version)
print('FastAPI import OK')
PY
```

## 4. 重启服务

```bash
sudo systemctl restart ai-operating-advisor
sudo systemctl restart nginx
```

## 5. 查看状态

```bash
sudo systemctl status ai-operating-advisor --no-pager -l
sudo systemctl status nginx --no-pager -l
```

## 6. 健康检查

```bash
curl -s http://127.0.0.1:8000/api/health
curl -s http://127.0.0.1:8000/api/system/repositories
curl -s http://127.0.0.1:8000/api/system/postgres-cutover-check
```

## 7. 前端缓存检查

浏览器访问正式入口：

```text
/
```

如果服务器已经更新但页面仍旧：

- 确认 Nginx 指向当前服务。
- 清理浏览器缓存。
- 检查 `web_demo/index.html` 中静态资源版本号。
- 不再使用临时 query 参数作为长期入口。

## 8. Demo 数据清理

仅在测试阶段使用：

```bash
curl -X POST 'http://127.0.0.1:8000/api/system/reset-runtime-data?confirm=true&include_audit_logs=true'
```

## 9. 回滚

```bash
cd /opt/ai-ecommerce-assistant || exit 1
git log --oneline -5
git reset --hard <上一稳定提交>
source .venv/bin/activate
python -m pip install -r requirements.txt
sudo systemctl restart ai-operating-advisor
sudo systemctl restart nginx
```

## 10. 禁止事项

- 不在 ECS 上手动改运行代码后不提交仓库。
- 不把临时 URL 参数当成正式部署方式。
- 不绕过 FastAPI import 检查直接重启。
- 不在未通过 cutover check 前切 PostgreSQL 主写。
