# 下一次继续开发时给 AI 的指令

请基于当前仓库继续开发 V7：API 可交互 Demo。

优先任务：

1. 新增 FastAPI 后端：`src/api/main.py`
2. 封装 `/api/health`
3. 封装 `/api/demo/run`
4. 封装 `/api/evals/run`
5. 修改 `web_demo/app.js`，将内置 Mock 数据改为调用 API
6. 增加任务确认 / 拒绝接口
7. 增加日志输出

开发原则：

- 不接真实 ERP / CRM
- 不接真实店铺后台
- 不自动改价
- 不自动投放
- 不自动群发客户
- 高风险任务必须人工确认

当前项目定位：

> Workflow-first 的 AI + RPA + ERP + CRM 电商经营自动化工作台 MVP。
