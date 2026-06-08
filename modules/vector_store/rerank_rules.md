# Vector Rerank Rules

After semantic retrieval, rerank results using business value.

## Priority Signals
1. Feedback level: L4 > L3 > L2 > L1.
2. Operation effect score > user experience score.
3. Same platform > adjacent platform.
4. Same mode > cross-mode.
5. Same category/product > adjacent category/product.
6. Similar price band > unrelated price band.
7. Recent effective pattern > old unverified pattern.

## Penalty Signals
- no feedback
- private or incomplete source
- high refund risk
- low profit effect
- cross-platform mismatch
- mode mismatch, such as strong paid-growth advice for natural-flow query

## Output Rule
The reranked context pack should explain why each retrieved pattern is relevant.
