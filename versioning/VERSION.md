Current Version: 12.12.0

V12.12.0 RAG baseline + LLM Agent SOP + product action cards

This release upgrades V12.11 from template-like Agent copy into a RAG/LLM-enhanced task generation chain.

Updated chain:

- System still extracts deterministic metric changes into `systemChangePack`.
- V12.12 seeds a basic RAG baseline database with metric rules, action playbooks, platform/category guidance, SOP guardrails and automatic recap rules.
- Agent generation now builds a `productContextPack`, retrieves RAG cards, builds an LLM prompt payload, calls the unified LLM provider gateway, then validates the SOP.
- When LLM is not enabled or output fails validation, the system falls back to deterministic RAG synthesis instead of raw if/else templates.
- Task detail now shows involved products and product-level action cards.
- Batch tasks keep product IDs, product titles, product links, product archive route state and product-specific actions.
- Product archive supports jumping from task detail into the specific product detail page.

Hard rules:

- Operators must not be asked to split traffic sources, split ad plans, manually recap ROI, or manually decide data causes.
- If hourly ad data is missing, the system must not generate time-slot actions like moving main delivery from 8am to 1pm.
- SOP must include product, action, submission evidence and system automatic recap line.

Current contract:

System extracts data changes. RAG provides baseline operation knowledge. LLM enhances judgment and SOP wording under guardrails. Operators execute and submit evidence. The system performs automatic recap after later report or interface data refreshes and writes the result to daily reports, weekly reports and the recap library.
