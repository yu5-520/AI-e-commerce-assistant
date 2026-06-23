# AI ERP 经营单元电商协同系统 MVP

> 当前版本：V5.4.0。项目已完成 SQLite-first PostgreSQL mirror 主链路、系统状态页、主写切换前检查清单，并完成 README / docs / CHANGELOG 文档分层。

## 项目定位

AI ERP 经营单元电商协同系统是一个货架电商运营 Demo，目标是把报表导入、经营预警、任务流转、Agent 建议、证据提交、审计追踪和生产化迁移路径串成一个可演示的最小系统。

核心规则：**报表确认导入就是自动入库；商品、报表、总览必须随导入同步刷新；任务按优先级、截止时间和风险域排序；Demo 阶段允许删除测试记录。**

## 当前主链路

```text
Browser / Client
↓
Nginx / FastAPI
↓
系统状态页：system / repository / architecture / cutover check
↓
SQLite Demo Runtime：核心写路径先成功
↓
PostgreSQL Mirror：hybrid/postgres 模式尝试写入 Production Repository
↓
PostgreSQL Cutover Check：主写切换前只读检查，不自动切换
```

## 演示入口

```text
/                              前端 Demo
/api/health                    健康检查
/api/system/security           系统安全状态
/api/system/repositories       Repository / Mirror 运行态
/api/system/postgres-cutover-check  PostgreSQL 主写切换前检查
/api/architecture/p0           P0 架构状态
```

## 文档入口

```text
docs/CHANGELOG.md              版本更新记录
docs/POSTGRESQL_ALEMBIC.md     PostgreSQL / Alembic / Repository 迁移说明
docs/P0_SAAS_ARCHITECTURE.md   SaaS P0 架构拆解
```

## 当前真实状态

```text
已完成：核心写路径 SQLite-first PostgreSQL mirror。
已完成：前端系统状态页。
已完成：mirror 公共控制层。
已完成：PostgreSQL 主写切换前检查清单。
已完成：README / docs / CHANGELOG 文档拆分。
仍待完成：生产 JWT / Session、hybrid 抽样对账、PostgreSQL 主写正式切换。
```
