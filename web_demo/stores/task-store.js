(function () {
  const TASK_KEY = "ai_ecommerce_v151_tasks";
  const LOG_KEY = "ai_ecommerce_v151_logs";
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

  function buildDedupeKey(task = {}) {
    if (typeof task === "string") return task;
    return task.dedupeKey || task.suggestedTaskKey || [task.entityType, task.entityId || task.productId || task.id, task.riskDomain, task.actionType].filter(Boolean).join(":");
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
      todoRoute: task.todoRoute || "business-actions",
      logRoute: task.logRoute || "business-report",
      entityType: task.entityType || "任务",
      entityId: task.entityId || task.productId || task.id,
      riskDomain: task.riskDomain || "通用",
      actionType: task.actionType || "复查",
      judgmentTags: task.judgmentTags || [],
      sourceTrail: task.sourceTrail || [],
      createdAt: task.createdAt || new Date().toISOString(),
      updatedAt: task.updatedAt || task.createdAt || new Date().toISOString(),
      manualOrder: Number.isFinite(task.manualOrder) ? task.manualOrder : Date.now(),
      ...task,
    };
    item.title = item.title || item.productTitle || item.task || item.taskType || "经营任务";
    item.productTitle = item.productTitle || item.title;
    item.productShort = item.productShort || item.shortName || item.productId || "任务";
    item.dedupeKey = buildDedupeKey(item) || item.id;
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
    const index = tasks.findIndex((item) => item.id === task.id || (item.dedupeKey && item.dedupeKey === task.dedupeKey && !doneStatus.has(item.status)));
    if (index >= 0) tasks[index] = normalize({ ...tasks[index], ...task });
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
      const key = buildDedupeKey(input || {});
      return getTasks().find((task) => (task.id === input?.activeTaskId || task.dedupeKey === key) && !doneStatus.has(task.status));
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
