# Current Version

```text
16.4
```

## V16.4 Meaning

V16.4 is the real-report fact-layer repair release.

It keeps the V16.2 real product judgment Agent, V16.2 real RAG task mapping Agent and V16.3 task-pool acceptance gate, then repairs the upstream data facts before Agent judgment:

```text
real report rows
  -> product/store/traffic fact namespace isolation
  -> metric_date from report rows
  -> product master dedupe by platform + store + productId + skuId
  -> fullProductBundle fact-layer validation
  -> real product judgment Agent
  -> real task mapping Agent
```

Core rules:

- 商品经营明细 creates product master rows and product-scope metric facts.
- 流量来源明细 creates child `trafficSourceFacts`; it never creates product master rows.
- 商品 ROI, 店铺 ROI and 流量来源 ROI are separate namespaces.
- Product detail ROI reads `product_metric_facts.roi` only; traffic ROI=0 cannot overwrite product ROI.
- `metricDate/reportDate/dataDate` priority is `统计日期 -> 更新时间 -> filename/dataVersion`; upload/current date is not a business metric date.
- Product master key is `platform + storeId/storeName + productId + skuId`.
- fullProductBundle now carries `factLayerValidation`, product metric fact count, traffic source fact count, metricDate and ROI source.
- Agent judgment must consume the validated fullProductBundle, not mixed raw rows.

一句话：V16.4 先把真实报表事实层打干净：ROI 不串层、日期不串今日、流量行不建商品、商品不重复建档，然后再让真实 Agent 判断。