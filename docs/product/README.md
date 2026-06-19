# Product Docs

本目录只保存当前产品本体相关文档。为避免重复，文档分工如下：

```text
README.md                         仓库首页：当前主线、快速启动、常用入口
CHANGELOG.md                      产品更新日志：每个版本的产品决策
mvp-scope.md                      MVP 范围：当前做什么、不做什么、验收标准
module-boundary.md                模块边界：API、账号、Agent、RAG、前后端边界
product-decision-log.md           重大产品决策日志
product-structure-cleanup-log.md  产品结构清理日志
```

## 单一事实源

```text
产品主线：README.md
模块 / API / 权限边界：docs/product/module-boundary.md
MVP 验收：docs/product/mvp-scope.md
工程版本：versioning/VERSION.md + versioning/CHANGELOG.md
产品版本：docs/product/CHANGELOG.md
专项设计：docs/V4.*.md
```

## 当前产品主线

```text
ERP / CRM Mock 数据
↓
模块预警 / 详情报告
↓
V4 模块 Agent
↓
V4.2 任务 Agent
↓
V4.3 创意 Agent
↓
统一任务池
↓
任务派发 / 运营提交 / 总管复核
↓
V4.4 回流 Agent
↓
V4.1 RAG Memory 复核入库 / 召回
```

## 当前原则

- Agent 可以增强判断，但不能越权执行。
- RAG 可以召回复核经验，但不能污染知识库。
- 任务、创意、回流都必须进入统一任务池、人工确认或复核链路。
- 后续新增版本只在对应事实源更新完整内容，其他文档只保留摘要和链接，避免一处更新、四处漂移。
