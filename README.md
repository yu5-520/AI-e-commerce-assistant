# AI ERP 企业级电商经营 SaaS 底座

当前基线：**V12.3.0 文档治理收口版**。

V12.3 不新增业务花活，重点是防止仓库被旧文档、旧前端和旧部署说明带偏。当前主线仍然是：报表布局 Agent → Block 级事实写入 → 经营对象身份主档 → 商品页 fail-closed → ROI 三口径隔离 → 任务证据闸门 → 导入诊断 → 账号 / 数据源接口契约修复。

## 当前执行入口

```text
前端唯一入口：web_demo/
后端唯一入口：src/api/main.py
版本主文件：VERSION.md + versioning/VERSION.md
运行态数据库：SQLite Demo runtime
部署脚本：scripts/deploy_fast.sh / scripts/deploy_atomic.sh
```

`frontend/` 已标记为历史资产，不作为当前 UI 修改依据。历史说明进入 `docs/archive/`，不作为当前架构依据。

## 当前主链路

```text
报表 / 接口数据导入
→ 当前账号识别
→ GET /api/data/source-connections 数据源契约可用
→ 文件解析保留 sheetRows / sheetMatrices / source_row_index / source_column_map
→ 报表布局 Agent 输出 sheetProfiles[].blocks[]
→ 一个 Sheet 可拆出 product / store / traffic_source / staging 多个区块
→ 按 block.targetTable + block.metricScope 写入 product/store/traffic 三类事实表
→ operating_products / operating_stores 只作为身份主档，不写指标缓存
→ data_gap_events 记录普通缺口，普通缺口不直接生成任务
→ importDiagnostics 输出 Sheet → Block → Fact → Gap → Staging
→ 商品页从事实表读取指标，事实表未命中显示“未识别”
→ product ROI / traffic_source ROI / store ROI 三口径隔离
→ business_signals_v6 生成趋势信号
→ task_evidence_gate_service 严格按 metric_scope 取证
→ 证据完整：经营执行任务
→ 关键证据缺失：补证任务
→ 任务详情、证据提交、总管复核、日志留痕、RAG 候选
```

## 当前主文档

```text
docs/API_CONTRACT.md              当前真实 API 契约
docs/MODULE_CHAIN.md              AI 修改仓库的模块链定位图
docs/PRODUCT_ARCHITECTURE.md      当前产品结构和模块边界
docs/DATA_TASK_LIFECYCLE.md       数据、事实、缺口、任务、复核生命周期
docs/V12_REPORT_GATEWAY.md        V12/V12.2 报表布局 Agent 和指标事实层
docs/DEPLOYMENT_RUNBOOK.md        V12.3 服务器部署和排障 SOP
docs/POSTGRESQL_CUTOVER.md        PostgreSQL 主写切换边界
docs/archive/README.md            历史文档归档规则
scripts/verify_release.py         版本一致性验收脚本
scripts/check_repo_hygiene.py     仓库文档和链路卫生检查脚本
```

## 当前主 API

```text
/                                      web_demo 前端入口
/api/health                            健康检查
/api/modules/dashboard                 总览
/api/modules/report                    数据 / 报表
/api/modules/operating-unit            经营
/api/modules/product                   商品档案
/api/modules/product?storeId=STORE_ID  店铺商品档案
/api/modules/product/{product_id}      单商品事实详情
/api/modules/todo                      任务
/api/modules/log                       日志
/api/accounts                          账号
/api/accounts/switch                   ECS Demo 账号切换验证
/api/data/source-connections           数据源接口契约
/api/data/upload/preview               上传文件预览 + 报表布局画像
/api/data/upload/confirm               上传确认导入 + 经营对象 / block事实 / 缺口 / 诊断同步
/api/data/metric-facts/summary         指标事实表统计
/api/data/data-gaps/summary            数据缺口池统计
/api/data/import-diagnostics           Sheet → Block → Fact → Gap → Staging 诊断
/api/system/runtime-diagnostics        运行态诊断
/api/system/reset-runtime-data          清空演示运行态
/api/system/repositories               Repository 状态
/api/system/postgres-cutover-check     PostgreSQL 主写切换前检查
```

## V12.3 硬规则

```text
VERSION.md、versioning/VERSION.md、FastAPI app.version、health.API_VERSION、web_demo/index.html 资源版本必须一致。
README 只做当前入口索引，不堆历史流水账。
API_CONTRACT 只记录当前真实可用 API。
MODULE_CHAIN 只记录当前执行链路，不能把 frontend/ 作为当前入口。
DEPLOYMENT_RUNBOOK 必须跟随当前版本，不允许停留在旧版本。
PRODUCT_ARCHITECTURE 和 DATA_TASK_LIFECYCLE 必须描述 V12 fact/layout/gap/evidence 主链路，不允许停留在 V11 商品档案阶段。
旧版本说明、PRD、阶段复盘、废弃前端必须进入 archive 或标记 deprecated。
事实表未命中的指标显示“未识别”，不能显示 0，不能读对象缓存。
product ROI、traffic_source ROI、store ROI 互相隔离，不能跨口径覆盖。
普通缺口只进入 data_gap_events；只有阻塞经营判断的关键证据缺失，才生成补证任务。
```

## 部署入口

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

## 验收入口

```bash
python scripts/verify_release.py
python scripts/check_repo_hygiene.py
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/data/source-connections
curl http://127.0.0.1:8000/api/data/import-diagnostics
```
