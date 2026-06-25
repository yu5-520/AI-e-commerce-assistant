# AI ERP 企业级电商经营 SaaS 底座

当前基线：V11.2 任务详情与任务去重链路修复。

## 产品定位

这是一个任务驱动型 AI 电商经营系统。

V11 的重点不是生成更多任务，而是验证真实报表导入后，系统能不能稳定完成商品入库、店铺聚合、标签沉淀、任务队列和详情页兜底。

V11.1 的重点是把后端治理结果转成运营能看懂的前端经营模块：总览不显示后端入库明细，经营模块不直接跳任务栏，店铺前端不显示工程 ID。

V11.2 的重点是修复任务主链路：任务列表和详情页必须使用同一套账号可见口径；老板账号能在执行队列看到的任务必须能打开真实任务详情；重复导入同一商品同一风险时，alertId / dataVersion 只进入证据链，不再制造重复待办。

## 当前主链路

```text
报表导入
→ 字段映射 / 校验
→ DataVersion
→ 商品入库ID识别
→ 商品历史深度判断
→ 商品标签 / 店铺标签
→ 店铺权重
→ 商品档案 / 竞品信号 / 上新测试 / 流量趋势
→ 高风险高时效任务队列
→ 任务详情基础兜底
→ 证据提交 / 总管复核
→ 日志留痕 / RAG 记忆候选
```

## V11.2 产品规则

```text
总览不是数据库状态页。
经营模块不是任务入口。
店铺前端只显示真实店铺名称，不显示工程 ID。
商品 / 竞品 / 上新 / 流量进入各自经营对象页。
新商品只做建档和基线校验，不做趋势任务。
低风险信号沉淀为商品/店铺标签，不进入任务栏。
高风险高时效事项进入执行队列。
任务进入执行队列后，详情页必须能打开。
老板账号在任务池可见的任务，详情页必须按同一口径可读。
任务去重以店铺 + 来源族 + 对象 + 风险域 + 动作作为稳定业务键。
alertId / dataVersion 是证据，不是生成新任务的主键。
```

## 当前主入口

```text
/                                      web_demo 前端入口
/api/health                            健康检查
/api/modules/dashboard                 总览
/api/modules/report                    报表
/api/modules/operating-unit            经营
/api/modules/todo                      任务
/api/modules/log                       日志
/api/accounts                          账号
/api/system/repositories               Repository 状态
/api/system/postgres-cutover-check     PostgreSQL 主写切换前检查
/api/architecture/v10/readiness         产品验收守卫
```

## 当前文档

```text
docs/PRODUCT_ARCHITECTURE.md      产品架构基线
docs/MODULE_CHAIN.md              AI 修改仓库的模块链定位图
docs/API_CONTRACT.md              当前 API 契约
docs/DATA_TASK_LIFECYCLE.md       数据到任务生命周期
docs/DEPLOYMENT_RUNBOOK.md        服务器部署和排障 SOP
docs/POSTGRESQL_CUTOVER.md        PostgreSQL 主写切换边界
```

## 模块化修改规则

AI 修改仓库时，先通过 `docs/MODULE_CHAIN.md` 定位模块链，再修改对应前端、API、Service、Repository 或 DB 层。

旧版本文档、历史流水账或废弃页面不作为当前架构依据。

## 当前主前端

```text
web_demo/
```

`frontend/` 若与当前主链路不一致，视为历史资产，不作为当前产品入口。

## 当前后端入口

```text
src/api/main.py
```

## 当前数据库边界

默认运行仍以 SQLite-first Demo 为主。PostgreSQL 是生产迁移目标，需要通过 cutover check 和抽样对账后再进入主写切换。
