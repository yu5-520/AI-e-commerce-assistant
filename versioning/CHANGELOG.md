# Changelog

## v2.3.5 - 2026-06-16

### Added
- Rebuilt owner-facing `复核审计` into `复盘审计`.
- Added daily / weekly / monthly / special retrospective intake data.
- Added audit issue list for missed weekly targets, low ROI, rising refund rate, and review delay.
- Added next-cycle task draft list for next week / next month task planning.

### Changed
- Owner navigation label changed from `复核审计` to `复盘审计`.
- The page no longer focuses on single task logs; it focuses on cycle retrospectives, operating failure review, and next-cycle task planning.
- Frontend assets were bumped to `?v=2.3.5`.
- FastAPI app version and health version are aligned to `2.3.5`.

### Product Engineering Rule
- Boss accounts usually do not dispatch tasks because of one store's short-term fluctuation.
- Boss tasks should come mainly from daily / weekly / monthly retrospectives and audit findings.
- `复盘审计` turns past reports into next-cycle tasks.

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
