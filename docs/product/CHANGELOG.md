# Product Changelog

## v2.3.4 - 2026-06-16

### Product Decision
- V2.3.4 changes owner-side `组织效率` from task-flow metrics into an organization governance console.
- Product truth: `人员总览`看人现在忙不忙；`组织效率`看组织结构、汇报链路、账号权限、店铺归属和权限治理。
- 账号页只回答“我是谁”，组织效率回答“组织怎么运转”。

### Changed
- Added position relationship network: 老板 → 店群总管 → 运营 / 财务 / 观察者.
- Moved role / account permission governance into `组织效率`.
- Added account role control, store authorization control, and role permission template control.
- Account page management button now routes to `组织效率` instead of the legacy role console.
- Added organization governance style file: `web_demo/org-efficiency.css`.
- Frontend assets now use `?v=2.3.4`; API and health versions are aligned.

### Product Boundary
- This remains mock account governance.
- Real version should add persistent org tree, manager assignment, tenant isolation, RBAC audit logs, and approval flow for high-permission changes.

## v2.3.3 - 2026-06-16

- Owner-side `利润预算` changed into `供投财务`.

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
