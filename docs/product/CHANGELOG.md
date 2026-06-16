# Product Changelog

## v2.3.0 - 2026-06-16

### Product Decision
- V2.3.0 removes the redundant owner `经营驾驶舱`.
- Product truth: 老板第一层应该先看经营盘面，不是先看风险结论。
- `风险中心` is repositioned into `店群总览`: platform / store / product / order / sales / profit / comment / refund / inventory / task summary first, risk and exceptions later drill down from these data points.

### Changed
- Owner navigation is now: 总览、店群总览、任务指挥、利润预算、组织效率、复核审计、账号.
- 店群总览 shows platform summary and store-level business data.
- 商品、竞品、上新、流量 remain first-line evidence and execution modules for 总管 / 运营, not owner daily tabs.
- Frontend assets now use `?v=2.3.0`; API and health versions are aligned.

### Product Boundary
- Store overview still uses mock operating data.
- The next step is to connect ERP / CRM / platform API data and let exceptions grow out of real metrics.

## v2.2.0 - 2026-06-16

### Product Decision
- V2.2.0 separates owner decision navigation from first-line operation navigation.
- Product truth: 老板账号不需要日常进入商品、竞品、上新、流量这些一线功能栏；这些模块是数据来源和执行工作台，不是老板的统筹入口。
- 老板账号应该看经营驾驶舱、风险中心、任务指挥、利润预算、组织效率和复核审计。

### Changed
- Added owner-facing modules: 经营驾驶舱、风险中心、任务指挥、利润预算、组织效率、复核审计.
- Owner role visible modules now use executive navigation instead of product / competitor / listing / traffic operation modules.
- 账号 page was slimmed to current identity, scope, permission summary, and role-console entry.
- Added role permission console for mock role changes, store-scope changes, and permission template changes.
- Frontend assets now use `?v=2.2.0`; API and health versions are aligned.

### Product Boundary
- The role console is still mock memory state, not production account management.
- Real enterprise version still needs persistent audit logs, tenant isolation, and SSO.
- Boss modules aggregate evidence from /api/modules/* but do not replace first-line workbenches.

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

## v2.0.0 - 2026-06-16

### Product Decision
- V2.0.0 moves the product from a single-user operating dashboard into a light enterprise collaboration skeleton.
- The active trunk is now `/api/modules/*` for business modules plus `/api/accounts` for account, role, permission, and store-scope context.

### Changed
- Added `账号` page for role permissions, account list, store scope, and task-flow explanation.
- Added five v2 roles: 老板账号、店群总管账号、运营账号、数据 / 财务账号、只读观察账号.
- Added task assignment, submit, and review actions to 待办.
- Product docs were cleaned so README、MVP 范围、模块边界 and smoke tests point to the current v2 trunk.

## Earlier History

- v1.6.1: Candidate report pages include `加入任务清单`.
- v1.6.0: Added independent detail report pages.
- v1.5.3: Completed tasks archive their source candidates.
- v1.5.2: Existing-task buttons jump to the matching task card inside 待办.
- v1.5.1: Backend owns task identity and active-task status.
- v1.5.0: Backend module-file split.
- v1.4.1: Closed the module API chain and moved task/log authority to backend mock services.
- v1.4.0: Backend aligned with modular frontend and removed active `/api/business/*` routes.
- v1.3.0: Frontend changed from hotfix-script stacking into a modular route-registry structure.
- v1.2.0: Added unified front-end route lifecycle coordinator.
