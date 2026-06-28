# DATA_TASK_LIFECYCLE

本文件只记录当前产品从数据到事实、缺口、ROI/GMV 经营判断、任务、复核、复盘和演示清空的主链路。

## 1. 主生命周期

```text
报表导入 / 接口同步
→ 当前账号识别
→ 文件解析保留 Sheet / 行 / 列 / Block 坐标
→ 报表布局 Agent 识别 sheetProfiles[].blocks[]
→ DataVersion
→ 原始行入库 / 快照 / 运行态记录
→ operating_products / operating_stores 身份主档 upsert
→ product_metric_facts / store_metric_facts / traffic_source_facts 指标事实写入
→ data_gap_events 普通缺口留痕
→ importDiagnostics 布局诊断：Sheet → Block → Fact → Gap → Staging
→ 商品 / 店铺 / 流量来源事实展示
→ 趋势计算
→ business_signals_v6 经营信号
→ operating_cadence_task_service 计算上传频率和趋势周期
→ ROI/GMV 四象限判断
→ 库存、流量、点击、转化、退款、毛利、广告消耗解释 ROI/GMV 变化
→ task_evidence_gate_service 按 metric_scope 取证
→ 高风险红线任务 / ROI-GMV 日常经营任务 / 周期复盘候选 / 补证任务
→ 运营接收
→ 运营提交证据
→ 总管复核
→ 老板查看结果
→ 日志留痕
→ RAG 记忆候选
→ v116 导入闭环反查
```

## 2. 导入阶段

入口：

```text
web_demo/modules/report/page.js
→ AppApi.uploadReportFile() / AppApi.confirmReportImport() / AppApi.syncDataSource()
→ /api/data/upload/confirm 或 /api/data/import/confirm 或 /api/data/source-connections/{source_id}/sync
→ src/api/routes/data_import.py
```

导入阶段必须完成：

- 识别数据集和 source_system。
- 保留 sheetRows / sheetMatrices / source_row_index / source_column_map。
- 生成或接收 reportProfile.sheetProfiles[].blocks[]。
- 创建或更新数据版本。
- 写入原始导入行和快照。
- upsert 商品身份主档 `operating_products`。
- upsert 店铺身份主档 `operating_stores`。
- 按 block.targetTable + block.metricScope 写入三类事实表。
- 将普通缺口写入 `data_gap_events`。
- 生成 `importDiagnostics`，解释 Sheet → Block → Fact → Gap → Staging。
- 生成趋势信号和风险信号。
- 触发 ROI/GMV 经营节奏判断。
- 触发任务证据闸门。
- 触发模块刷新契约。
- 执行 v116 闭环反查。

## 3. 报表布局与事实阶段

```text
Sheet
→ Block
→ targetTable
→ metricScope
→ Fact Table
```

区块规则：

```text
product_metric_detail  → product_metric_facts   → metric_scope=product
store_summary          → store_metric_facts     → metric_scope=store
traffic_source_detail  → traffic_source_facts   → metric_scope=traffic_source
staging_unknown        → staging / gap only     → metric_scope=unknown
```

事实表规则：

```text
商品整体指标只读 product_metric_facts。
流量来源指标只读 traffic_source_facts。
店铺指标只读 store_metric_facts。
事实表未命中显示“未识别”。
不允许从 operating_products / operating_stores 读取经营指标缓存。
product ROI、traffic_source ROI、store ROI 不可互相替代。
```

## 4. ROI/GMV 主轴阶段

运营每天最关注的是 ROI 投产比和 GMV/支付金额。

```text
ROI = 投放效率主指标
GMV / 支付金额 = 经营规模主指标
广告消耗 = ROI 是否被预算拉低或放大的解释指标
库存 / 可售天数 = GMV 能不能承接的解释指标
流量 / 点击率 / 转化率 = ROI/GMV 变化原因的解释指标
退款率 / 毛利率 = ROI/GMV 是否安全的解释指标
```

四象限：

```text
高 ROI + 高 GMV → 放量承接任务
高 ROI + 低 GMV → 扩流测试任务
低 ROI + 高 GMV → 效率复核任务
低 ROI + 低 GMV → 降投排查任务
```

