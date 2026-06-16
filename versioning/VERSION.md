# Version

Current Version: v2.3.5

## Version History

- v2.3.5: Rebuilt owner `复核审计` into `复盘审计`, receiving daily / weekly / monthly retrospectives, auditing missed targets and execution failures, and forming next-cycle task drafts.
- v2.3.4: Rebuilt owner `组织效率` into an organization governance console with position relationship network, account role control, store authorization, and permission template control.
- v2.3.3: Rebuilt owner `利润预算` into `供投财务`, combining supply, traffic, and finance views.
- v2.3.2: Owner-side task command was repositioned into `人员总览`, showing employee realtime state, task load, completed count, return count, timeout count, average handling time, and workload.
- v2.3.1: Fixed `店群总览` layout and upgraded it into a realtime operations board with sync status, trend chips, platform live cards, and a horizontal store table.
- v2.3.0: Removed redundant owner `经营驾驶舱`; changed `风险中心` into `店群总览` around platform / store / product / order / sales / profit / comments / inventory summaries.
- v2.2.0: Refactored owner navigation from first-line operation modules into executive modules and added the role permission console.
- v2.1.0: Added global mock account switching, role-based task visibility, permission-based todo actions, and role-specific insight depth.
- v2.0.0: Added `/api/accounts`, account roles, permissions, and the dispatch / submit / review collaboration flow.
- v1.0.0-v1.6.1: Product trunk cleanup, modular backend/frontend, task lifecycle, detail reports, and report-to-task conversion.
- v0.1.0-v0.9.2: Early workflow, RAG, frontend, generation, and Agent governance iterations.

## Version Rules

- Patch: copy, prompt, template, or wording changes.
- Minor: new module, new mode, new interface, or new runtime config.
- Major: breaking workflow, API contract, schema, or folder migration changes.

## Logging Rule

- Any architecture-level cleanup, route removal, folder migration, or deployment-entry change must update both `versioning/CHANGELOG.md` and this file.
- Product-specific decisions should also update the matching log under `docs/product/`.
