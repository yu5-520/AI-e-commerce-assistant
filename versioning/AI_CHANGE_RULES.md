# AI Change Rules

These rules guide every future AI-assisted repository change.

## Core Rules

1. Identify the user-requested scope before editing.
2. Only edit requested files/modules and the minimum necessary linked files.
3. Do not refactor unrelated files for style or preference.
4. Do not delete, rename, or move files unless the user explicitly asks.
5. Do not rewrite working workflow/script/interface files unless required.
6. Preserve the current runnable chain before improving structure.
7. Prefer adding small module files over putting business logic into workflow.
8. If frontend/backend/runtime/schema changes, record the affected layer.
9. Every meaningful change must update changelog or add a log file.
10. In final response, state what changed and what was intentionally not changed.

## Forbidden By Default

- Broad rewrites.
- Silent migrations.
- Deleting compatibility docs.
- Changing secrets handling casually.
- Modifying workflow when only template text was requested.
