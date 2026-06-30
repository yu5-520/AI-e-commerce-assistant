Current Version: 14.8.1

V14.8.1 Product Facts + Data-Gap Safe Task Streaming

Core chain:

`Import -> product projection -> fullProductBundle -> RAG boundary -> Agent soft routing -> task snapshot -> task pool -> frontend read model`

Key updates:

- Product detail no longer depends only on the compact frontend read model. It merges runtime product projection so SKU, 商品定位, 指标事实, 流量事实 and 数据缺口摘要 are visible again.
- Agent判断中的关键字段缺失 no longer stops task generation. It creates a formal data verification SOP task.
- The Agent station streams mature/data-gap judgments into task snapshot and task pool immediately.
- Product manual task creation also routes missing metrics into 数据核验任务.
- Frontend read isolation remains: page switching still must not run materialize/generate/Agent/worker.

Boundary:

Read APIs stay read-only. Compute happens in worker/stations. Data gaps become executable tasks, not hard blocking rules.
