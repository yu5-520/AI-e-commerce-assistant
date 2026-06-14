# V6 到 V7 技术差距

## V6 已完成

- 静态前端 Demo
- Python Mock Workflow
- Mock ERP / CRM 数据
- 简单 RAG 检索
- RPA 任务草案
- Evals
- 文档与求职材料

## V7 需要补齐

### 1. 后端服务

当前缺口：没有 API 服务。

补齐方式：FastAPI。

### 2. 前端数据来源

当前缺口：前端使用内置 Mock 数据。

补齐方式：`fetch('/api/demo/run')`。

### 3. 状态流转

当前缺口：任务没有真实确认 / 拒绝状态。

补齐方式：新增 approve / reject 接口。

### 4. 日志存储

当前缺口：输出只写本地文件。

补齐方式：SQLite 或 JSON 日志。

### 5. 部署方式

当前缺口：没有统一启动命令。

补齐方式：新增 run script 或 Makefile。

## 结论

V6 是“静态可展示 + 命令行可运行”，V7 是“前后端可交互”。
