# Demo 展示话术

## 1. 开场定位

这个项目不是一个单纯的 AI 文案生成器，也不是深度自治 Agent，而是一个 Workflow-first 的电商 AI 自动化工作台。

它的核心链路是：

```text
ERP 管货
CRM 管人
RAG 补知识
AI 做判断
人工控风险
RPA 做执行
日志做复盘
```

## 2. 展示顺序

### 第一步：展示 README

强调：

- 项目定位已经从 AI 商品助手升级为 AI + RPA + ERP + CRM 电商经营自动化工作台。
- 当前不是无边界 Agent，而是确定性业务工作流。
- 高风险动作必须人工确认。

### 第二步：运行 Python Mock Workflow

命令：

```bash
python -m src.run_demo
```

展示输出：

- 商品诊断 JSON
- 客户分层 JSON
- RPA 任务草案 JSON
- RAG 召回上下文 JSON
- Markdown 复盘报告

### 第三步：展示前端 Demo

打开：

```text
web_demo/index.html
```

依次点击：

1. 导入 Mock 数据
2. 生成 AI 诊断
3. 生成 RPA 任务草案
4. 查看人工确认项

### 第四步：展示 Evals

命令：

```bash
python evals/run_evals.py
```

强调：

- CRM 是否识别售后敏感客户。
- RPA 是否禁止自动改价、自动群发、自动退款。
- 任务是否默认进入人工确认。

## 3. 面试解释

可以这样讲：

> 当前 Demo 先用规则引擎模拟 AI 诊断节点，用关键词检索模拟 RAG 节点，用结构化 JSON 模拟 RPA 任务草案。这样做是为了先跑通业务闭环和安全边界，后续可以逐步替换成 LLM、Embedding 向量库、Function Calling、MCP 和真实 RPA 执行器。

## 4. 项目亮点

- 有业务场景：电商 ERP / CRM。
- 有数据输入：Mock 商品、订单、库存、退款、客户、标签、互动记录。
- 有 AI 工作流：诊断、分层、归因、任务生成。
- 有 RAG 骨架：平台规则、合规规则、运营方法、客服 SOP。
- 有 RPA 任务草案：日报、SKU 表、客户分层、售后归因。
- 有 Human-in-the-loop：高风险动作必须人工确认。
- 有 Evals：验证风险边界和任务安全。
- 有前端 Demo：可视化展示流程。

## 5. 结束语

这个项目的价值不是让 AI 自动接管店铺，而是证明我能把 AI 放进真实业务系统里：

> 数据进入系统，AI 做判断，RAG 给依据，人工控风险，RPA 做低风险执行，日志做复盘。
