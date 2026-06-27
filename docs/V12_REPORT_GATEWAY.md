# V12 / V12.1 报表画像 Agent 与指标事实层

V12 的目标不是继续扩大任务数量，而是把报表上传从“商品壳入库”升级成“报表画像 → 系统编码 → 指标事实 → 数据缺口池 → 任务证据闸门 → 导入诊断验收”。V12.1.6 已合并 V12.1.4、V12.1.5、V12.1.6 三个补丁：任务证据闸门、导入诊断接口、前端产品化基线。

## 1. 核心原则

- Agent 负责判断报表结构，不负责逐行读取全表。
- 代码脚本按 Agent 输出的画像批量读取数据。
- 商品名称完整保留，但不作为商品同一性主键。
- 商品页负责商品定位和指标事实；任务页负责交叉验证、SOP 和复盘。
- 缺字段不直接生成任务；只有经营判断被关键证据阻塞时，任务证据闸门才允许生成补证任务。
- 指标事实必须可查询、可复用、可被任务证据闸门引用，不能只藏在商品 payload 里。
- 多 Sheet 报表必须按 Sheet 画像分流，不能用扁平 rows 代替业务结构。
- 数据缺口必须聚合留痕，不能按商品逐条打扰运营。

## 2. 服务边界

### `metric_catalog_service.py`

统一字段字典和指标格式化，覆盖库存、客单价、支付金额、成本、毛利、ROI、广告、点击率、转化率、退款率、自然/付费流量等经营指标。

### `report_profile_agent_service.py`

读取上传文件的 sheet、表头、样本行，输出结构化画像：

```text
商品经营明细 → product_metric_facts
店铺经营汇总 → store_metric_facts
流量来源明细 → traffic_source_facts
未知或低置信 Sheet → staging / gap log
```

它只判断“怎么读”，不生成任务。

### `metric_fact_store_service.py`

负责创建并写入独立事实表：

```text
product_metric_facts
store_metric_facts
traffic_source_facts
```

V12.1.1 后上传确认优先走：

```text
ingest_metric_facts_from_sheet_rows(result, parsed, report_profile=...)
```

也就是按 `parsed.sheetRows + reportProfile.sheetProfiles[*].targetTable` 明确分流。

### `product_archive_detail_service.py`

V12.1.2 新增。把商品对象和独立事实表合并为商品详情：

```text
productPosition      商品定位
metricSections       成交与投产 / 成本与利润 / 流量与广告 / 库存与售后
trafficSourceFacts   流量来源事实
metricFactSummary    三类事实数量
taskHistorySummary   任务历史摘要
```

商品页只做资产展示，不展开 SOP。

### `data_gap_event_service.py`

V12.1.3 新增。创建并写入：

```text
data_gap_events
```

它只记录缺口，不创建任务。普通缺口默认为：

```text
is_decision_blocking = 0
status = logged
```

### `task_evidence_gate_service.py`

V12.1.4 新增。它不主动创建任务，只评估已经由经营异常 / 趋势信号产生的任务候选。

规则：

```text
经营判断成立
→ 读取任务类型需要的关键证据
→ 查询 product/store/traffic facts
→ 证据完整：保留经营执行任务
→ 关键证据缺失：降级为经营证据补齐任务
→ 同步把相关 data_gap_events 标记为 decision_blocking
```

这一步把任务生成从“字段缺失驱动”改成“经营判断缺证驱动”。

### `import_diagnostics_service.py`

V12.1.5 新增。输出导入验收报告：

```text
/api/data/import-diagnostics
```

返回：

```text
sheetCount
factSummary
gapSummary
sheets[].targetTables
sheets[].recognizedMetrics
sheets[].issues
acceptance.status
```

它用于回答 Demo 中最关键的问题：系统到底读到了哪些 Sheet、识别了哪些字段、写入了多少事实、哪些问题只是普通缺口、哪些问题真的阻塞判断。

## 3. 上传导入链路

```text
/api/data/upload/confirm
→ parse_upload_file
→ compact_upload_meta(reportProfile + sheetRows)
→ confirm_report_import(auto_create_tasks=False)
→ upsert_operating_objects_from_import
→ ingest_metric_facts_from_sheet_rows
→ ingest_data_gaps_from_import
→ ingest_product_trends
→ generate_risk_tasks_for_signals
→ task_evidence_gate_service
→ importDiagnostics
```

旧规则不得因为字段缺失直接创建任务。

## 4. 数据缺口池规则

会记录：

```text
metric_not_in_sheet
metric_sparse_values
identity_not_in_sheet
profile_issue
unrouted_sheet
```

不会做：

```text
商品A缺ROI → 任务
商品B缺ROI → 任务
商品C缺ROI → 任务
```

只有任务证据闸门判断“该缺口阻塞当前经营判断”时，才会升级为补证任务。

## 5. 任务证据闸门规则

不同任务需要不同证据：

```text
流量 / 投产高风险：ROI、广告消耗、点击率、转化率、支付金额、毛利率
库存高风险：库存数量、支付金额、转化率
利润高风险：毛利率、成本、支付金额
售后高风险：退款率、退款金额、退款订单数
趋势高风险：ROI、支付金额、毛利率、库存
```

证据缺失时，任务会变成：

```text
经营证据补齐任务
24小时内补充缺失指标
补齐前禁止降投、下架、加预算、调库存或调价格
补齐后重新触发任务证据闸门
```

## 6. 验收接口

```text
/api/data/metric-facts/summary      指标事实表统计
/api/data/data-gaps/summary         数据缺口池统计
/api/data/import-diagnostics        导入诊断验收
/api/health                         版本和入口检查
```

ERA 文件上传后，至少检查：

```text
factCount > 0
gapCount >= 0
importDiagnostics.acceptance.status 存在
metricFactSync.sheetSummaries 存在
dataGapSync.sheetSummaries 存在
riskTaskSync.evidenceBlockedTaskCount 存在
```

## 7. V12.1.6 前端产品化基线

- 前端资源版本统一到 12.1.6。
- `AppApi` 增加 metricFactsSummary、dataGapSummary、importDiagnostics。
- 商品详情继续使用产品化卡片，不回退字段堆叠。
- 金额和百分比以格式化结果为准，后端事实层输出 `displayValue`。
- 任务必须保留最低商品定位：商品ID、店铺、系统编码或事实来源。
- 前端接口失败时显示错误态，不展示本地业务兜底。

## 8. 当前版本边界

V12.1.6 已完成：

```text
V12.1.4 task_evidence_gate_service
V12.1.5 import_diagnostics_service
V12.1.6 frontend/api baseline
```

下一步再做时，应该进入 V12.2：把导入诊断做成前端诊断页，并把任务详情页的证据闸门区做成可读报告。
