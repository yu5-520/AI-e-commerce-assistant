# AI ERP 企业级电商经营 SaaS 底座

当前基线：V12.2.5 报表布局 Agent、Block 级事实写入、经营对象身份主档、商品页 fail-closed、ROI 三口径隔离。

## 产品定位

这是一个任务驱动型 AI 电商经营系统。当前 Demo 重点不是生成更多任务，而是验证真实报表或接口数据进入系统后，能否稳定完成：报表布局识别、单 Sheet 多区块拆分、商品身份入库、店铺聚合、系统编码、独立指标事实、数据缺口留痕、商品定位详情、导入诊断验收、趋势信号、证据闸门、执行任务、详情报告、复核留痕和演示运行态清空。

## 当前主链路

```text
报表 / 接口数据导入
→ 当前账号识别
→ V12.2.1 文件解析保留 sheetRows / sheetMatrices / source_row_index / source_column_map
→ V12.2.0 报表布局 Agent 判断 Sheet 内 blocks
→ 一个 Sheet 可拆出 product / store / traffic_source / staging 多个区块
→ V12.2.2 按 blockRows 写入 product_metric_facts / store_metric_facts / traffic_source_facts
→ V12.2.3 operating_products / operating_stores 只作为身份主档，不写指标缓存
→ V12.1.3 按 Sheet/指标聚合写入 data_gap_events，普通缺口只留痕
→ V12.1.5 生成 importDiagnostics 导入诊断验收
→ DataVersion / imported_report_rows / snapshots
→ 系统编码：STORE / SPU / LINK / SKU
→ V12.2.4 商品页 fail-closed，事实表未命中显示未识别
→ V12.2.5 product ROI / traffic ROI / store ROI 三口径隔离
→ 商品 / 店铺标签与权重
→ 趋势信号 business_signals_v6
→ task_evidence_gate_service 按 metric_scope 取证
→ 证据完整：经营执行任务
→ 关键证据缺失：补证任务
→ 普通缺口：只留痕，不进入任务池
→ 任务详情结构化报告
→ 证据提交 / 总管复核
→ 日志留痕 / RAG 记忆候选
→ v116 导入闭环反查
```

## V12.2.5 可信展示规则

```text
VERSION.md、FastAPI app.version、health.API_VERSION、前端资源版本必须一致。
README 只记录当前入口，不堆历史流水账。
MODULE_CHAIN 必须对齐真实代码链路。
API_CONTRACT 必须只记录真实可用接口。
清空演示环境必须删除导入行、快照、业务信号、任务、日志、经营商品、经营店铺、指标事实和数据缺口。
账号、角色、权限和基础店铺配置不能被演示清空误删。
经营中心发现源数据为 0 但派生运行态仍残留时，必须 fail-closed，不聚合旧对象。
前端接口失败时显示明确错误态，不展示本地业务兜底。
商品档案必须走 AppApi.product 真实接口，不再读取 AppMockData.products。
店铺进入商品档案时必须带 storeId / storeName 作用域，不再共用全局商品列表。
商品档案必须使用 objectId / archiveId 作为唯一档案 ID，避免不同店铺同商品 ID 串联。
商品列表必须使用产品化商品卡片视觉，不回退成字段堆叠。
商品详情必须展示商品定位卡片、指标事实区、流量来源区和任务历史摘要。
商品页只展示资产和定位；完整交叉验证、SOP 和提交证明在任务详情页处理。
商品名称不作为商品同一性的主识别依据；系统编码、商品链接、ERP 编码、SKU、店铺编码才是主轴。
上传解析必须保留 sheetRows、sheetMatrices、source_row_index、source_column_map。
报表布局 Agent 必须输出 blocks，而不是只输出 sheet targetTable。
上传确认必须按 block.targetTable + block.metricScope 写入 product/store/traffic 三类事实表。
指标事实必须独立落表，不能只藏在 payload.metricFacts。
operating_products / operating_stores 只保留身份定位、权限归属和来源坐标，不保留 ROI / 支付金额 / 转化率 / 广告消耗等经营指标缓存。
商品整体指标只读 product_metric_facts；流量来源指标只读 traffic_source_facts；店铺指标只读 store_metric_facts。
事实表未命中的指标显示“未识别”，不能显示 0，不能读商品对象缓存。
product ROI、traffic_source ROI、store ROI 互相隔离，任何一层 ROI 都不能覆盖另一层。
普通缺口必须进入 data_gap_events 留痕，但不能生成任务。
只有经营判断被关键证据阻塞时，任务证据闸门才允许把缺口升级为补证任务。
导入完成必须返回 importDiagnostics，展示 Sheet、Block、字段命中、事实写入、缺口和阻塞状态。
任务必须包含最低商品定位：商品ID / 店铺 / 系统编码或可追溯来源。
```

