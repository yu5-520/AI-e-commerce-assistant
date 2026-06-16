(function () {
  const TASK_KEY = "ai_ecommerce_v111_tasks";
  const LOG_KEY = "ai_ecommerce_v111_logs";
  const BOOT_KEY = "ai_ecommerce_v111_booted";

  const priorityRank = { 高: 1, 中: 2, 低: 3 };
  const statusDone = new Set(["已完成", "已确认", "已拒绝"]);

  const seedTasks = [
    {
      id: "A001",
      priority: "高",
      priorityLevel: "danger",
      deadline: "今天 18:00 前",
      timeBucket: "今天 18:00 前",
      source: "流量触发",
      sourceModule: "流量测试台",
      sourceRoute: "business-traffic",
      todoRoute: "business-actions",
      productRoute: "business-products",
      productId: "P002",
      entityType: "商品",
      entityId: "P002",
      riskDomain: "售后",
      actionType: "复查",
      imageLabel: "架",
      taskType: "售后优先",
      taskSignal: "先查售后",
      productShort: "厨房置物架",
      productTitle: "厨房置物架免打孔收纳架壁挂多层家用置物架",
      title: "厨房置物架免打孔收纳架壁挂多层家用置物架",
      platform: "拼多多",
      store: "家居百货店",
      link: "https://shop.example.com/products/P002",
      judgmentTags: ["ROI 低", "退款率高", "尺寸咨询高"],
      task: "先查售后，不继续放大推广预算",
      reason: "搜索推广 ROI 1.1，退款率 6.8%，安装和尺寸咨询偏高。",
      status: "待确认",
      manualOrder: 1,
    },
    {
      id: "A002",
      priority: "高",
      priorityLevel: "danger",
      deadline: "今天内",
      timeBucket: "今天内",
      source: "商品触发",
      sourceModule: "商品经营列表",
      sourceRoute: "business-products",
      todoRoute: "business-actions",
      productRoute: "business-products",
      productId: "P003",
      entityType: "商品",
      entityId: "P003",
      riskDomain: "售后",
      actionType: "复查",
      imageLabel: "垫",
      taskType: "商品复查",
      taskSignal: "暂停投放",
      productShort: "护腰坐垫",
      productTitle: "护腰坐垫久坐办公室靠垫人体工学支撑款",
      title: "护腰坐垫久坐办公室靠垫人体工学支撑款",
      platform: "抖音小店",
      store: "家居好物号",
      link: "https://shop.example.com/products/P003",
      judgmentTags: ["ROI 低", "退款异常", "售后敏感"],
      task: "暂停投放并复查材质、支撑感和客服承诺",
      reason: "售后敏感未解决，推荐流量 ROI 0.9，退款率 8.4%。",
      status: "待确认",
      manualOrder: 2,
    },
    {
      id: "A003",
      priority: "高",
      priorityLevel: "danger",
      deadline: "今天 20:00 前",
      timeBucket: "今天 20:00 前",
      source: "上新触发",
      sourceModule: "上新测试台",
      sourceRoute: "business-listing",
      todoRoute: "business-actions",
      productRoute: "business-products",
      productId: "P001",
      entityType: "商品",
      entityId: "P001",
      riskDomain: "价格",
      actionType: "确认",
      imageLabel: "伞",
      taskType: "活动价确认",
      taskSignal: "确认利润线",
      productShort: "遮阳伞",
      productTitle: "遮阳伞户外便携防晒防紫外线晴雨两用",
      title: "遮阳伞户外便携防晒防紫外线晴雨两用",
      platform: "淘宝",
      store: "家居生活主店",
      link: "https://shop.example.com/products/P001",
      judgmentTags: ["活动测试", "利润安全线", "库存承接"],
      task: "确认平台券活动价和利润安全线",
      reason: "活动测试进入确认期，需确认 ROI、退款率和库存承接。",
      status: "待确认",
      manualOrder: 3,
    },
    {
      id: "A004",
      priority: "中",
      priorityLevel: "warning",
      deadline: "明天 12:00 前",
      timeBucket: "明天前",
      source: "商品触发",
      sourceModule: "商品经营列表",
      sourceRoute: "business-products",
      todoRoute: "business-actions",
      productRoute: "business-products",
      productId: "P004",
      entityType: "商品",
      entityId: "P004",
      riskDomain: "库存",
      actionType: "复查",
      imageLabel: "盒",
      taskType: "库存承接",
      taskSignal: "确认补货周期",
      productShort: "收纳盒",
      productTitle: "透明收纳盒衣柜整理箱家用大容量防尘款",
      title: "透明收纳盒衣柜整理箱家用大容量防尘款",
      platform: "淘宝",
      store: "家居生活主店",
      link: "https://shop.example.com/products/P004",
      judgmentTags: ["库存低", "活动流量", "谨慎放量"],
      task: "确认补货周期，再决定是否继续活动流量",
      reason: "库存 46，接近安全线；活动流量 ROI 1.3，可谨慎放量。",
      status: "待确认",
      manualOrder: 4,
    },
    {
      id: "A005",
      priority: "中",
      priorityLevel: "warning",
      deadline: "明天 18:00 前",
      timeBucket: "明天前",
      source: "竞品触发",
      sourceModule: "竞品观察列表",
      sourceRoute: "business-competitors",
      todoRoute: "business-actions",
      productRoute: "business-products",
      productId: "P002",
      entityType: "商品",
      entityId: "P002",
      riskDomain: "上新",
      actionType: "测试",
      imageLabel: "装",
      taskType: "竞品机会",
      taskSignal: "确认测试版本",
      productShort: "厨房置物架",
      productTitle: "厨房置物架：新增安装说明图 + 尺寸参照图版本",
      title: "厨房置物架：新增安装说明图 + 尺寸参照图版本",
      platform: "拼多多",
      store: "家居百货店",
      link: "https://shop.example.com/products/P002",
      judgmentTags: ["安装差评", "尺寸差评", "可转上新"],
      task: "生成详情页测试版本并加入上新测试",
      reason: "竞品差评集中在安装困难 / 尺寸不符，可转为测试动作。",
      status: "待确认",
      manualOrder: 5,
    },
    {
      id: "A006",
      priority: "中",
      priorityLevel: "warning",
      deadline: "3 天后复盘",
      timeBucket: "本周内",
      source: "上新触发",
      sourceModule: "上新测试台",
      sourceRoute: "business-listing",
      todoRoute: "business-actions",
      productRoute: "business-products",
      productId: "P004",
      entityType: "商品",
      entityId: "P004",
      riskDomain: "上新",
      actionType: "复盘",
      imageLabel: "盒",
      taskType: "SKU 复盘",
      taskSignal: "复盘测试结果",
      productShort: "收纳盒",
      productTitle: "透明收纳盒衣柜整理箱家用大容量防尘款",
      title: "透明收纳盒衣柜整理箱家用大容量防尘款",
      platform: "淘宝",
      store: "家居生活主店",
      link: "https://shop.example.com/products/P004",
      judgmentTags: ["SKU 测试", "库存占用", "转化复盘"],
      task: "复盘 SKU 基础款 / 加厚款 / 组合款测试",
      reason: "组合款会占用库存，需观察转化率和库存承接。",
      status: "处理中",
      manualOrder: 6,
    },
    {
      id: "A007",
      priority: "低",
      priorityLevel: "good",
      deadline: "本周内",
      timeBucket: "本周内",
      source: "报表触发",
      sourceModule: "ERP / CRM 报表管理",
      sourceRoute: "data-check",
      todoRoute: "business-actions",
      productRoute: "data-check",
      productId: "R001",
      entityType: "报表",
      entityId: "refunds",
      riskDomain: "报表",
      actionType: "导入",
      imageLabel: "表",
      taskType: "报表补齐",
      taskSignal: "导入退款报表",
      productShort: "退款报表",
      productTitle: "退款报表与商品报表同步检查",
      title: "退款报表与商品报表同步检查",
      platform: "ERP / CRM",
      store: "家居生活店铺组",
      link: "#data-check",
      judgmentTags: ["数据缺口", "售后归因", "复盘需要"],
      task: "导入最新退款报表，生成本轮复盘摘要",
      reason: "流量测试和售后归因需要最新退款原因数据。",
      status: "待确认",
      manualOrder: 7,
    },
  ];

  const seedLogs = [
    { id: "G001", time: "16:08", type: "任务进入池", source: "流量触发", status: "已加入任务池", level: "danger", imageLabel: "架", title: "厨房置物架免打孔收纳架壁挂多层家用置物架", platform: "拼多多", store: "家居百货店", productId: "P002", action: "搜索推广测试进入统一任务池", reason: "ROI 1.1，退款率 6.8%，安装和尺寸咨询偏高。", result: "进入售后归因，暂不继续放大推广预算。", route: "business-traffic", taskRoute: "business-actions", createdAt: new Date().toISOString() },
    { id: "G002", time: "15:47", type: "用户操作", source: "上新触发", status: "已确认测试", level: "warning", imageLabel: "伞", title: "遮阳伞户外便携防晒防紫外线晴雨两用", platform: "淘宝", store: "家居生活主店", productId: "P001", action: "确认平台券活动价测试", reason: "活动测试进入确认期，需要同时观察 ROI、退款率和库存承接。", result: "进入待办执行队列，今天 20:00 前完成首轮观察。", route: "business-listing", taskRoute: "business-actions", createdAt: new Date().toISOString() },
    { id: "G003", time: "15:35", type: "AI 判定", source: "商品触发", status: "异常提醒", level: "danger", imageLabel: "垫", title: "护腰坐垫久坐办公室靠垫人体工学支撑款", platform: "抖音小店", store: "家居好物号", productId: "P003", action: "识别售后敏感商品", reason: "推荐流量 ROI 0.9，退款率 8.4%，材质和支撑感反馈集中。", result: "生成暂停投放和商品复查任务。", route: "business-products", taskRoute: "business-actions", createdAt: new Date().toISOString() },
  ];

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

  function nowTime() {
    const d = new Date();
    return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
  }

  function makeId(prefix) {
    return `${prefix}${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`.toUpperCase();
  }

  function normalizeDomain(value) {
    return String(value || "").trim() || "通用";
  }

  function inferRiskDomain(task) {
    const text = [task.riskDomain, task.taskType, task.taskSignal, task.task, task.reason, ...(task.judgmentTags || [])].join(" ");
    if (/售后|退款|材质|尺寸|安装|客服/.test(text)) return "售后";
    if (/库存|补货|承接/.test(text)) return "库存";
    if (/流量|ROI|投放|推广|点击|转化/.test(text)) return "流量";
    if (/上新|主图|标题|SKU|测试版本|详情页/.test(text)) return "上新";
    if (/价格|活动价|利润|券/.test(text)) return "价格";
    if (/报表|导入|同步|数据/.test(text)) return "报表";
    return "通用";
  }

  function inferActionType(task) {
    const text = [task.actionType, task.taskType, task.taskSignal, task.task].join(" ");
    if (/复盘/.test(text)) return "复盘";
    if (/测试|版本|上新/.test(text)) return "测试";
    if (/导入|同步/.test(text)) return "导入";
    if (/观察/.test(text)) return "观察";
    if (/确认/.test(text)) return "确认";
    return "复查";
  }

  function buildDedupeKey(input = {}) {
    if (input.dedupeKey) return input.dedupeKey;
    const entityType = normalizeDomain(input.entityType || (String(input.productId || "").startsWith("R") ? "报表" : "商品"));
    const entityId = normalizeDomain(input.entityId || input.productId || input.sourceEvent || input.id || "unknown");
    const riskDomain = normalizeDomain(input.riskDomain || inferRiskDomain(input));
    const actionType = normalizeDomain(input.actionType || inferActionType(input));
    return `${entityType}:${entityId}:${riskDomain}:${actionType}`;
  }

  function normalizeTask(task) {
    const priority = task.priority || "中";
    const createdAt = task.createdAt || new Date().toISOString();
    const id = task.id || makeId("A");
    const normalized = {
      todoRoute: "business-actions",
      productRoute: task.productRoute || task.sourceRoute || "business-products",
      logRoute: "business-report",
      status: "待确认",
      judgmentTags: [],
      sourceTrail: [],
      actions: ["确认处理", "继续观察", "拒绝"],
      ...task,
      id,
      priority,
      priorityLevel: task.priorityLevel || (priority === "高" ? "danger" : priority === "中" ? "warning" : "good"),
      title: task.title || task.productTitle || task.task || task.taskType || "经营任务",
      productTitle: task.productTitle || task.title || "经营任务",
      productShort: task.productShort || task.shortName || task.sourceName || task.productId || "任务",
      timeBucket: task.timeBucket || task.deadline || "本周内",
      entityType: task.entityType || (String(task.productId || "").startsWith("R") ? "报表" : "商品"),
      entityId: task.entityId || task.productId || id,
      riskDomain: task.riskDomain || inferRiskDomain(task),
      actionType: task.actionType || inferActionType(task),
      createdAt,
      updatedAt: task.updatedAt || createdAt,
      manualOrder: Number.isFinite(task.manualOrder) ? task.manualOrder : Date.now(),
    };
    normalized.dedupeKey = buildDedupeKey(normalized);
    normalized.sourceTrail = Array.from(new Set([...(normalized.sourceTrail || []), normalized.sourceModule || normalized.source || "系统"].filter(Boolean)));
    return normalized;
  }

  function sortTasks(tasks) {
    return [...tasks].sort((a, b) => {
      const pr = (priorityRank[a.priority] || 9) - (priorityRank[b.priority] || 9);
      if (pr) return pr;
      const order = (a.manualOrder || 9999) - (b.manualOrder || 9999);
      if (order) return order;
      return new Date(a.createdAt || 0) - new Date(b.createdAt || 0);
    });
  }

  function getTasks() {
    return read(TASK_KEY, seedTasks.map(normalizeTask)).map(normalizeTask);
  }

  function setTasks(tasks) {
    write(TASK_KEY, tasks.map(normalizeTask));
  }

  function getLogs() {
    return read(LOG_KEY, seedLogs);
  }

  function setLogs(logs) {
    write(LOG_KEY, logs);
  }

  function notify() {
    window.dispatchEvent(new CustomEvent("operation-task-store-change"));
  }

  function toLog(input) {
    const task = input.task || {};
    return {
      id: input.id || makeId("G"),
      time: input.time || nowTime(),
      type: input.type || "任务记录",
      source: input.source || task.source || task.sourceModule || "系统",
      status: input.status || task.status || "已记录",
      level: input.level || task.priorityLevel || "good",
      imageLabel: input.imageLabel || task.imageLabel || "记",
      title: input.title || task.title || task.productTitle || input.message || "任务记录",
      platform: input.platform || task.platform || "经营单元",
      store: input.store || task.store || "任务池",
      productId: input.productId || task.productId || task.id || "TASK",
      action: input.action || input.message || "任务池动作",
      reason: input.reason || task.reason || "来自统一任务池。",
      result: input.result || "已写入日志。",
      route: input.route || task.sourceRoute || "dashboard",
      taskRoute: input.taskRoute || "business-actions",
      createdAt: input.createdAt || new Date().toISOString(),
    };
  }

  function createLog(input) {
    const logs = getLogs();
    const log = toLog(input);
    logs.unshift(log);
    setLogs(logs.slice(0, 200));
    notify();
    return log;
  }

  function findOpenTask(input) {
    const key = typeof input === "string" ? input : buildDedupeKey(input || {});
    return getTasks().find((item) => item.dedupeKey === key && !statusDone.has(item.status));
  }

  function mergeDuplicateTask(existing, incoming) {
    const tasks = getTasks();
    const index = tasks.findIndex((item) => item.id === existing.id);
    if (index < 0) return existing;
    const mergedTags = Array.from(new Set([...(existing.judgmentTags || []), ...(incoming.judgmentTags || [])].filter(Boolean))).slice(0, 8);
    const mergedTrail = Array.from(new Set([...(existing.sourceTrail || []), incoming.sourceModule || incoming.source || "手动加入"].filter(Boolean)));
    const merged = normalizeTask({
      ...existing,
      judgmentTags: mergedTags,
      sourceTrail: mergedTrail,
      updatedAt: new Date().toISOString(),
      mergeCount: (existing.mergeCount || 0) + 1,
    });
    tasks[index] = merged;
    setTasks(tasks);
    createLog({
      type: "任务合并",
      task: merged,
      status: "已合并",
      action: `${incoming.sourceModule || incoming.source || "模块"} 重复加入：已合并到现有任务`,
      reason: `去重键：${merged.dedupeKey}`,
      result: "没有创建重复任务，已补充来源和判断标签。",
    });
    notify();
    return merged;
  }

  function createTask(taskInput) {
    const tasks = getTasks();
    const task = normalizeTask(taskInput);
    const duplicate = tasks.find((item) => item.dedupeKey === task.dedupeKey && !statusDone.has(item.status));
    if (duplicate) {
      const merged = mergeDuplicateTask(duplicate, task);
      merged.dedupeHit = true;
      return merged;
    }
    tasks.push(task);
    setTasks(tasks);
    createLog({ type: "任务创建", task, status: "已加入任务池", action: `${task.sourceModule || task.source || "模块"} 创建任务：${task.taskType || task.task || task.title}`, result: "已同步到首页、待办和日志。" });
    notify();
    task.dedupeHit = false;
    return task;
  }

  function updateTask(taskId, patch, logOptions = {}) {
    const tasks = getTasks();
    const index = tasks.findIndex((task) => task.id === taskId);
    if (index < 0) return null;
    const task = normalizeTask({ ...tasks[index], ...patch, updatedAt: new Date().toISOString() });
    tasks[index] = task;
    setTasks(tasks);
    createLog({ type: logOptions.type || "任务更新", task, status: task.status, action: logOptions.action || `${task.taskType || task.title} 已更新`, result: logOptions.result || "任务状态已同步。" });
    notify();
    return task;
  }

  function completeTask(taskId) {
    return updateTask(taskId, { status: "已完成", completedAt: new Date().toISOString() }, { type: "任务完成", action: "任务已完成", result: "首页移除该任务，日志保留处理记录。" });
  }

  function pinTask(taskId) {
    const tasks = getTasks();
    const minOrder = Math.min(...tasks.map((task) => task.manualOrder || 9999), 0);
    return updateTask(taskId, { manualOrder: minOrder - 1 }, { type: "任务置顶", action: "任务已置顶", result: "首页和待办同步排序。" });
  }

  function reorderTask(taskId, direction) {
    const tasks = sortTasks(getTasks().filter((task) => !statusDone.has(task.status)));
    const index = tasks.findIndex((task) => task.id === taskId);
    const targetIndex = direction === "up" ? index - 1 : index + 1;
    if (index < 0 || targetIndex < 0 || targetIndex >= tasks.length) return null;
    const current = tasks[index];
    const target = tasks[targetIndex];
    const currentOrder = current.manualOrder || index + 1;
    const targetOrder = target.manualOrder || targetIndex + 1;
    updateTask(current.id, { manualOrder: targetOrder }, { type: "任务排序", action: "任务顺序已调整", result: "首页和待办同步排序。" });
    updateTask(target.id, { manualOrder: currentOrder }, { type: "任务排序", action: "相邻任务顺序已交换", result: "排序变更已写入日志。" });
    return current;
  }

  function resetDemoData() {
    setTasks(seedTasks.map(normalizeTask));
    setLogs(seedLogs);
    createLog({ type: "演示重置", status: "已重置", action: "统一任务池已恢复默认演示数据", result: "首页、待办、日志已同步刷新。" });
    notify();
  }

  if (!localStorage.getItem(BOOT_KEY)) {
    setTasks(seedTasks.map(normalizeTask));
    setLogs(seedLogs);
    localStorage.setItem(BOOT_KEY, "1");
  }

  window.OPERATION_TASK_STORE = {
    listTasks: () => sortTasks(getTasks()),
    listActiveTasks: () => sortTasks(getTasks().filter((task) => !statusDone.has(task.status))),
    listDashboardTasks: () => sortTasks(getTasks().filter((task) => !statusDone.has(task.status))).slice(0, 5),
    createTask,
    updateTask,
    completeTask,
    pinTask,
    reorderTask,
    findOpenTask,
    buildDedupeKey,
    listLogs: () => getLogs(),
    createLog,
    subscribe(listener) {
      window.addEventListener("operation-task-store-change", listener);
      return () => window.removeEventListener("operation-task-store-change", listener);
    },
    resetDemoData,
    priorityRank,
  };
})();
