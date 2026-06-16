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

  function identityFromItem(item = {}) {
    return {
      dedupeKey: item.suggestedTaskKey || item.dedupeKey,
      suggestedTaskKey: item.suggestedTaskKey || item.dedupeKey,
      activeTaskId: item.activeTaskId,
    };
  }

  function findOpenTask(item = {}) {
    return store().findOpenTask(identityFromItem(item));
  }

  function openTodoTask(taskOrId) {
    const taskId = typeof taskOrId === "string" ? taskOrId : taskOrId?.id || taskOrId?.activeTaskId;
    if (!taskId) return false;
    AppRouter.navigate("business-actions", { focusTaskId: taskId });
    return true;
  }

  function openTaskReport(taskOrId) {
    const taskId = typeof taskOrId === "string" ? taskOrId : taskOrId?.id || taskOrId?.activeTaskId;
    if (!taskId) return false;
    AppRouter.navigate("task-report", { taskId });
    return true;
  }

  function openCandidateReport(module, entityId) {
    if (!module || !entityId) return false;
    AppRouter.navigate("task-report", { module, entityId });
    return true;
  }

  function buttonLabel(item = {}) {
    return findOpenTask(item) ? "已在任务清单" : "加入任务清单";
  }

  function buttonClass(item = {}) {
    return findOpenTask(item) ? "ghost" : "";
  }

  function productIdentity(product) {
    return identityFromItem(product);
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

  window.AppTaskActions = { createProductTask, createCompetitorTask, createListingTask, createTrafficTask, createReportTask, productIdentity, identityFromItem, findOpenTask, openTodoTask, openTaskReport, openCandidateReport, buttonLabel, buttonClass };
})();
