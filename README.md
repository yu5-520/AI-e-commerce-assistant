# AI ERP 经营单元电商协同系统 MVP

> 当前版本：V5.3.9。新增 PostgreSQL 主写切换前检查清单：`/api/system/postgres-cutover-check` 会输出连接、迁移、Repository Mirror、Demo 回退、身份边界、回滚策略等检查项。系统状态页已可视化 pass / warn / blocked。

## 当前主链路

```text
Browser / Client
↓
Nginx / FastAPI
↓
系统状态页：system / repository / architecture / cutover check
↓
Repository Runtime：DB_REPOSITORY_MODE=sqlite | hybrid | postgres
↓
repository_mirror_base_service：统一 mirror 控制流
↓
SQLite Demo Runtime：核心写路径先成功
↓
PostgreSQL Mirror：hybrid/postgres 模式尝试写入 Production Repository
↓
PostgreSQL Cutover Check：主写切换前只读检查，不自动切换
```

核心规则：**首页展示经营摘要，不展示工程代号；报表确认导入就是自动入库；商品、报表、总览必须随导入同步刷新；当前任务按优先级、截止时间和风险域排序；Demo 阶段可删除单条导入记录。**

## V5.3.9 新增

```text
src/services/postgres_cutover_check_service.py  PostgreSQL 主写切换前检查服务
src/api/routes/system.py                        GET /api/system/postgres-cutover-check
web_demo/modules/system-status/page.js          系统状态页展示 cutover check
web_demo/system-status.css                      pass / warn / blocked 状态样式
```

## 当前真实状态

```text
已完成：核心写路径 SQLite-first PostgreSQL mirror。
已完成：前端系统状态页。
已完成：mirror 公共控制层。
已完成：PostgreSQL 主写切换前检查清单。
默认模式：DB_REPOSITORY_MODE=sqlite，主写切换检查会提示先进入 hybrid。
可测模式：DB_REPOSITORY_MODE=hybrid，检查连接和抽样对账条件。
仍待完成：生产 JWT / Session、README / docs / CHANGELOG 拆分、PostgreSQL 主写正式切换。
```

## 下一步

```text
A. V5.4.0：README / docs / CHANGELOG 拆分，降低文档重复
B. V5.4.0：hybrid 抽样对账接口
```