## 5. 数据缺口阶段

缺口分两类：

```text
普通缺口 = 缺了但暂时不用，只进入 data_gap_events。
决策缺口 = 缺了导致系统不能继续判断 ROI/GMV 动作，才被证据闸门升级为补证任务。
```

补证任务必须说明：

- 当前已有判断是什么。
- 缺少什么证据。
- 这个证据影响哪个动作。
- 补齐前系统不会生成什么高风险建议。

## 6. 标签、趋势和经营节奏阶段

趋势不是单点指标，必须支持变化判断：

- 3天短波动。
- 7天小趋势。
- 14天中短趋势。
- 30天中趋势。
- 90天大趋势。
- 上传频率。
- ROI / GMV 变化方向。
- 广告、库存、流量、点击、转化、退款、毛利的解释联动。

经营信号进入任务前，必须能说明：

- 哪个商品、店铺或流量来源触发。
- 来自哪个数据版本。
- ROI 和 GMV 如何变化。
- 解释指标是什么。
- metric_scope 是 product、traffic_source 还是 store。
- 为什么需要人工介入。
- 是否具备关键证据。

## 7. 任务生成阶段

任务必须包含：

- task id。
- 来源模块。
- 来源实体。
- 风险域。
- 任务标题。
- 处理动作。
- 优先级。
- 截止时间。
- 队列类型。
- 判断标签。
- 证据要求。
- 数据版本。
- metricScope。
- requiredFactTables。
- forbiddenCrossScope。
- ROI/GMV 四象限或解释标签。

任务生成规则：

```text
红线风险 → 强制任务。
高 ROI + 高 GMV → 放量承接任务。
高 ROI + 低 GMV → 扩流测试任务。
低 ROI + 高 GMV → 效率复核任务。
低 ROI + 低 GMV → 降投排查任务。
证据缺失且阻塞 ROI/GMV 动作 → 经营证据补齐任务。
轻微波动 → 观察项 / 日报周报素材。
```

任务进入执行队列后，其他模块不再重复展示已完成任务。

## 8. 执行和复核阶段

```text
总管派发
→ 运营接收
→ 运营提交
→ 总管复核
→ 老板查看
→ 日志 / RAG 候选
```

同一个 task id 在不同角色下展示不同视图：

- 老板：查看进度和结果。
- 总管：派发、复核、驳回。
- 运营：接收、提交、补充。

前端不展示“跨账号生命周期”工程标注，只展示任务状态、执行人、复核和证据。

## 9. 完成和留痕阶段

任务完成后必须：

- 从待处理任务池中移出。
- 同步更新来源模块展示状态。
- 写入任务事件。
- 写入日志。
- 生成可复盘内容。
- 必要时生成 RAG 记忆候选。

## 10. 日报 / 周报阶段

日报 / 周报不能只等已生成任务。

```text
日报 / 周报基础 = 已生成任务 + 候选任务 + 趋势信号 + 观察项
```

优先结构：

```text
ROI 变化最大的商品
GMV 增长 / 下滑最明显的商品
广告消耗上升但 ROI 转弱的商品
ROI 好但库存不足的机会商品
ROI / GMV 同时转弱的排查商品
```

## 11. 演示运行态清空阶段

Demo 测试反复导入时，清空必须反向删除完整派生链路：

```text
任务 / 复核 / 提交
→ alert_events
→ business_signals_v6
→ operating_cadence_signals
→ product_metric_facts / store_metric_facts / traffic_source_facts
→ data_gap_events
→ metric_snapshots
→ data_snapshots
→ imported_report_rows
→ report_records / import_records / workflow_runs
→ operating_products
→ operating_stores
```

清空后必须为 0：

```text
imported_report_rows
data_snapshots
metric_snapshots
business_signals_v6
operating_cadence_signals
operating_products
operating_stores
product_metric_facts
store_metric_facts
traffic_source_facts
data_gap_events
task_status
alert_events
```

保留：账号、角色、权限、基础店铺配置。
