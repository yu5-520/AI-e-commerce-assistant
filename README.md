# AI 垂直货架电商经营循环系统 MVP

> 一个面向垂直类目的货架电商 AI 工作流原型：先接入商家已有 ERP / CRM 数据，完成商品、库存、订单、退款、客户和售后的经营判断；再围绕同类目竞品做比对；再生成优化、上新和流量测试方案；最后把测试结果回流到经营判断系统，形成持续循环。

## 1. 项目定位

本项目当前主定位升级为：

> **AI 垂直货架电商经营循环系统 MVP**

它不是泛电商大而全系统，也不是只生成标题 / 主图的一次性工具，而是一个围绕垂直类目商家的 **Workflow-first，Agent-ready** 经营循环原型。

真实商家的接受路径通常不是一上来就“全自动铺货”，而是：

```text
先接入已有商品、库存、订单、退款、客户、售前售后
↓
用 AI 做 ERP + CRM 经营判断
↓
由经营问题触发同类目竞品比对
↓
再生成优化老品 / 上新增长 / 流量测试方案
↓
测试数据回流到经营判断系统
↓
循环运行
```

一句话：

> **垂直类目定规则，ERP 管货，CRM 管人，竞品找差距，上新补增长，RPA 做文档任务，日志做复盘。**

## 2. 当前版本边界

当前仓库已经完成的是 **V0.8：ERP + CRM 经营判断底座**，并已开始接入 **V0.9：垂直类目配置层** 的最小骨架。

当前可运行能力：

```text
防晒服垂直类目档案
↓
Mock ERP / CRM 数据
↓
数据导入与校验
↓
商品经营诊断
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

当前尚未实现，但已经纳入架构升级路线的能力：

```text
同类目竞品比对系统
同类目上新增长系统
流量测试与数据回流系统
业务档案长期落库
```

## 3. 核心架构

```text
0. 垂直类目知识层
类目规则 / 价格带 / 客群 / 季节性 / 售后风险 / 竞品维度
↓
1. ERP + CRM 经营判断系统
已有商品 / 库存 / 订单 / 退款 / 客户 / 售前售后
↓
2. 同类目竞品比对系统
价格 / 标题 / 主图 / SKU / 评价 / 差评 / 活动 / 售后承诺
↓
3. 同类目上新增长系统
新品候选 / 铺货草案 / 标题主图 / SKU / 定价 / 测试计划
↓
4. 流量测试与数据回流系统
曝光 / 点击 / 转化 / 退款 / ROI / 库存变化 / 客户反馈 / 复盘日志
↓
回到 ERP + CRM 经营判断系统
```

## 4. 当前可运行内容

### 4.1 命令行 Mock Workflow

```bash
python -m src.run_demo
```

运行后生成：

```text
outputs/category_context.json
outputs/product_diagnosis.json
outputs/customer_segmentation.json
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

安装依赖：

```bash
pip install -r requirements.txt
```

启动 API：

```bash
uvicorn src.api.main:app --reload
```

常用接口：

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

启动 FastAPI 后打开：

```text
http://127.0.0.1:8000/
```

或：

```text
http://127.0.0.1:8000/web_demo/index.html
```

页面会优先调用 `/api/demo/run`。如果没有启动 API，直接打开 `web_demo/index.html` 时会自动回退到本地样例数据。

## 5. 当前已经完成

```text
统一产品文档
+ 防晒服垂直类目档案
+ 类目上下文加载模块
+ Mock ERP / CRM 数据
+ Python Mock Workflow
+ 简单 RAG 检索
+ RPA 任务草案
+ Human-in-the-loop 风控
+ Evals
+ FastAPI API
+ 前端 fetch API / 本地 fallback
+ SQLite / JSONL 日志记录
```

## 6. 当前核心模块

### 6.1 垂直类目配置

当前已加入防晒服类目样板。

位置：

```text
knowledge_base/category_profiles/sun_protection_clothing.md
src/category/
```

类目上下文会进入 Mock Workflow，并输出到 `outputs/category_context.json`。

### 6.2 ERP / 表格数据接入

MVP 阶段优先支持 Mock CSV / Excel 数据，不直接接入真实商家后台。

数据类型：商品、订单、库存、退款、SKU、成本、售价、活动价、投放摘要。

### 6.3 CRM 客户数据接入

MVP 阶段只使用脱敏 Mock 数据。

数据类型：客户 ID、昵称哈希、首单时间、最近购买时间、消费金额、退款次数、客户标签、互动记录。

不保存真实姓名、手机号、微信号、地址等隐私信息。

### 6.4 AI / RAG 决策层

当前版本使用规则引擎模拟 AI 诊断，用关键词检索模拟 RAG。RAG 已支持读取 `knowledge_base/category_profiles/` 下的垂直类目知识。

### 6.5 Human-in-the-loop 人工确认

关键动作必须由用户确认：改标题、改主图、改价、报名活动、增加投放预算、下架 / 清货、批量回写 ERP / CRM、客户触达、优惠券策略执行和售后处理动作。

### 6.6 RPA 任务草案层

MVP 阶段生成低风险任务草案，不执行真实自动化。

可生成：运营日报、SKU 价格建议表、活动准备表、客户分层表、复购任务表、售后归因表、复盘报告。

不执行：自动上架、自动改价、自动投放、自动报名活动、自动群发、自动退款、自动诱导好评。

## 7. 下一阶段升级路线

```text
V0.8：ERP + CRM 经营判断系统（当前已跑通）
V0.9：垂直类目配置层（当前已接入最小骨架）
V1.0：同类目竞品比对系统
V1.1：同类目上新增长系统
V1.2：流量测试与数据回流系统
V1.3：完整货架电商经营循环系统
```

详细升级清单见：

```text
docs/system-upgrade-roadmap.md
```

## 8. 重点目录

```text
examples/        Mock ERP / CRM 数据
knowledge_base/  简单 RAG 知识片段，含垂直类目知识
src/             Python Mock Workflow 与 API
evals/           最小评测
web_demo/        前端 Demo
docs/            架构、PRD、升级路线与风险边界
```

核心入口：

```text
src/run_demo.py        命令行工作流
src/api/main.py        FastAPI 后端
web_demo/index.html    前端 Demo
evals/run_evals.py     Evals 运行器
```

## 9. 风险边界

本项目定位是：

> **AI 辅助经营决策 + RPA 可控任务草案原型，而不是违规自动化工具，也不是无约束 Agent 自治系统。**

本产品不提供以下能力：

- 绕过平台审核
- 擦边营销话术
- 虚假功效宣传
- 侵权素材复制
- 自动化违规爬虫
- 绕过验证码或平台风控
- 未经用户确认的自动上架、自动改价、自动投放、自动报名活动
- 未经用户确认的客户触达、自动群发、自动退款或诱导好评
- 保存真实客户姓名、手机号、微信号、地址等隐私数据
