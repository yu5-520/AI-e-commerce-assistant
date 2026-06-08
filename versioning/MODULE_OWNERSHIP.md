# Module Ownership

## `.github/`
GitHub input and automation layer. Do not change workflow unless trigger, permissions, or runtime env must change.

## `runtime/`
Runtime chain registry and manifest. It decides which modules are read for each mode.

## `scripts/`
Execution layer. Scripts should connect modules, parse deterministic fields, call interfaces, and write results. Avoid business rules here.

## `modules/platforms/`
Platform rules and style, such as Pinduoduo title/image/price style.

## `modules/operation_modes/`
Business mode modules: natural flow, paid growth, hot product.

## `modules/interfaces/`
External interfaces: LLM, GitHub, future platform APIs.

## `modules/frontend/`
Frontend card schema, mobile layout, copy buttons, and display sections.

## `modules/backend/`
Future backend API contracts, data flow, and storage plan.

## `docs/`
Product documents and compatibility/history notes. Not the primary runtime source.

## `versioning/`
Version governance, changelog, AI edit rules, change request template, and update logs.
