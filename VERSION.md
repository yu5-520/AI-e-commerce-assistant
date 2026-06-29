# Current Version

```text
14.5.1
```

## V14.5.1 Meaning

V14.5.1 separates permission stamps from business payloads and compacts import responses.

Mainline:

```text
report import
  -> backend storage
  -> compact counters and refs
  -> station details by paged diagnostics only
```

Core rules:

- Permission stamp is a station scan reference, not business payload content.
- Product snapshots carry `permissionStampId` and `permissionGateStatus`, not the full permission object.
- Agent packages do not carry owner, assignee, or visible-user details.
- Upload/confirm endpoints return counters and refs only.
- Rows, station outputs, product packages, signal packages, and task packages stay in backend storage.
