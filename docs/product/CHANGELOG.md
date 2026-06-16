# Product Changelog

## v2.3.3 - 2026-06-16

### Product Decision
- V2.3.3 changes owner-side `利润预算` into `供投财务`.
- Product truth: 老板不是只看利润结果，而是看货、流量、钱三条链路有没有一起跑顺。
- 供应链、投流和财务需要放在同一个经营判断页面里。

### Changed
- Owner navigation label changed from `利润预算` to `供投财务`.
- Added supply overview: 供应商、品类、采购成本变化、供货周期、库存金额、安全库存、状态.
- Added traffic overview: 广告消耗、ROAS、点击成本、转化率、付费订单、自然订单、状态.
- Added finance summary: 销售额、毛利、广告费、退款、物流、平台扣点、库存资金、净利润.
- Added `web_demo/supply-finance.css`.
- Frontend assets now use `?v=2.3.3`; API and health versions are aligned.

### Product Boundary
- This remains mock operating data.
- Real version should connect supplier records, inventory sync, ad platform data, order profit data, and finance settlement data.

## v2.3.2 - 2026-06-16

- Owner-side `任务指挥` changed into `人员总览`.

## v2.3.1 - 2026-06-16

- `店群总览` was upgraded into a realtime business operations board.

## v2.3.0 - 2026-06-16

- Removed owner `经营驾驶舱` and repositioned `风险中心` into `店群总览`.

## v2.2.0 - 2026-06-16

- Separated owner decision navigation from first-line operation navigation.

## v2.1.0 - 2026-06-16

- Added global account switching and role-based task/report views.

## v2.0.0 - 2026-06-16

- Added account roles, permissions, and dispatch / submit / review collaboration flow.

## Earlier History

- v1.6.1: Candidate report pages include `加入任务清单`.
- v1.6.0: Added independent detail reports.
- v1.5.3: Completed tasks archive their source candidates.
- v1.5.2: Existing-task buttons jump to the matching task card inside 待办.
- v1.5.1: Backend owns task identity and active-task status.
