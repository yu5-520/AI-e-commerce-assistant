# AI ERP 企业级电商经营 SaaS 底座

当前基线：**V12.5.0 首份报表基线模式 + 任务页同步修复**。

V12.5 保留 V12.4.1 的 ROI/GMV 中心化经营任务权重，但修复两个关键断点：第一份报表只建立商品、店铺、ROI、GMV、库存、广告、转化等基线，不生成扩流、加投、降投、转化排查等经营测试任务；任务页进入时强制读取 `/api/modules/todo` 并 hydrate `AppTaskStore`，保证总览和任务栏来自同一个后端任务池。

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
→ 首份报表进入 baseline_snapshot，只沉淀商品 / 店铺 / ROI / GMV / 库存 / 广告 / 转化基线
→ 两份报表才允许环比经营任务
→ 三份报表或 7 天窗口才允许 3/7/14/30/90 天趋势任务
→ 红线任务强制生成，非红线 ROI/GMV 经营任务必须有可比数据
→ task_evidence_gate_service 严格按 metric_scope 取证
→ 候选任务 / 趋势信号 / 观察项进入日报和周报素材
→ AppApi.refreshTaskState() 从 /api/modules/todo 同步后端任务池
→ 任务详情、证据提交、总管复核、日志留痕、RAG 候选
```

## V12.5 基线规则

```text
1份报表：只建基线；只允许红线任务、补证任务、数据质量任务。
2份报表：允许环比任务；可以生成 ROI/GMV 日常经营复核。
3份报表：允许短周期趋势任务；可以生成 3天 / 7天节奏任务。
7天窗口：允许小趋势任务。
14天 / 30天 / 90天：进入中短、中期、大周期复盘。
```

首份报表禁止生成：

```text
扩流测试任务
加投判断任务
降投排查任务
转化排查任务
高 ROI + 低 GMV 经营测试任务
低 ROI + 高 GMV 效率复核任务
```

首份报表仍可生成：

```text
库存归零红线任务
毛利率跌穿红线任务
退款率红线任务
报表结构识别失败任务
关键证据补齐任务
```

## ROI/GMV 经营规则

```text
ROI 是投放效率主指标。
GMV/支付金额是经营规模主指标。
广告消耗解释 ROI 是否被预算拉低或放大。
库存和可售天数解释 GMV 能不能继续承接。
流量、点击率、转化率解释 ROI/GMV 变化原因。
退款率和毛利率解释 ROI/GMV 是否安全。
```

四象限只有在至少两份可比报表后生效：

```text
高 ROI + 高 GMV：放量承接。
高 ROI + 低 GMV：扩流测试。
低 ROI + 高 GMV：效率复核。
低 ROI + 低 GMV：降投排查。
```

## 当前主文档

```text
docs/API_CONTRACT.md              当前真实 API 契约
docs/MODULE_CHAIN.md              AI 修改仓库的模块链定位图
docs/PRODUCT_ARCHITECTURE.md      当前产品结构和模块边界
docs/DATA_TASK_LIFECYCLE.md       数据、事实、缺口、任务、复核生命周期
docs/V12_REPORT_GATEWAY.md        V12/V12.2 报表布局 Agent 和指标事实层
docs/DEPLOYMENT_RUNBOOK.md        V12.5 服务器部署和排障 SOP
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
/api/modules/todo                      任务；总览和任务栏必须共用该任务源
/api/modules/log                       日志
/api/accounts                          账号
/api/accounts/switch                   ECS Demo 账号切换验证
/api/data/source-connections           数据源接口契约
/api/data/upload/preview               上传文件预览 + 报表布局画像
/api/data/upload/confirm               上传确认导入 + 经营对象 / block事实 / 缺口 / 诊断 / 基线优先任务同步
/api/data/metric-facts/summary         指标事实表统计
/api/data/data-gaps/summary            数据缺口池统计
/api/data/import-diagnostics           Sheet → Block → Fact → Gap → Staging 诊断
/api/system/runtime-diagnostics        运行态诊断
/api/system/reset-runtime-data          清空演示运行态
/api/system/repositories               Repository 状态
/api/system/postgres-cutover-check     PostgreSQL 主写切换前检查
```

## V12.5 硬规则

```text
VERSION.md、versioning/VERSION.md、FastAPI app.version、health.API_VERSION、web_demo/index.html 资源版本必须一致。
README 只做当前入口索引，不堆历史流水账。
API_CONTRACT 只记录当前真实可用 API。
MODULE_CHAIN 只记录当前执行链路，不能把 frontend/ 作为当前入口。
事实表未命中的指标显示“未识别”，不能显示 0，不能读对象缓存。
product ROI、traffic_source ROI、store ROI 互相隔离，不能跨口径覆盖。
普通缺口只进入 data_gap_events；只有阻塞经营判断的关键证据缺失，才生成补证任务。
第一份报表只做基线，非红线经营任务必须有至少两份可比报表。
总览任务和任务栏必须来自 /api/modules/todo，不允许任务页只读本地空 AppTaskStore。
日报 / 周报不能只依赖已生成任务，必须能承接候选任务、趋势信号和观察项。
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
