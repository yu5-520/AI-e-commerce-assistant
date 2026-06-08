# RAG Fallback Rules

Fallback rules define what to do when retrieval is unavailable or low quality.

## Fallback Cases

### No vector store available
Use active runtime modules and output template only.

### No relevant retrieved knowledge
Do not force irrelevant examples into the prompt. Generate from user input and active modules.

### Only low-level knowledge available
L2 liked knowledge may be used as weak reference, but must not be treated as proven operation effect.

### Retrieved knowledge conflicts with user input
User input wins. Retrieved knowledge should be ignored or treated as non-applicable.

### Retrieved knowledge is cross-platform or cross-mode
Penalize or discard it unless explicitly requested.

## Output Rule
If RAG context is missing, the product should still generate a first usable result. RAG improves quality but should not block generation.
