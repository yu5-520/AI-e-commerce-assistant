# Current Version

```text
14.5.0
```

## V14.5 Meaning

V14.5 adds Permission Stamp Propagation.

Mainline:

```text
report uploader
  -> permission stamp
  -> imported rows
  -> operating objects
  -> product projection
  -> system product snapshot
  -> product signal package
  -> Agent judgment
  -> TaskIntent
  -> PermissionEnvelope
  -> task lifecycle
```

Core rules:

- Uploading a report grants the uploader default operating ownership for rows in that report.
- ERP/CRM explicit ownership overrides the uploader stamp.
- Projection gates check the permission stamp before old store-scope fallback.
- Historical unstamped rows can pass projection through operating object ownership checks.
- System product snapshots carry permission fields forward.
