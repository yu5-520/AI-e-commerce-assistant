# 面试问答：下一步怎么做？

## 问题

如果继续推进这个项目，下一步你会做什么？

## 回答

下一步我会优先做前后端打通，而不是继续堆概念。

当前已经有两部分：

1. Python Mock Workflow：可以运行 `python -m src.run_demo`。
2. 静态前端 Demo：可以打开 `web_demo/index.html`。

下一步要把它们连接起来：

```text
FastAPI 后端
↓
封装 /api/demo/run
↓
前端 fetch 调用 API
↓
页面渲染真实工作流输出
↓
用户确认 / 拒绝 RPA 任务
↓
日志回写
```

完成这一步后，项目就会从“命令行可运行 + 静态可展示”，升级为“前后端可交互 Demo”。

## 后续再升级

再往后可以替换关键节点：

- 规则诊断 → LLM 诊断
- 关键词 RAG → Embedding + 向量库
- Mock 数据 → ERP / CRM API
- RPA 草案 → RPA 执行器
- 本地日志 → 数据库日志

## 一句话总结

> 下一步不是继续扩概念，而是把 Python 工作流 API 化，让前端真正调用后端结果。
