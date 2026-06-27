# V12 / V12.1 报表画像 Agent 与指标事实层

V12 的目标不是继续扩大任务数量，而是把报表上传从“商品壳入库”升级成“报表画像 → 系统编码 → 指标事实 → 数据缺口池 → 任务证据闸门”。V12.1.0 将指标事实从 `payload.metricFacts` 兼容缓存升级为独立 SQLite 事实表；V12.1.1 将上传确认升级为按 `reportProfile.sheetProfiles + sheetRows` 分 Sheet 写入事实表；V12.1.2 将商品详情页升级为读取独立事实表的商品定位和指标事实页；V12.1.3 新增 `data_gap_events`，普通缺口只留痕，不生成任务。

## 1. 核心原则

- Agent 负责判断报表结构，不负责逐行读取全表。
- 代码脚本按 Agent 输出的画像批量读取数据。
- 商品名称完整保留，但不作为商品同一性主键。
- 商品页负责商品定位和指标事实；任务页负责交叉验证、SOP 和复盘。
- 缺字段不直接生成任务；只有经营判断被关键证据阻塞时，后续证据闸门才允许生成补证任务。
- 指标事实必须可查询、可复用、可被任务证据闸门引用，不能只藏在商品 payload 里。
- 多 Sheet 报表必须按 Sheet 画像分流，不能用扁平 rows 代替业务结构。
- 数据缺口必须聚合留痕，不能按商品逐条打扰运营。

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

### `src/services/product_archive_detail_service.py`

V12.1.2 新增。负责把商品对象和独立事实表合并为商品详情可展示的数据：

```text
productPosition：系统店铺编码 / SPU / LINK / SKU / 平台 / 店铺 / 商品ID / SKU / ERP / 链接
metricSections：成交与投产 / 成本与利润 / 流量与广告 / 库存与售后
trafficSourceFacts：自然搜索 / 推荐流量 / 付费推广 / 店铺首页 / 活动会场等来源
metricFactSummary：product/store/traffic 三类事实数量
taskHistorySummary：任务次数、当前任务、最近完成摘要
```

该服务只做商品资产展示，不生成 SOP 任务。

### `src/services/data_gap_event_service.py`

V12.1.3 新增。负责创建并写入数据缺口池：

```text
data_gap_events
```

它只记录缺口，不创建任务。当前缺口统一为：

```text
is_decision_blocking = 0
status = logged
```

后续 V12.1.4 任务证据闸门会根据真实经营判断，把少量关键缺口升级为补证任务。

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

## 6. V12.1.2 商品详情页

商品模块接口：

```text
/api/modules/product
/api/modules/product?storeId=STORE_ID
/api/modules/product/{product_id}
```

返回对象新增：

```text
productPosition
metricSections
trafficSourceFacts
taskHistorySummary
metricFactSummary
```

前端商品详情页展示：

- 商品定位卡片：系统店铺编码、系统SPU、系统LINK、系统SKU、平台、店铺、商品ID、SKU、ERP编码、商品链接。
- 指标事实区：成交与投产、成本与利润、流量与广告、库存与售后。
- 流量来源区：按 traffic_source 展示访客、点击率、转化率、ROI、广告消耗。
- 任务历史摘要：只展示任务次数和状态，不展开 SOP。

商品页边界：商品页只展示“这个商品是谁、在哪、有哪些事实、做过多少任务”；完整交叉验证、SOP、提交证明在任务详情页处理。

## 7. V12.1.3 数据缺口池

新增表：

```text
data_gap_events
```

核心字段：

```text
gap_id
data_version
dataset_name
source_system
source_report_id
source_sheet
target_table
entity_level
store_code / spu_code / link_code / sku_code
metric_code
identity_field
gap_type
gap_scope
affected_row_count
missing_count
present_count
is_decision_blocking
related_signal_id
related_task_id
status
severity
reason
payload
created_at / updated_at
```

V12.1.3 只做聚合留痕：

```text
某 Sheet 缺 ROI → 记录一条 sheet 级普通缺口
某 Sheet ROI 有部分空值 → 记录一条 sheet_metric_aggregate 普通缺口
某 Sheet 缺商品ID/店铺字段 → 记录 identity_not_in_sheet 普通缺口
某 Sheet 未进入事实表 → 记录 unrouted_sheet 普通缺口
```

不会做：

```text
商品A缺ROI → 任务
商品B缺ROI → 任务
商品C缺ROI → 任务
```

只有 V12.1.4 证据闸门判断“某个经营判断已经成立，但缺少 ROI 作为升级证据”时，才会把对应缺口升级为补证任务。

## 8. 经营对象入库变化

`operating_object_store_service.py` 升级到 V12：

- 使用系统编码承接店铺、SPU、LINK、SKU
- 保留 ERP 编码、平台商品 ID、SKU ID、商品链接等外部身份
- 将指标事实继续兼容沉淀到 `payload.metricFacts`
- 商品卡片展示结构化指标，不再只展示库存、售价、毛利率三个窄字段

从 V12.1.0 开始，`payload.metricFacts` 只是展示缓存，独立事实表才是后续趋势和任务证据的主来源。

## 9. ERA 文件验收标准

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

数据缺口池验收：

```text
/api/data/data-gaps/summary
```

应能看到：

- `gapCount` 记录普通缺口数量
- `ordinaryGapCount` 等于普通留痕缺口数量
- `decisionBlockingGapCount` 在 V12.1.3 仍应为 0
- `byType` 展示 metric_not_in_sheet、metric_sparse_values、identity_not_in_sheet 等聚合缺口类型

上传确认返回的 `metricFactSync.sheetSummaries` 应包含每个 Sheet 的 `targetTable`、`rowCount`、`factCount`、`confidence`。上传确认返回的 `dataGapSync.sheetSummaries` 应包含每个 Sheet 的缺口数量。

商品详情验收：

- 商品定位卡片包含系统编码、平台、店铺、商品ID、SKU。
- 指标事实区展示库存、客单价、支付金额、毛利率、ROI、点击率、转化率、退款率、广告消耗等。
- 流量来源区能展示自然搜索、推荐流量、付费推广等来源数据。
- 商品页不展示完整任务 SOP，只展示任务历史摘要。

任务生成不得因为“某张表缺 ROI”直接生成补 ROI 任务。只有当某个商品已经形成经营异常假设，且 ROI 阻塞任务升级时，才生成补证任务。

## 10. 后续 V12.1.x 方向

- V12.1.4：新增任务证据闸门，完整展示数据比对、交叉验证、SOP 和提交证明。
