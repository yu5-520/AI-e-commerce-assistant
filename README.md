# AI + RPA + ERP + CRM 电商经营自动化工作台 MVP

> 一个 Workflow-first 的电商 AI 自动化工作流原型：以 ERP / 店铺后台 / 表格数据和 CRM 客户数据为输入，通过 RAG 知识增强、AI 诊断、人工确认、RPA 执行与日志回写，帮助商家完成商品运营分析、SKU 利润判断、库存预警、客户分层、售后归因、活动准备和复盘迭代。

## 1. 项目定位

本项目从原来的“拼多多 AI 商品增长工作台”升级为 **AI + RPA + ERP + CRM 电商经营自动化工作台 MVP**。

它不是简单的标题生成器，也不是一次性上新助手，更不是深度自治 Agent 系统，而是一个 **Workflow-first，Agent-ready** 的 AI 工作流项目：

- Workflow-first：当前以确定性业务流程为主，AI 作为判断与生成节点，RPA 作为低风险执行节点。
- Agent-ready：未来可以在低风险场景逐步引入 Agent，例如数据异常排查、RAG 检索选择、报告生成和失败原因分析。

新的核心目标是：

- 将商品、订单、库存、SKU、成本、售价、活动价、退款、投放数据统一进入商品运营档案。
- 将客户、标签、复购周期、售后记录、触达记录、客户价值统一进入客户运营档案。
- 通过 AI / RAG 判断商品问题、客户问题和经营问题：曝光不足、点击不足、转化不足、库存风险、利润风险、复购风险、售后风险或合规风险。
- 生成可执行的运营方案：标题测试、主图方向、SKU 调整、价格测试、库存处理、客户分层、复购建议、售后归因、活动准备、复盘报告。
- 通过 Human-in-the-loop 人工确认机制，将改价、活动报名、投放、客户触达、ERP / CRM 回写等高风险动作控制在用户确认之后。
- 使用 RPA 执行低风险、高重复的运营动作，例如整理日报、生成活动表、生成客户清单、回写测试记录、导出 SKU 建议表。
- 记录每一轮 AI 判断、RAG 召回、用户确认、RPA 执行和数据回流，让系统持续迭代。

一句话：

> **ERP 管货，CRM 管人，RAG 补知识，AI 做判断，人工控风险，RPA 做执行，日志做复盘。**

## 2. 核心架构

```text
ERP 数据层
商品 / 订单 / 库存 / 成本 / SKU / 活动 / 退款
↓
CRM 数据层
客户 / 标签 / 复购 / 售后 / 触达 / 客户价值
↓
数据接入与清洗层
字段映射 / 数据清洗 / 缺失值检查 / Mock 数据导入
↓
商品档案 + 客户档案
商品运营记忆 / 客户运营记忆 / 历史测试 / 售后归因
↓
RAG 知识增强层
商品档案库 / 平台规则库 / 合规风控库 / 运营方法库 / 客服 SOP 库
↓
AI 诊断与策略生成层
商品诊断 / SKU 利润测算 / 库存预警 / 客户分层 / 复购判断 / 售后归因
↓
Human-in-the-loop 人工确认层
改价 / 活动 / 投放 / 客户触达 / ERP 回写 / CRM 回写必须确认
↓
RPA 执行任务层
生成日报 / 导出表格 / 生成活动表 / 客户清单 / 复盘报告 / 任务清单
↓
日志回写与复盘层
AI 报告 / RAG 召回记录 / 用户确认记录 / RPA 执行日志 / 下一轮动作
```

## 3. 当前可运行内容

### 3.1 Mock Workflow 脚本

运行：

```bash
python -m src.run_demo
```

生成：

```text
outputs/product_diagnosis.json
outputs/customer_segmentation.json
outputs/rpa_task_draft.json
outputs/rag_retrieval_context.json
outputs/demo_report.md
```

### 3.2 Evals 评测

运行：

```bash
python evals/run_evals.py
```

生成：

```text
evals/results/latest_results.json
```

### 3.3 静态前端 Demo

直接用浏览器打开：

```text
web_demo/index.html
```

页面展示三段式流程：

```text
导入 Mock 数据
↓
生成 AI / RAG 诊断
↓
生成 RPA 任务草案
↓
查看人工确认项
```

## 4. 目标用户

### 4.1 电商运营新人 / 小商家

典型需求：

- 不知道如何从商品、订单、库存、退款数据里判断问题。
- 不知道标题、主图、价格、SKU 哪个变量优先测试。
- 没有固定复盘流程，每次改图、改标题、改价都无法追溯。

### 4.2 有 ERP / 表格管理习惯的电商团队

典型需求：

- 需要把商品、订单、库存、活动价、退款数据拉通分析。
- 希望自动生成运营日报、库存预警、活动准备表和 SKU 利润建议。
- 希望将重复性整理工作交给 RPA，但关键动作仍由人工确认。

### 4.3 有 CRM / 客户运营需求的电商团队

典型需求：

- 需要识别高价值客户、沉睡客户、价格敏感客户、售后敏感客户。
- 希望根据订单、退款、互动记录进行客户分层和复购判断。
- 希望自动生成客户运营任务表、售后归因报告和复购建议，但不希望系统未经确认自动触达客户。

### 4.4 AI 产品 / RPA 自动化学习场景

典型需求：

- 需要一个真实业务场景来展示 AI 工作流、RAG 架构、数据建模、RPA 任务编排、CRM 分析和合规风控。
- 需要证明 AI 不只是生成文案，而是可以进入业务流程、数据链路和自动化执行层。

## 5. 核心模块

### 5.1 ERP / 表格数据接入

