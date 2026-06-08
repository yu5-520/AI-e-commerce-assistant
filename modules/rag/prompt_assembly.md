# RAG Prompt Assembly

Prompt assembly defines how user input, runtime modules, retrieved knowledge, and output template are sent to the LLM.

## Assembly Order
1. System role: ecommerce operation assistant for the selected platform and mode.
2. User input summary.
3. Active platform and operation mode modules.
4. Output template.
5. Retrieved knowledge context pack.
6. Safety and grounding rules.

## Grounding Rules
- User input has highest priority.
- Retrieved knowledge is reference context, not absolute truth.
- Do not invent missing store data.
- If information is missing, generate a first usable version and list at most 3 clear follow-up questions.
- Keep output aligned with the selected mode.

## Output Rule
The final answer should follow the active output template and should not expose internal retrieval details unless debug mode is enabled.
