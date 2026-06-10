# Runtime Results

This folder stores generated operation results from the local backend API.

Each result record is created by:

```text
POST /api/generate
```

Records include:
- result_id
- created_at
- mode
- product
- user input
- generated markdown
- fallback or LLM status
- local backflow status

Current status: local MVP storage only. Do not store private production user data here without authentication, permission, and data isolation.
