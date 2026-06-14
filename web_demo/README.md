# Web Demo

这是 AI + RPA + ERP + CRM 电商经营工作台的前端产品原型。

当前页面已经从单页流程演示升级为带侧边栏的工作台结构，包含：

```text
经营总览
数据导入
AI 诊断
任务中心
审批中心
报告中心
知识库
```

## 运行方式一：API 模式

在仓库根目录安装依赖：

```bash
pip install -r requirements.txt
```

启动服务：

```bash
uvicorn src.api.main:app --reload
```

然后打开：

```text
http://127.0.0.1:8000/
```

或：

```text
http://127.0.0.1:8000/web_demo/index.html
```

页面会优先调用 FastAPI。

## 运行方式二：本地样例模式

直接用浏览器打开：

```text
web_demo/index.html
```

这种方式不会调用 API，只展示内置样例数据。

## 当前页面模块

### 经营总览

展示商品诊断数量、客户分层数量、任务草案数量和待人工确认数量。

### 数据导入

展示当前 Mock ERP / CRM 数据源，后续扩展为 CSV / Excel 上传和字段映射。

### AI 诊断

展示商品诊断、客户分层和风险等级。

### 任务中心

展示由 AI 诊断生成的 RPA 任务草案。

### 审批中心

支持任务确认 / 拒绝。

API 模式下调用：

```text
POST /api/approvals/{task_id}/approve
POST /api/approvals/{task_id}/reject
```

### 报告中心

API 模式下读取：

```text
GET /api/reports/demo
```

### 知识库

展示当前 RAG 召回依据。

## 当前边界

当前页面和 API 都不连接真实 ERP / CRM，不执行真实店铺后台操作，不自动改价、不自动投放、不自动群发、不自动退款。
