# V9.3 前端模块一致性

V9.3 是前端模块一致性版本。

V9.0 建立 SaaS 企业级一致性底座，V9.1 固定仓库结构，V9.2 固定后端主流程，V9.3 的目标是防止后端能力继续把前端拆散：前端主模块保持稳定，V8/V9 后端能力通过套餐展示深度补强原模块。

## 1. V9.3 目标

```text
不新增前端业务主模块。
不把 V8 权重接口变成运营主页面。
不让基础版看到高阶权重算法细节。
同一模块根据套餐展示不同深度。
前端展示必须服从后端套餐、RAG、权限和审计边界。
```

## 2. 稳定前端主模块

V9.3 稳定模块：

```text
总览
经营单元
商品
竞品
上新
流量
报表中心
待办
日志
系统状态
账号
```

这些模块是当前前端产品入口，不因为后端新增权重、RAG、审批、执行回写能力而继续拆出大量主页面。

## 3. 后端能力进入原模块的规则

```text
店铺权重 -> 经营单元增强字段
商品权重 -> 商品模块增强字段
交叉验证 -> 详情页 / Agent 报告增强字段
任务强度 -> 待办任务增强字段
执行回写 -> 日志 / 复盘增强字段
RAG 证据 -> Agent 证据链增强字段
套餐范围 -> 所有模块展示深度控制
权限范围 -> 所有模块可见数据控制
```

这条规则的重点是：

```text
不是模块变多，
而是同一模块根据权限和套餐变深。
```

## 4. 模块职责

### 4.1 总览

入口：

```text
/api/modules/dashboard
```

职责：

```text
经营首页
最新导入
核心指标
当前任务队列
风险摘要
套餐化能力摘要
```

### 4.2 经营单元

入口：

```text
/api/modules/operating-unit
```

职责：

```text
店铺、店群、平台和经营归属视图
店铺权重摘要
店铺角色
拖累商品
租户范围
```

### 4.3 商品

入口：

```text
/api/modules/product
```

职责：

```text
商品经营问题
库存、点击、转化、ROI、退款
商品权重摘要
店铺影响
任务强度
证据链
```

### 4.4 竞品

入口：

```text
/api/modules/competitor
```

职责：

```text
竞品信号
价格、素材、上新和对照动作
市场信号
联动指标证据
候选任务证据
```

### 4.5 上新

入口：

```text
/api/modules/listing
```

职责：

```text
已有商品测试
竞品对照上新
测试任务
趋势上下文
RAG 证据
```

### 4.6 流量

入口：

```text
/api/modules/traffic
```

职责：

```text
推广
活动
自然流量
平台趋势
活动趋势
流量权重影响
```

### 4.7 报表中心

入口：

```text
/api/modules/report
```

职责：

```text
报表上传
字段预览
确认导入
版本记录
回滚
Demo 清理
导入影响摘要
```

### 4.8 待办

入口：

```text
/api/modules/todo
```

职责：

```text
统一任务池
任务生命周期
提交证据
审批状态
执行证据要求
复核指标
完成归档
```

### 4.9 日志

入口：

```text
/api/modules/log
```

职责：

```text
完成记录
执行回写
复盘结果
审计摘要
RAG 经验候选
```

### 4.10 系统状态

入口：

```text
/api/system/security
/api/system/repositories
/api/architecture/p0
/api/architecture/v9/backend-flow
/api/architecture/v9/frontend-modules
```

职责：

```text
安全状态
Repository 状态
部署模式
RAG namespace
功能开关
审计状态
架构状态
```

### 4.11 账号

入口：

```text
/api/accounts
```

职责：

```text
账号
角色
店铺归属
可见范围
套餐范围
权限边界
```

## 5. 三层展示深度

### 5.1 基础版 / Starter

```text
展示深度：basic
显示：基础报表、商品问题、商品任务、共享脱敏 RAG 证据
隐藏：店铺权重、商品权重、平台趋势深度联动、活动趋势深度联动、审批流细节、私有部署状态
```

### 5.2 专业版 / Professional

```text
展示深度：weighted_operation
显示：店铺权重、商品权重、平台趋势、活动趋势、租户 RAG 证据、任务强度
隐藏：企业私有化部署、受托运维、高层授权配置修改、private RAG 维护链路
```

### 5.3 企业版 / Enterprise

```text
展示深度：private_governance
显示：私有化部署、private RAG、受托运维、高层审批、审计留痕、执行回写、复盘记录
隐藏：无；但所有关键操作仍必须走权限和审批链路
```

## 6. 禁止的前端扩张

```text
不要为店铺权重新增独立主模块，补强经营单元。
不要为商品权重新增独立主模块，补强商品模块。
不要为交叉验证新增独立主模块，补强任务详情和 Agent 报告。
不要为执行回写新增独立主模块，补强日志和复盘。
不要把 architecture/v8 调试入口当成运营主页面。
不要把套餐隔离只做成前端隐藏按钮，后端必须同步控制。
```

## 7. 架构可视入口

新增入口：

```text
/api/architecture/v9/frontend-modules
```

主要文件：

```text
src/services/v93_frontend_module_contract_service.py
src/api/routes/architecture.py
```

这个接口只输出前端模块契约，不生成业务任务，不执行经营动作。

## 8. CI 检查

V9.3 新增：

```text
scripts/check_frontend_module_consistency.py
```

检查内容：

```text
V9.3 文档存在
V9.3 服务存在
/api/architecture/v9/frontend-modules 路由存在
README 指向 V9.3
VERSION / main.py / health / Agent registry 版本一致
web_demo/index.html 前端缓存为 9.3.0
稳定主模块存在
禁止新增的主模块名称没有进入导航
workflow 运行 frontend module consistency check
```

## 9. Definition of Done

```text
Current Version = v9.3.0。
FastAPI API_VERSION = 9.3.0。
Health API_VERSION = 9.3.0。
Agent registry version = 9.3.0。
新增 docs/V9_FRONTEND_MODULE_CONSISTENCY.md。
新增 src/services/v93_frontend_module_contract_service.py。
新增 /api/architecture/v9/frontend-modules。
新增 scripts/check_frontend_module_consistency.py。
GitHub Actions 跑 frontend module consistency check。
README、VERSION、CHANGELOG、前端缓存全部对齐 V9.3。
```
