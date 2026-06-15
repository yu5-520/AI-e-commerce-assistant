# 服务器部署说明

本文档用于把当前项目接到 ECS / 云服务器上。

当前部署目标：

```text
FastAPI 后端 + 前端静态页
同一个服务端口直接访问
默认端口：3000
默认访问：http://47.118.29.46:3000
```

## 1. 服务器前置条件

服务器需要：

```text
Ubuntu / Debian 系统
Python 3
Git
3000 端口已在安全组放行
```

如果使用阿里云 ECS，需要在安全组放行：

```text
入方向 TCP 3000
来源 0.0.0.0/0
```

## 2. 一键部署

在服务器上执行：

```bash
sudo apt-get update
sudo apt-get install -y git

git clone https://github.com/yu5-520/AI-e-commerce-assistant.git /opt/ai-ecommerce-assistant
cd /opt/ai-ecommerce-assistant
sudo bash scripts/deploy_server.sh
```

部署完成后访问：

```text
http://47.118.29.46:3000
```

健康检查：

```bash
curl http://127.0.0.1:3000/api/health
curl http://127.0.0.1:3000/api/business/today
```

## 3. 手动启动

如果不使用 systemd，也可以手动启动：

```bash
cd /opt/ai-ecommerce-assistant
cp .env.example .env
chmod +x scripts/start_server.sh
bash scripts/start_server.sh
```

默认会启动：

```text
uvicorn src.api.main:app --host 0.0.0.0 --port 3000
```

## 4. systemd 管理

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

## 5. 更新线上代码

进入服务器目录：

```bash
cd /opt/ai-ecommerce-assistant
git pull origin main
sudo systemctl restart ai-operating-advisor
```

## 6. 环境变量

`.env.example` 已包含服务器运行配置：

```text
APP_HOST=0.0.0.0
APP_PORT=3000
APP_WORKERS=1
PUBLIC_BASE_URL=http://47.118.29.46:3000
```

如需改端口：

```bash
nano .env
sudo systemctl restart ai-operating-advisor
```

## 7. 可选：Nginx 反向代理

如果后续要用 80 端口或域名访问，可以启用 Nginx。

```bash
sudo apt-get install -y nginx
sudo cp deploy/nginx-ai-operating-advisor.conf /etc/nginx/sites-available/ai-operating-advisor
sudo ln -sf /etc/nginx/sites-available/ai-operating-advisor /etc/nginx/sites-enabled/ai-operating-advisor
sudo nginx -t
sudo systemctl reload nginx
```

然后访问：

```text
http://47.118.29.46
```

## 8. 当前服务入口

```text
/                         前端首页
/api/business/today       产品主接口
/api/business/report      经营报告
/api/health               健康检查
/docs                     FastAPI 接口文档
```

## 9. 注意事项

当前仍然是 MVP / Mock 数据演示版本：

```text
不连接真实店铺后台
不执行真实上架、改价、投放
不触达真实客户
不保存真实客户隐私数据
```

服务器部署只是让产品 Demo 可以在线访问，不代表已经接入真实商家系统。
