(function () {
  const data = () => window.AppMockData;
  const store = () => window.AppTaskStore;

  function notifyTask(task, name) {
    return task?.dedupeHit ? `${name}已有相关待办，已合并到现有任务。` : `${name}已进入统一任务池。`;
  }

  function productIdentity(product) {
    const riskDomain = product.afterSalesLevel !== "good" ? "售后" : product.inventoryLevel === "danger" ? "库存" : "商品";
    return { entityType: "商品", entityId: product.id, riskDomain, actionType: riskDomain === "商品" ? "观察" : "复查" };
  }

  function createProductTask(productId) {
    const product = data().products.find((item) => item.id === productId);
    if (!product) return null;
    const identity = productIdentity(product);
    const highRisk = product.afterSalesLevel !== "good" || product.inventoryLevel === "danger";
    const task = store().createTask({
      ...identity,
      sourceModule: "商品经营列表",
      source: "商品触发",
      sourceRoute: "business-products",
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
      taskType: product.afterSalesLevel !== "good" ? "售后复查" : product.inventoryLevel === "danger" ? "库存承接" : "商品优化",
      taskSignal: product.afterSalesLevel !== "good" ? "先查售后" : product.inventoryLevel === "danger" ? "确认补货" : "优化测试",
      task: product.afterSalesLevel !== "good" ? "复查售后原因，暂不扩大推广" : product.inventoryLevel === "danger" ? "确认补货周期，再决定活动节奏" : "加入商品优化观察",
      reason: product.suggestion,
      judgmentTags: [product.inventoryStatus, product.afterSales, `毛利 ${product.grossMargin}`],
    });
    return { task, message: notifyTask(task, product.shortName) };
  }

  function createCompetitorTask(id) {
    const item = data().competitors.find((row) => row.id === id);
    if (!item) return null;
    const identity = { entityType: "竞品", entityId: item.id, riskDomain: item.status === "风险" ? "风险" : "上新", actionType: item.status === "风险" ? "复查" : "测试" };
    const task = store().createTask({ ...identity, sourceModule: "竞品观察列表", source: "竞品触发", sourceRoute: "business-competitors", productId: item.id, imageLabel: item.imageLabel, productShort: item.targetProduct, productTitle: item.title, title: item.title, platform: item.platform, store: item.store, priority: item.status === "风险" ? "高" : "中", priorityLevel: item.status === "风险" ? "danger" : "warning", deadline: item.status === "风险" ? "今天内" : "明天前", taskType: item.status === "风险" ? "竞品风险" : "竞品机会", taskSignal: item.opportunity, task: item.status === "风险" ? "复查竞品风险，不直接跟价" : "生成对标测试任务", reason: item.suggestion, judgmentTags: [item.pricePosition, item.badReview, item.status] });
    return { task, message: notifyTask(task, item.targetProduct) };
  }

  function createListingTask(id) {
    const item = data().listings.find((row) => row.id === id);
    if (!item) return null;
    const identity = { entityType: item.mode === "competitor" ? "竞品机会" : "商品", entityId: item.id, riskDomain: "上新", actionType: item.testType.includes("复盘") ? "复盘" : "测试" };
    const task = store().createTask({ ...identity, sourceModule: "上新测试台", source: "上新触发", sourceRoute: "business-listing", productId: item.id, imageLabel: item.imageLabel, productShort: item.sourceName, productTitle: item.title, title: item.title, platform: item.platform, store: item.store, priority: item.statusLevel === "danger" ? "高" : "中", priorityLevel: item.statusLevel, deadline: item.due, taskType: item.testType, taskSignal: "确认测试版本", task: `${item.testType}：${item.testPlan}`, reason: `${item.risk} ${item.suggestion}`, judgmentTags: [item.sourceLabel, item.testType, item.targetMetric], testVersion: item.testPlan });
    return { task, message: notifyTask(task, item.testType) };
  }

  function createTrafficTask(id) {
    const item = data().traffic.find((row) => row.id === id);
    if (!item) return null;
    const text = `${item.status} ${item.backflow} ${item.nextStep}`;
    const riskDomain = /售后|退款|材质|尺寸|安装|客服/.test(text) ? "售后" : /库存|补货|承接/.test(text) ? "库存" : "流量";
    const identity = { entityType: "商品", entityId: item.productId, riskDomain, actionType: riskDomain === "流量" && item.statusLevel === "good" ? "观察" : "复查" };
    const task = store().createTask({ ...identity, sourceModule: "流量测试台", source: "流量触发", sourceRoute: "business-traffic", productId: item.productId, imageLabel: item.imageLabel, productShort: item.title.slice(0, 6), productTitle: item.title, title: item.title, platform: item.platform, store: item.store, link: item.link, priority: item.statusLevel === "danger" ? "高" : item.statusLevel === "warning" ? "中" : "低", priorityLevel: item.statusLevel, deadline: item.statusLevel === "danger" ? "今天 18:00 前" : "明天前", taskType: item.backflow, taskSignal: item.status, task: item.nextStep, reason: `${item.channel} ${item.source}：ROI ${item.roi}，退款率 ${item.refundRate}，库存 ${item.inventory}。`, judgmentTags: [`ROI ${item.roi}`, `退款率 ${item.refundRate}`, item.status] });
    return { task, message: notifyTask(task, item.channel) };
  }

  function createReportTask(id) {
    const card = data().reportGroups.flatMap((group) => group.reports).find((report) => report.id === id);
    if (!card) return null;
    const task = store().createTask({ entityType: "报表", entityId: card.id, riskDomain: "报表", actionType: "导入", sourceModule: "ERP / CRM 报表管理", source: "报表触发", sourceRoute: "data-check", productId: `R-${card.id}`, imageLabel: "表", productShort: card.name, productTitle: `${card.name}导入后复盘`, title: `${card.name}导入后复盘`, platform: card.source, store: "家居生活店铺组", productRoute: "data-check", priority: card.id === "refunds" || card.id === "orders" ? "高" : "中", priorityLevel: card.id === "refunds" || card.id === "orders" ? "danger" : "warning", deadline: card.id === "refunds" || card.id === "orders" ? "今天内" : "本周内", taskType: "报表复盘", taskSignal: "导入后生成任务", task: `复盘${card.name}，生成下一轮经营任务`, reason: `${card.desc}。导入后需要同步首页、待办和日志。`, judgmentTags: [card.source, card.status, card.count] });
    return { task, message: notifyTask(task, card.name) };
  }

  window.AppTaskActions = { createProductTask, createCompetitorTask, createListingTask, createTrafficTask, createReportTask, productIdentity };
})();
