# DATA_TASK_LIFECYCLE

本文件只记录 **V12.8.1 当前产品从数据到任务生命周期、自动复盘、RAG反馈增强的主链路**。历史版本流程不得放在本文件占据当前判断位置。

## 1. 当前主生命周期

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
→ rag_business_memory_service 读取公司基线 + approved/effective 经验卡
→ action_impact_estimation_service 系统估算动作影响
→ operating_weight_policy_service 判断权重来源与置信度
→ action_authorization_gate_service 判断账号权限和审批路径
→ task_cluster_service 生成后端真实聚合任务
→ task_lifecycle_orchestrator_service 挂载 taskLifecycle
→ /api/modules/todo 返回任务池
→ 运营接收任务
→ 运营提交处理材料 / evidence
→ 主管复核材料
→ task_recap_scheduler_service 自动生成复盘周期
→ 系统按后续事实表/报表完成复盘
→ rag_feedback_loop_service 生成RAG候选
→ 人工审核 approved
→ 下一次任务生成召回 approved/effective 经验卡
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

任务生成必须遵守基线优先：

```text
1份报表：只建 baseline_snapshot，非红线不生成经营测试任务。
2份报表：允许环比任务。
3份报表或更长周期：允许 3/7/14/30/90 天趋势任务。
红线风险：可立即生成 urgent_execution。
轻微波动：进入观察项 / 日报周报素材。
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

## 6. 任务生成阶段

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
- taskLifecycle。

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

重复商品任务必须由后端 `task_cluster_service` 聚合成真实后端任务。前端不得再次做同类任务聚合。

## 7. 任务生命周期阶段

生命周期阶段：

```text
generated                 生成任务
accepted                  接收任务
evidence_submitted        提交处理材料
manager_reviewed          主管复核
recap_scheduled           生成自动复盘周期
recap_completed           复盘完成
rag_candidate_created     进入RAG候选
rag_approved              RAG增强任务生成
returned                  退回补充
archived                  归档
```

同一个 task id 在不同角色下展示不同视图：

- 老板：查看进度、结果、预算和策略影响。
- 总管：派发、复核、驳回、确认是否进入RAG。
- 运营：接收、提交事实材料、补充处理证据。

前端只展示任务状态、执行人、复核、生命周期阶段和详情入口；完整 SOP、证据链、自动复盘周期、RAG 候选状态进入任务详情页。

## 8. 自动复盘阶段

系统根据任务类型生成复盘周期：

```text
活动任务 → T+3 / T+7
素材/标题/主图测试 → T+3
库存任务 → T+3 / T+7
投放/ROI任务 → T+1 / T+3
售后任务 → T+7
```

复盘指标：

```text
ROI
GMV/支付金额
访客数
点击率
转化率
广告消耗
库存消耗
退款率
毛利率
```

规则：运营不能手填 ROI/GMV/销量预测。运营只提交客观材料；系统从后续事实表/报表读取指标变化，生成 `autoRecapResult`。

## 9. RAG 反馈增强阶段

```text
自动复盘完成
→ rag_feedback_loop_service.build_rag_candidate_from_recap
→ experience_memory_service.draft_experience_from_task
→ status=pending_review
→ owner / manager 人工审核
→ status=approved 且 effective=true
→ rag_business_memory_service 下次任务生成召回
```

边界：pending_review 只做候选，不直接增强任务生成。只有 approved/effective 经验卡可以进入后续任务生成。

## 10. 日报 / 周报阶段

日报 / 周报不能只等已生成任务。

```text
日报 / 周报基础 = 已生成任务 + 候选任务 + 趋势信号 + 观察项 + 自动复盘结果 + RAG候选状态
```

优先结构：

```text
ROI 变化最大的商品
GMV 增长 / 下滑最明显的商品
广告消耗上升但 ROI 转弱的商品
ROI 好但库存不足的机会商品
ROI / GMV 同时转弱的排查商品
复盘周期到达但效果未确认的任务
可进入RAG的有效经验卡候选
```

## 11. 演示运行态清空阶段

Demo 测试反复导入时，清空必须反向删除完整派生链路：

```text
RAG候选 / 复盘周期 / 任务 / 复核 / 提交
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

保留：账号、角色、权限、基础店铺配置。
