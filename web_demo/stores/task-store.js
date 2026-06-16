(function () {
  const TASK_KEY = "ai_ecommerce_v141_tasks";
  const LOG_KEY = "ai_ecommerce_v141_logs";
  const doneStatus = new Set(["已完成", "已拒绝", "已确认"]);
  const priorityRank = { 高: 1, 中: 2, 低: 3 };

  function read(key, fallback) {
    try {
      const raw = localStorage.getItem(key);
      return raw ? JSON.parse(raw) : fallback;
    } catch {
      return fallback;
    }
  }

  function write(key, value) {
    localStorage.setItem(key, JSON.stringify(value));
  }

  function inferDomain(task = {}) {
    const text = [task.riskDomain, task.taskType, task.taskSignal, task.task, task.reason, ...(task.judgmentTags || [])].join(" ");
    if (/售后|退款|尺寸|材质|安装|客服/.test(text)) return "售后";
    if (/库存|补货|承接/.test(text)) return "库存";
    if (/流量|ROI|推广|投放|点击|转化/.test(text)) return "流量";
    if (/上新|主图|标题|SKU|详情页|测试版本/.test(text)) return "上新";
    if (/价格|利润|券|活动价/.test(text)) return "价格";
    if (/报表|导入|同步|数据/.test(text)) return "报表";
    return "通用";
  }

  function inferAction(task = {}) {
    const text = [task.actionType, task.taskType, task.taskSignal, task.task].join(" ");
    if (/复盘/.test(text)) return "复盘";
    if (/测试|版本|上新/.test(text)) return "测试";
    if (/导入|同步/.test(text)) return "导入";
    if (/观察/.test(text)) return "观察";
    if (/确认/.test(text)) return "确认";
    return "复查";
  }

  function buildDedupeKey(task = {}) {
    const entityType = task.entityType || (String(task.productId || "").startsWith("R") ? "报表" : "商品");
    const entityId = task.entityId || task.productId || task.sourceEvent || task.id || "unknown";
    const riskDomain = task.riskDomain || inferDomain(task);
    const actionType = task.actionType || inferAction(task);
    return `${entityType}:${entityId}:${riskDomain}:${actionType}`;
  }

  function normalize(task = {}) {
    const priority = task.priority || "中";
    const item = {
      id: task.id || `A${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`.toUpperCase(),
      status: "待确认",
      priority,
      priorityLevel: task.priorityLevel || (priority === "高" ? "danger" : priority === "低" ? "good" : "warning"),
      deadline: task.deadline || "本周内",
      timeBucket: task.timeBucket || task.deadline || "本周内",
      source: task.source || task.sourceModule || "系统",
      sourceModule: task.sourceModule || task.source || "系统",
      sourceRoute: task.sourceRoute || "dashboard",
      productRoute: task.productRoute || task.sourceRoute || "business-products",
      todoRoute: "business-actions",
      logRoute: "business-report",
      entityType: task.entityType || (String(task.productId || "").startsWith("R") ? "报表" : "商品"),
      entityId: task.entityId || task.productId || task.id,
      riskDomain: task.riskDomain || inferDomain(task),
      actionType: task.actionType || inferAction(task),
      judgmentTags: [],
      sourceTrail: [],
      createdAt: task.createdAt || new Date().toISOString(),
      updatedAt: task.updatedAt || task.createdAt || new Date().toISOString(),
      manualOrder: Number.isFinite(task.manualOrder) ? task.manualOrder : Date.now(),
      ...task,
    };
    item.title = item.title || item.productTitle || item.task || item.taskType || "经营任务";
    item.productTitle = item.productTitle || item.title;
    item.productShort = item.productShort || item.shortName || item.productId || "任务";
    item.dedupeKey = item.dedupeKey || buildDedupeKey(item);
    return item;
  }

  function sort(tasks) {
    return [...tasks].sort((a, b) => {
      const pr = (priorityRank[a.priority] || 9) - (priorityRank[b.priority] || 9);
      if (pr) return pr;
      const order = (a.manualOrder || 9999) - (b.manualOrder || 9999);
      if (order) return order;
      return new Date(a.createdAt || 0) - new Date(b.createdAt || 0);
    });
  }

  function notify() {
    window.dispatchEvent(new CustomEvent("task-store-change"));
  }

  function getTasks() {
    return read(TASK_KEY, []).map(normalize);
  }

  function setTasks(tasks) {
    write(TASK_KEY, tasks.map(normalize));
  }

  function getLogs() {
    return read(LOG_KEY, []);
  }

  function setLogs(logs) {
    write(LOG_KEY, logs || []);
  }

  function hydrate(tasks = [], logs = []) {
    setTasks(Array.isArray(tasks) ? tasks : []);
    setLogs(Array.isArray(logs) ? logs : []);
    notify();
  }

  function createTask(input = {}) {
    const task = normalize(input);
    const tasks = getTasks();
    const index = tasks.findIndex((item) => item.dedupeKey === task.dedupeKey && !doneStatus.has(item.status));
    if (index >= 0) tasks[index] = normalize({ ...tasks[index], ...task, dedupeHit: task.dedupeHit ?? true });
    else tasks.push(task);
    setTasks(tasks);
    notify();
    return task;
  }

  function updateTask(taskId, patch = {}) {
    const tasks = getTasks();
    const index = tasks.findIndex((task) => task.id === taskId);
    if (index < 0) return null;
    const task = normalize({ ...tasks[index], ...patch, updatedAt: new Date().toISOString() });
    tasks[index] = task;
    setTasks(tasks);
    notify();
    return task;
  }

  function completeTask(taskId) {
    return updateTask(taskId, { status: "已完成", completedAt: new Date().toISOString() });
  }

  function pinTask(taskId) {
    const min = Math.min(...getTasks().map((task) => task.manualOrder || 9999), 0);
    return updateTask(taskId, { manualOrder: min - 1 });
  }

  function reorderTask(taskId, direction) {
    const active = sort(getTasks().filter((task) => !doneStatus.has(task.status)));
    const index = active.findIndex((task) => task.id === taskId);
    const targetIndex = direction === "up" ? index - 1 : index + 1;
    if (index < 0 || targetIndex < 0 || targetIndex >= active.length) return null;
    const current = active[index];
    const target = active[targetIndex];
    const tasks = getTasks();
    const currentRef = tasks.find((task) => task.id === current.id);
    const targetRef = tasks.find((task) => task.id === target.id);
    if (!currentRef || !targetRef) return null;
    const currentOrder = currentRef.manualOrder || index + 1;
    currentRef.manualOrder = targetRef.manualOrder || targetIndex + 1;
    targetRef.manualOrder = currentOrder;
    setTasks(tasks);
    notify();
    return currentRef;
  }

  function resetDemoData() {
    hydrate([], []);
  }

  window.AppTaskStore = {
    hydrate,
    listTasks: () => sort(getTasks()),
    listActiveTasks: () => sort(getTasks().filter((task) => !doneStatus.has(task.status))),
    listDashboardTasks: () => sort(getTasks().filter((task) => !doneStatus.has(task.status))).slice(0, 5),
    listLogs: () => getLogs(),
    createTask,
    updateTask,
    completeTask,
    pinTask,
    reorderTask,
    findOpenTask(input) {
      const key = typeof input === "string" ? input : buildDedupeKey(input || {});
      return getTasks().find((task) => task.dedupeKey === key && !doneStatus.has(task.status));
    },
    buildDedupeKey,
    createLog(log) {
      const logs = getLogs();
      logs.unshift(log);
      setLogs(logs.slice(0, 200));
      notify();
      return log;
    },
    resetDemoData,
    subscribe(handler) {
      window.addEventListener("task-store-change", handler);
      return () => window.removeEventListener("task-store-change", handler);
    },
  };
  window.OPERATION_TASK_STORE = window.AppTaskStore;
})();