MVP 阶段优先支持 Mock CSV / Excel 数据，不直接接入真实商家后台。

数据类型：

- 商品数据：商品 ID、标题、类目、成本、售价、库存、SKU。
- 订单数据：订单号、商品 ID、成交金额、成交时间、退款状态。
- 库存数据：当前库存、可售库存、补货状态、库存预警线。
- 退款数据：退款原因、退款金额、售后备注。
- 活动数据：活动价、活动库存、活动周期、毛利风险。

### 5.2 CRM 客户数据接入

MVP 阶段只使用脱敏 Mock 数据。

数据类型：

- 客户数据：customer_id、昵称哈希、首单时间、最近购买时间、消费金额、退款次数。
- 客户标签：高价值客户、新客、沉睡客户、价格敏感、活动敏感、售后敏感、复购潜力、流失风险。
- 客户互动：客服咨询、售后反馈、优惠券触达、活动提醒、复购提醒、投诉反馈。
- 客户分群：RFM 分层、人群规则、推荐动作、风险等级。

不保存真实姓名、手机号、微信号、地址等隐私信息。

### 5.3 商品档案与客户档案

每个商品建立独立运营档案，保存商品基础信息、ERP 同步记录、标题版本、主图方案、SKU 方案、库存快照、订单与退款摘要、活动记录、AI 诊断报告、用户确认记录、RPA 执行日志和下一轮复盘建议。

每个客户建立脱敏运营档案，保存客户基础摘要、RFM 分层、客户标签、复购周期、售后记录摘要、互动记录摘要、AI 客户运营建议、触达任务草案和人工确认记录。

### 5.4 AI / RAG 决策层

AI 不直接替用户做高风险操作，而是基于业务数据和知识库输出判断：

- 商品运营诊断
- SKU 利润测算
- 库存预警
- 订单 / 退款异常分析
- 客户分层
- 复购判断
- 售后归因
- 标题与主图测试建议
- 活动报名准备
- 合规风险检查
- 下一轮运营动作

RAG 知识源分为商品档案库、客户档案库、平台规则库、合规风控库、运营方法库和客服 SOP 库。

### 5.5 Human-in-the-loop 人工确认

关键动作必须由用户确认：改标题、改主图、改价、报名活动、增加投放预算、下架 / 清货、批量导入或回写 ERP、批量回写 CRM、客户触达、优惠券策略执行和售后处理动作。

AI 只生成建议、草案、检查表、风险提示和执行方案；RPA 只在用户确认后执行低风险或可回滚任务。

### 5.6 RPA 执行任务层

MVP 阶段优先实现低风险自动化：

- 生成运营日报
- 整理商品测试记录
- 生成活动报名准备表
- 生成 SKU 价格建议表
- 生成客户分层表
- 生成复购任务表
- 生成售后归因表
- 导出 Excel / CSV
- 回写本地测试记录
- 生成下一轮任务清单

不在 MVP 阶段直接执行：自动上架、自动改价、自动修改主图、自动报名活动、自动投放广告、自动下架商品、自动群发消息、自动处理退款、自动诱导好评。

## 6. 文档目录

- [`docs/demo-runbook.md`](docs/demo-runbook.md)：Mock Workflow 运行说明
- [`docs/frontend-demo-design.md`](docs/frontend-demo-design.md)：前端三段式 Demo 设计
- [`docs/product-architecture.md`](docs/product-architecture.md)：原 AI 商品增长工作台产品架构
- [`docs/mvp-prd.md`](docs/mvp-prd.md)：MVP 产品需求文档
- [`docs/ai-workflows.md`](docs/ai-workflows.md)：AI 工作流与生成逻辑
- [`docs/data-model.md`](docs/data-model.md)：核心数据结构
- [`docs/compliance-and-risk.md`](docs/compliance-and-risk.md)：合规与风险边界
- [`docs/erp-rpa-architecture.md`](docs/erp-rpa-architecture.md)：ERP / RPA 总体架构
- [`docs/erp-data-mapping.md`](docs/erp-data-mapping.md)：ERP 字段映射
- [`docs/rag-design.md`](docs/rag-design.md)：RAG 知识库架构
- [`docs/rpa-workflows.md`](docs/rpa-workflows.md)：RPA 工作流场景
- [`docs/human-approval-design.md`](docs/human-approval-design.md)：人工确认机制
- [`docs/roadmap-ai-rpa-erp.md`](docs/roadmap-ai-rpa-erp.md)：AI + RPA + ERP 迭代路线
- [`docs/crm-analysis.md`](docs/crm-analysis.md)：CRM 客户运营分析
- [`docs/crm-data-model.md`](docs/crm-data-model.md)：CRM 数据模型
- [`docs/customer-segmentation.md`](docs/customer-segmentation.md)：客户分层设计
- [`docs/workflow-vs-agent-boundary.md`](docs/workflow-vs-agent-boundary.md)：Workflow 与 Agent 边界
- [`docs/evals-and-monitoring.md`](docs/evals-and-monitoring.md)：Evals 与监控设计

## 7. 风险边界

本项目定位是：

> **AI 辅助经营决策 + RPA 可控执行原型，而不是违规自动化工具，也不是无约束 Agent 自治系统。**

本产品不提供以下能力：

- 绕过平台审核
- 擦边营销话术
- 虚假功效宣传
- 侵权素材复制
- 未授权品牌词使用
- 自动化违规爬虫
- 绕过验证码或平台风控
- 未经用户确认的自动上架、自动改价、自动投放、自动报名活动
- 未经用户确认的客户触达、自动群发、自动退款或诱导好评
- 保存真实客户姓名、手机号、微信号、地址等隐私数据
