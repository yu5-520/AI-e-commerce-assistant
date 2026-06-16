(function () {
  const data = () => window.AppMockData;
  const store = () => window.AppTaskStore;

  function notifyTask(task, name) {
    return task?.dedupeHit ? `${name}已有相关待办，已合并到现有任务。` : `${name}已进入统一任务池。`;
  }

  async function syncAfter(serverTask) {
    if (serverTask) store().createTask(serverTask);
    await window.AppApi?.refreshTaskState?.();
    return serverTask;
  }

  function productIdentity(product) {
    const riskDomain = product.afterSalesLevel !== "good" ? "售后" : product.inventoryLevel === "danger" ? "库存" : "商品";
    return { entityType: "商品", entityId: product.id, riskDomain, actionType: riskDomain === "商品" ? "观察" : "复查" };
  }

  async function createProductTask(productId) {
    const product = data().products.find((item) => item.id === productId);
    if (!product) return null;
    const task = await syncAfter(await window.AppApi.createProductTask(productId));
    return { task, message: notifyTask(task, product.shortName) };
  }

  async function createCompetitorTask(id) {
    const item = data().competitors.find((row) => row.id === id);
    if (!item) return null;
    const task = await syncAfter(await window.AppApi.createCompetitorTask(id));
    return { task, message: notifyTask(task, item.targetProduct) };
  }

  async function createListingTask(id) {
    const item = data().listings.find((row) => row.id === id);
    if (!item) return null;
    const task = await syncAfter(await window.AppApi.createListingTask(id));
    return { task, message: notifyTask(task, item.testType) };
  }

  async function createTrafficTask(id) {
    const item = data().traffic.find((row) => row.id === id);
    if (!item) return null;
    const task = await syncAfter(await window.AppApi.createTrafficTask(id));
    return { task, message: notifyTask(task, item.channel) };
  }

  async function createReportTask(id) {
    const card = data().reportGroups.flatMap((group) => group.reports).find((report) => report.id === id);
    if (!card) return null;
    const task = await syncAfter(await window.AppApi.createReportTask(id));
    return { task, message: notifyTask(task, card.name) };
  }

  window.AppTaskActions = { createProductTask, createCompetitorTask, createListingTask, createTrafficTask, createReportTask, productIdentity };
})();
