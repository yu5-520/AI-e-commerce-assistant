# AI ERP 企业级电商经营 SaaS 底座

当前基线：**V12.7.2 真实后端聚合任务生命周期 + 库存动作识别修复**。

V12.7.2 保留 V12.7 的高权重判定规则和 V12.7.1 的聚合队列，但把聚合任务从“前端临时展示”收口为“后端真实任务对象”。同一店铺、同一动作、同一原因的商品任务会合并成一个稳定 task_id 的批量任务，受影响商品写入 affectedProducts，接收、提交、复核和详情页都使用同一个任务来源。库存、补货、可售天数、断货、缺货信号会优先识别为库存警告，不再被 SOP 里的“素材”字样误判为素材测试。

## 当前执行入口

```text
前端唯一入口：web_demo/
后端唯一入口：src/api/main.py
版本主文件：VERSION.md + versioning/VERSION.md
运行态数据库：SQLite Demo runtime
部署脚本：scripts/deploy_fast.sh / scripts/deploy_atomic.sh
```

## 当前主链路

```text
报表 / 接口数据导入
→ 报表布局 Agent / 指标事实表 / 数据缺口池
→ 首份报表 baseline_snapshot，只建基线
→ 两份报表才允许环比经营任务
→ risk_task_service 生成红线任务 + ROI/GMV经营任务
→ action_authorization_gate_service 先识别库存/补货/可售天数，再识别素材/标题/主图
→ task_cluster_service 生成真实后端聚合任务
→ /api/modules/todo 返回已聚合任务池
→ accept / submit / review 先更新内存任务池，再 best-effort 同步 Repository
→ task_report_service 根据同一个 task_id 输出详情报告和 affectedProducts
```

## V12.7.2 硬规则

```text
经营表现不等于权限权重。
高ROI、高GMV、任务优先级、生命周期标签和首份报表标签不能触发高权重审批。
第一份报表只做基线，非红线经营任务必须有至少两份可比报表。
重复商品任务不能刷屏，同类任务必须聚合成真实后端任务。
聚合任务必须有稳定 task_id、affectedProducts 和 taskDetailReport。
接收按钮必须更新当前可见任务池状态，不能只写 Repository。
库存/补货/可售天数信号必须显示为库存警告或补货承接，不能显示成素材测试。
任务详情接口不能 500，异常时返回 failClosed 结构化报告。
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
/api/modules/todo                      聚合后的真实任务队列来源
/api/modules/task-reports/tasks/{id}   任务详情报告，支持批量任务 affectedProducts
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
```

## 部署入口

```bash
bash scripts/deploy_fast.sh
```
