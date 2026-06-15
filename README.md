# AI ERP 经营单元电商循环系统 MVP

> 一个基于商家 ERP 商品结构识别经营单元的货架电商 AI 工作流原型：先从商品、库存、订单、退款和客户数据中推断当前经营单元，再匹配类目知识、循环频率、竞品比对、上新增长和流量测试回流，最后生成下一轮动作草案。

## 1. 项目定位

本项目当前主定位升级为：

> **AI ERP 经营单元电商循环系统 MVP**

它不是先默认某个垂直类目，也不是只生成标题 / 主图的一次性工具，而是一个围绕商家真实 ERP 商品结构运行的 **Workflow-first，Agent-ready** 经营循环原型。

真实产品逻辑不是：

```text
默认防晒服
↓
跑一轮经营循环
```

而是：

```text
读取 ERP 商品、库存、订单、退款、客户数据
↓
识别经营单元 / 商品群
↓
匹配经营单元知识档案
↓
生成日 / 周循环策略
↓
经营判断、竞品比对、上新增长、流量测试回流
↓
经营循环总控决定下一轮回到哪里
```

一句话：

> **ERP 决定经营单元，经营单元决定类目知识，商品节奏决定循环频率，系统再生成经营判断、竞品比对、上新草案、测试复盘和下一轮动作。**

## 2. 当前版本边界

当前仓库已经完成的是 **V0.8 - V1.4 的 Mock 闭环骨架**，并新增了 ERP 经营单元识别、循环频率策略和产品化后端接口。

当前可运行能力：

```text
Mock ERP / CRM 数据
↓
ERP 商品结构识别
↓
经营单元推断
↓
循环频率策略
↓
经营单元知识档案
↓
商品经营诊断
↓
同经营单元竞品比对
↓
同经营单元上新增长草案
↓
流量测试与数据回流
↓
经营循环总控
↓
CRM 客户分层
↓
轻量 RAG 知识召回
↓
RPA 任务草案
↓
人工确认
↓
报告与日志回写
```

当前 mock ERP 商品会推断为：

```text
经营单元：家居生活商品
类目档案：knowledge_base/category_profiles/home_living_goods.md
循环频率：daily
报告类型：daily_operation_report
```

防晒服仍然保留为一个可复制的 demo 样板，但不再是产品默认前提。

## 3. 核心架构

```text
0. ERP 商品结构识别
商品标题 / 平台类目 / 商品群 / 库存 / 订单 / 销售额 / 价格带
↓
1. 经营单元推断
家居生活商品 / 防晒商品 / 服饰商品 / 大宗商品 / 快消商品等
↓
2. 循环频率策略
日循环 / 周循环 / 月循环 / 异常触发
↓
3. ERP + CRM 经营判断系统
已有商品 / 库存 / 订单 / 退款 / 客户 / 售前售后
↓
4. 同经营单元竞品比对系统
价格 / 标题 / 主图 / SKU / 评价 / 差评 / 活动 / 售后承诺
↓
5. 同经营单元上新增长系统
新品候选 / 上新草案 / 标题主图 / SKU / 定价 / 测试计划
↓
6. 流量测试与数据回流系统
曝光 / 点击 / 转化 / 退款 / ROI / 库存变化 / 客户反馈 / 复盘日志
↓
7. 经营循环总控
决定下一轮回到 ERP、CRM、竞品、上新、流量测试或继续循环
↓
8. 产品化 API 层
把内部工作流结果包装成今日建议、经营单元、商品体检、竞品机会、上新建议、流量复盘、待确认动作和经营报告
```

## 4. 当前可运行内容

### 4.1 命令行 Mock Workflow

```bash
python -m src.run_demo
```

运行后生成：

```text
outputs/operating_unit.json
outputs/cycle_policy.json
outputs/category_context.json
outputs/product_diagnosis.json
outputs/customer_segmentation.json
outputs/competitor_analysis.json
outputs/listing_growth_plan.json
outputs/traffic_feedback_report.json
outputs/operating_loop_summary.json
outputs/rpa_task_draft.json
outputs/approval_required_tasks.json
outputs/rag_retrieval_context.json
outputs/demo_report.md
```

### 4.2 Evals 评测

```bash
python evals/run_evals.py
```

运行后生成：

```text
evals/results/latest_results.json
```

### 4.3 FastAPI 后端

本地开发：

```bash
pip install -r requirements.txt
uvicorn src.api.main:app --reload
```

前端优先使用产品化接口：

