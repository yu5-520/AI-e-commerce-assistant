(function () {
  function store() {
    return window.OPERATION_TASK_STORE;
  }

  function notify(text) {
    let notice = document.querySelector(".v110-task-bridge-notice");
    if (!notice) {
      notice = document.createElement("section");
      notice.className = "v110-task-bridge-notice";
      const host = document.querySelector(".product-toolbar, .competitor-toolbar, .listing-toolbar, .traffic-toolbar, .report-hero, .product-detail-hero, .competitor-detail-hero, .listing-detail-hero, .traffic-detail-hero, .report-detail-hero");
      host?.after(notice);
    }
    if (notice) notice.innerHTML = `<strong>任务池同步</strong><span>${text}</span>`;
  }

  function addButton(container, label, attr, value) {
    if (!container || container.querySelector(`[${attr}="${value}"]`)) return;
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.setAttribute(attr, value);
    container.appendChild(button);
  }

  function createProductTask(productId) {
    if (typeof productManagerPayload === "undefined") return;
    const product = productManagerPayload.products.find((item) => item.id === productId);
    if (!product || !store()) return;
    const highRisk = product.afterSalesLevel !== "good" || product.inventoryLevel === "danger";
    const task = store().createTask({
      sourceModule: "商品经营列表",
      source: "商品触发",
      sourceRoute: "business-products",
      sourceEvent: `product:${product.id}:review`,
      productId: product.id,
      imageLabel: product.imageLabel,
      productShort: product.shortName,
      productTitle: product.title,
      title: product.title,
      platform: product.platform,
      store: product.store,
      link: product.link,
      priority: highRisk ? "高" : "中",
      priorityLevel: highRisk ? "danger" : "warning",
      deadline: highRisk ? "今天内" : "明天前",
      timeBucket: highRisk ? "今天内" : "明天前",
      taskType: product.afterSalesLevel !== "good" ? "售后复查" : product.inventoryLevel === "danger" ? "库存承接" : "商品优化",
      taskSignal: product.afterSalesLevel !== "good" ? "先查售后" : product.inventoryLevel === "danger" ? "确认补货" : "优化测试",
      task: product.afterSalesLevel !== "good" ? "复查售后原因，暂不扩大推广" : product.inventoryLevel === "danger" ? "确认补货周期，再决定活动节奏" : "加入商品优化观察",
      reason: product.suggestion,
      judgmentTags: [product.inventoryStatus, product.afterSales, `毛利 ${product.grossMargin}`],
    });
    notify(`${task.productShort || product.shortName}已进入统一任务池。`);
  }

  function createCompetitorTask(competitorId) {
    if (typeof competitorManagerPayload === "undefined") return;
    const item = competitorManagerPayload.competitors.find((competitor) => competitor.id === competitorId);
    if (!item || !store()) return;
    const task = store().createTask({
      sourceModule: "竞品观察列表",
      source: "竞品触发",
      sourceRoute: "business-competitors",
      sourceEvent: `competitor:${item.id}:opportunity`,
      productId: item.id,
      imageLabel: item.imageLabel,
      productShort: item.targetProduct,
      productTitle: item.title,
      title: item.title,
      platform: item.platform,
      store: item.store,
      link: item.link,
      priority: item.status === "风险" ? "高" : "中",
      priorityLevel: item.status === "风险" ? "danger" : "warning",
      deadline: item.status === "风险" ? "今天内" : "明天前",
      timeBucket: item.status === "风险" ? "今天内" : "明天前",
      taskType: item.status === "风险" ? "竞品风险" : "竞品机会",
      taskSignal: item.opportunity,
      task: item.status === "风险" ? "复查竞品风险，不直接跟价" : "生成对标测试任务",
      reason: item.suggestion,
      judgmentTags: [item.pricePosition, item.badReview, item.status],
    });
    notify(`${task.productShort || item.targetProduct}竞品信号已进入统一任务池。`);
  }

  function createListingTask(listingId) {
    if (typeof listingManagerPayload === "undefined") return;
    const item = listingManagerPayload.experiments.find((experiment) => experiment.id === listingId);
    if (!item || !store()) return;
    const task = store().createTask({
      sourceModule: "上新测试台",
      source: "上新触发",
      sourceRoute: "business-listing",
      sourceEvent: `listing:${item.id}:test`,
      productId: item.id,
      imageLabel: item.imageLabel,
      productShort: item.sourceName,
      productTitle: item.title,
      title: item.title,
      platform: item.platform,
      store: item.store,
      productRoute: item.linkRoute || "business-products",
      priority: item.statusLevel === "danger" ? "高" : "中",
      priorityLevel: item.statusLevel === "danger" ? "danger" : "warning",
      deadline: item.due,
      timeBucket: item.due.includes("今天") ? "今天内" : item.due.includes("明天") ? "明天前" : "本周内",
      taskType: item.testType,
      taskSignal: "确认测试版本",
      task: `${item.testType}：${item.testPlan}`,
      reason: `${item.risk} ${item.suggestion}`,
      judgmentTags: [item.sourceLabel, item.testType, item.targetMetric],
      testVersion: item.testPlan,
    });
    notify(`${item.testType}已进入统一任务池。`);
  }

  function createTrafficTask(trafficId) {
    if (typeof trafficManagerPayload === "undefined") return;
    const item = trafficManagerPayload.tests.find((test) => test.id === trafficId);
    if (!item || !store()) return;
    const task = store().createTask({
      sourceModule: "流量测试台",
      source: "流量触发",
      sourceRoute: "business-traffic",
      sourceEvent: `traffic:${item.id}:backflow`,
      productId: item.productId,
      imageLabel: item.imageLabel,
      productShort: item.title.slice(0, 6),
      productTitle: item.title,
      title: item.title,
      platform: item.platform,
      store: item.store,
      link: item.link,
      priority: item.statusLevel === "danger" ? "高" : item.statusLevel === "warning" ? "中" : "低",
      priorityLevel: item.statusLevel,
      deadline: item.statusLevel === "danger" ? "今天 18:00 前" : "明天前",
      timeBucket: item.statusLevel === "danger" ? "今天 18:00 前" : "明天前",
      taskType: item.backflow,
      taskSignal: item.status,
      task: item.nextStep,
      reason: `${item.channel} ${item.source}：ROI ${item.roi}，退款率 ${item.refundRate}，库存 ${item.inventory}。`,
      judgmentTags: [`ROI ${item.roi}`, `退款率 ${item.refundRate}`, item.status],
    });
    notify(`${item.channel}流量判断已进入统一任务池。`);
  }

  function createReportTask(reportId) {
    if (typeof reportManagerPayload === "undefined") return;
    const card = reportManagerPayload.groups.flatMap((group) => group.reports).find((report) => report.id === reportId);
    if (!card || !store()) return;
    const task = store().createTask({
      sourceModule: "ERP / CRM 报表管理",
      source: "报表触发",
      sourceRoute: "data-check",
      sourceEvent: `report:${card.id}:import`,
      productId: `R-${card.id}`,
      imageLabel: "表",
      productShort: card.name,
      productTitle: `${card.name}导入后复盘`,
      title: `${card.name}导入后复盘`,
      platform: card.source,
      store: "家居生活店铺组",
      productRoute: "data-check",
      priority: card.id === "refunds" || card.id === "orders" ? "高" : "中",
      priorityLevel: card.id === "refunds" || card.id === "orders" ? "danger" : "warning",
      deadline: card.id === "refunds" || card.id === "orders" ? "今天内" : "本周内",
      timeBucket: card.id === "refunds" || card.id === "orders" ? "今天内" : "本周内",
      taskType: "报表复盘",
      taskSignal: "导入后生成任务",
      task: `复盘${card.name}，生成下一轮经营任务`,
      reason: `${card.desc}。导入后需要同步首页、待办和日志。`,
      judgmentTags: [card.source, card.status, card.count],
    });
    notify(`${card.name}导入复盘任务已进入统一任务池。`);
  }

  function bindButtons() {
    document.querySelectorAll("[data-product-report]").forEach((button) => addButton(button.parentElement, "加入待办", "data-v110-product-task", button.dataset.productReport));
    document.querySelectorAll("[data-v110-product-task]").forEach((button) => {
      if (button.dataset.taskBridgeBound) return;
      button.dataset.taskBridgeBound = "1";
      button.addEventListener("click", () => createProductTask(button.dataset.v110ProductTask));
    });

    document.querySelectorAll("[data-competitor-watch]").forEach((button) => {
      if (button.dataset.taskBridgeBound) return;
      button.dataset.taskBridgeBound = "1";
      button.addEventListener("click", () => createCompetitorTask(button.dataset.competitorWatch));
    });

    document.querySelectorAll("[data-listing-task]").forEach((button) => {
      if (button.dataset.taskBridgeBound) return;
      button.dataset.taskBridgeBound = "1";
      button.addEventListener("click", () => createListingTask(button.dataset.listingTask));
    });

    document.querySelectorAll("[data-traffic-task]").forEach((button) => {
      if (button.dataset.taskBridgeBound) return;
      button.dataset.taskBridgeBound = "1";
      button.addEventListener("click", () => createTrafficTask(button.dataset.trafficTask));
    });

    document.querySelectorAll("[data-report-confirm-import]").forEach((button) => {
      if (button.dataset.taskBridgeBound) return;
      button.dataset.taskBridgeBound = "1";
      button.addEventListener("click", () => {
        if (typeof selectedImportFileName !== "undefined" && selectedImportFileName) createReportTask(button.dataset.reportConfirmImport);
      });
    });
  }

  const observer = new MutationObserver(() => bindButtons());
  observer.observe(document.body, { childList: true, subtree: true });
  window.addEventListener("hashchange", () => setTimeout(bindButtons, 0));
  window.addEventListener("load", () => setTimeout(bindButtons, 0));
  setTimeout(bindButtons, 0);
})();
