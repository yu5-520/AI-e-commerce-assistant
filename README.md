# AI 垂直货架电商经营循环系统 MVP

> 一个面向垂直类目的货架电商 AI 工作流原型：先接入商家已有 ERP / CRM 数据，完成商品、库存、订单、退款、客户和售后的经营判断；再围绕同类目竞品做比对；再生成优化、上新和流量测试方案；最后把测试结果回流到经营判断系统，形成持续循环。

## 1. 项目定位

本项目当前主定位是：

> **AI 垂直货架电商经营循环系统 MVP**

它不是泛电商大而全系统，也不是只生成标题 / 主图的一次性工具，而是一个围绕垂直类目商家的 **Workflow-first，Agent-ready** 经营循环原型。

真实商家的接受路径通常不是一上来就“全自动铺货”，而是：

```text
先接入已有商品、库存、订单、退款、客户、售前售后
↓
用 AI 做 ERP + CRM 经营判断
↓
由经营问题触发同类目竞品比对
↓
再生成优化老品 / 上新增长 / 流量测试方案
↓
测试数据回流到经营判断系统
↓
循环运行
```

一句话：

> **垂直类目定规则，ERP 管货，CRM 管人，竞品找差距，上新补增长，流量测结果，循环定方向，RPA 做文档任务，日志做复盘。**

## 2. 当前版本边界

当前仓库已经完成的是 **V0.8：ERP + CRM 经营判断底座**，并已接入 **V0.9：垂直类目配置层**、**V1.0：同类目竞品比对系统**、**V1.1：同类目上新增长系统**、**V1.2：流量测试与数据回流系统** 和 **V1.3：完整经营循环总控** 的 Mock 骨架。

当前可运行能力：

```text
防晒服垂直类目档案
↓
Mock ERP / CRM 数据
↓
数据导入与校验
↓
商品经营诊断
↓
同类目竞品比对
↓
同类目上新增长草案
↓
流量测试与数据回流
↓
经营循环总控
↓
CRM 客户分层
↓
轻量 RAG 知识召回
↓
RPA 任务草案
↓
人工确认
↓
报告与日志回写
```

当前尚未实现，但已经纳入架构升级路线的能力：

```text
业务档案长期落库
第二个垂直类目复制
更完整 API / 前端页面
Embedding + 向量库 RAG
真实低风险 RPA Adapter
```

## 3. 核心架构

```text
0. 垂直类目知识层
类目规则 / 价格带 / 客群 / 季节性 / 售后风险 / 竞品维度
↓
1. ERP + CRM 经营判断系统
已有商品 / 库存 / 订单 / 退款 / 客户 / 售前售后
↓
2. 同类目竞品比对系统
价格 / 标题 / 主图 / SKU / 评价 / 差评 / 活动 / 售后承诺
↓
3. 同类目上新增长系统
新品候选 / 铺货草案 / 标题主图 / SKU / 定价 / 测试计划
↓
4. 流量测试与数据回流系统
曝光 / 点击 / 转化 / 退款 / ROI / 库存变化 / 客户反馈 / 复盘日志
↓
5. 经营循环总控
决定下一轮回到 ERP、CRM、竞品、上新、流量测试或继续循环
↓
回到 ERP + CRM 经营判断系统
```

## 4. 当前可运行内容

### 4.1 命令行 Mock Workflow

```bash
python -m src.run_demo
```

运行后生成：

```text
outputs/category_context.json
outputs/product_diagnosis.json
outputs/customer_segmentation.json
outputs/competitor_analysis.json
outputs/listing_growth_plan.json
outputs/traffic_feedback_report.json
outputs/operating_loop_summary.json
outputs/rpa_task_draft.json
outputs/approval_required_tasks.json
outputs/rag_retrieval_context.json
outputs/demo_report.md
```

### 4.2 Evals 评测

```bash
python evals/run_evals.py
```

运行后生成：

```text
evals/results/latest_results.json
```

### 4.3 FastAPI 后端

```bash
pip install -r requirements.txt
uvicorn src.api.main:app --reload
```

常用接口：

```text
GET  /api/health
GET  /api/demo/run
GET  /api/demo/report
GET  /api/evals/run
POST /api/tasks/{task_id}/approve
POST /api/tasks/{task_id}/reject
GET  /api/tasks/status
```

### 4.4 前端 Demo

启动 FastAPI 后打开：

```text
http://127.0.0.1:8000/
```

或：

```text
http://127.0.0.1:8000/web_demo/index.html
```

页面会优先调用 `/api/demo/run`。如果没有启动 API，直接打开 `web_demo/index.html` 时会自动回退到本地样例数据。

## 5. 当前已经完成

```text
统一产品文档
+ 防晒服垂直类目档案
+ 类目上下文加载模块
+ 同类目竞品 Mock 数据
+ 同类目竞品比对模块
+ 供应链货盘 Mock 数据
+ 同类目上新增长模块
+ 流量测试 Mock 数据
+ 流量测试与回流模块
+ 经营循环总控模块
+ Mock ERP / CRM 数据
+ Python Mock Workflow
+ 简单 RAG 检索
+ RPA 任务草案
+ Human-in-the-loop 风控
+ Evals
+ FastAPI API
+ 前端 fetch API / 本地 fallback
+ SQLite / JSONL 日志记录
```

