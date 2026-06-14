# 前端重构计划

## 1. 背景

当前 `web_demo/` 是单页 Demo，用于展示“导入数据 → AI 诊断 → RPA 任务草案 → 人工确认”的流程。

它已经能展示产品主线，但还不是完整产品原型。

下一步需要从单页 Demo 重构为多页面工作台结构。

## 2. 当前问题

```text
页面只有一个 index.html
模块没有独立页面
数据导入、诊断、任务、审批、报告混在一个页面
缺少侧边栏和产品导航
没有产品级状态管理
```

## 3. 目标页面结构

```text
/dashboard          经营总览
/data-import        数据导入
/products           商品列表
/products/:id       商品详情
/customers          客户列表
/customers/:id      客户详情
/diagnosis          诊断中心
/tasks              任务中心
/approvals          审批中心
/reports            报告中心
/knowledge          知识库中心
/settings           系统设置
```

## 4. MVP 前端最小页面

第一阶段先做 5 个页面：

```text
/dashboard
/data-import
/diagnosis
/tasks
/reports
```

### 4.1 Dashboard

展示：

```text
商品数量
客户数量
待审批任务数
高风险任务数
最近一次工作流运行状态
```

### 4.2 Data Import

展示：

```text
上传商品表
上传订单表
上传库存表
上传退款表
上传客户表
上传互动表
字段校验结果
导入记录
```

### 4.3 Diagnosis

展示：

```text
商品诊断
客户分层
售后归因
RAG 召回依据
风险等级
建议动作
```

### 4.4 Tasks

展示：

```text
任务列表
任务类型
风险等级
审批状态
是否允许自动执行
```

### 4.5 Reports

展示：

```text
商品诊断报告
客户分层报告
售后归因报告
经营日报
复盘报告
```

## 5. 推荐目录结构

如果继续使用轻量原生前端：

```text
web_demo/
├── index.html
├── styles.css
├── app.js
├── pages/
│   ├── dashboard.js
│   ├── data-import.js
│   ├── diagnosis.js
│   ├── tasks.js
│   └── reports.js
└── components/
    ├── sidebar.js
    ├── card.js
    ├── task-card.js
    └── risk-badge.js
```

如果后续改 React / Vue，再迁移。

## 6. 重构顺序

### Step 1：增加侧边栏

先让页面看起来像工作台。

### Step 2：拆页面区域

把当前四个区域拆成：

```text
Dashboard
Diagnosis
Tasks
Reports
```

### Step 3：增加 Data Import 页面

先支持展示 Mock 数据导入，不急着做真实文件上传。

### Step 4：连接模块 API

逐步从 `/api/demo/run` 迁移到模块化 API。

## 7. 当前不做

```text
不做复杂 UI 框架
不做用户登录
不做真实店铺后台授权
不做真实客户数据导入
```

## 8. 结论

前端重构目标是让用户看到一个真实产品的工作台结构，而不是只看到一个演示页。
