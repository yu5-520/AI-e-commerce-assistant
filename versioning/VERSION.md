Current Version: 16.4

V16.4 Real Report Fact-Layer Repair

Core chain:

`Report schema Agent -> system cleaning -> product/store/traffic fact namespace isolation -> report metricDate -> product master dedupe -> validated fullProductBundle -> real product judgment Agent -> product_judgment_package 70% gate -> real task mapping Agent with RAG permissions/SOP -> current-run task-pool acceptance`

Key fix:

- Product master rows now come only from product metric/detail rows.
- Traffic-source rows become child `trafficSourceFacts`; they do not create product master rows.
- Product ROI, store ROI and traffic-source ROI are isolated namespaces.
- Product detail ROI can only be overwritten by product-scope metrics, not traffic-source ROI=0.
- Business metric date comes from `统计日期` / `更新时间` / filename or dataVersion, not the current upload date.
- Product dedupe key is `platform + store + productId + skuId`.
- fullProductBundle carries fact-layer validation before real Agent judgment.

Boundary:

V16.4 does not fake missing facts. If ROI/date/product facts are missing, the bundle exposes the gap to the Agent instead of hiding it with current date, traffic ROI, or duplicated product rows.
