# V12.2 报表布局 Agent 与指标事实层

V12.2 的目标不是继续扩大任务数量，而是把报表上传从“Sheet 画像”升级成“Sheet 内 Block 画像”：系统不只判断这个 Sheet 是什么表，还要判断这个 Sheet 里有哪些数据区块、每个区块属于什么经营口径。

## 1. 核心原则

- Agent 负责判断报表布局、区块边界和经营口径，不负责逐行读取全表。
- 代码脚本按 Agent 输出的 block 合同批量读取和入库。
- 一个 Sheet 可以同时拆出商品经营区、店铺汇总区、流量来源区和暂存区。
- 商品名称完整保留，但不作为商品同一性主键。
- 商品页负责商品定位和指标事实；任务页负责交叉验证、SOP 和复盘。
- 缺字段不直接生成任务；只有经营判断被关键证据阻塞时，任务证据闸门才允许生成补证任务。
- 指标事实必须可查询、可复用、可被任务证据闸门引用，不能只藏在商品 payload 里。
- 商品指标展示必须 fail-closed：事实表没有就是未识别，不能读对象缓存，不能用 0 伪装成功。
- ROI 必须按 product / traffic_source / store 三个口径隔离，不能互相覆盖。
- importDiagnostics 必须解释 Sheet → Block → Fact → Gap → Staging 的完整链路。

## 2. V12.2.0：报表布局 Agent

`report_profile_agent_service.py` 从 Sheet Profile 升级为 Block Profile。

旧结构：

```text
Sheet → targetTable
```

新结构：

```text
Sheet → blocks[] → targetTable / metricScope
```

Agent 输出示例：

```text
sheetProfiles[].blocks[] = {
  blockId,
  sheetName,
  blockType,
  targetTable,
  metricScope,
  range,
  rowStart,
  rowEnd,
  headerRows,
  confidence,
  issues
}
```

区块类型：

```text
product_metric_detail  → product_metric_facts    → metricScope=product
store_summary          → store_metric_facts      → metricScope=store
traffic_source_detail  → traffic_source_facts    → metricScope=traffic_source
staging_unknown        → staging_rows            → metricScope=unknown
```

## 3. V12.2.1：导入解析器保留行列坐标

`import_adapter_service.py` 现在保留：

```text
sheetRows
sheetMatrices
__source_sheet
__source_row_index
__source_header_row_index
__source_column_map
```

意义：每一条事实都能追溯到：

```text
来自哪个 Sheet
来自哪一行
来自哪个字段列
属于哪个 block
属于什么经营口径
```

这一步为导入诊断、审计、RAG 留痕和任务证据闸门提供来源坐标。

## 4. V12.2.2：事实表按 Block 写入

`metric_fact_store_service.py` 现在优先读取：

```text
reportProfile.sheetProfiles[].blocks
```

写入流程：

```text
blockRows + block.targetTable + block.metricScope
→ product_metric_facts / store_metric_facts / traffic_source_facts
```

事实表新增兼容列：

```text
source_block_id
source_row_index
source_column_index
metric_scope
source_block_type
```

这解决了同一张 Sheet 同时命中三种口径的问题：

```text
商品经营区 ROI → product_metric_facts.roi, metric_scope=product
流量来源区 ROI → traffic_source_facts.roi, metric_scope=traffic_source
店铺汇总区 ROI → store_metric_facts.roi, metric_scope=store
```

## 5. V12.2.3：经营对象只保留身份定位

`operating_object_store_service.py` 已收紧：

```text
operating_products
operating_stores
```

只保留：

```text
商品ID / SKU / ERP编码 / 链接
店铺ID / 店铺名称 / 平台
系统 STORE / SPU / LINK / SKU 编码
权限归属
来源 Sheet / 行号 / block_id
sourceDatasets / sourceDataVersions
```

不再保留：

```text
ROI
支付金额
广告消耗
点击率
转化率
退款率
毛利率
库存
payload.metricFacts
```

这一步是把“对象主档”和“经营账本”彻底拆开：对象主档是身份证，事实表才是经营账本。

## 6. V12.2.4：商品页 fail-closed

`product_archive_detail_service.py` 已收紧：

```text
商品整体指标区只读 product_metric_facts
流量来源区只读 traffic_source_facts
店铺层指标只读 store_metric_facts
```

如果事实表未命中：

```text
显示：未识别
```

不再显示：

```text
0
商品对象缓存
payload.metricFacts
流量来源 ROI 冒充商品 ROI
```

## 7. V12.2.5：ROI 口径隔离

ROI 不再是一个全局字段，而是三种不同事实：

