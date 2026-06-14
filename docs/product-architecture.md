# 产品架构：AI + RPA + ERP + CRM 电商经营自动化工作台

## 1. 统一产品定位

本仓库的主产品定位统一为：

> **AI + RPA + ERP + CRM 电商经营自动化工作台 MVP**

它不是单点标题生成器，也不是只服务某一个平台的运营小工具，而是一个面向货架电商经营流程的 **Workflow-first，Agent-ready** 工作台原型。

统一叙事：

```text
ERP 管货
CRM 管人
RAG 补知识
AI 做诊断
人工控风险
RPA 生成任务草案
日志做复盘
```

旧版“拼多多商品增长 / 商品裂变”不再作为主产品定位，只保留为一个平台场景案例：用于验证白牌商品、低预算测款、标题/主图/SKU/活动复盘等货架电商问题。

## 2. 架构目标

本产品的目标不是一次性生成电商文案，而是让商家围绕商品、库存、订单、客户、售后和活动形成一个可追踪、可审批、可复盘的 AI 工作流。

核心目标：

1. 把 ERP / 表格里的商品、订单、库存、退款数据接入工作流。
2. 把 CRM / 客户表里的客户分层、复购、售后、互动记录接入工作流。
3. 用规则引擎 + RAG 知识增强完成可解释诊断。
4. 生成低风险 RPA 任务草案，而不是直接执行平台动作。
5. 对改价、活动、投放、客户触达、退款等关键动作加入人工确认。
6. 用日志、审批记录、报告记录沉淀每一次工作流运行结果。
7. 后续可以逐步把规则节点替换为 LLM / Embedding / Agent 节点。

## 3. 总体分层

```text
数据源层
ERP / 店铺后台 / Excel / CSV / CRM
↓
数据接入与校验层
字段映射 / 缺失检查 / 数值校验 / 关系校验
↓
经营对象层
商品档案 / 客户档案 / 订单记录 / 库存状态 / 售后记录
↓
知识增强层
平台规则 / 合规风控 / 运营方法 / 客服 SOP / 活动规则
↓
AI 诊断层
商品诊断 / SKU 利润判断 / 库存预警 / 客户分层 / 售后归因
↓
任务草案层
日报 / SKU 建议表 / 活动准备表 / 客户分层表 / 售后归因表 / 复盘报告
↓
人工确认层
审批 / 拒绝 / 备注 / 操作留痕 / 高风险拦截
↓
日志与复盘层
WorkflowRun / ExecutionLog / ApprovalRecord / ReportRecord / 下一轮动作
```

## 4. 当前实现映射

| 架构层 | 当前实现 | 说明 |
|---|---|---|
| 数据源层 | `examples/*.csv` | 使用 Mock ERP / CRM 数据验证流程 |
| 数据接入与校验层 | `src/services/data_import_service.py` | 校验字段、数值、表关系，并生成导入记录 |
| 经营对象层 | `src/data_loader/load_mock_data.py` | 当前以 CSV 字典对象承载，后续升级为业务表 |
| 知识增强层 | `knowledge_base/*.md` + `src/rag/simple_retriever.py` | 当前为关键词检索，后续可替换为 Embedding + 向量库 |
| AI 诊断层 | `src/diagnosis/*` | 规则引擎模拟 AI 诊断，保持结构化输出契约 |
| 任务草案层 | `src/rpa_tasks/generate_task_draft.py` | 只生成 RPA 草案，不执行真实平台动作 |
| 人工确认层 | `src/services/approval_service.py` | 记录 approve / reject 状态，并写入 SQLite / JSONL |
| 日志与复盘层 | `src/services/log_service.py` + `src/repositories/sqlite_repository.py` | 沉淀 WorkflowRun、ExecutionLog、ApprovalRecord、ReportRecord |
| API 层 | `src/api/main.py` | 当前唯一主后端入口 |
| 前端层 | `web_demo/` | 当前唯一主前端演示入口 |

## 5. 核心工作流

### 5.1 数据导入工作流

```text
Mock CSV / Excel
↓
字段完整性校验
↓
数值合法性校验
↓
商品、订单、库存、退款、客户、标签、互动关系校验
↓
生成 ImportRecord
↓
写入 WorkflowRun / ExecutionLog
```