```text
GET  /api/business/today             今日经营建议
GET  /api/business/operating-unit    经营单元与循环频率
GET  /api/business/data-health       数据体检
GET  /api/business/products          商品体检
GET  /api/business/competitors       竞品机会
GET  /api/business/listing           上新建议
GET  /api/business/traffic           流量复盘
GET  /api/business/actions           待确认动作
GET  /api/business/report            经营报告
```

兼容旧版和内部调试接口：

```text
GET  /api/health
GET  /api/demo/run
GET  /api/demo/report
GET  /api/evals/run
POST /api/tasks/{task_id}/approve
POST /api/tasks/{task_id}/reject
GET  /api/tasks/status
```

### 4.4 前端 Demo

本地启动 FastAPI 后打开：

```text
http://127.0.0.1:8000/
```

或：

```text
http://127.0.0.1:8000/web_demo/index.html
```

页面会优先调用 `/api/business/today` 和其他 `/api/business/*` 产品接口。如果没有启动 API，直接打开 `web_demo/index.html` 时会自动回退到本地样例数据。

### 4.5 服务器部署

服务器推荐结构：

```text
公网用户 → 80/443 → Nginx → 127.0.0.1:3000 → FastAPI
```

安全组建议只开放：

```text
80 / 443：公网访问
22：仅限你的固定公网 IP
3000：不要对公网开放
```

一键部署入口：

```bash
sudo apt-get update
sudo apt-get install -y git

git clone https://github.com/yu5-520/AI-e-commerce-assistant.git /opt/ai-ecommerce-assistant
cd /opt/ai-ecommerce-assistant
sudo bash scripts/deploy_server.sh
```

部署完成后访问：

```text
http://47.118.29.46
```

健康检查：

```bash
curl http://127.0.0.1:3000/api/health
curl http://127.0.0.1:3000/api/business/today
curl http://47.118.29.46/api/health
```

详细部署说明见：

```text
docs/server-deploy.md
```

## 5. 当前已经完成

```text
统一产品文档
+ ERP 经营单元推断模块
+ 循环频率策略模块
+ 产品化 Business API
+ 安全服务器部署脚本（Nginx 公网入口 + FastAPI 本机监听）
+ 家居生活经营单元档案
+ 家居生活竞品 / 货盘 / 流量测试 Mock 数据
+ 防晒服 demo 样板保留
+ 类目上下文加载模块
+ 同经营单元竞品比对模块
+ 同经营单元上新增长模块
+ 流量测试与回流模块
+ 经营循环总控模块
+ Mock ERP / CRM 数据
+ Python Mock Workflow
+ 简单 RAG 检索
+ RPA 任务草案
+ Human-in-the-loop 风控
+ Evals
+ FastAPI API
+ 产品化前端 UI
+ SQLite / JSONL 日志记录
```

## 6. 当前核心模块

### 6.1 ERP 经营单元推断

```text
src/operating_unit/
```

当前能力：

```text
读取 ERP 商品表
识别商品类目、标题关键词、商品群和库存结构
推断经营单元
输出经营单元 ID、商品群、关键词信号和推断理由
```

当前 mock ERP 会从遮阳伞、厨房置物架、护腰坐垫等商品推断出：

```text
home_living_goods / 家居生活商品
```

### 6.2 循环频率策略

```text
src/scheduler/
```

当前能力：

```text
根据经营单元、价格带、库存和商品节奏生成循环策略
快消 / 低客单 / 高库存商品 → daily
大宗 / 高客单 / 低频商品 → weekly
其他商品 → weekly operation review
```

当前 mock ERP 推断为：

```text
daily_fast_moving_goods_loop
```

### 6.3 产品化 Business API

```text
src/api/routes/business.py
src/services/business_view_service.py
```

当前能力：

```text
把内部 workflow 结果包装成前端可直接消费的产品视图
隐藏 workflow、RAG、SQLite、ExecutionLog 等工程表达
保留 raw 字段用于兼容旧前端数据结构
```

### 6.4 服务器部署

```text
scripts/start_server.sh
scripts/deploy_server.sh
deploy/nginx-ai-operating-advisor.conf
docs/server-deploy.md
```

当前能力：

```text
FastAPI 绑定 127.0.0.1:3000
Nginx 作为公网入口
安全组无需开放 3000
生成 systemd 服务
支持 Nginx 反向代理配置
```

### 6.5 经营单元知识档案

```text
knowledge_base/category_profiles/home_living_goods.md
knowledge_base/category_profiles/sun_protection_clothing.md
src/category/
```

家居生活商品是当前 ERP 推断出的主经营单元。防晒服保留为可复制的第二样板，但不再作为默认值。
