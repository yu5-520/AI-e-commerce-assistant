# Product Changelog

## v2.1.0 - 2026-06-16

### Product Decision
- V2.1.0 turns the account system from a static role list into a role-view simulation.
- Product truth: the same system should show different task ranges, buttons, and report explanations when switching between 老板、店群总管、运营、数据 / 财务、只读观察.
- Higher roles get broader scope and deeper management context; execution roles get narrower task scope and clearer checklists.

### Changed
- Added a global account switcher in the topbar.
- 账号 page now changes by current role, including visible modules, allowed actions, hidden fields, and insight depth.
- 权限 cards now show productized Chinese permission labels instead of raw permission ids.
- 待办 now filters visible tasks by current account and hides unavailable action buttons.
- 详情报告 now adds a role-specific interpretation block.
- Frontend assets now use `?v=2.1.0`; API and health versions are aligned.

### Product Boundary
- This is still mock role switching, not real login.
- The frontend stores the selected mock user locally and sends it with `X-Mock-User-Id`.
- Production enterprise auth, tenant isolation, and audit storage still need a later version.

## v2.0.0 - 2026-06-16

### Product Decision
- V2.0.0 moves the product from a single-user operating dashboard into a light enterprise collaboration skeleton.
- Product truth: 老板不是直接处理每个任务；老板看总览和完整报告后，下发给店群总管，总管拆分给运营，运营提交后再由总管复核。
- The active trunk is now `/api/modules/*` for business modules plus `/api/accounts` for account, role, permission, and store-scope context.

### Changed
- Added `账号` page for role permissions, account list, store scope, and task-flow explanation.
- Added five v2 roles: 老板账号、店群总管账号、运营账号、数据 / 财务账号、只读观察账号.
- Added task assignment, submit, and review actions to 待办.
- 待办 cards now show assignee, reviewer, assigner, and workflow status.
- Task flow now supports: `候选预警 -> 任务池 -> 派发 -> 处理中 -> 提交复核 -> 通过 / 退回 -> 归档`.
- Product docs were cleaned so README、MVP 范围、模块边界 and smoke tests point to the current v2 trunk.
- Frontend assets now use `?v=2.0.0`; API and health versions are aligned.

### Product Boundary
- This is still Mock account context, not real login or enterprise SSO.
- This does not connect real ERP / CRM / shop backend data.
- This does not execute real price, inventory, ad, listing, customer, or refund actions.
- Agent remains a report-enrichment boundary, not an execution owner.

## v1.6.1 - 2026-06-16

### Product Decision
- V1.6.1 makes the independent candidate report page a task conversion page, not only a read-only explanation page.
- Product truth: operators normally read the compact warning, open the full report, then add the task from that same report page.

### Changed
- Candidate report pages now include a bottom `加入任务清单` primary action.
- Added `createTaskFromReport(module, entityId)` in `web_demo/core/task-actions.js` to map report context to the correct module task creation action.
- After creating the task from a report, the UI refreshes task/module state and jumps to the new task position in 待办.
- Frontend assets now use `?v=1.6.1`; API and health versions are aligned.

### Product Boundary
- This still uses the existing module task creation endpoints.
- No new high-risk execution is added; creating a task still only enters 待办 and waits for human handling.

## v1.6.0 - 2026-06-16

### Product Decision
- V1.6.0 adds an independent detail report page instead of an inline drawer.
- Product truth: tasks need decision context, not just execution buttons. A task report explains why the warning exists, what evidence supports it, and how operators should handle it.

### Changed
- Added `src/services/task_report_service.py` as the report-generation boundary and future Agent insertion point.
- Added task report APIs:
  - `GET /api/modules/task-reports/tasks/{task_id}`
  - `GET /api/modules/task-reports/candidates/{module}/{entity_id}`
- Added `web_demo/modules/task-report/page.js` as an independent detail page.
- 待办 cards now include `详情报告`.
- 商品、竞品、上新、流量、报表 now include `查看预警` before task creation and `任务报告` after the task enters 待办.
- Existing report content includes warning summary, evidence, AI assessment, suggested actions, operation checklist, needed data, human decision points, next step, and Agent boundary.
- Frontend assets now use `?v=1.6.0`; API and health versions are aligned.

### Product Boundary
- This is still template-based report generation from current Mock ERP / CRM data.
- Agent is not yet connected; the report service is the reserved insertion point.
- Agent should enrich reports and checklist suggestions, not directly complete tasks or mutate ERP / CRM / shop data.

## v1.5.3 - 2026-06-16

### Product Decision
- V1.5.3 changes completed-task behavior from `completed -> can be added again` to `completed -> archived from source modules`.
- Product truth: source modules are current-cycle queues. Once a task is completed, it frees the source module position and belongs only in 日志 until a new signal / new cycle enters.

### Changed
- Added source-candidate lifecycle state in `module_task_service.py`: `pending_candidate`, `active_task`, and `completed_archived`.
- Product, competitor, listing, traffic, and report APIs now hide completed candidates from their source module lists.
- Completing a task now marks the source candidate as `completed_archived` and writes a log entry that the source module slot has been released.
- Direct attempts to re-create an already completed candidate are intercepted and logged instead of creating a duplicate task.
- `web_demo/core/api-client.js` now refreshes source module data after task/log state changes, so completed work disappears from related modules after 待办 completion.
- Frontend assets now use `?v=1.5.3`; API and health versions are aligned.

### Product Boundary
- This is still in-memory server-side mock persistence.
- Completion archive is based on the current dedupe key; a future new signal should use a new cycle id / source event to re-enter the source module queue.
- Completed tasks remain visible through 日志, not through 待办 or source modules.

## Earlier History

- v1.5.2: Existing-task buttons jump to the matching task card inside 待办.
- v1.5.1: Backend owns task identity and active-task status.
- v1.5.0: Backend module-file split.
- v1.4.1: Closed the module API chain and moved task/log authority to backend mock services.
- v1.4.0: Backend aligned with modular frontend and removed active `/api/business/*` routes.
- v1.3.0: Frontend changed from hotfix-script stacking into a modular route-registry structure.
- v1.2.0: Added unified front-end route lifecycle coordinator.
- v1.1.2: Fixed fast module-switch crash introduced by observer-based task bridge binding.
