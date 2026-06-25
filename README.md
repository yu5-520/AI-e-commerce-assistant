# AI ERP 企业级电商经营 SaaS 底座

当前基线：V11.7 经营对象入库优先。

## 产品定位

这是一个任务驱动型 AI 电商经营系统。

V11 的重点不是生成更多任务，而是验证真实报表导入后，系统能不能稳定完成商品入库、店铺聚合、标签沉淀、任务队列和详情页兜底。

V11.1 的重点是把后端治理结果转成运营能看懂的前端经营模块：总览不显示后端入库明细，经营模块不直接跳任务栏，店铺前端不显示工程 ID。

V11.2 的重点是修复任务主链路：任务列表和详情页必须使用同一套账号可见口径；老板账号能在执行队列看到的任务必须能打开真实任务详情；重复导入同一商品同一风险时，alertId / dataVersion 只进入证据链，不再制造重复待办。

V11.3 的重点是只在账号页提供 MVP 测试身份切换，不做全局账号切换器，不改变正式权限配置。

V11.4 的重点是后端账号隔离安全闸：生产模式禁止信任前端 mock 身份；Repository 查询强制 tenant + org + role data scope；严格模式下缺 tenant / org / store 归属的数据进入隔离区，不进入经营模块。

V11.5 的重点是去本地兜底：前端接口失败不再展示模拟账号、模拟商品、模拟店铺、模拟任务或历史内存数据；接口失败显示明确错误态，接口正常但无数据显示真实空态。

V11.6 的重点是导入闭环校验：报表导入完成后反查经营 / 任务 / 数据真实模块状态，导入提示必须按“导入行数、商品数、店铺数、可执行任务数、标签沉淀数”展示；任务页内存为空时从 TaskRepository 读取可见任务；经营入口收口为商品 / 竞品 / 上新 / 流量。

V11.7 的重点是经营对象入库优先：报表导入后先完成清洗、分类、商品主档 upsert、店铺主档 upsert；商品和店铺进入经营单元不依赖标签或任务生成，低风险可以只沉淀标签，但经营对象必须可见。

## 当前主链路

```text
报表导入
→ 字段映射 / 校验
→ DataVersion
→ 数据清洗
→ 数据分类
→ 商品主档 upsert
→ 店铺主档 upsert
→ 商品 / 店铺经营状态更新
→ 商品标签 / 店铺标签
→ 风险判断
→ 高风险高时效任务队列
→ 导入闭环真实反查
→ 任务详情基础兜底
→ 证据提交 / 总管复核
→ 日志留痕 / RAG 记忆候选
```

## V11.7 可信展示规则

```text
账号 Account 只表达登录身份，不直接拥有业务数据。
权限 Role / Permission 表达这个身份能做什么。
数据范围 Data Scope 表达这个身份能看哪些经营单元、店铺、商品、任务、报表。
店铺归属 Store Assignment 表达店铺由谁运营、谁复核、谁管理。
生产模式禁止信任 X-Mock-User-Id。
生产模式必须从可信登录态 / JWT / Session 生成 UserContext。
所有 Repository 查询必须追加 tenant_id + org_id + soft delete + role data scope。
导入数据缺 tenant_id / org_id / store_id 时进入隔离区，不进入经营模块。
MVP 账号页切换只允许 demo_mode 使用，不代表正式系统能力。
前端接口失败时显示“接口异常”，不得返回本地业务兜底。
后端正常返回空数组 / 空对象时显示“暂无数据”，不得补模拟数据。
顶部状态只允许“后端正常 / 接口异常 / 接口检测中”，不再出现“本地兜底”。
导入成功文案必须来自模块真实反查结果，不能只来自导入响应层。
标签沉淀不是任务栏任务；可执行任务数必须单独展示。
不生成任务不等于不更新商品。
不生成任务不等于不更新店铺。
低风险沉淀标签不阻塞商品 / 店铺进入经营单元。
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
