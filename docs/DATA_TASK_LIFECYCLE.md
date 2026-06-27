# DATA_TASK_LIFECYCLE

本文件只记录当前产品从数据到标签、任务、复核、复盘和演示清空的主链路。后续 AI 修改任务系统、报表系统、经营模块时，以本文件为定位依据。

## 1. 主生命周期

```text
报表导入 / 接口同步
→ 当前账号识别
→ 字段映射
→ 数据校验
→ DataVersion
→ 原始行入库 / 运行态记录
→ 商品入库ID识别
→ operating_products 主档 upsert
→ operating_stores 主档 upsert
→ 商品历史深度判断
→ 商品标签
→ 店铺聚合
→ 店铺标签 / 店铺权重
→ 趋势计算
→ business_signals_v6 风险信号
→ 任务队列门控
→ 高风险高时效执行任务
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

- 识别数据集。
- 完成字段映射。
- 创建或更新数据版本。
- 写入原始导入行和快照。
- 按商品入库ID识别新商品 / 老商品。
- upsert 商品主档 `operating_products`。
- upsert 店铺主档 `operating_stores`。
- 按店铺聚合商品数据。
- 生成商品标签、店铺标签、店铺权重。
- 生成趋势信号和风险信号。
- 触发任务门控。
- 触发模块刷新契约。
- 返回前端可刷新目标。
- 执行 v116 闭环反查。

## 3. 商品入库ID阶段

同一份报表可能同时包含新商品和已入库商品，所以不能按“第几次上传报表”判断分析阶段。

```text
product_id + sku_id + store_id + platform
→ product_runtime_id / operating object id
→ 查询历史 stat_date / 快照数
→ 判断 analysisStage
```

分析阶段：

```text
new_product：首次出现，只做建档和基线校验。
compare_ready：已有 1 个历史周期，可做轻量变化提示。
trend_ready：已有多个历史周期，可做短趋势。
stable_trend：历史较充足，可做趋势线和交叉验证。
```

## 4. 经营对象阶段

```text
rows
→ operating_object_store_service
→ operating_products
→ operating_stores
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
```

## 5. 标签阶段

低风险和观察信号不进入任务栏，先沉淀为标签。

商品标签：

- 新入库商品。
- 待建立趋势线。
- ROI 低于基线。
- 退款率高于基线。
- 投放产出低于基线。

店铺标签：

- 高权重店铺。
- 中权重店铺。
- 测试 / 低权重店铺。
- 高销售额店铺。
- 高 ROI 店铺。
- 高投放依赖店铺。
- 退款风险店铺。

## 6. 趋势和风险阶段

趋势不是单点指标，必须支持变化判断：

- 环比。
- 同比。
- 趋势方向。
- 波动幅度。
- 指标联动。
- 数据版本对比。

V11 规则：新商品不做趋势任务；没有历史深度时，只允许做基线校验和标签。

风险信号进入任务前，必须能说明：

- 哪个商品或店铺触发。
- 来自哪个数据版本。
- 哪个指标异常。
- 为什么需要人工介入。
- 是否已经具备足够历史深度。

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

任务生成规则：

```text
低风险 → 商品 / 店铺标签。
中风险 → 观察候选或标签。
高风险 + 高时效 → 执行队列。
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
task_status
alert_events
```

保留：账号、角色、权限、基础店铺配置。

## 12. 验收标准

一次完整 V11 验收必须覆盖：

```text
导入真实 ERA / ERP 报表
→ 商品入库ID识别
→ operating_products / operating_stores 主档写入
→ 新商品 / 老商品分流
→ 商品标签生成
→ 店铺标签和店铺权重生成
→ 低风险不进入任务栏
→ 高风险高时效进入执行队列
→ 任务详情全部可打开
→ 运营接收提交
→ 总管复核通过
→ 任务完成
→ 日志留痕
→ RAG 候选生成
→ 清空演示运行态后无残留
```
