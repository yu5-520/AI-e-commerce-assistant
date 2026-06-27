# DATA_TASK_LIFECYCLE

本文件只记录当前产品从数据到事实、缺口、任务、复核、复盘和演示清空的主链路。后续 AI 修改任务系统、报表系统、经营模块时，以本文件为定位依据。

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
→ importDiagnostics 布局诊断
→ 商品 / 店铺 / 流量来源事实展示
→ 趋势计算
→ business_signals_v6 经营信号
→ task_evidence_gate_service 按 metric_scope 取证
→ 高风险高时效执行任务 或 关键证据缺失补证任务
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

## 4. 经营对象阶段

```text
rows / blockRows
→ operating_object_store_service
→ operating_products / operating_stores
→ 当前账号可见商品 / 店铺
→ 经营中心展示
```

规则：

```text
上传账号决定正常报表导入归属。
新店铺直接创建并归属上传账号。
商品继承店铺归属。
任务继承商品 / 店铺归属。
任务不能反向制造商品 / 店铺权限。
经营对象只保留身份定位、权限归属、来源 Sheet / 行 / block 坐标。
```

## 5. 数据缺口阶段

缺口分两类：

```text
普通缺口 = 缺了但暂时不用，只进入 data_gap_events。
决策缺口 = 缺了导致系统不能继续判断，才被证据闸门升级为补证任务。
```

补证任务必须说明：

- 当前已有判断是什么。
- 缺少什么证据。
- 这个证据影响哪个动作。
- 补齐前系统不会生成什么高风险建议。

## 6. 标签、趋势和风险阶段

趋势不是单点指标，必须支持变化判断：

- 环比。
- 同比。
- 趋势方向。
- 波动幅度。
- 指标联动。
- 数据版本对比。

风险信号进入任务前，必须能说明：

- 哪个商品、店铺或流量来源触发。
- 来自哪个数据版本。
- 哪个指标异常。
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

任务生成规则：

```text
低风险 → 商品 / 店铺标签或观察项。
中风险 → 观察候选或标签。
高风险 + 证据完整 + 高时效 → 执行队列。
高风险 + 证据缺失 → 经营证据补齐任务。
高风险 + 需审批 → 审批生命周期。
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

## 10. 详情页兜底

只要任务进入执行队列，详情页必须能打开。

```text
完整报告可用 → 展示深度报告。
完整报告不可用 → 展示基础兜底报告。
```

禁止因为深度报告或 alert 同步失败，让前端显示“报告加载失败”。

## 11. 演示运行态清空阶段

Demo 测试反复导入时，清空必须反向删除完整派生链路：

```text
任务 / 复核 / 提交
→ alert_events
→ business_signals_v6
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

## 12. 验收标准

一次完整 V12.3 验收必须覆盖：

```text
导入真实 ERA / ERP 报表
→ reportProfile.sheetProfiles[].blocks[] 存在
→ metricFactSync.mode = layout_block_metric_fact_routing
→ product_metric_facts / store_metric_facts / traffic_source_facts 有事实写入
→ data_gap_events 有普通缺口留痕但不制造任务
→ importDiagnostics.layoutMode = sheet_block_fact_gap_staging
→ operating_products / operating_stores 只保留身份定位
→ 商品页事实表未命中显示“未识别”
→ ROI 按 product / traffic_source / store 三口径隔离
→ 任务 evidenceGate 返回 metricScope / requiredFactTables / forbiddenCrossScope
→ 高风险证据完整进入执行队列
→ 关键证据缺失降级为补证任务
→ 任务详情全部可打开
→ 运营接收提交
→ 总管复核通过
→ 任务完成
→ 日志留痕
→ RAG 候选生成
→ 清空演示运行态后无残留
```
