# AI ERP 企业级电商经营 SaaS 底座

当前基线：V11.16 仓库版本统一与前端链路收口基线。

## 产品定位

这是一个任务驱动型 AI 电商经营系统。当前 Demo 重点不是生成更多任务，而是验证真实报表或接口数据进入系统后，能否稳定完成：商品入库、店铺聚合、标签沉淀、趋势信号、执行任务、详情报告、复核留痕和演示运行态清空。

## 当前主链路

```text
报表 / 接口数据导入
→ 当前账号识别
→ 文件解析 / 字段映射 / 校验
→ DataVersion / imported_report_rows / snapshots
→ operating_products / operating_stores 主档 upsert
→ 商品 / 店铺标签与权重
→ 趋势信号 business_signals_v6
→ risk_task_service 任务门控
→ 高风险高时效进入任务队列
→ 任务详情结构化报告
→ 证据提交 / 总管复核
→ 日志留痕 / RAG 记忆候选
→ v116 导入闭环反查
```

## V11.16 可信展示规则

```text
VERSION.md、FastAPI app.version、health.API_VERSION、前端资源版本必须一致。
README 只记录当前入口，不堆历史流水账。
MODULE_CHAIN 必须对齐真实代码链路。
API_CONTRACT 必须只记录真实可用接口。
清空演示环境必须删除导入行、快照、业务信号、任务、日志、经营商品和经营店铺。
账号、角色、权限和基础店铺配置不能被演示清空误删。
经营中心发现源数据为 0 但派生运行态仍残留时，必须 fail-closed，不聚合旧对象。
前端接口失败时显示明确错误态，不展示本地业务兜底。
商品档案必须走 AppApi.product 真实接口，不再读取 AppMockData.products。
店铺经营状态必须以一店一行产品化卡片展示，不回退成字段堆叠。
后端正常返回空数组 / 空对象时显示真实空态。
```

## 当前主入口

```text
/                                      web_demo 前端入口
/api/health                            健康检查
/api/modules/dashboard                 总览
/api/modules/report                    数据 / 报表
/api/modules/operating-unit            经营
/api/modules/product                   商品
/api/modules/todo                      任务
/api/modules/log                       日志
/api/accounts                          账号
/api/system/runtime-diagnostics        运行态诊断
/api/system/reset-runtime-data          清空演示运行态
/api/system/backfill-operating-objects 经营对象回填
/api/system/repositories               Repository 状态
/api/system/postgres-cutover-check     PostgreSQL 主写切换前检查
/api/architecture/v10/readiness         产品验收守卫
```

## 当前文档

```text
docs/PRODUCT_ARCHITECTURE.md      产品结构和模块边界
docs/MODULE_CHAIN.md              AI 修改仓库的模块链定位图
docs/API_CONTRACT.md              当前真实 API 契约
docs/DATA_TASK_LIFECYCLE.md       数据、标签、任务、复核、日志生命周期
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

默认运行仍以 SQLite-first Demo 为主。PostgreSQL 是生产迁移目标，需要通过 cutover check 和抽样对账后再进入主写切换。
