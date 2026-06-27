# V12 / V12.1 报表画像 Agent 与指标事实层

V12 的目标不是继续扩大任务数量，而是把报表上传从“商品壳入库”升级成“报表画像 → 系统编码 → 指标事实 → 任务证据闸门”。V12.1.0 将指标事实从 `payload.metricFacts` 兼容缓存升级为独立 SQLite 事实表；V12.1.1 将上传确认升级为按 `reportProfile.sheetProfiles + sheetRows` 分 Sheet 写入事实表。

## 1. 核心原则

- Agent 负责判断报表结构，不负责逐行读取全表。
- 代码脚本按 Agent 输出的画像批量读取数据。
- 商品名称完整保留，但不作为商品同一性主键。
- 商品页负责商品定位和指标事实；任务页负责交叉验证、SOP 和复盘。
- 缺字段不直接生成任务；只有经营判断被关键证据阻塞时才生成补证任务。
- 指标事实必须可查询、可复用、可被任务证据闸门引用，不能只藏在商品 payload 里。
- 多 Sheet 报表必须按 Sheet 画像分流，不能用扁平 rows 代替业务结构。

## 2. 服务边界

### `src/services/metric_catalog_service.py`

统一字段字典和指标格式化。

覆盖字段包括：

- 库存数量 / 可售天数
- 客单价 / 支付金额 / 商品成本金额
- 毛利金额 / 毛利率
- ROI / 广告消耗 / 广告点击数 / 广告成交数
- 点击率 / 支付转化率
- 退款订单数 / 退款金额 / 退款率
- 自然流量访客数 / 付费流量访客数

### `src/services/report_profile_agent_service.py`

读取上传文件的 sheet、表头、样本行，输出结构化画像：

- 商品经营明细 → `product_metric_facts`
- 店铺经营汇总 → `store_metric_facts`
- 流量来源明细 → `traffic_source_facts`

它只判断“怎么读”，不生成任务。

### `src/services/metric_fact_store_service.py`

V12.1 新增。负责创建并写入独立事实表：

```text
product_metric_facts
store_metric_facts
traffic_source_facts
```

V12.1.1 增强：

```text
ingest_metric_facts_from_sheet_rows(result, parsed, report_profile=...)
```

该路径读取 `parsed.sheetRows`，并按 `reportProfile.sheetProfiles[*].targetTable` 明确写入对应事实表。该服务只存证据，不生成任务。

## 3. 上传解析变化

`import_adapter_service.py` 从 V12 开始保留：

- `rows`：兼容旧流程的扁平行数据
- `sheetRows`：按 sheet 保存的原始行数据
- `uploadMeta.reportProfile`：V12 报表画像

这样一份 Excel 不再被当成单一商品表，而能按 sheet 分流到不同事实层。

## 4. V12.1 独立事实表

V12.1 写入的事实字段包括：

```text
fact_id
tenant_id
org_id
data_version
dataset_name
source_system
source_sheet
source_report_id
entity_level
store_code
spu_code
link_code
sku_code
platform
store_id
store_name
product_id
sku_id
erp_product_code
product_link
traffic_source
metric_code
metric_value
display_value
raw_field_name
raw_value
stat_date
time_window
confidence
payload
created_at
updated_at
```

事实表用于后续：

- 商品详情页读取指标事实
- 趋势系统按时间查询
- 任务证据闸门判断是否缺关键证据
- RAG/审计引用具体指标来源

## 5. V12.1.1 Sheet 分流规则

上传确认时：

```text
parsed.sheetRows[商品经营明细]
→ product_metric_facts

parsed.sheetRows[店铺经营汇总]
→ store_metric_facts

parsed.sheetRows[流量来源明细]
→ traffic_source_facts
```

如果某个 Sheet 的画像是 `staging_rows` 或存在 blocked issue，则不写入正式事实表，只在 `metricFactSync.sheetSummaries` 中记录跳过原因。

`metricFactSync` 返回：

```text
mode = profile_sheet_rows_metric_fact_routing
sheetSummaries
blockedSheetCount
stagingSheetCount
productMetricFactCount
storeMetricFactCount
trafficSourceFactCount
factCount
```

## 6. 经营对象入库变化

`operating_object_store_service.py` 升级到 V12：

- 使用系统编码承接店铺、SPU、LINK、SKU
- 保留 ERP 编码、平台商品 ID、SKU ID、商品链接等外部身份
- 将指标事实继续兼容沉淀到 `payload.metricFacts`
- 商品卡片展示结构化指标，不再只展示库存、售价、毛利率三个窄字段

从 V12.1.0 开始，`payload.metricFacts` 只是展示缓存，独立事实表才是后续趋势和任务证据的主来源。

## 7. ERA 文件验收标准

上传 `ERA经营数据报表` 后，系统应能识别：

- 商品经营明细
- 店铺经营汇总
- 流量来源明细

商品对象以以下颗粒度稳定定位：

```text
平台 + 店铺ID + 商品ID + SKU ID
```

独立事实表验收：

```text
/api/data/metric-facts/summary
```

应能看到：

- `product_metric_facts` 数量增加
- `store_metric_facts` 数量增加
- `traffic_source_facts` 数量增加
- `factCount` 大于 0

上传确认返回的 `metricFactSync.sheetSummaries` 应包含每个 Sheet 的 `targetTable`、`rowCount`、`factCount`、`confidence`。

任务生成不得因为“某张表缺 ROI”直接生成补 ROI 任务。只有当某个商品已经形成经营异常假设，且 ROI 阻塞任务升级时，才生成补证任务。

## 8. 后续 V12.1.x 方向

- V12.1.2：前端商品详情改为“商品定位卡片 + 指标事实区 + 任务历史摘要”。
- V12.1.3：新增 `data_gap_events`，普通缺口只留痕，决策缺口才进入候选任务。
- V12.1.4：新增任务证据闸门，完整展示数据比对、交叉验证、SOP 和提交证明。
