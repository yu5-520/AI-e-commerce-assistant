# 模块边界

## 1. 当前边界目标

本文件只描述 v1.0.2 当前 active trunk 的模块边界。

当前产品是：

```text
AI ERP 经营单元工作台
```

当前产品不是：

```text
完整 ERP
完整 CRM
多页面后台系统
自动运营 Agent
旧标题 / 图片生成 demo
旧 Material Observer Agent 链路
```

## 2. API 入口边界

### 负责

```text
src.api.main:app
挂载 /api/business/* 当前产品接口
挂载 /api/health 健康检查
挂载 /api/data/* Mock 数据校验与导入记录
挂载 /api/approvals/* 待确认动作记录
挂载 /api/system/* 系统状态与清理接口
服务 web_demo/index.html 当前单页前端
```

### 不负责

```text
不挂载旧 /api/demo
不挂载旧 /api/products
不挂载旧 /api/customers
不挂载旧 /api/diagnosis
不挂载旧 /api/tasks
不挂载旧 /api/reports
不挂载旧 /api/evals
不挂载旧 /api/logs
不暴露旧 evals 结果接口
不恢复 backend/server.py
```

## 3. Business API 边界

### 负责

```text
/api/business/today              今日经营建议
/api/business/operating-unit     经营单元识别结果
/api/business/data-health        数据健康状态
/api/business/products           商品体检卡片
/api/business/competitors        竞品机会
/api/business/listing            上新建议
/api/business/traffic            流量复盘
/api/business/actions            待确认动作
/api/business/report             经营报告
```

### 不负责

```text
不直接接真实店铺 API
不直接执行 RPA
不直接发布商品
不直接改价
不直接投放广告
不直接触达客户
```

## 4. Workflow 边界

### 负责

```text
读取 Mock ERP / CRM 数据
校验数据关系
识别经营单元
加载经营单元知识档案
生成循环频率策略
生成商品、竞品、上新、流量、动作和报告结果
输出可供 business_view_service 包装的结构化结果
```

### 不负责

```text
不连接真实商家系统
不绕过平台接口限制
不保存真实客户隐私
不产生真实经营动作
```

## 5. Frontend 边界

### 负责

```text
web_demo/index.html
web_demo/app-v2.js
展示当前经营单元工作台
调用 /api/business/*
展示 Mock 数据下的经营建议、报告和待确认动作
```

### 不负责

```text
不恢复 web_demo/app.js
不恢复旧标题生成 UI
不恢复旧素材观察 UI
不实现未来多页面后台路由
```

## 6. Scripts / CI 边界

### 负责

```text
scripts/check_version_governance.py   检查版本、日志、旧入口残留
scripts/smoke_test_runtime.py         检查当前 workflow 主链路
scripts/smoke_test_api.py             检查当前产品 API
scripts/start_server.sh               本机启动
scripts/deploy_server.sh              服务器部署
.github/workflows/runtime-smoke-test.yml
                                      CI 执行治理检查和 smoke tests
```

### 不负责

```text
不运行 src/run_demo.py
不运行 evals/run_evals.py
不运行 scripts/material_observer.py
不检查旧 demo route
```

## 7. Documentation 边界

### 负责

```text
README.md                         当前主说明
docs/server-deploy.md             服务器部署说明
versioning/VERSION.md             当前版本与版本规则
versioning/CHANGELOG.md           工程版本日志
docs/product/CHANGELOG.md         产品主线日志
docs/product/mvp-scope.md         当前 MVP 范围
docs/product/module-boundary.md   当前模块边界
```

### 不负责

```text
不保留旧 demo 文档
不保留未来多页面蓝图作为当前说明
不保留已删除接口的验收命令
不把历史 Agent 设计放在 active trunk 文档中
```

## 8. 当前原则

```text
AI 可以建议，但不能越权执行。
系统可以生成待确认动作，但不能绕过人工确认。
报告可以辅助经营判断，但不能替用户承担经营责任。
版本治理必须先于 smoke tests 执行。
文档必须服务当前可运行主线，而不是召回旧模板。
```
