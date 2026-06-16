# Version

Current Version: v1.1.1

## Version History

- v0.1.0: GitHub Issue input, Actions workflow, and result comment loop became runnable.
- v0.2.0: Runtime module chain was introduced through `runtime/module_chain.json`.
- v0.3.0: Version governance layer was added to control AI edits, update logs, and module boundaries.
- v0.4.0: Feedback flow and knowledge base modules were added for template backflow and reusable operation patterns.
- v0.5.0: Vector store module and vector retrieval chain were added for future RAG retrieval.
- v0.6.0: RAG module and RAG chain were added to connect knowledge base, vector retrieval, context pack, and LLM prompt assembly.
- v0.6.1: Issue workflow was adjusted so first input directly generates a full result package; follow-up info only improves precision.
- v0.7.0: Static frontend UI prototype was added with light/dark theme switch and cloud-console style layout.
- v0.8.0: Local backend API was added so frontend input can generate results, return AI output to UI, and write result/feedback backflow records.
- v0.8.1: Productized rendering cleanup was added so frontend displays copyable titles, image directions, SKU plans, price advice, and next actions instead of engineering output.
- v0.8.2: Generation configuration controls were added for title counts, image plan counts, image generation credit estimates, and free/VIP output limits.
- v0.8.3: Responsive page experience was optimized for desktop, tablet, and mobile layouts.
- v0.8.4: Workflow breakpoints were reduced by adding runtime smoke checks, fixing DeepSeek provider configuration, and aligning Issue workflow templates with generation configuration limits.
- v0.8.5: UI microcopy was reduced so the page behaves more like a product tool and less like an engineering explanation page.
- v0.8.6: Navigation was simplified with a non-fixed top bar, unified product naming, and collapsible/sidebar-drawer behavior.
- v0.8.7: Anonymous page memory was added so each browser can restore its own recent product plans after refresh without sharing one global screen.
- v0.8.8: Title timeliness calibration was added with current time context, optional material references, and stale-year filtering.
- v0.8.9: Material observation Agent light version was added to extract current wording structure from user-provided market materials before generation.
- v0.9.0: Pre-generation material sampling UI was added so users can observe wording signals before generating a product plan.
- v0.9.1: Material observation was moved back into an implicit backend pipeline so users only see generation progress and final copyable outputs.
- v0.9.2: Agent module governance was added with a stable material observer contract, source policy, confidence, risk flags, and runtime registry.
- v1.0.0: Main branch was recut into one current product trunk, removing old frontend templates, legacy compatibility APIs, stale demo helpers, and aligning README, smoke tests, and version logs with `/api/business/*`.
- v1.0.1-v1.0.6: Product trunk cleanup, script repair, legacy route removal, active API alignment, and server startup fixes.
- v1.0.7-v1.0.14: Dashboard task board, operating unit, ERP/CRM report center, import/export, and frontend cache/version governance were added.
- v1.0.15-v1.0.20: 商品、竞品、上新 and 流量 pages were productized into compact operating surfaces.
- v1.0.21: Actions page was repositioned as `待办任务`, showing tasks from 商品、竞品、上新、流量、报表 and AI 自动判定.
- v1.0.22: Report page was repositioned as `日志`, recording task completion, AI judgment, data import/export, and user actions.
- v1.0.23: Dashboard task board used a unified cross-module task pool for homepage summaries.
- v1.0.24: Dashboard task board was simplified into a command-board scheduling view with short judgment tags.
- v1.1.0: Added a unified front-end task store and dynamic module-driven task flow. 商品、竞品、上新、流量 and 报表 can now create shared tasks; dashboard and 待办 read the same task pool; task actions create operation logs; refresh preserves the demo task state through localStorage.
- v1.1.1: Added task identity and dedupe keys. Manual module actions now check `entityType + entityId + riskDomain + actionType`; same-product same-problem tasks are merged or routed to existing 待办 instead of duplicated, while different problem domains can still create separate tasks.

## Version Rules

- Patch: copy, prompt, template, or wording changes.
- Minor: new module, new mode, new interface, or new runtime config.
- Major: breaking workflow, API contract, schema, or folder migration changes.

## Logging Rule

- Any architecture-level cleanup, route removal, folder migration, or deployment-entry change must update both `versioning/CHANGELOG.md` and this file.
- Product-specific decisions should also update the matching log under `docs/product/`.
