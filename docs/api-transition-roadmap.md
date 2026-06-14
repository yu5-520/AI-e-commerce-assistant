# API 化路线图

## 阶段 1：静态 Demo

已完成。

```text
web_demo/index.html
↓
app.js 内置 Mock 数据
↓
页面展示三段式流程
```

价值：快速演示项目业务链路。

## 阶段 2：本地 Python Workflow

已完成。

```text
python -m src.run_demo
↓
读取 examples 数据
↓
输出 outputs 报告
```

价值：证明项目不是纯页面，而是有可运行的数据处理链路。

## 阶段 3：FastAPI 包装

待完成。

```text
src/api/main.py
↓
/api/demo/run
↓
/api/evals/run
```

价值：前端可以调用真实工作流输出。

## 阶段 4：前端连接 API

待完成。

```text
web_demo/app.js
↓
fetch('/api/demo/run')
↓
渲染真实 JSON
```

价值：项目从静态展示变成可交互 Demo。

## 阶段 5：审批状态流转

待完成。

```text
任务草案
↓
用户确认 / 拒绝 / 修改
↓
状态更新
↓
日志回写
```

价值：Human-in-the-loop 从文档机制变成页面交互。

## 阶段 6：模型和 RAG 替换

待完成。

```text
规则诊断节点
↓
LLM + RAG 诊断节点
↓
结构化输出校验
```

价值：从规则 MVP 升级为真实 AI 应用。
