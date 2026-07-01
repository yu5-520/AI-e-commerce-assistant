# Current Version

```text
16.24
```

## V16.24

Task repository context cleanup.

`src/repositories/task_repository.py` and `src/repositories/scoped_repository.py` no longer import the deleted `src.core.context` module. The task lifecycle mainline remains active and uses a V16 lightweight `UserContext` value object at the repository boundary.

## Verify

```bash
python scripts/check_v16_manifest.py
```
