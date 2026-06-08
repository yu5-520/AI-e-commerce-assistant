# 后端 API 契约占位

后续从 GitHub Issue 迁移到前端 UI 时，建议保留同一条分析链路。

建议接口：

POST /api/analyze
- 输入：platform、mode、product、body、comment
- 输出：result markdown 或结构化 result sections

GET /api/result/:id
- 查询历史分析结果

POST /api/feedback
- 回传用户选择、点击、成交、复盘数据

当前阶段 GitHub Actions 临时代替后端调度。