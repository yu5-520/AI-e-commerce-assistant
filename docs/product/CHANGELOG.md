# Product Changelog

## v2.3.2 - 2026-06-16

### Product Decision
- V2.3.2 changes owner-side `任务指挥` into `人员总览`.
- Product truth: 老板不需要盯每条任务，老板需要看任务压在谁身上、谁忙、谁空闲、谁被退回、谁可能成为闭环卡点。
- 具体任务派发、提交、复核仍属于店群总管和运营执行层。

### Changed
- Owner navigation label changed from `任务指挥` to `人员总览`.
- Added employee realtime status cards for 店群总管、运营 A、运营 B、数据财务.
- Added personnel task mapping table: 人员、角色、状态、当前任务、今日完成、待派发、待复核、退回、超时、平均处理、负荷、最近动作.
- Added `web_demo/people-overview.css` for personnel table layout.
- Frontend assets now use `?v=2.3.2`; API and health versions are aligned.

### Product Boundary
- This remains mock realtime employee state.
- Real version should connect assignment records, user sessions, submit/review logs, and timeout rules.

## v2.3.1 - 2026-06-16

### Product Decision
- V2.3.1 fixes `店群总览` from a card-text page into a realtime business operations board.
- Product truth: 老板不是读长句子，而是横向扫平台、店铺、订单、销售额、利润、评论、退款率、库存金额和待办状态。
- 实时科技感来自同步状态、趋势变化、状态灯和横向对比，不是把风险商品提前摆到第一屏。

### Changed
- 店铺经营明细从大卡片长句改成横向数据表，修复店铺名称竖排问题。
- Added realtime sync strip: ERP time, platform sync state, delay marker, and task count.
- Added platform live cards with status dot, order, sales, profit, comments, progress bar, and sync footer.
- Added trend chips for order, sales, profit, and refund/operation indicators.
- Frontend assets now use `?v=2.3.1`; API and health versions are aligned.

## v2.3.0 - 2026-06-16

### Product Decision
- V2.3.0 removes the redundant owner `经营驾驶舱`.
- Product truth: 老板第一层应该先看经营盘面，不是先看风险结论。
- `风险中心` is repositioned into `店群总览`.

### Changed
- Owner navigation is now: 总览、店群总览、任务指挥、利润预算、组织效率、复核审计、账号.
- 店群总览 shows platform summary and store-level business data.
- 商品、竞品、上新、流量 remain first-line evidence and execution modules for 总管 / 运营, not owner daily tabs.

## v2.2.0 - 2026-06-16

- Separated owner decision navigation from first-line operation navigation.

## v2.1.0 - 2026-06-16

- Added global account switching and role-based task/report views.

## v2.0.0 - 2026-06-16

- Added account roles, permissions, and dispatch / submit / review collaboration flow.

## Earlier History

- v1.6.1: Candidate report pages include `加入任务清单`.
- v1.6.0: Added independent detail report pages.
- v1.5.3: Completed tasks archive their source candidates.
- v1.5.2: Existing-task buttons jump to the matching task card inside 待办.
- v1.5.1: Backend owns task identity and active-task status.
