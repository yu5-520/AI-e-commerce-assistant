# Product Docs

本目录只保存当前产品本体相关文档。

## 当前文档结构

```text
CHANGELOG.md                         产品更新日志
mvp-scope.md                         当前 MVP 范围与验收标准
module-boundary.md                   当前模块边界
product-decision-log.md              重大产品决策日志
product-structure-cleanup-log.md     产品结构清理日志
```

## 当前产品主线

```text
ERP / CRM Mock 数据
↓
经营单元识别
↓
商品、竞品、上新、流量、报表模块
↓
候选预警 / 详情报告
↓
V4.2 自动解析生成任务 Agent
↓
V4.3 标题主图垂直类目 Agent
↓
V4 模块 Agent 分析 / 摘要 / 任务草案
↓
V4.2 任务解析运营方式 Agent
↓
统一任务池
↓
账号角色 / 权限 / 店群范围
↓
任务派发 / 运营提交 / 总管复核
↓
V4.4 回流任务 Agent
↓
V4.1 经验卡草案 / 复核入库 / RAG 召回
↓
/api/modules/* + /api/accounts
↓
web_demo/index.html + web_demo/modules/*/page.js
```

## 当前原则

- 先跑通企业协同的最小闭环，再接真实登录、企业租户、真实 ERP / CRM 接口。
- V4 Agent 只做模块增强，不绕过 `/api/accounts` 权限边界，不直接执行经营动作。
- V4.1 RAG memory 只召回复核过的结构化经验卡，不把原始日志直接写入正式知识库。
- V4.2 task Agent 只生成任务候选和运营打法，不绕过统一任务池、人审和复核。
- V4.3 creative Agent 只生成标题、主图方向、卖点排序和测试计划，不直接发布商品或回写店铺后台。
- V4.4 feedback Agent 只生成周期摘要、学习候选和经验卡草案，不自动批准经验入库。
- 当前主线以 README、`src/api/main.py`、`/api/modules/*`、`/api/accounts` 和 smoke tests 为准。
- 产品主链路、页面结构、API 边界或产品定位发生变化时，必须同步更新 `CHANGELOG.md`。
- 结构级清理还必须同步更新 `versioning/CHANGELOG.md` 和 `versioning/VERSION.md`。
