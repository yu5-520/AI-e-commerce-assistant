# 产品化后端接口说明

本项目的前端 UI 已从工程控制台升级为「AI 经营参谋」。对应后端也新增了产品化接口，前端优先使用 `/api/business/*`。

## 1. 接口分层

```text
/api/business/*    当前前端推荐使用的产品接口
/api/operation/*   operation 命名别名，便于后续产品命名实验
/api/demo/*        旧版完整工作流接口，保留兼容
/api/logs/*        内部运行记录接口，不建议直接暴露给普通商家 UI
/api/system/*      内部系统状态接口，不建议直接暴露给普通商家 UI
```

产品 UI 应尽量使用 `/api/business/*`，避免直接展示 workflow、logs、sqlite、rag 等工程概念。

## 2. 推荐给前端使用的接口

### 2.1 今日总览

```text
GET /api/business/today
```

用途：前端首页一次性读取本轮经营建议。

返回内容包含：

```text
priority          今天优先看的问题
action_status     待确认动作状态
operating_unit    当前经营单元
cycle             循环频率
cards             首页统计卡片
boundaries         使用边界
raw               完整内部结果，供前端兜底使用
```

### 2.2 经营单元

```text
GET /api/business/operating-unit
```

用途：展示系统根据 ERP 商品结构识别出的经营单元，以及日 / 周循环策略。

返回内容包含：

```text
unit_name
unit_id
source
dominant_product_group
reason
product_group_summary
keyword_signals
cycle_policy
```

### 2.3 数据体检

```text
GET /api/business/data-health
```

用途：展示当前商品、订单、库存、退款、客户数据是否足够支撑经营判断。

返回内容包含：

```text
status
summary
datasets
message
```

### 2.4 商品体检

```text
GET /api/business/products
```

用途：展示商品经营问题，例如库存高、利润薄、退款异常、承诺不清。

返回内容包含：

```text
title
summary
items
```

### 2.5 竞品机会

```text
GET /api/business/competitors
```

用途：展示同经营单元竞品里的价格、规格、差评和机会点。

返回内容包含：

```text
trigger_product
price_gap
bad_review_keywords
opportunity_actions
next_action
safe_use_policy
```

### 2.6 上新建议

```text
GET /api/business/listing
```

用途：展示最值得测试的上新候选和上新资料草案。

返回内容包含：

```text
candidate_count
top_candidate
title_draft
image_plan
sku_plan
compliance_checklist
next_action
safe_use_policy
```

### 2.7 流量复盘

```text
GET /api/business/traffic
```

用途：展示点击、转化、退款、ROI 的测试结果和回流动作。

返回内容包含：

```text
experiment_count
decision_summary
risk_summary
next_action
loopback_actions
items
safe_use_policy
```

### 2.8 待确认动作

```text
GET /api/business/actions
```

用途：展示需要商家确认后才能继续执行的动作。

返回内容包含：

```text
items[].action_id
items[].action_name
items[].risk_level
items[].risk_label
items[].suggestion
items[].status
items[].auto_execution_allowed
items[].policy_reason
```

### 2.9 经营报告

```text
GET /api/business/report
```

用途：读取本轮经营报告文本，适合前端预览或导出。

返回格式：纯文本 Markdown。

## 3. 前端调用建议

首页优先调用：

```text
GET /api/business/today
```

其余页面可以按需调用：

```text
经营单元页：GET /api/business/operating-unit
数据体检页：GET /api/business/data-health
待确认动作：GET /api/business/actions
经营报告页：GET /api/business/report
```

当前前端已优先调用 `/api/business/today`，并用 `raw` 字段兼容原有渲染结构。

## 4. 安全边界

产品接口只返回建议、草案、复盘和待确认动作。

不提供以下能力：

```text
自动真实上架
自动改价
自动投放
自动活动报名
自动客户触达
自动退款
自动复制竞品素材
```

涉及资金、客户、平台后台、不可回滚的动作，必须进入人工确认。
