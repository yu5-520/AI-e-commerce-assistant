(function () {
  const TASK_KEY = "ai_ecommerce_v130_tasks";
  const LOG_KEY = "ai_ecommerce_v130_logs";
  const BOOT_KEY = "ai_ecommerce_v130_booted";
  const doneStatus = new Set(["已完成", "已拒绝", "已确认"]);
  const priorityRank = { 高: 1, 中: 2, 低: 3 };

  function now() {
    const d = new Date();
    return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
  }

  function id(prefix) {
    return `${prefix}${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`.toUpperCase();
  }

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
    const createdAt = task.createdAt || new Date().toISOString();
    const priority = task.priority || "中";
    const normalized = {
      id: task.id || id("A"),
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
      createdAt,
      updatedAt: task.updatedAt || createdAt,
      manualOrder: Number.isFinite(task.manualOrder) ? task.manualOrder : Date.now(),
      ...task,
    };
    normalized.title = normalized.title || normalized.productTitle || normalized.task || normalized.taskType || "经营任务";
    normalized.productTitle = normalized.productTitle || normalized.title;
    normalized.productShort = normalized.productShort || normalized.shortName || normalized.productId || "任务";
    normalized.dedupeKey = task.dedupeKey || buildDedupeKey(normalized);
    normalized.sourceTrail = Array.from(new Set([...(normalized.sourceTrail || []), normalized.sourceModule].filter(Boolean)));
    return normalized;
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

  function seedTasks() {
    return [
      normalize({ id: "A001", priority: "高", priorityLevel: "danger", deadline: "今天 18:00 前", source: "流量触发", sourceModule: "流量测试台", sourceRoute: "business-traffic", productId: "P002", entityType: "商品", entityId: "P002", riskDomain: "售后", actionType: "复查", imageLabel: "架", taskType: "售后优先", taskSignal: "先查售后", productShort: "厨房置物架", productTitle: "厨房置物架免打孔收纳架壁挂多层家用置物架", platform: "拼多多", store: "家居百货店", judgmentTags: ["ROI 低", "退款率高", "尺寸咨询高"], task: "先查售后，不继续放大推广预算", reason: "搜索推广 ROI 1.1，退款率 6.8%，安装和尺寸咨询偏高。", manualOrder: 1 }),
      normalize({ id: "A002", priority: "高", priorityLevel: "danger", deadline: "今天内", source: "商品触发", sourceModule: "商品经营列表", sourceRoute: "business-products", productId: "P003", entityType: "商品", entityId: "P003", riskDomain: "售后", actionType: "复查", imageLabel: "垫", taskType: "商品复查", taskSignal: "暂停投放", productShort: "护腰坐垫", productTitle: "护腰坐垫久坐办公室靠垫人体工学支撑款", platform: "抖音小店", store: "家居好物号", judgmentTags: ["ROI 低", "退款异常", "售后敏感"], task: "暂停投放并复查材质、支撑感和客服承诺", reason: "售后敏感未解决，推荐流量 ROI 0.9，退款率 8.4%。", manualOrder: 2 }),
      normalize({ id: "A003", priority: "中", priorityLevel: "warning", deadline: "明天前", source: "商品触发", sourceModule: "商品经营列表", sourceRoute: "business-products", productId: "P004", entityType: "商品", entityId: "P004", riskDomain: "库存", actionType: "复查", imageLabel: "盒", taskType: "库存承接", taskSignal: "确认补货周期", productShort: "收纳盒", productTitle: "透明收纳盒衣柜整理箱家用大容量防尘款", platform: "淘宝", store: "家居生活主店", judgmentTags: ["库存低", "活动流量"], task: "确认补货周期，再决定是否继续活动流量", reason: "库存 46，接近安全线。", manualOrder: 3 }),
    ];
  }

  function seedLogs() {
    return [
      { id: "G001", time: "16:08", type: "任务进入池", source: "流量触发", status: "已加入任务池", level: "danger", imageLabel: "架", title: "厨房置物架免打孔收纳架壁挂多层家用置物架", platform: "拼多多", store: "家居百货店", productId: "P002", action: "搜索推广测试进入统一任务池", reason: "ROI 1.1，退款率 6.8%。", result: "进入售后归因，暂不继续放大推广预算。", route: "business-traffic", taskRoute: "business-actions", createdAt: new Date().toISOString() },
    ];
  }

  function getTasks() { return read(TASK_KEY, seedTasks()).map(normalize); }
  function setTasks(tasks) { write(TASK_KEY, tasks.map(normalize)); }
  function getLogs() { return read(LOG_KEY, seedLogs()); }
  function setLogs(logs) { write(LOG_KEY, logs); }
  function notify() { window.dispatchEvent(new CustomEvent("task-store-change")); }

  function log(input = {}) {
    const task = input.task || {};
    const item = { id: input.id || id("G"), time: input.time || now(), type: input.type || "任务记录", source: input.source || task.source || task.sourceModule || "系统", status: input.status || task.status || "已记录", level: input.level || task.priorityLevel || "good", imageLabel: input.imageLabel || task.imageLabel || "记", title: input.title || task.title || task.productTitle || "任务记录", platform: input.platform || task.platform || "经营单元", store: input.store || task.store || "任务池", productId: input.productId || task.productId || task.id || "TASK", action: input.action || "任务池动作", reason: input.reason || task.reason || "来自统一任务池。", result: input.result || "已写入日志。", route: input.route || task.sourceRoute || "dashboard", taskRoute: input.taskRoute || "business-actions", createdAt: new Date().toISOString() };
    const logs = getLogs();
    logs.unshift(item);
    setLogs(logs.slice(0, 200));
    notify();
    return item;
  }

  function findOpenTask(input) {
    const key = typeof input === "string" ? input : buildDedupeKey(input || {});
    return getTasks().find((task) => task.dedupeKey === key && !doneStatus.has(task.status));
  }

  function createTask(input = {}) {
    const task = normalize(input);
    const tasks = getTasks();
    const duplicate = tasks.find((item) => item.dedupeKey === task.dedupeKey && !doneStatus.has(item.status));
    if (duplicate) {
      const index = tasks.findIndex((item) => item.id === duplicate.id);
      const merged = normalize({ ...duplicate, judgmentTags: Array.from(new Set([...(duplicate.judgmentTags || []), ...(task.judgmentTags || [])])).slice(0, 8), sourceTrail: Array.from(new Set([...(duplicate.sourceTrail || []), task.sourceModule])), updatedAt: new Date().toISOString(), mergeCount: (duplicate.mergeCount || 0) + 1 });
      tasks[index] = merged;
      setTasks(tasks);
      log({ type: "任务合并", task: merged, status: "已合并", action: `${task.sourceModule} 重复加入，已合并到现有任务`, reason: `去重键：${merged.dedupeKey}`, result: "未创建重复任务。" });
      merged.dedupeHit = true;
      notify();
      return merged;
    }
    tasks.push(task);
    setTasks(tasks);
    log({ type: "任务创建", task, status: "已加入任务池", action: `${task.sourceModule || task.source} 创建任务：${task.taskType || task.task || task.title}`, result: "已同步到首页、待办和日志。" });
    task.dedupeHit = false;
    notify();
    return task;
  }

  function updateTask(taskId, patch = {}, logOptions = {}) {
    const tasks = getTasks();
    const index = tasks.findIndex((task) => task.id === taskId);
    if (index < 0) return null;
    const task = normalize({ ...tasks[index], ...patch, updatedAt: new Date().toISOString() });
    tasks[index] = task;
    setTasks(tasks);
    log({ type: logOptions.type || "任务更新", task, status: task.status, action: logOptions.action || `${task.title} 已更新`, result: logOptions.result || "任务状态已同步。" });
    notify();
    return task;
  }

  function completeTask(taskId) { return updateTask(taskId, { status: "已完成", completedAt: new Date().toISOString() }, { type: "任务完成", action: "任务已完成", result: "首页移除该任务，日志保留处理记录。" }); }
  function pinTask(taskId) { const min = Math.min(...getTasks().map((task) => task.manualOrder || 9999), 0); return updateTask(taskId, { manualOrder: min - 1 }, { type: "任务置顶", action: "任务已置顶", result: "首页和待办同步排序。" }); }
  function reorderTask(taskId, direction) { const active = sort(getTasks().filter((task) => !doneStatus.has(task.status))); const index = active.findIndex((task) => task.id === taskId); const targetIndex = direction === "up" ? index - 1 : index + 1; if (index < 0 || targetIndex < 0 || targetIndex >= active.length) return null; const current = active[index]; const target = active[targetIndex]; const currentOrder = current.manualOrder || index + 1; const targetOrder = target.manualOrder || targetIndex + 1; updateTask(current.id, { manualOrder: targetOrder }, { type: "任务排序", action: "任务顺序已调整", result: "首页和待办同步排序。" }); updateTask(target.id, { manualOrder: currentOrder }, { type: "任务排序", action: "相邻任务顺序已交换", result: "排序变更已写入日志。" }); return current; }
  function resetDemoData() { setTasks(seedTasks()); setLogs(seedLogs()); log({ type: "演示重置", status: "已重置", action: "统一任务池已恢复默认演示数据", result: "首页、待办、日志已同步刷新。" }); }

  if (!localStorage.getItem(BOOT_KEY)) { setTasks(seedTasks()); setLogs(seedLogs()); localStorage.setItem(BOOT_KEY, "1"); }

  window.AppTaskStore = { listTasks: () => sort(getTasks()), listActiveTasks: () => sort(getTasks().filter((task) => !doneStatus.has(task.status))), listDashboardTasks: () => sort(getTasks().filter((task) => !doneStatus.has(task.status))).slice(0, 5), listLogs: () => getLogs(), createTask, updateTask, completeTask, pinTask, reorderTask, findOpenTask, buildDedupeKey, createLog: log, resetDemoData, subscribe(handler) { window.addEventListener("task-store-change", handler); return () => window.removeEventListener("task-store-change", handler); } };
  window.OPERATION_TASK_STORE = window.AppTaskStore;
})();
