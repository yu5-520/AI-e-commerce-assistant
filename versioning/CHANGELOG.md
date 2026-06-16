# Changelog

## v2.3.4 - 2026-06-16

### Added
- Rebuilt owner-facing `组织效率` into an organization governance console.
- Added position relationship network: 老板 → 店群总管 → 运营 / 财务 / 观察者.
- Added organization KPI metrics: employee count, manager count, operator count, finance count, read-only count, permission exception count, unassigned account count, and permission change count.
- Added account role control, store authorization control, and role permission template control inside `组织效率`.
- Added `web_demo/org-efficiency.css` for organization map and permission governance layout.

### Changed
- `账号` page now only shows current identity, scope, visible modules, and permission summary; its management button routes to `组织效率`.
- Legacy `role-console` remains as a compatibility route, but daily role / store / permission governance is now under `组织效率`.
- Frontend assets were bumped to `?v=2.3.4`.
- FastAPI app version and health version are aligned to `2.3.4`.

### Product Engineering Rule
- `人员总览` shows realtime employee state.
- `组织效率` shows organization structure, reporting chain, account permissions, store ownership, and permission governance.
- `账号` answers “我是谁”; `组织效率` answers “组织怎么运转”.

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
