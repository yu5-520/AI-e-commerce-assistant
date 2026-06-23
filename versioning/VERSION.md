# Version

Current Version: v9.4.0

## Version History

- v9.4.0: Added tier isolation consistency. V9.4 defines Starter, Professional, and Enterprise boundaries for feature flags, RAG namespaces, data scope, audit depth, deployment mode, and weight algorithms. It adds `docs/V9_TIER_ISOLATION_CONSISTENCY.md`, `src/services/v94_tier_isolation_contract_service.py`, `/api/architecture/v9/tier-isolation`, and `scripts/check_tier_isolation_consistency.py`.
- v9.3.0: Added frontend module consistency. V9.3 keeps frontend business modules stable and routes backend capabilities into tiered enhancement fields instead of adding new primary modules. It adds `docs/V9_FRONTEND_MODULE_CONSISTENCY.md`, `src/services/v93_frontend_module_contract_service.py`, `/api/architecture/v9/frontend-modules`, and `scripts/check_frontend_module_consistency.py`.
- v9.2.0: Added backend main-flow consistency. V9.2 defines the ImportJob -> DataVersion -> RawRows -> ModuleProjection -> AlertEvent -> WeightSignal -> DecisionTask -> AgentReport -> ApprovalFlow -> ExecutionFeedback -> ReviewLog -> RagMemoryCandidate contract. It adds `docs/V9_BACKEND_FLOW_CONSISTENCY.md`, `src/services/v92_backend_flow_service.py`, `/api/architecture/v9/backend-flow`, and `scripts/check_backend_flow_consistency.py`.
- v9.1.0: Added repository structure consistency governance. It adds `docs/V9_REPOSITORY_CONSISTENCY.md` and `scripts/check_repository_consistency.py`.
- v9.0.0: Established the SaaS enterprise consistency baseline. Stable product entries remain `/api/modules` and `/api/accounts`.
