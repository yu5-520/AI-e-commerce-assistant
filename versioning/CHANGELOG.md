# Changelog

## v2.3.8 - 2026-06-16

### Added
- Added manager-specific execution pages: `店群任务`, `任务派发`, `运营复核`, `经营模块`, `复盘提交`, and `数据报表`.
- Added `web_demo/modules/manager/page.js` for the store-group manager workflow.
- Added `web_demo/manager-console.css` for manager execution boards, cards, workload panels, and report tables.
- Added manager-specific dashboard view for 店群执行总览.

### Changed
- 店群总管 navigation no longer exposes 商品 / 竞品 / 上新 / 流量 as scattered first-line tabs.
- Manager role now uses a store-group execution management flow: receive boss tasks, split tasks, dispatch operators, review results, submit retrospectives, and use data reports as evidence.
- Frontend assets were bumped to `?v=2.3.8`.
- FastAPI app version and health version are aligned to `2.3.8`.

### Product Engineering Rule
- 老板端负责看经营、人员、供投、组织和复盘审计，并定下周期任务。
- 店群总管端负责承接老板任务，拆成运营动作，派发员工，复核结果，再提交日报、周报、月报复盘。

## v2.3.7 - 2026-06-16

- `账号` was simplified into a basic account center.

## v2.3.6 - 2026-06-16

- `复盘审计` changed from wide tables into expandable retrospective cards.

## v2.3.5 - 2026-06-16

- Rebuilt owner-facing `复核审计` into `复盘审计`.

## v2.3.4 - 2026-06-16

- Rebuilt owner-facing `组织效率` into an organization governance console.

## v2.3.3 - 2026-06-16

- Rebuilt owner `利润预算` into `供投财务`, combining supply, traffic, and finance views.

## v2.3.2 - 2026-06-16

- Owner-side `任务指挥` was repositioned into `人员总览`.

## v2.3.1 - 2026-06-16

- `店群总览` was upgraded into a realtime operations board.

## v2.3.0 - 2026-06-16

- Removed owner `经营驾驶舱` and repositioned `风险中心` into `店群总览`.

## v2.2.0 - 2026-06-16

- Refactored owner navigation from first-line operation modules into executive modules and added the role permission console.

## v2.1.0 - 2026-06-16

- Added global mock account switching and role-based task visibility.

## v2.0.0 - 2026-06-16

- Added `/api/accounts` and upgraded the task pool into dispatch / submit / review collaboration flow.

## Earlier History

- v1.6.1: Candidate report pages include `加入任务清单` and jump to the matching 待办 task.
- v1.6.0: Added independent task detail report pages and candidate report APIs.
- v1.5.3: Added source-candidate lifecycle archiving.
- v1.5.2: Existing-task buttons jump to the matching task card inside 待办.
- v1.5.1: Backend owns task identity and active-task status.
