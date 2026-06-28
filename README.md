# AI ERP 企业级电商经营 SaaS 底座

当前基线：**V12.6.0 RAG经营动作权限闸门 + 系统估算 + 自动确认 / 主管审批流**。

V12.6 保留 V12.5 首份报表基线模式和任务页同步修复，在任务生成后增加统一经营动作权限闸门。活动报名、标题测试、主图测试、素材测试、扩流、价格调整、投放预算调整、主推位调整、补货/调拨、下架/降权等经营动作，都必须经过账号权限、店铺权重、商品权重、公司基线和系统保守估算下限校验。运营只补充客观事实，系统估算 ROI、GMV、毛利率、库存消耗等影响，RAG 控制权限和历史经验。

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
→ 文件解析 / 报表布局 Agent / 指标事实表 / 数据缺口池
→ 商品页从 product_metric_facts / traffic_source_facts / store_metric_facts 读取事实
→ 首份报表 baseline_snapshot，只建商品、店铺、ROI、GMV、库存、广告、转化基线
→ 两份报表才允许环比经营任务
→ 三份报表或 7 天窗口才允许 3/7/14/30/90 天趋势任务
→ risk_task_service 生成红线任务 + ROI/GMV经营任务
→ module_task_service.apply_v126_task_governance
→ rag_business_memory_service 读取公司基线和历史经营记忆
→ action_impact_estimation_service 系统生成保守 / 正常 / 乐观估算
→ action_authorization_gate_service 判断账号权限、动作类型、店铺权重、商品权重
→ 权限内且保守下限通过：auto_execute，生成运营执行任务
→ 超权限或低于基线：manager_approval_required / owner_approval_required
→ AppApi.refreshTaskState() 从 /api/modules/todo 同步后端任务池
→ 任务详情、证据提交、总管复核、日志留痕、RAG 候选
```

## V12.6 经营动作权限规则

```text
Agent 负责判断经营问题。
系统负责估算经营动作影响。
RAG 负责账号权限、公司基线、历史活动/标题/主图测试记忆。
运营只补充平台活动、竞品、标题、主图、素材等客观事实。
主管只审批超权限、低于基线或高权重对象动作。
```

动作分流：

```text
auto_execute：权限内，直接生成运营执行任务。
manager_approval_required：需要主管确认。
owner_approval_required：需要老板或总管确认。
evidence_required：缺少客观事实，先补证再判断。
```

活动任务：

```text
运营上传活动入口、活动价、平台补贴、商家让利、报名门槛、资源位、竞品价格、竞品销量截图。
系统估算活动后 ROI、GMV、毛利率、库存消耗、退款风险。
自动确认只看保守估算下限。
活动开始后第3天自动复盘，并写入周报和 RAG 记忆候选。
```

标题 / 主图测试：

```text
中权重店铺 / 商品 + 中权重运营权限：直接生成测试任务。
高权重店铺 / 商品 + 中权重运营权限：生成主管确认任务。
测试第3天自动复盘点击率、访客数、转化率、ROI、GMV变化。
```

## 当前主文档

```text
docs/API_CONTRACT.md              当前真实 API 契约
docs/MODULE_CHAIN.md              AI 修改仓库的模块链定位图
docs/PRODUCT_ARCHITECTURE.md      当前产品结构和模块边界
docs/DATA_TASK_LIFECYCLE.md       数据、事实、缺口、任务、复核生命周期
docs/V12_REPORT_GATEWAY.md        V12/V12.2 报表布局 Agent 和指标事实层
docs/DEPLOYMENT_RUNBOOK.md        V12.6 服务器部署和排障 SOP
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
/api/data/upload/confirm               上传确认导入 + 经营对象 / block事实 / 缺口 / 诊断 / 任务同步
/api/data/metric-facts/summary         指标事实表统计
/api/data/data-gaps/summary            数据缺口池统计
/api/data/import-diagnostics           Sheet → Block → Fact → Gap → Staging 诊断
/api/system/runtime-diagnostics        运行态诊断
/api/system/reset-runtime-data          清空演示运行态
/api/system/repositories               Repository 状态
/api/system/postgres-cutover-check     PostgreSQL 主写切换前检查
```

## V12.6 硬规则

```text
VERSION.md、versioning/VERSION.md、FastAPI app.version、health.API_VERSION、web_demo/index.html 资源版本必须一致。
README 只做当前入口索引，不堆历史流水账。
API_CONTRACT 只记录当前真实可用 API。
MODULE_CHAIN 只记录当前执行链路，不能把 frontend/ 作为当前入口。
事实表未命中的指标显示“未识别”，不能显示 0，不能读对象缓存。
product ROI、traffic_source ROI、store ROI 互相隔离，不能跨口径覆盖。
第一份报表只做基线，非红线经营任务必须有至少两份可比报表。
经营动作必须经过 RAG 权限闸门。
运营不做预测，系统做影响估算。
任务列表只做时间和紧急度排序，完整 SOP 放详情页。
经营页店铺卡片永远保留查看商品入口，有任务时追加查看任务。
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
