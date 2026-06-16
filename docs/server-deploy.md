# 服务器部署说明

本文档用于把当前项目接到 ECS / 云服务器上。

## 1. 推荐部署结构

```text
公网用户
↓
80 / 443
↓
Nginx
↓
127.0.0.1:3000
↓
FastAPI + 前端静态页
```

默认访问：

```text
http://47.118.29.46
```

安全原则：

```text
3000 只监听本机 127.0.0.1
安全组不开放 3000 到 0.0.0.0/0
公网只开放 80 / 443
```

## 2. 服务器前置条件

服务器需要：

```text
Ubuntu / Debian 系统
Python 3
Git
Nginx
```

阿里云 ECS 安全组建议：

```text
入方向 TCP 80   来源 0.0.0.0/0
入方向 TCP 443  来源 0.0.0.0/0
入方向 TCP 22   来源仅限你的固定公网 IP
```

不建议添加：

```text
入方向 TCP 3000 来源 0.0.0.0/0
```

## 3. 一键部署

在服务器上执行：

```bash
sudo apt-get update
sudo apt-get install -y git

git clone https://github.com/yu5-520/AI-e-commerce-assistant.git /opt/ai-ecommerce-assistant
cd /opt/ai-ecommerce-assistant
sudo bash scripts/deploy_server.sh
```

如果服务器已经克隆过仓库：

```bash
cd /opt/ai-ecommerce-assistant
git pull origin main
sudo bash scripts/deploy_server.sh
```

部署完成后访问：

```text
http://47.118.29.46
```

健康检查：

```bash
curl http://127.0.0.1:3000/api/health
curl http://127.0.0.1:3000/api/modules/dashboard
curl http://127.0.0.1:3000/api/accounts
curl http://47.118.29.46/api/health
```

## 4. 手动启动

如果不使用 systemd，也可以手动启动本机服务：

```bash
cd /opt/ai-ecommerce-assistant
cp .env.example .env
chmod +x scripts/start_server.sh
bash scripts/start_server.sh
```

默认会启动：

```text
uvicorn src.api.main:app --host 127.0.0.1 --port 3000
```

这时公网不能直接访问 3000，需要 Nginx 转发。

## 5. systemd 管理

一键部署会创建服务：

```text
ai-operating-advisor.service
```

常用命令：

```bash
sudo systemctl status ai-operating-advisor
sudo systemctl restart ai-operating-advisor
sudo systemctl stop ai-operating-advisor
sudo journalctl -u ai-operating-advisor -f
```

## 6. 更新线上代码

```bash
cd /opt/ai-ecommerce-assistant
git pull origin main
sudo systemctl restart ai-operating-advisor
sudo systemctl reload nginx
```

## 7. 环境变量

`.env.example` 已包含服务器运行配置：

```text
APP_HOST=127.0.0.1
APP_PORT=3000
APP_WORKERS=1
PUBLIC_BASE_URL=http://47.118.29.46
```

如需改端口：

```bash
nano .env
sudo systemctl restart ai-operating-advisor
sudo nginx -t
sudo systemctl reload nginx
```

## 8. Nginx 反向代理

一键部署脚本会自动写入 Nginx 配置。

配置模板位置：

```text
deploy/nginx-ai-operating-advisor.conf
```

手动配置方式：

```bash
sudo apt-get install -y nginx
sudo cp deploy/nginx-ai-operating-advisor.conf /etc/nginx/sites-available/ai-operating-advisor
sudo ln -sf /etc/nginx/sites-available/ai-operating-advisor /etc/nginx/sites-enabled/ai-operating-advisor
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

## 9. 当前服务入口

```text
/                                  前端首页
/api/modules/dashboard              模块总览
/api/modules/todo                   待办任务池
/api/modules/task-reports/tasks/{id} 任务详情报告
/api/accounts                       账号角色权限
/api/health                         健康检查
/docs                               FastAPI 接口文档
```

## 10. 安全检查清单

部署后检查：

```bash
ss -lntp | grep 3000
```

应看到类似：

```text
127.0.0.1:3000
```

不应看到：

```text
0.0.0.0:3000
```

安全组检查：

```text
80 / 443 可以公网访问
3000 不要对公网开放
22 只允许你的固定公网 IP
```

## 11. 注意事项

当前仍然是 MVP / Mock 数据演示版本：

```text
不连接真实店铺后台
不接真实企业 SSO
不执行真实上架、改价、投放
不触达真实客户
不保存真实客户隐私数据
```

服务器部署只是让产品 Demo 可以在线访问，不代表已经接入真实商家系统。
