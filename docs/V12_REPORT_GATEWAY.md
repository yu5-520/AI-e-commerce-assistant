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

## 5. 商品详情 fail-closed

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

## 6. 上传导入链路

```text
/api/data/upload/confirm
→ parse_upload_file，保留 row/column 坐标
→ compact_upload_meta，生成 Sheet + Block profile
→ confirm_report_import(auto_create_tasks=False)
→ upsert_operating_objects_from_import
→ ingest_metric_facts_from_sheet_rows，按 blocks 写事实表
→ ingest_data_gaps_from_import
→ ingest_product_trends
→ generate_risk_tasks_for_signals
→ task_evidence_gate_service
→ importDiagnostics
```

旧规则不得因为字段缺失直接创建任务。

## 7. 验收接口

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
product_metric_facts 中 ROI 不被 traffic_source_facts 的 ROI 覆盖
商品详情 ROI 未命中时显示“未识别”，不显示 0 或缓存
```

## 8. 当前版本边界

V12.2.2 已完成：

```text
V12.2.0：报表布局 Agent，Sheet Profile → Block Profile
V12.2.1：导入解析器保留行列坐标和 block 可追溯字段
V12.2.2：事实表按 block 写入 product/store/traffic facts
附加收紧：商品指标展示 fail-closed，只读事实表
```

下一步建议进入 V12.2.3：把 importDiagnostics 升级成前端布局诊断页，让你直接在页面上看到 Sheet → Block → Fact → Gap 的识别结果。
