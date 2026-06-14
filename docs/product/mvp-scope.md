# MVP 范围

## 1. 设计目标

MVP 范围用于明确当前阶段必须完成什么、暂时不做什么，以及后续怎么升级。

当前目标不是做完整企业系统，而是跑通一个可交互、可验证、可追溯的电商 AI 经营工作台最小闭环。

## 2. 当前 MVP 定义

当前 MVP 是：

```text
Mock ERP / CRM 数据
↓
数据校验与加载
↓
商品诊断 + 客户分层
↓
简单 RAG 召回
↓
RPA 任务草案
↓
人工确认 / 拒绝
↓
报告输出
↓
日志记录
```

## 3. 必须完成

### 3.1 数据输入

必须支持：

```text
商品表
订单表
库存表
退款表
客户表
客户标签表
客户互动表
```

当前阶段可以使用 Mock CSV。

### 3.2 数据校验

必须校验：

```text
必填字段
数字字段
product_id 关联
customer_id 关联
退款与订单关联
客户互动与客户关联
```

### 3.3 商品诊断

必须支持：

```text
SKU 利润风险
活动价风险
库存风险
退款风险
敏感类目风险
```

### 3.4 客户分层

必须支持：

```text
高价值客户
新客
沉睡客户
售后敏感客户
流失风险客户
复购潜力客户
```

### 3.5 RAG 依据

必须支持至少四类知识：

```text
平台规则
合规风控
运营方法
客服 SOP
```

当前阶段可以用关键词检索模拟向量检索。

### 3.6 任务草案

必须支持：

```text
经营日报
SKU 价格建议表
客户分层报告
售后归因表
复盘报告
```

所有任务默认：

```text
requires_approval = true
auto_execution_allowed = false
```

### 3.7 人工确认

必须支持：

```text
确认
拒绝
状态记录
审批日志
```

### 3.8 报告输出

必须支持：

```text
JSON 输出
Markdown 报告
前端展示
```

## 4. 当前暂不做

当前不做：

```text
真实 ERP API
真实 CRM API
真实店铺后台登录
真实 RPA 执行器
自动改价
自动上架 / 下架
自动报名活动
自动投放广告
自动群发客户
自动处理退款
真实客户隐私存储
生产级权限系统
生产级计费系统
```

## 5. 当前实现方式

### 5.1 AI 节点

当前用规则引擎模拟 AI 诊断。

后续替换为：

```text
LLM 结构化输出
Prompt 模板
Function Calling
输出 Schema 校验
```

### 5.2 RAG 节点

当前用关键词检索模拟 RAG。

后续替换为：

```text
文档切片
Embedding
向量库
Top-K 检索
召回质量评测
```

### 5.3 数据存储

当前使用 Mock CSV 和本地 JSON / JSONL 输出。

后续替换为：

```text
SQLite
PostgreSQL
对象存储
日志表
```

### 5.4 前端

当前前端是单页 Demo。

后续升级为：

```text
Dashboard
Data Import
Products
Customers
Diagnosis
Tasks
Approvals
Reports
Knowledge
```

## 6. MVP 验收标准

### 6.1 运行验收

```text
python -m src.run_demo 可以运行
uvicorn src.api.main:app --reload 可以启动 API
/api/demo/run 可以返回完整工作流结果
前端可以优先调用 API，失败时回退本地样例
```

### 6.2 产品验收

```text
用户能看到数据导入结果
用户能看到商品诊断结果
用户能看到客户分层结果
用户能看到 RAG 依据
用户能看到任务草案
用户能确认 / 拒绝任务
用户能导出或查看报告
```

### 6.3 风险验收

```text
系统不自动改价
系统不自动投放
系统不自动群发客户
系统不自动处理退款
所有中高风险任务必须人工确认
审批记录必须可追溯
```

## 7. 后续版本路线

### P0：产品结构摸底

```text
产品地图
领域模型
用户流程
模块边界
MVP 范围
```

### P1：可交互 MVP

```text
上传 Mock CSV
运行诊断
生成任务
人工确认
导出报告
```

### P2：可持久化 MVP

```text
SQLite / 数据库
商品档案
客户档案
任务和审批日志
WorkflowRun
ExecutionLog
```

### P3：AI 能力替换

```text
规则诊断 → LLM 诊断
关键词 RAG → 向量 RAG
固定任务草案 → LLM 任务生成
```

### P4：真实系统适配

```text
ERP API Adapter
CRM API Adapter
RPA Adapter
权限系统
日志监控
```

## 8. 当前结论

当前阶段只追求：

> 用 Mock 数据跑通产品闭环，并把用户流程、数据对象、模块边界和风险边界摸清楚。