当前不直接接入真实店铺后台，也不保存真实客户手机号、地址、微信号等隐私数据。

### 5.2 商品经营诊断工作流

```text
商品表 + 订单表 + 库存表 + 退款表
↓
成本 / 售价 / 活动价 / 物流成本计算
↓
库存压力判断
↓
退款异常判断
↓
敏感类目合规判断
↓
输出风险等级、风险原因和建议动作
```

当前使用透明规则模拟 AI 节点，后续可升级为：

```text
规则前置校验 + RAG 证据召回 + LLM 诊断 + 结构化输出校验
```

### 5.3 CRM 客户分层工作流

```text
客户表 + 客户标签 + 客户互动记录
↓
订单次数 / 消费金额 / 退款次数 / RFM / 互动情绪判断
↓
高价值客户 / 新客 / 沉睡客户 / 售后敏感客户分层
↓
输出客户标签、分层依据、风险提示和建议动作
```

客户触达类动作默认不自动执行，只输出任务草案和人工确认项。

### 5.4 RPA 任务草案工作流

```text
商品诊断结果 + 客户分层结果
↓
生成日报、SKU 价格建议表、售后归因表、客户分层表、复购任务表
↓
根据任务类型做风险分级
↓
全部进入人工确认
↓
只记录审批状态，不执行真实平台动作
```

RPA 在当前产品里不是“自动乱点后台”，而是低风险执行材料的生成层。

### 5.5 日志回写与复盘工作流

```text
WorkflowRun
↓
ExecutionLog
↓
ApprovalRecord
↓
TaskStatus
↓
ReportRecord
↓
下一轮诊断输入
```

这部分是产品从“一次性 AI 工具”升级为“经营工作台”的核心。

## 6. 风险边界

MVP 阶段默认保守：

- 不自动上架。
- 不自动改价。
- 不自动报名活动。
- 不自动增加广告预算。
- 不自动群发客户消息。
- 不自动退款。
- 不绕过验证码或平台风控。
- 不生成违规爬虫方案。
- 不保存真实隐私数据。

涉及资金、客户触达、平台后台写入和不可回滚动作时，必须 Human-in-the-loop。

## 7. 统一目录策略

当前主线目录：

```text
src/             当前主后端、工作流、诊断、RAG、审批、日志
web_demo/        当前主前端演示
examples/        Mock ERP / CRM 数据
knowledge_base/  RAG 知识片段
evals/           最小评测
logs/            本地运行日志与 SQLite 文件
docs/            当前产品文档
```

旧版目录处理原则：

```text
backend/         旧 http.server 后端，已从主架构中移除
frontend/        旧静态前端，如无依赖则不再作为主入口
scripts/pdd_*    旧平台命名脚本，统一改为 ecommerce_workflow_* 命名
```

主入口统一为：

```text
python -m src.run_demo
uvicorn src.api.main:app --reload
http://127.0.0.1:8000/
```

## 8. 后续架构升级方向

### V0.9：数据接入增强

- Excel 上传。
- 字段映射 UI。
- 导入失败提示。
- 数据样例模板下载。

### V1.0：业务档案落库

- 商品档案表。
- 客户档案表。
- 商品经营实验表。
- AI 报告与任务草案关联。

### V1.1：RAG 升级

- 知识片段 metadata。
- 检索 trace。
- Embedding + 向量库。
- RAG 证据参与诊断。

### V1.2：Agent-ready 节点

- 数据异常排查 Agent。
- 报告生成 Agent。
- 失败原因分析 Agent。
- 仅限低风险、可回滚、可审计场景。

### V1.3：真实 RPA Adapter

- 只接低风险动作。
- 默认 dry-run。
- 用户二次确认。
- 每次执行必须写日志。

## 9. 架构结论

本产品的核心价值不是“AI 生成得快”，而是把电商经营动作放进一个可解释、可确认、可追踪、可复盘的工作流里。

最终目标：

> 让商家从“凭感觉改标题、改图、改价”升级为“基于 ERP / CRM 数据和 AI 诊断的可控经营自动化”。
