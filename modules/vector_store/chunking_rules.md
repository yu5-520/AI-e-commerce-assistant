# Vector Chunking Rules

Vector store should index knowledge chunks, not whole documents.

## Chunk Types
- one title pattern = one chunk
- one image structure = one chunk
- one SKU structure = one chunk
- one price strategy = one chunk
- one operation case can be split into multiple chunks
- one feedback summary = one chunk

## Chunk Content
Each chunk should include:
- reusable pattern
- applicable scenario
- feedback level
- effect summary
- source reference

## Chunk Size Rule
Keep chunks short and focused. Avoid embedding long raw reports.

## Privacy Rule
Remove user private data before chunking. Store reusable operation structure, not private shop details.
