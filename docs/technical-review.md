# 技术视角复盘

## 1. 当前技术结构

```text
examples/       Mock ERP / CRM 数据
knowledge_base/ RAG 知识片段
src/            可运行 Mock Workflow
schemas/        数据契约
prompts/        Prompt 模板
evals/          最小评测
web_demo/       静态前端 Demo
docs/           产品与架构文档
```

## 2. 当前实现方式

### 2.1 数据读取

使用 Python 标准库读取 CSV，不引入额外依赖。

### 2.2 诊断节点

当前使用规则引擎模拟 AI 诊断：

- 商品诊断
- 客户分层
- 售后敏感识别

### 2.3 RAG 节点

当前使用关键词检索模拟 RAG：

- 平台规则
- 合规规则
- 运营方法
- 客服 SOP

### 2.4 RPA 节点

当前生成 RPA 任务草案，不执行真实自动化。

### 2.5 审批节点

当前通过风险规则标记：

- risk_level
- requires_approval
- auto_execution_allowed

### 2.6 报告节点

输出 JSON 和 Markdown 报告。

## 3. 技术优势

- 依赖少，容易运行。
- 输入输出结构清晰。
- 方便后续替换 AI / RAG / API。
- 风险边界写进任务结构。
- 具备最小 Evals。

## 4. 技术限制

- 未使用真实后端服务。
- 未使用真实数据库。
- 未使用真实模型 API。
- RAG 不是向量检索。
- RPA 不执行真实操作。

## 5. 技术下一步

推荐顺序：

```text
FastAPI
↓
SQLite / JSON 日志
↓
前端 fetch
↓
Embedding RAG
↓
LLM 节点
↓
MCP / Function Calling
```

## 6. 技术结论

当前不是生产级技术实现，而是一个低依赖、可解释、可替换的 MVP 技术骨架。
