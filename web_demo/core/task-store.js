(function () {
  let tasks = [];
  let logs = [];
  let events = [];
  let counterState = {};
  const listeners = new Set();

  function clone(value) {
    try { return JSON.parse(JSON.stringify(value)); }
    catch (_) { return value; }
  }

  function notify() {
    listeners.forEach((listener) => {
      try { listener(); }
      catch (error) { console.error("[task-store] listener error", error); }
    });
  }

  function normalizeLog(item) {
    return {
      id: item.id || item.eventId || `LOG-${Date.now()}-${Math.random().toString(16).slice(2)}`,
      time: item.time || item.createdAt || item.at || "--:--",
      type: item.type || item.eventLabel || item.eventType || "任务记录",
      title: item.title || item.taskTitle || item.message || "任务记录",
      productId: item.productId || item.entityId || item.taskId || "TASK",
      platform: item.platform || "经营单元",
      store: item.store || item.storeName || "任务池",
      source: item.source || item.sourceModule || item.actorName || "系统",
      status: item.status || item.toStatus || "已记录",
      action: item.action || item.eventLabel || item.eventType || "任务池动作",
      reason: item.reason || item.message || "统一任务池记录。",
      result: item.result || item.toStatus || "已写入日志。",
      route: item.route || item.sourceRoute || "dashboard",
      taskRoute: item.taskRoute || "business-actions",
      level: item.level || "info",
      imageLabel: item.imageLabel || "记",
    };
  }

  function hydrate(nextTasks = [], nextLogs = [], nextEvents = [], nextCounters = {}) {
    tasks = Array.isArray(nextTasks) ? clone(nextTasks) : [];
    events = Array.isArray(nextEvents) ? clone(nextEvents) : [];
    const eventLogs = events.map(normalizeLog);
    const rawLogs = Array.isArray(nextLogs) ? nextLogs.map(normalizeLog) : [];
    logs = rawLogs.length ? rawLogs : eventLogs;
    counterState = nextCounters && typeof nextCounters === "object" ? clone(nextCounters) : {};
    notify();
    return snapshot();
  }

  function snapshot() {
    return {
      tasks: listTasks(),
      activeTasks: listActiveTasks(),
      logs: listLogs(),
      events: listEvents(),
      counters: counters(),
    };
  }

  function listTasks() { return clone(tasks); }
  function listActiveTasks() {
    return tasks.filter((task) => !["已完成", "已归档", "已写入复盘"].includes(task.status) && !["已完成", "已归档"].includes(task.workflowStatus)).map(clone);
  }
  function listLogs() { return clone(logs); }
  function listEvents() { return clone(events); }
  function counters() { return clone(counterState); }

  function upsert(task) {
    if (!task || !task.id) return null;
    const index = tasks.findIndex((item) => item.id === task.id);
    if (index >= 0) tasks[index] = { ...tasks[index], ...task };
    else tasks.unshift(task);
    notify();
    return clone(task);
  }

  function subscribe(listener) {
    if (typeof listener !== "function") return () => {};
    listeners.add(listener);
    return () => listeners.delete(listener);
  }

  window.AppTaskStore = { hydrate, snapshot, listTasks, listActiveTasks, listLogs, listEvents, counters, upsert, subscribe };

  window.AppTaskActions = {
    openTodoTask(taskId) {
      window.AppRouter?.navigate?.("business-actions", taskId ? { focusTaskId: taskId } : null);
    },
    openTaskReport(taskId) {
      window.AppRouter?.navigate?.("task-report", taskId ? { taskId } : null);
    },
    async createTaskFromReport(module, entityId) {
      if (!window.AppApi) return null;
      const map = {
        product: window.AppApi.createProductTask,
        competitor: window.AppApi.createCompetitorTask,
        listing: window.AppApi.createListingTask,
        traffic: window.AppApi.createTrafficTask,
        report: window.AppApi.createReportTask,
      };
      const fn = map[module];
      if (!fn) return null;
      const result = await fn(entityId);
      if (result?.task) upsert(result.task);
      return result;
    },
  };
})();
