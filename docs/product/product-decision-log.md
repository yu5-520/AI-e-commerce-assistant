# 产品决策日志

## 2026-06-15：main 分支只保留当前产品主线

### 背景

仓库曾同时存在旧前端模板、旧 demo 接口、旧 CLI 入口、旧测试脚本和当前 ERP 经营单元产品链路。多套入口并存会导致服务器部署、AI 代码更新、README 说明和测试脚本反复拉回旧模板。

### 决策

从 v1.0.0 开始，main 分支只保留当前可运行产品主线：

```text
src/api/main.py
↓
/api/business/*
↓
web_demo/index.html
↓
web_demo/app-v2.js
```

旧版 demo、旧兼容 API、旧前端模板、旧 CLI 入口不再留在当前主分支。需要回看旧实现时，通过 Git commit 历史查看。

### 保留能力

```text
ERP / CRM Mock 数据
经营单元识别
循环频率策略
商品体检
竞品机会
上新建议
流量复盘
待确认动作
经营报告
审批记录
数据校验
系统状态
服务器部署
```

### 停止保留

```text
旧 web_demo/app.js
旧 /api/demo
旧 /api/products
旧 /api/customers
旧 /api/diagnosis
旧 /api/tasks
旧 /api/reports
旧 /api/evals
旧 /api/logs
旧 src.run_demo
旧 standalone eval runner
```

### 新规则

```text
结构级变更必须更新 versioning/CHANGELOG.md
版本号变更必须更新 versioning/VERSION.md
产品决策必须更新 docs/product/product-decision-log.md
产品结构清理必须更新 docs/product/product-structure-cleanup-log.md
测试脚本必须跟随当前 API 主线同步
```

---

## 2026-06-14：从简历展示仓库切回产品仓库

### 背景

此前仓库中存在较多简历、面试、HR 展示、阶段标记类文档，导致项目更像“求职展示材料”，而不是一个正在完成的产品。

### 决策

从本阶段开始，仓库文档层优先服务产品本体，只保留产品骨架、运行说明、API、日志和必要架构文档。

新增 `docs/product/` 目录，作为产品结构的主目录。

### 当前产品主线

```text
导入经营数据
↓
数据校验与清洗
↓
建立商品档案与客户档案
↓
AI / RAG 经营诊断
↓
生成任务草案
↓
人工确认
↓
导出报告 / 低风险执行
↓
日志回写与复盘
```

### 保留方向

```text
产品地图
领域模型
用户流程
模块边界
MVP 范围
运行日志
API 说明
```

### 暂停方向

```text
简历包装
面试话术
HR 展示
BOSS 展示
重复的 DONE / STOP / FINAL 标记
```

## 下一步

基于 `docs/product/`，继续重构 API 路由和前端信息架构。
