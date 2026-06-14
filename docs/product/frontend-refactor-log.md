# 前端重构日志

## 2026-06-14：从单页 Demo 改为工作台骨架

### 背景

此前 `web_demo` 是单页流程演示，适合展示“导入数据 → AI 诊断 → RPA 任务草案 → 人工确认”。

产品阶段需要让前端结构对齐产品地图，而不是只服务一次演示。

### 本轮调整

更新文件：

```text
web_demo/index.html
web_demo/app.js
web_demo/styles.css
web_demo/README.md
```

### 新页面结构

```text
经营总览
数据导入
AI 诊断
任务中心
审批中心
报告中心
知识库
```

### 核心变化

- 增加侧边栏导航。
- 增加工作台布局。
- 增加 hash route 页面切换。
- 保留 API 优先、本地样例 fallback 机制。
- 审批接口从旧的 `/api/tasks/{task_id}/approve` 切换到产品化的 `/api/approvals/{task_id}/approve`。
- 报告中心调用 `/api/reports/demo`。

### 当前仍不做

```text
不引入 React / Vue
不做真实文件上传
不做用户登录
不接真实 ERP / CRM
不执行真实 RPA
```

## 下一步

继续补产品级数据导入能力：

```text
Data Import API
字段校验
导入记录
错误行报告
WorkflowRun 日志
```
