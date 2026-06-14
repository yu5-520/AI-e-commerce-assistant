# AI + RPA + ERP + CRM 电商经营自动化工作台 MVP

> 一个 Workflow-first 的电商 AI 自动化工作流原型：以 ERP / 店铺后台 / 表格数据和 CRM 客户数据为输入，通过 RAG 知识增强、AI 诊断、人工确认、RPA 任务草案与日志回写，帮助商家完成商品运营分析、SKU 利润判断、库存预警、客户分层、售后归因、活动准备和复盘迭代。

## 1. 项目定位

本项目从原来的“拼多多 AI 商品增长工作台”升级为 **AI + RPA + ERP + CRM 电商经营自动化工作台 MVP**。

它不是简单的标题生成器，也不是一次性上新助手，更不是深度自治 Agent 系统，而是一个 **Workflow-first，Agent-ready** 的 AI 工作流项目：

- **Workflow-first**：当前以确定性业务流程为主，AI 作为判断与生成节点，RPA 作为低风险执行节点。
- **Agent-ready**：未来可以在低风险场景逐步引入 Agent，例如数据异常排查、RAG 检索选择、报告生成和失败原因分析。

一句话：

> **ERP 管货，CRM 管人，RAG 补知识，AI 做判断，人工控风险，RPA 做任务草案，日志做复盘。**

## 2. 核心架构

```text
ERP 数据层
商品 / 订单 / 库存 / 成本 / SKU / 活动 / 退款
↓
CRM 数据层
客户 / 标签 / 复购 / 售后 / 触达 / 客户价值
↓
数据接入与清洗层
字段映射 / 数据清洗 / 缺失值检查 / Mock 数据导入
↓
商品档案 + 客户档案
商品运营记忆 / 客户运营记忆 / 历史测试 / 售后归因
↓
RAG 知识增强层
商品档案库 / 平台规则库 / 合规风控库 / 运营方法库 / 客服 SOP 库
↓
AI 诊断与策略生成层
商品诊断 / SKU 利润测算 / 库存预警 / 客户分层 / 复购判断 / 售后归因
↓
Human-in-the-loop 人工确认层
改价 / 活动 / 投放 / 客户触达 / ERP 回写 / CRM 回写必须确认
↓
RPA 任务草案层
生成日报 / 导出表格 / 生成活动表 / 客户清单 / 复盘报告 / 任务清单
↓
日志回写与复盘层
AI 报告 / RAG 召回记录 / 用户确认记录 / RPA 任务日志 / 下一轮动作
```

## 3. 当前可运行内容

### 3.1 命令行 Mock Workflow

```bash
python -m src.run_demo
```

运行后生成：

```text
outputs/product_diagnosis.json
outputs/customer_segmentation.json
outputs/rpa_task_draft.json
outputs/approval_required_tasks.json
outputs/rag_retrieval_context.json
outputs/demo_report.md
```

### 3.2 Evals 评测

```bash
python evals/run_evals.py
```

运行后生成：

```text
evals/results/latest_results.json
```

### 3.3 V7 FastAPI 后端

安装依赖：

```bash
pip install -r requirements.txt
```

启动 API：

```bash
uvicorn src.api.main:app --reload
```

可用接口：

```text
GET  /api/health
GET  /api/demo/run
GET  /api/demo/report
GET  /api/evals/run
POST /api/tasks/{task_id}/approve
POST /api/tasks/{task_id}/reject
GET  /api/tasks/status
```

### 3.4 前端 Demo

启动 FastAPI 后打开：

```text
http://127.0.0.1:8000/
```

或：

```text
http://127.0.0.1:8000/web_demo/index.html
```

页面会优先调用 `/api/demo/run`。如果没有启动 API，直接打开 `web_demo/index.html` 时会自动回退到本地样例数据。

## 4. 当前已经完成

```text
文档架构
+ Mock ERP / CRM 数据
+ Python Mock Workflow
+ 简单 RAG 检索
+ RPA 任务草案
+ Human-in-the-loop 风控
+ Evals
+ FastAPI API
+ 前端 fetch API / 本地 fallback
```

## 5. 核心模块

### 5.1 ERP / 表格数据接入

MVP 阶段优先支持 Mock CSV / Excel 数据，不直接接入真实商家后台。

数据类型：商品、订单、库存、退款、SKU、成本、售价、活动价、投放摘要。

### 5.2 CRM 客户数据接入

MVP 阶段只使用脱敏 Mock 数据。

数据类型：客户 ID、昵称哈希、首单时间、最近购买时间、消费金额、退款次数、客户标签、互动记录。

不保存真实姓名、手机号、微信号、地址等隐私信息。

### 5.3 AI / RAG 决策层

当前版本使用规则引擎模拟 AI 诊断，用关键词检索模拟 RAG。后续可替换为 LLM + Embedding + 向量库。

### 5.4 Human-in-the-loop 人工确认

关键动作必须由用户确认：改标题、改主图、改价、报名活动、增加投放预算、下架 / 清货、批量回写 ERP / CRM、客户触达、优惠券策略执行和售后处理动作。

### 5.5 RPA 任务草案层

MVP 阶段生成低风险任务草案，不执行真实自动化。

可生成：运营日报、SKU 价格建议表、活动准备表、客户分层表、复购任务表、售后归因表、复盘报告。

不执行：自动上架、自动改价、自动投放、自动报名活动、自动群发、自动退款、自动诱导好评。

## 6. 重点目录

```text
examples/        Mock ERP / CRM 数据
knowledge_base/  简单 RAG 知识片段
src/             Python Mock Workflow 与 API
evals/           最小评测
web_demo/        前端 Demo
docs/            架构、演示、求职与复盘文档
```

核心入口：

```text
src/run_demo.py        命令行工作流
src/api/main.py        FastAPI 后端
web_demo/index.html    前端 Demo
evals/run_evals.py     Evals 运行器
```

## 7. 风险边界

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