## 6. 当前核心模块

### 6.1 垂直类目配置

```text
knowledge_base/category_profiles/sun_protection_clothing.md
src/category/
```

当前已加入防晒服类目样板，类目上下文会进入 Mock Workflow，并输出到 `outputs/category_context.json`。

### 6.2 同类目竞品比对

```text
examples/category_sun_protection/mock_competitors.csv
src/competitor/
```

当前能力：竞品数据读取、价格带比对、SKU 结构摘要、差评机会分析、触发商品选择、下一步动作建议、安全使用边界。

当前不做真实平台数据抓取，只使用 Mock / 手动准备的竞品数据。

### 6.3 同类目上新增长

```text
examples/category_sun_protection/mock_supplier_products.csv
src/listing/
```

当前能力：货盘数据读取、新品候选评分、利润空间判断、库存承接判断、类目卖点匹配、竞品差评机会承接、标题草案、主图方向、SKU 建议、定价建议、合规检查表、安全使用边界。

当前只生成上新资料草案，不自动上架、不自动改价、不自动投放。

### 6.4 流量测试与数据回流

```text
examples/category_sun_protection/mock_traffic_tests.csv
src/traffic_test/
```

当前能力：流量测试数据读取、点击率诊断、转化率诊断、退款率诊断、ROI 诊断、下一步动作判断、回流动作生成、测试复盘报告、安全使用边界。

回流方向：

```text
点击低 → 回流标题 / 主图复查
转化低 → 回流 SKU / 价格 / 详情页承接
退款高 → 回流售后归因
ROI 低 → 回流预算止损
指标健康 → 小幅放量但继续人工确认
```

当前只生成复盘和下一步动作建议，不操作真实广告账户、不自动加预算、不自动改价。

### 6.5 经营循环总控

```text
src/operating_loop/
```

当前能力：汇总商品风险、客户风险、竞品比对、上新增长、流量测试回流，判断下一轮进入哪个模块，并生成下一轮动作计划。

下一轮可能进入：

```text
CRM 售后归因
ERP 利润与预算复核
竞品标题 / 主图复查
上新 SKU / 定价复查
ERP 商品风险复查
可控小幅放量复核
继续经营循环
```

完整循环默认要求人工确认，不允许自动执行平台侧关键动作。

### 6.6 ERP / 表格数据接入

MVP 阶段优先支持 Mock CSV / Excel 数据，不直接接入真实商家后台。

### 6.7 CRM 客户数据接入

MVP 阶段只使用脱敏 Mock 数据，不保存真实姓名、手机号、微信号、地址等隐私信息。

### 6.8 AI / RAG 决策层

当前版本使用规则引擎模拟 AI 诊断，用关键词检索模拟 RAG。RAG 已支持读取 `knowledge_base/category_profiles/` 下的垂直类目知识。

### 6.9 Human-in-the-loop 人工确认

关键动作必须由用户确认：改标题、改主图、改价、报名活动、增加投放预算、下架 / 清货、批量回写 ERP / CRM、客户触达、优惠券策略执行和售后处理动作。

### 6.10 RPA 任务草案层

MVP 阶段生成低风险任务草案，不执行真实自动化。

## 7. 下一阶段升级路线

```text
V0.8：ERP + CRM 经营判断系统（当前已跑通）
V0.9：垂直类目配置层（当前已接入最小骨架）
V1.0：同类目竞品比对系统（当前已接入 Mock 骨架）
V1.1：同类目上新增长系统（当前已接入 Mock 骨架）
V1.2：流量测试与数据回流系统（当前已接入 Mock 骨架）
V1.3：完整货架电商经营循环系统（当前已接入 Mock 骨架）
```

详细升级清单见：

```text
docs/system-upgrade-roadmap.md
```

## 8. 重点目录

```text
examples/        Mock ERP / CRM 数据 + 垂直类目样例数据
knowledge_base/  简单 RAG 知识片段，含垂直类目知识
src/             Python Mock Workflow 与 API
evals/           最小评测
web_demo/        前端 Demo
docs/            架构、PRD、升级路线与风险边界
```

核心入口：

```text
src/run_demo.py        命令行工作流
src/api/main.py        FastAPI 后端
web_demo/index.html    前端 Demo
evals/run_evals.py     Evals 运行器
```

## 9. 风险边界

本项目定位是：

> **AI 辅助经营决策 + RPA 可控任务草案原型，而不是无约束自动化系统。**

本产品不做：

- 未经确认的真实上架、改价、投放、活动报名。
- 未经确认的客户触达、批量消息、退款或好评诱导。
- 侵权素材复制、虚假功效宣传或平台规则不允许的运营方式。
- 保存真实客户姓名、手机号、微信号、地址等隐私数据。
