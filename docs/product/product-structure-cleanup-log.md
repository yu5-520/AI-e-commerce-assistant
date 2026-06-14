# 产品结构清理日志

## 清理目标

将仓库从“求职展示导向”收敛为“产品完成导向”。

## 本轮新增产品骨架文档

```text
docs/product/README.md
docs/product/product-map.md
docs/product/domain-model.md
docs/product/user-flow.md
docs/product/module-boundary.md
docs/product/mvp-scope.md
docs/product/product-decision-log.md
```

## 本轮原则

- 不新增简历、面试、HR、BOSS 类文档。
- 不继续堆解释型包装材料。
- 产品文档只服务用户、场景、模块、对象、流程、边界和 MVP。
- 后续围绕产品结构继续重构 API 和前端。

## 下一步建议

```text
1. 拆分 FastAPI routes
2. 按 product-map 重构前端信息架构
3. 增加 SQLite / JSON 日志持久化
4. 增加 Data Import 页面和 API
5. 从 Demo Workflow 逐步拆成产品级 workflows
```
