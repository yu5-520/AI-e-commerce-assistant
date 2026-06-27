# AI ERP 企业级电商经营 SaaS 底座

当前基线：V12.1.0 报表画像 Agent、系统标准编码与独立指标事实表。

## 产品定位

这是一个任务驱动型 AI 电商经营系统。当前 Demo 重点不是生成更多任务，而是验证真实报表或接口数据进入系统后，能否稳定完成：报表画像、商品入库、店铺聚合、系统编码、独立指标事实、趋势信号、执行任务、详情报告、复核留痕和演示运行态清空。

## 当前主链路

```text
报表 / 接口数据导入
→ 当前账号识别
→ 文件解析 / Sheet 保留 / 字段映射 / 校验
→ V12 报表画像 Agent 判断 Sheet 结构和目标事实层
→ DataVersion / imported_report_rows / snapshots
→ operating_products / operating_stores 主档 upsert
→ 系统编码：STORE / SPU / LINK / SKU
→ V12.1 独立事实表：product_metric_facts / store_metric_facts / traffic_source_facts
→ 商品 / 店铺标签与权重
→ 趋势信号 business_signals_v6
→ risk_task_service 任务门控
→ 仅高风险高时效或经营判断缺证进入任务队列
→ 任务详情结构化报告
→ 证据提交 / 总管复核
→ 日志留痕 / RAG 记忆候选
→ v116 导入闭环反查
```

## V12.1 可信展示规则

```text
VERSION.md、FastAPI app.version、health.API_VERSION、前端资源版本必须一致。
README 只记录当前入口，不堆历史流水账。
MODULE_CHAIN 必须对齐真实代码链路。
API_CONTRACT 必须只记录真实可用接口。
清空演示环境必须删除导入行、快照、业务信号、任务、日志、经营商品、经营店铺和指标事实。
账号、角色、权限和基础店铺配置不能被演示清空误删。
经营中心发现源数据为 0 但派生运行态仍残留时，必须 fail-closed，不聚合旧对象。
前端接口失败时显示明确错误态，不展示本地业务兜底。
商品档案必须走 AppApi.product 真实接口，不再读取 AppMockData.products。
店铺进入商品档案时必须带 storeId / storeName 作用域，不再共用全局商品列表。
商品档案必须使用 objectId / archiveId 作为唯一档案 ID，避免不同店铺同商品 ID 串联。
商品列表必须使用产品化商品卡片视觉，不回退成字段堆叠。
商品名称不作为商品同一性的主识别依据；系统编码、商品链接、ERP 编码、SKU、店铺编码才是主轴。
上传解析必须保留 sheetRows，不能把多 Sheet 报表直接压平成一个单表逻辑。
指标事实必须独立落表，不能只藏在 payload.metricFacts。
缺字段不直接生成任务；只有经营判断被关键证据阻塞时才生成补证任务。
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
/api/modules/todo                      任务
/api/modules/log                       日志
/api/accounts                          账号
/api/system/runtime-diagnostics        运行态诊断
/api/system/reset-runtime-data          清空演示运行态
/api/system/backfill-operating-objects 经营对象回填
/api/system/repositories               Repository 状态
/api/system/postgres-cutover-check     PostgreSQL 主写切换前检查
/api/data/upload/preview               上传文件预览 + V12 报表画像
/api/data/upload/confirm               上传确认导入 + 经营对象 / 独立指标事实同步
/api/data/metric-facts/summary         V12.1 指标事实表统计
/api/architecture/v10/readiness         产品验收守卫
```

## 当前文档

```text
docs/PRODUCT_ARCHITECTURE.md      产品结构和模块边界
docs/MODULE_CHAIN.md              AI 修改仓库的模块链定位图
docs/API_CONTRACT.md              当前真实 API 契约
docs/DATA_TASK_LIFECYCLE.md       数据、标签、任务、复核、日志生命周期
docs/V12_REPORT_GATEWAY.md        V12/V12.1 报表画像 Agent 和指标事实层
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

SQLite 仍是 Demo 主写运行态；PostgreSQL 主写切换必须通过 cutover check。V12.1 已新增 product_metric_facts / store_metric_facts / traffic_source_facts 独立事实表，payload.metricFacts 仅作为商品对象的兼容展示缓存，不再作为唯一事实来源。
