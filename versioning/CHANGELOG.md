# Changelog

## v0.7.0 - 2026-06-08

### Added
- Added `frontend/` static UI prototype.
- Added `frontend/index.html` with cloud-console style product workspace.
- Added `frontend/styles.css` with white/dark theme variables and responsive card layout.
- Added `frontend/app.js` for theme switching, mode selection, and mock result rendering.
- Added `frontend/README.md` to document UI status and boundaries.

### Preserved
- Existing GitHub Issue -> Actions -> DeepSeek -> Issue comment workflow remains unchanged.
- Existing `scripts/pdd_operation_analyzer.py` remains unchanged in this update.
- Existing backend, RAG, vector, feedback, and knowledge-base structures remain unchanged.

### Risk
- Frontend is a static prototype only; it is not yet connected to backend API, GitHub Issue workflow, RAG, or model generation.

## v0.6.1 - 2026-06-08

### Changed
- Updated `scripts/pdd_operation_analyzer.py` so the first Issue input directly requests a full executable result package from the LLM.
- Updated all Issue templates to explain that more detailed input produces clearer output, while light input still generates a first version.
- Reframed follow-up comments such as “下一步” as refinement/continuation, not as a required second step for first output.

### Preserved
- Existing GitHub Issue -> Actions -> DeepSeek -> Issue comment workflow remains unchanged.
- Existing LLM provider configuration remains unchanged.
- Existing runtime module, RAG, vector, feedback, and knowledge-base structures remain unchanged.

### Risk
- The first output may be longer because it now directly generates the full execution package instead of waiting for a follow-up command.

## v0.6.0 - 2026-06-08

### Added
- Added `modules/rag/` for RAG design.
- Added query schema, retrieval pipeline, context pack rules, prompt assembly rules, and fallback rules.
- Added `runtime/rag_chain.json` to connect runtime modules, knowledge retrieval, vector retrieval, context pack, and LLM prompt assembly.

### Preserved
- Existing GitHub Issue -> Actions -> DeepSeek -> Issue comment workflow remains unchanged.
- Existing `scripts/pdd_operation_analyzer.py` remains unchanged in this update.
- Existing `runtime/module_chain.json` remains the active generation chain.
- Existing vector, feedback, and knowledge-base modules remain structural definitions.

### Risk
- RAG chain is a structural definition only; it is not yet connected to runtime generation.

## v0.5.0 - 2026-06-08

### Added
- Added `modules/vector_store/` for vector store design.
- Added embedding schema, metadata schema, chunking rules, retrieval rules, rerank rules, and storage options.
- Added `runtime/vector_retrieval_chain.json` for future RAG retrieval.

### Preserved
- Existing GitHub Issue -> Actions -> DeepSeek -> Issue comment workflow remains unchanged.
- Existing `scripts/pdd_operation_analyzer.py` remains unchanged in this update.
- Existing `runtime/module_chain.json` remains the active generation chain.
- Existing feedback and knowledge-base modules remain structural definitions.

### Risk
- Vector store and retrieval chain are structural definitions only; they are not yet connected to runtime generation.

## v0.4.0 - 2026-06-08

### Added
- Added `modules/knowledge_base/` for title, image, SKU, price, operation case, and feedback-level knowledge.
- Added `modules/feedback/` for feedback schema, feedback flow, usage metrics, and effectiveness metrics.
- Added `runtime/feedback_chain.json` and `runtime/knowledge_retrieval_chain.json`.
- Added frontend feedback UI schema and backend feedback/knowledge storage contracts.
- Added sample data folders under `data/feedback_samples/` and `data/knowledge_samples/`.

### Preserved
- Existing GitHub Issue -> Actions -> DeepSeek -> Issue comment workflow remains unchanged.
- Existing `scripts/pdd_operation_analyzer.py` remains unchanged in this update.
- Existing `runtime/module_chain.json` remains the active generation chain.

### Risk
- Feedback and knowledge modules are structural definitions only; they are not yet connected to runtime generation.

## v0.3.0 - 2026-06-08

### Added
- Added version governance directory: `versioning/`.
- Added AI change rules, module ownership, change request template, and update logs.
- Added runtime version manifest for quick AI/context lookup.

### Preserved
- Existing GitHub Issue -> Actions -> DeepSeek -> Issue comment workflow remains unchanged.
- Existing `runtime/module_chain.json` remains the active runtime chain.
- Existing `docs/` files remain as compatibility/history files.

### Risk
- Version governance is documentation-enforced first; future automation can validate changelog and scope rules.

## v0.2.0 - 2026-06-08

### Added
- Added `runtime/module_chain.json`.
- Added modular folders for platform, operation modes, interface, frontend, and backend.

### Changed
- `scripts/pdd_operation_analyzer.py` now reads runtime module chain instead of hardcoded docs paths.

## v0.1.0 - 2026-06-08

### Added
- GitHub Issue templates.
- GitHub Actions workflow.
- DeepSeek/OpenAI-compatible LLM interface.
- Issue comment output loop.