```text
product_metric_facts.roi        → 商品整体 ROI
traffic_source_facts.roi        → 流量来源 ROI
store_metric_facts.roi          → 店铺汇总 ROI
```

任何一层 ROI 都不能覆盖另一层。

## 8. V12.2.6：导入诊断升级为布局诊断

`import_diagnostics_service.py` 现在输出：

```text
layoutMode = sheet_block_fact_gap_staging
stageTrace = Sheet → Block → Fact → Gap → Staging → EvidenceGate
sheets[].blocks[]
```

每个 block 会展示：

```text
blockId
blockType
targetTable
metricScope
range / rowStart / rowEnd / columnStart / columnEnd
factCount
gapCount
blockingGapCount
recognizedMetrics
rawFields
issues
acceptanceStatus
```

这一步专门解决 Demo 的信任问题：上传后可以直接看到系统到底把哪个 Sheet、哪个 block、哪个字段写进了哪张事实表，哪些只是普通缺口，哪些进入暂存。

暂存规则：

```text
无法路由 / 低置信 / 未知口径 / staging_unknown
→ Staging
→ 不进入商品页事实展示
→ 不生成经营任务
```

## 9. V12.2.7：任务证据闸门严格按 metric_scope 取证

`task_evidence_gate_service.py` 现在返回：

```text
metricScope
scopeLabel
requiredFactTables
forbiddenCrossScope
presentMetrics[].metricScope
presentMetrics[].factTable
```

取证规则：

```text
商品降投 / 商品投产任务 → 只查 product_metric_facts, metric_scope=product
流量来源任务 → 只查 traffic_source_facts, metric_scope=traffic_source
店铺经营任务 → 只查 store_metric_facts, metric_scope=store
```

这意味着：

```text
product ROI 缺失时，不能拿 traffic_source ROI 补。
traffic_source ROI 缺失时，不能拿 product ROI 补。
store ROI 缺失时，不能拿 product ROI 补。
```

证据缺失时，任务会降级为“经营证据补齐任务”，不会直接进入高风险执行。

## 10. 上传导入链路

```text
/api/data/upload/confirm
→ parse_upload_file，保留 row/column 坐标
→ compact_upload_meta，生成 Sheet + Block profile
→ confirm_report_import(auto_create_tasks=False)
→ upsert_operating_objects_from_import，只写身份主档
→ ingest_metric_facts_from_sheet_rows，按 blocks 写事实表
→ ingest_data_gaps_from_import
→ ingest_product_trends
→ generate_risk_tasks_for_signals
→ task_evidence_gate_service，严格按 metric_scope 取证
→ importDiagnostics，输出 Sheet → Block → Fact → Gap → Staging
```

旧规则不得因为字段缺失直接创建任务。

## 11. 验收接口

```text
/api/health
/api/data/metric-facts/summary
/api/data/data-gaps/summary
/api/data/import-diagnostics
```

ERA 文件上传后，至少检查：

```text
reportProfile.profileMode = sheet_to_block_profile
reportProfile.sheetProfiles[].blocks 存在
metricFactSync.mode = layout_block_metric_fact_routing
metricFactSync.blockSummaries 存在
operatingObjectSync.metricCacheDisabled = true
importDiagnostics.layoutMode = sheet_block_fact_gap_staging
importDiagnostics.stageTrace 存在
importDiagnostics.sheets[].blocks[] 存在
product_metric_facts 中 ROI 不被 traffic_source_facts 的 ROI 覆盖
商品详情 ROI 未命中时显示“未识别”，不显示 0 或缓存
任务 evidenceGate.metricScope 存在
任务 evidenceGate.requiredFactTables 与 metricScope 一致
任务 evidenceGate.forbiddenCrossScope 不为空
```

## 12. 当前版本边界

V12.2.7 已完成：

```text
V12.2.0：报表布局 Agent，Sheet Profile → Block Profile
V12.2.1：导入解析器保留行列坐标和 block 可追溯字段
V12.2.2：事实表按 block 写入 product/store/traffic facts
V12.2.3：经营对象只保留身份定位，取消商品指标对象缓存托底
V12.2.4：商品页 fail-closed，事实表没有就显示未识别
V12.2.5：ROI 口径隔离，product ROI / traffic ROI / store ROI 不互相替代
V12.2.6：导入诊断升级为 Sheet → Block → Fact → Gap → Staging 布局诊断
V12.2.7：任务证据闸门严格按 metric_scope 取证，禁止跨口径 ROI
```

下一步建议进入 V12.2.8：把 importDiagnostics 的布局诊断做成前端诊断卡片，让你在“数据”页面直接看到 Sheet → Block → Fact → Gap 的识别结果。