## 当前主入口

```text
/                                      web_demo 前端入口
/api/health                            健康检查
/api/modules/dashboard                 总览
/api/modules/report                    数据 / 报表
/api/modules/operating-unit            经营
/api/modules/product                   商品
/api/modules/product?storeId=STORE_ID  店铺商品档案
/api/modules/product/{product_id}      单商品事实详情
/api/modules/todo                      任务
/api/modules/log                       日志
/api/accounts                          账号
/api/system/runtime-diagnostics        运行态诊断
/api/system/reset-runtime-data          清空演示运行态
/api/system/backfill-operating-objects 经营对象回填
/api/system/repositories               Repository 状态
/api/system/postgres-cutover-check     PostgreSQL 主写切换前检查
/api/data/upload/preview               上传文件预览 + V12.2 报表布局画像
/api/data/upload/confirm               上传确认导入 + 经营对象 / block事实 / 数据缺口 / 导入诊断同步
/api/data/metric-facts/summary         指标事实表统计
/api/data/data-gaps/summary            数据缺口池统计
/api/data/import-diagnostics           导入诊断验收
/api/architecture/v10/readiness         产品验收守卫
```

## 当前文档

```text
docs/PRODUCT_ARCHITECTURE.md      产品结构和模块边界
docs/MODULE_CHAIN.md              AI 修改仓库的模块链定位图
docs/API_CONTRACT.md              当前真实 API 契约
docs/DATA_TASK_LIFECYCLE.md       数据、标签、任务、复核、日志生命周期
docs/V12_REPORT_GATEWAY.md        V12/V12.2 报表布局 Agent 和指标事实层
docs/DEPLOYMENT_RUNBOOK.md        服务器部署和排障 SOP
docs/POSTGRESQL_CUTOVER.md        PostgreSQL 主写切换边界
scripts/deploy_fast.sh            Demo 快速部署脚本
scripts/deploy_atomic.sh          ECS 轻量原子部署脚本
scripts/verify_release.py         版本一致性验收脚本
scripts/check_repo_hygiene.py     仓库文档和链路卫生检查脚本
```

## 模块化修改规则

AI 修改仓库时，先通过 `docs/MODULE_CHAIN.md` 定位模块链，再修改对应前端、API、Service、Repository 或 DB 层。旧版本文档、历史流水账或废弃页面不作为当前架构依据。

## 当前主前端

```text
web_demo/
```

`frontend/` 若与当前主链路不一致，视为历史资产，不作为当前产品入口。

## 当前后端入口

```text
src/api/main.py
```

## 当前部署入口

Demo 高频小改：

```bash
bash scripts/deploy_fast.sh
```

阶段收口：

```bash
bash scripts/deploy_atomic.sh
```

完整严格发布：

```bash
LIGHT_DEPLOY=0 ROUTE_GUARD_MODE=strict RUNTIME_ROUTE_GUARD=strict bash scripts/deploy_atomic.sh
```

## 当前数据库边界

SQLite 仍是 Demo 主写运行态；PostgreSQL 主写切换必须通过 cutover check。V12.2.5 已支持 source_block_id / source_row_index / source_column_index / metric_scope / source_block_type 写入事实表。商品对象主档只作为身份定位来源，经营指标展示必须从事实表读取，未命中显示“未识别”。
