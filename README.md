# AI ERP 企业级电商经营 SaaS 底座

当前基线：V11.12 轻量原子部署 + 共享 venv。

## 产品定位

这是一个任务驱动型 AI 电商经营系统。

V11 的重点不是生成更多任务，而是验证真实报表导入后，系统能不能稳定完成商品入库、店铺聚合、标签沉淀、任务队列和详情页结构化报告。

V11.1 的重点是把后端治理结果转成运营能看懂的前端经营模块：总览不显示后端入库明细，经营模块不直接跳任务栏，店铺前端不显示工程 ID。

V11.2 的重点是修复任务主链路：任务列表和详情页必须使用同一套账号可见口径；老板账号能在执行队列看到的任务必须能打开真实任务详情；重复导入同一商品同一风险时，alertId / dataVersion 只进入证据链，不再制造重复待办。

V11.3 的重点是只在账号页提供 MVP 测试身份切换，不做全局账号切换器，不改变正式权限配置。

V11.4 的重点是后端账号隔离安全闸：生产模式禁止信任前端 mock 身份；Repository 查询强制 tenant + org + role data scope；严格模式下缺 tenant / org / store 归属的数据进入隔离区，不进入经营模块。

V11.5 的重点是去本地兜底：前端接口失败不再展示模拟账号、模拟商品、模拟店铺、模拟任务或历史内存数据；接口失败显示明确错误态，接口正常但无数据显示真实空态。

V11.6 的重点是导入闭环校验：报表导入完成后反查经营 / 任务 / 数据真实模块状态，导入提示必须按“导入行数、商品数、店铺数、可执行任务数、标签沉淀数”展示；任务页内存为空时从 TaskRepository 读取可见任务；经营入口收口为商品 / 竞品 / 上新 / 流量。

V11.7 的重点是经营对象入库优先：报表导入后先完成清洗、分类、商品主档 upsert、店铺主档 upsert；商品和店铺进入经营单元不依赖标签或任务生成，低风险可以只沉淀标签，但经营对象必须可见。

V11.8 的重点是上传账号归属优先：正常报表导入由上传账号决定商品 / 店铺归属；报表出现新店铺时直接创建并归属上传账号；店铺权限迁移才需要接收确认；新任务必须由经营对象、指标证据和 SOP 任务包生成，旧规则退出主链路。

V11.9 的重点是导入闭环硬校验：导入成功必须绑定经营对象主档写入结果；rows > 0 但商品 / 店铺为 0 时不再显示假成功；商品 / 竞品 / 上新 / 流量页面脚本重新挂载，经营模块入口必须能跳到对应模块。

V11.10 的重点是运行态诊断和历史回填：系统页优先展示 imported_report_rows、operating_products、operating_stores、当前账号可见商品 / 店铺；历史导入数据可以显式回填经营对象主档；经营页有数据版本但对象为 0 时显示“经营对象未入库”。

V11.11 的重点是部署原子化：ECS 不再作为半开发环境原地覆盖运行；新版本先进入独立 releases 目录，版本、前端资源和关键 API 路由全部验收通过后才切换 current，失败自动回滚上一版。

V11.12 的重点是轻量原子部署：保留 releases/current 原子切换，但默认复用 shared/.venv；requirements 未变化时跳过 pip install；版本一致性仍强校验，路由守卫默认 warn，适配低配 ECS。

## 当前主链路

```text
报表导入
→ 当前账号识别
→ 字段映射 / 校验
→ DataVersion
→ 数据清洗
→ 数据分类
→ 显式 rows 进入经营对象 upsert
→ 新店铺自动创建并归属上传账号
→ 商品主档 upsert 并继承店铺归属
→ 商品 / 店铺经营状态更新
→ 商品标签 / 店铺标签
→ 趋势 / 风险判断
→ SOP 任务包生成
→ 任务继承经营对象归属
→ 任务详情结构化报告
→ 证据提交 / 总管复核
→ 日志留痕 / RAG 记忆候选
```

## V11.12 可信展示规则

```text
账号 Account 只表达登录身份，不直接拥有业务数据。
正常报表导入的数据归属来源是上传账号。
报表字段只提供经营数据、展示名、去重和校验，不决定跨账号权限。
运营上传报表时，新店铺直接创建并归属该运营。
只有店铺权限从一个运营迁移到另一个运营时，才需要接收确认。
商品继承店铺归属。
任务继承商品 / 店铺归属。
任务不能反向制造商品 / 店铺权限。
生产模式禁止信任 X-Mock-User-Id。
生产模式必须从可信登录态 / JWT / Session 生成 UserContext。
所有 Repository 查询必须追加 tenant_id + org_id + soft delete + role data scope。
前端接口失败时显示“接口异常”，不得返回本地业务兜底。
后端正常返回空数组 / 空对象时显示“暂无数据”，不得补模拟数据。
导入成功文案必须来自模块真实反查结果，不能只来自导入响应层。
rows > 0 但商品 / 店铺为 0 时，必须显示经营对象入库失败。
有 dataVersion 但经营对象为 0 时，经营页必须显示“经营对象未入库”。
系统页必须展示真实运行态诊断，而不是只展示旧验收清单。
历史导入数据可以通过系统页显式回填 operating_products / operating_stores。
标签沉淀不是任务栏任务；可执行任务数必须单独展示。
不生成任务不等于不更新商品。
不生成任务不等于不更新店铺。
旧 infer / v5_rule_based / 详情兜底报告不得生成新任务。
部署必须通过 VERSION / app.version / health / 前端资源版本一致性检查。
fetch 失败不得继续 reset 到旧缓存。
ECS 运行态以 /opt/ai-ecommerce-assistant-deploy/current 为准。
低配 ECS 默认使用 /opt/ai-ecommerce-assistant-deploy/shared/.venv，不每次重装依赖。
```

## 当前主入口

```text
/                                      web_demo 前端入口
/api/health                            健康检查
/api/modules/dashboard                 总览
/api/modules/report                    报表
/api/modules/operating-unit            经营
/api/modules/product                   商品
/api/modules/todo                      任务
/api/modules/log                       日志
/api/accounts                          账号
/api/system/runtime-diagnostics        运行态诊断
/api/system/backfill-operating-objects 经营对象回填
/api/system/isolation                  后端账号隔离状态
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
scripts/deploy_atomic.sh          ECS 轻量原子部署脚本
scripts/verify_release.py         版本一致性验收脚本
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

## 当前部署入口

```text
bash scripts/deploy_atomic.sh
```

默认低配 ECS 模式：

```text
LIGHT_DEPLOY=1
ROUTE_GUARD_MODE=warn
RUNTIME_ROUTE_GUARD=warn
```

部署后运行态以：

```text
/opt/ai-ecommerce-assistant-deploy/current
```

为准。

## 当前数据库边界

默认运行仍以 SQLite-first Demo 为主。PostgreSQL 是生产迁移目标，需要通过 cutover check 和抽样对账后再进入主写切换。
