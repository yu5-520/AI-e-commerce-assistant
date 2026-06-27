# PRODUCT_ARCHITECTURE

## 产品定位

AI ERP 企业级电商经营 SaaS 底座是一个任务驱动型 AI 经营系统。V12.3 的当前目标不是继续堆功能，而是把真实报表或接口数据进入系统后的主链路固定下来：报表布局识别、Block 级事实写入、经营对象身份主档、商品页事实展示、数据缺口留痕、任务证据闸门、账号权限和文档治理。

## 当前主导航

- 总览：经营同步结果、今日执行任务、风险事项、待复核事项、完成进度。
- 数据：Excel / CSV / JSON 上传、报表布局诊断、数据源同步、数据版本、导入记录、演示运行态清空。
- 经营：商品档案、竞品信号、上新测试、流量趋势、店铺标签、店铺权重。
- 任务：证据闸门后的执行队列、接收、提交、复核、完成。
- 日志：任务完成记录、复核记录、复盘候选、审计线索。
- 账号：老板、总管、运营、角色权限、店铺归属、ECS Demo 账号切换。
- 系统：健康检查、运行态诊断、Repository 状态、PostgreSQL cutover、LLM 状态。

## 核心用户角色

- 老板：查看经营结果、店铺权重、风险进度、总管复核结果和组织效率。
- 总管：拆分执行任务、派发任务、复核运营提交、沉淀经验。
- 运营：只接收高风险 / 高时效 / 需要人处理的执行任务，低风险信号在商品或店铺档案中查看。

## 当前主业务链路

```text
数据导入 / 接口同步
→ 当前账号识别
→ 报表布局 Agent 识别 Sheet / Block / metricScope
→ 原始行、Sheet 坐标、Block 坐标留痕
→ DataVersion / imported_report_rows / snapshots
→ operating_products / operating_stores 身份主档
→ product_metric_facts / store_metric_facts / traffic_source_facts 独立事实表
→ data_gap_events 普通缺口池
→ importDiagnostics 布局诊断
→ 商品页按事实表展示指标，缺失显示“未识别”
→ 趋势和业务信号 business_signals_v6
→ task_evidence_gate_service 按 metric_scope 取证
→ 高风险高时效执行任务 / 关键证据缺失补证任务
→ 任务详情报告
→ 证据提交 / 总管复核
→ 日志留痕 / RAG 记忆候选
→ 导入闭环反查
```

## 前端产品规则

```text
总览不是数据库状态页，不展示“已入库多少条记录”等后端明细。
经营模块不是任务入口，商品 / 竞品 / 上新 / 流量进入各自对象页。
店铺前端只显示真实店铺名称，不显示工程 ID。
经营页店铺状态必须一店一行，横向分区展示店铺、标签、商品状态和执行任务。
点击经营页店铺时，商品档案必须进入店铺作用域，不能共用全局商品列表。
商品档案必须通过 AppApi.product({storeId, storeName}) 读取后端清洗商品。
商品档案必须使用 objectId / archiveId 作为唯一档案 ID，不使用裸 productId 做详情主键。
商品页只展示资产和定位；完整交叉验证、SOP 和提交证明在任务详情页处理。
商品列表必须使用 product-ui.css 产品化卡片视觉，不回退成字段堆叠。
接口异常显示错误态，不展示本地业务兜底。
正常空数据展示“暂无数据”。
```

## 数据规则

```text
报表是批次，商品 / 店铺 / 流量来源才是分析主体。
同一个 productId 在不同店铺中必须形成不同 objectId / archiveId。
商品名称不作为商品同一性的主识别依据。
系统编码、商品链接、ERP 编码、SKU、店铺编码才是主轴。
operating_products / operating_stores 只保留身份定位、权限归属和来源坐标。
ROI / 支付金额 / 转化率 / 广告消耗 / 退款率等经营指标只写事实表。
商品整体指标只读 product_metric_facts。
流量来源指标只读 traffic_source_facts。
店铺指标只读 store_metric_facts。
事实表未命中显示“未识别”，不能显示 0，不能读对象缓存。
product ROI、traffic_source ROI、store ROI 互相隔离，不能跨口径覆盖。
```

## 任务规则

```text
字段缺失不是任务源，经营判断才是任务源。
普通缺口进入 data_gap_events 留痕，不进入任务栏。
只有经营判断被关键证据阻塞时，证据闸门才允许生成补证任务。
低风险信号沉淀为商品 / 店铺标签或观察项。
高风险 + 高时效 + 证据完整才进入执行队列。
高风险 + 需审批才进入审批生命周期。
任务进入执行队列后，详情页必须能打开。
```

## 架构边界

- 前端当前主入口：`web_demo/`。
- 历史前端目录：`frontend/`，不作为当前 UI 修改依据。
- 后端当前主入口：`src/api/main.py`。
- 当前 Demo 主存储：SQLite runtime。
- 生产迁移目标：PostgreSQL + Alembic + Repository。
- LLM / Agent 只增强报表布局识别、判断、标签、报告和任务草案，不直接执行真实经营动作。
- 任务状态、审批、复核、日志必须保持确定性。
- `architecture.py` 中历史架构接口只作验收展示，不作为当前 Demo 主链路入口。

## 当前不做

- 不保留旧版本过程文档作为当前架构依据。
- 不把历史 V1-V11 作为当前主链路依据。
- 不让前端直接承载核心业务判断。
- 不让 LLM 直接执行投放、下架、改价等真实经营动作。
- 不在生产环境绕过 cutover check 直接切 PostgreSQL 主写。
