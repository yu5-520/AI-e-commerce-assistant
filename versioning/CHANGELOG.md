# Changelog

## v2.3.6 - 2026-06-16

### Added
- Added expandable retrospective cards for daily / weekly / monthly / special reports.
- Added expandable audit detail cards with evidence and Agent judgment placeholders.
- Added expandable next-cycle task draft cards with goal, split direction, and future action buttons.
- Added `web_demo/review-audit.css` for detail-card layout and mobile-safe wrapping.

### Changed
- Replaced wide retrospective audit tables with summary-first expandable panels to avoid compressed / garbled layout on iPad and smaller screens.
- Frontend assets were bumped to `?v=2.3.6`.
- FastAPI app version and health version are aligned to `2.3.6`.

### Product Engineering Rule
- `复盘审计` should not be a wide table page.
- The owner should scan summaries first, then expand details when Agent evidence, audit reasoning, or task-generation basis is needed.

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
