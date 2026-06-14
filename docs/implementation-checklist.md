# 实现检查清单

## 1. 已完成

### 架构文档

- [x] README 项目定位升级
- [x] ERP / RPA 架构文档
- [x] ERP 字段映射文档
- [x] RAG 架构文档
- [x] RPA 工作流文档
- [x] Human-in-the-loop 人工确认文档
- [x] CRM 分析文档
- [x] CRM 数据模型
- [x] Workflow vs Agent 边界文档
- [x] Evals 与监控文档

### Mock 数据

- [x] 商品数据
- [x] 订单数据
- [x] 库存数据
- [x] 退款数据
- [x] 客户数据
- [x] 客户标签
- [x] 客户互动记录

### 可运行脚本

- [x] Mock 数据读取
- [x] 商品诊断规则
- [x] 客户分层规则
- [x] 简单 RAG 检索
- [x] RPA 任务草案生成
- [x] 报告生成
- [x] 最小 Evals 运行器

### 前端 Demo

- [x] 三段式静态页面
- [x] 导入 Mock 数据交互
- [x] AI / RAG 诊断展示
- [x] RPA 任务草案展示
- [x] 人工确认项展示
- [x] 示例输出文件

## 2. 待完成

### 后端 API

- [ ] FastAPI 服务
- [ ] /api/demo/run
- [ ] /api/demo/report
- [ ] /api/evals/run
- [ ] /api/tasks/{task_id}/approve
- [ ] /api/tasks/{task_id}/reject

### 前端连接后端

- [ ] 使用 fetch 调用后端 API
- [ ] 渲染真实 Python 工作流输出
- [ ] 增加确认 / 拒绝按钮
- [ ] 增加任务状态变化

### RAG 升级

- [ ] 文档切片
- [ ] Embedding
- [ ] 向量库
- [ ] Top-K 检索日志
- [ ] RAG Evals

### AI 节点升级

- [ ] 商品诊断 LLM 节点
- [ ] 客户分层 LLM 节点
- [ ] 售后归因 LLM 节点
- [ ] RPA 任务生成 LLM 节点

### 工具调用升级

- [ ] Function Calling 设计
- [ ] MCP 工具接口设计
- [ ] ERP / CRM Mock API Adapter
- [ ] 日志写入工具

## 3. 当前推荐下一步

优先完成：

```text
FastAPI 后端 API
↓
前端 fetch 调用 API
↓
任务确认 / 拒绝状态流转
```

这一步完成后，项目会从“静态展示 + 命令行可跑”升级为“前后端可交互 Demo”。
