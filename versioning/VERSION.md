# Version

Current Version: v1.0.6

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
- v1.0.1: Script chain was repaired so GitHub Actions runs current runtime/API smoke tests plus version governance checks. Legacy Material Observer Agent files and runtime registry were removed from the active product trunk.
- v1.0.2: Documentation trunk was cleaned so active docs describe only the current ERP operating-unit product path. Outdated future product-map, user-flow, and broad domain-model docs were removed, and governance now checks active docs for stale legacy snippets.
- v1.0.3: Legacy module-chain memory was removed from active trunk. Old runtime module-chain registry and obsolete modules were deleted, report generation was renamed from demo report to operating report, and governance now blocks removed module-chain roots.
- v1.0.4: Frontend UI was aligned with productized `/api/business/*` endpoints. Old standalone data-import stylesheet was removed, business hash routes were clarified, and governance now blocks the removed frontend component stylesheet.
- v1.0.5: Backend API contract was repaired so business actions merge persisted approval status, health returns the current version, system cleanup has a runtime-data alias, and API smoke tests verify approval status roundtrip.
- v1.0.6: Server runtime import failure was fixed by disabling the homepage response model and removing the invalid `FileResponse | Dict` response annotation.

## Version Rules

- Patch: copy, prompt, template, or wording changes.
- Minor: new module, new mode, new interface, or new runtime config.
- Major: breaking workflow, API contract, schema, or folder migration changes.

## Logging Rule

- Any architecture-level cleanup, route removal, folder migration, or deployment-entry change must update both `versioning/CHANGELOG.md` and this file.
- Product-specific decisions should also update the matching log under `docs/product/`.
