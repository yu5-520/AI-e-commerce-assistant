# AI ERP 企业级电商经营 SaaS 底座

当前基线：V10.9 任务驱动产品架构。

## 产品定位

这是一个任务驱动型 AI 电商经营系统。

系统以报表导入为触发器，以经营数据趋势和风险信号为判断依据，以任务池为主界面，以老板 / 总管 / 运营三端流转为执行链路，以日志、审计和 RAG 记忆作为复盘底座。

## 当前主链路

```text
报表导入
→ 字段映射 / 校验
→ DataVersion
→ 模块投影
→ 趋势计算
→ 风险信号
→ Agent 经营档案 / 自动标签
→ 标签变化任务
→ 统一任务池
→ 跨账号流转
→ 证据提交 / 总管复核
→ 日志留痕 / RAG 记忆候选
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
/api/architecture/v10/readiness         V10 产品验收守卫
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
