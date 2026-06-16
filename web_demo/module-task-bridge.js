(function () {
  let bindScheduled = false;

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
    const html = `<strong>任务池同步</strong><span>${text}</span>`;
    if (notice && notice.innerHTML !== html) notice.innerHTML = html;
  }

  function addButton(container, label, attr, value) {
    if (!container || container.querySelector(`[${attr}="${value}"]`)) return;
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.setAttribute(attr, value);
    container.appendChild(button);
  }

  function setButtonState(button, label, hasExisting) {
    if (!button) return;
    if (button.textContent !== label) button.textContent = label;
    if (button.classList.contains("ghost") !== hasExisting) button.classList.toggle("ghost", hasExisting);
    const title = hasExisting ? "已有同商品/同问题待办，点击跳转任务池" : "创建新的待办任务";
    if (button.title !== title) button.title = title;
  }

  function riskForProduct(product) {
    if (product.afterSalesLevel !== "good") return "售后";
    if (product.inventoryLevel === "danger") return "库存";
    return "商品";
  }

  function actionForRisk(riskDomain) {
    if (riskDomain === "库存") return "复查";
    if (riskDomain === "商品") return "观察";
    return "复查";
  }

  function productIdentity(product) {
    const riskDomain = riskForProduct(product);
    return { entityType: "商品", entityId: product.id, riskDomain, actionType: actionForRisk(riskDomain) };
  }

  function competitorIdentity(item) {
    return { entityType: "竞品", entityId: item.id, riskDomain: item.status === "风险" ? "风险" : "上新", actionType: item.status === "风险" ? "复查" : "测试" };
  }

  function listingIdentity(item) {
    return { entityType: item.mode === "competitor" ? "竞品机会" : "商品", entityId: item.id, riskDomain: "上新", actionType: item.testType.includes("复盘") ? "复盘" : "测试" };
  }

  function trafficIdentity(item) {
    const text = `${item.status} ${item.backflow} ${item.nextStep}`;
    const riskDomain = /售后|退款|材质|尺寸|安装|客服/.test(text) ? "售后" : /库存|补货|承接/.test(text) ? "库存" : "流量";
    const actionType = riskDomain === "流量" && item.statusLevel === "good" ? "观察" : "复查";
    return { entityType: "商品", entityId: item.productId, riskDomain, actionType };
  }

  function reportIdentity(card) {
    return { entityType: "报表", entityId: card.id, riskDomain: "报表", actionType: "导入" };
  }

  function existingTask(identity) {
    return store()?.findOpenTask?.(identity);
  }

  function routeToTodo(existing, name) {
    if (!existing) return false;
    notify(`${name}已有相关待办，已跳转任务池，不重复创建。`);
    location.hash = "business-actions";
    return true;
  }

  function createProductTask(productId) {
    if (typeof productManagerPayload === "undefined") return;
    const product = productManagerPayload.products.find((item) => item.id === productId);
    if (!product || !store()) return;
    const identity = productIdentity(product);
    if (routeToTodo(existingTask(identity), product.shortName)) return;
    const highRisk = product.afterSalesLevel !== "good" || product.inventoryLevel === "danger";
    const task = store().createTask({
      ...identity,
      sourceModule: "商品经营列表",
      source: "商品触发",
      sourceRoute: "business-products",
      sourceEvent: `product:${product.id}:${identity.riskDomain}:${identity.actionType}`,
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
    const identity = competitorIdentity(item);
    if (routeToTodo(existingTask(identity), item.targetProduct)) return;
    const task = store().createTask({
      ...identity,
      sourceModule: "竞品观察列表",
      source: "竞品触发",
      sourceRoute: "business-competitors",
      sourceEvent: `competitor:${item.id}:${identity.riskDomain}:${identity.actionType}`,
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
    const identity = listingIdentity(item);
    if (routeToTodo(existingTask(identity), item.testType)) return;
    const task = store().createTask({
      ...identity,
      sourceModule: "上新测试台",
      source: "上新触发",
      sourceRoute: "business-listing",
      sourceEvent: `listing:${item.id}:${identity.riskDomain}:${identity.actionType}`,
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
    const identity = trafficIdentity(item);
    if (routeToTodo(existingTask(identity), item.title.slice(0, 8))) return;
    const task = store().createTask({
      ...identity,
      sourceModule: "流量测试台",
      source: "流量触发",
      sourceRoute: "business-traffic",
      sourceEvent: `traffic:${item.id}:${identity.riskDomain}:${identity.actionType}`,
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
    const identity = reportIdentity(card);
    if (routeToTodo(existingTask(identity), card.name)) return;
    const task = store().createTask({
      ...identity,
      sourceModule: "ERP / CRM 报表管理",
      source: "报表触发",
      sourceRoute: "data-check",
      sourceEvent: `report:${card.id}:${identity.actionType}`,
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

  function updateButtonState(button, identity, activeLabel = "加入待办") {
    if (!button || !store()) return;
    const existed = existingTask(identity);
    setButtonState(button, existed ? "已在待办" : activeLabel, Boolean(existed));
  }

  function bindButtons() {
    if (typeof productManagerPayload !== "undefined") {
      document.querySelectorAll("[data-product-report]").forEach((button) => addButton(button.parentElement, "加入待办", "data-v111-product-task", button.dataset.productReport));
      document.querySelectorAll("[data-v111-product-task]").forEach((button) => {
        const product = productManagerPayload.products.find((item) => item.id === button.dataset.v111ProductTask);
        if (product) updateButtonState(button, productIdentity(product), "加入待办");
        if (button.dataset.taskBridgeBound) return;
        button.dataset.taskBridgeBound = "1";
        button.addEventListener("click", () => createProductTask(button.dataset.v111ProductTask));
      });
    }

    if (typeof competitorManagerPayload !== "undefined") {
      document.querySelectorAll("[data-competitor-watch]").forEach((button) => {
        const item = competitorManagerPayload.competitors.find((competitor) => competitor.id === button.dataset.competitorWatch);
        if (item) updateButtonState(button, competitorIdentity(item), "加入观察");
        if (button.dataset.taskBridgeBound) return;
        button.dataset.taskBridgeBound = "1";
        button.addEventListener("click", () => createCompetitorTask(button.dataset.competitorWatch));
      });
    }

    if (typeof listingManagerPayload !== "undefined") {
      document.querySelectorAll("[data-listing-task]").forEach((button) => {
        const item = listingManagerPayload.experiments.find((experiment) => experiment.id === button.dataset.listingTask);
        if (item) updateButtonState(button, listingIdentity(item), "加入任务清单");
        if (button.dataset.taskBridgeBound) return;
        button.dataset.taskBridgeBound = "1";
        button.addEventListener("click", () => createListingTask(button.dataset.listingTask));
      });
    }

    if (typeof trafficManagerPayload !== "undefined") {
      document.querySelectorAll("[data-traffic-task]").forEach((button) => {
        const item = trafficManagerPayload.tests.find((test) => test.id === button.dataset.trafficTask);
        if (item) updateButtonState(button, trafficIdentity(item), "加入任务清单");
        if (button.dataset.taskBridgeBound) return;
        button.dataset.taskBridgeBound = "1";
        button.addEventListener("click", () => createTrafficTask(button.dataset.trafficTask));
      });
    }

    if (typeof reportManagerPayload !== "undefined") {
      document.querySelectorAll("[data-report-confirm-import]").forEach((button) => {
        const card = reportManagerPayload.groups.flatMap((group) => group.reports).find((report) => report.id === button.dataset.reportConfirmImport);
        if (card) updateButtonState(button, reportIdentity(card), "确认导入");
        if (button.dataset.taskBridgeBound) return;
        button.dataset.taskBridgeBound = "1";
        button.addEventListener("click", () => {
          if (typeof selectedImportFileName !== "undefined" && selectedImportFileName) createReportTask(button.dataset.reportConfirmImport);
        });
      });
    }
  }

  function scheduleBind() {
    if (bindScheduled) return;
    bindScheduled = true;
    requestAnimationFrame(() => {
      bindScheduled = false;
      bindButtons();
    });
  }

  const observer = new MutationObserver(() => scheduleBind());
  observer.observe(document.body, { childList: true, subtree: true });
  window.addEventListener("operation-task-store-change", scheduleBind);
  window.addEventListener("hashchange", scheduleBind);
  window.addEventListener("load", scheduleBind);
  scheduleBind();
})();
