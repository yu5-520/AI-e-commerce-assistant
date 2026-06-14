# 当前项目状态

## 1. 当前定位

AI + RPA + ERP + CRM 电商经营自动化工作台 MVP。

项目采用 Workflow-first 架构，而不是深度自治 Agent。

## 2. 当前已完成

### 文档层

- 架构说明
- ERP / CRM 数据模型
- RAG 设计
- RPA 工作流
- Human-in-the-loop
- Workflow vs Agent 边界
- Evals 与监控
- Demo 展示话术
- 简历项目表述

### 数据层

- Mock 商品数据
- Mock 订单数据
- Mock 库存数据
- Mock 退款数据
- Mock 客户数据
- Mock 客户标签
- Mock 客户互动

### 运行层

- Python Mock Workflow
- 商品诊断规则
- 客户分层规则
- 简单 RAG 检索
- RPA 任务草案生成
- Markdown / JSON 报告输出
- 最小 Evals

### 前端层

- 静态三段式 Demo
- 导入 Mock 数据交互
- AI / RAG 诊断展示
- RPA 任务草案展示
- 人工确认项展示

## 3. 当前命令

运行主流程：

```bash
python -m src.run_demo
```

运行评测：

```bash
python evals/run_evals.py
```

打开前端：

```text
web_demo/index.html
```

## 4. 当前边界

项目当前不接真实 ERP / CRM，不接真实店铺后台，不保存真实客户隐私，不自动改价、不自动投放、不自动群发、不自动处理退款。

## 5. 下一步

最推荐下一步：

```text
FastAPI 后端
↓
前端 fetch 调用
↓
任务确认 / 拒绝状态流转
↓
日志回写
```
