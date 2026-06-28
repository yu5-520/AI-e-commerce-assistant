(function () {
  const ACCOUNT_KEY = "ai_ecommerce_v442_current_user_id";
  const status = { source: "unknown", failures: [], lastImportSync: null, lastError: null };
  let account = null;

  function getCurrentUserId() { return localStorage.getItem(ACCOUNT_KEY) || "U001"; }
  function setCurrentUserId(userId) { localStorage.setItem(ACCOUNT_KEY, userId || "U001"); }
  function currentUser() { return account?.currentUser || null; }
  function currentPermissions() { return currentUser()?.permissions || []; }
  function can(permission) { return currentPermissions().includes(permission); }
  function failureSummary() {
    if (!status.failures.length) return "所有模块接口请求正常。";
    return status.failures.slice(-5).map((item) => `${item.path}: ${item.message}`).join("\n");
  }
  function setServerHealthy(path = "") {
    status.source = "server";
    status.lastError = null;
    window.dispatchEvent(new CustomEvent("api-client-status", { detail: { source: status.source, path } }));
  }
  function recordFailure(path, error) {
    const message = error?.message || String(error || "接口异常");
    status.source = "error";
    status.lastError = { path, message, at: Date.now() };
    status.failures.push(status.lastError);
    window.dispatchEvent(new CustomEvent("api-client-error", { detail: status.lastError }));
    console.error(`[api-client] request failed for ${path}`, error);
  }
  function buildQuery(params = {}) {
    const query = new URLSearchParams();
    Object.entries(params || {}).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") query.set(key, value);
    });
    return query.toString() ? `?${query.toString()}` : "";
  }
  async function parseError(response) {
    let detail = "";
    try {
      const payload = await response.json();
      detail = payload?.detail || payload?.message || "";
    } catch (error) {
      detail = "";
    }
    return detail || `${response.status} ${response.statusText}`;
  }
  async function request(path, _fallback = null, options = {}) {
    try {
      const response = await fetch(path, {
        method: options.method || "GET",
        headers: { Accept: "application/json", "Content-Type": "application/json", "X-Mock-User-Id": getCurrentUserId() },
        body: options.body ? JSON.stringify(options.body) : undefined,
      });
      if (!response.ok) throw new Error(await parseError(response));
      setServerHealthy(path);
      return await response.json();
    } catch (error) {
      recordFailure(path, error);
      throw error;
    }
  }
  async function optionalRequest(path, fallback = {}) {
    try { return await request(path); }
    catch (error) { return { ...fallback, optionalError: error?.message || String(error || "接口异常"), optionalPath: path }; }
  }
  async function uploadRequest(path, file, fields = {}) {
    try {
      const form = new FormData();
      form.append("file", file);
      Object.entries(fields || {}).forEach(([key, value]) => form.append(key, value));
      const response = await fetch(path, { method: "POST", headers: { Accept: "application/json", "X-Mock-User-Id": getCurrentUserId() }, body: form });
      if (!response.ok) throw new Error(await parseError(response));
      setServerHealthy(path);
      return await response.json();
    } catch (error) {
      recordFailure(path, error);
      throw error;
    }
  }
  async function loadAccount() { account = await request("/api/accounts"); return account; }
  async function applyAccountMutation(path, body) {
    const result = await request(path, null, { method: "POST", body });
    account = result?.account || (await loadAccount());
    window.dispatchEvent(new CustomEvent("mock-account-change", { detail: { account } }));
    return result;
  }
  function clearViewState() { ["manager_task_state_v241", "manager_task_sort_v241", "manager_selected_task_v241", "owner_review_state", "owner_dashboard_state"].forEach((key) => localStorage.removeItem(key)); }
  function clearClientRuntime() {
    clearViewState();
    window.AppMockData.products = [];
    window.AppMockData.competitors = [];
    window.AppMockData.listings = [];
    window.AppMockData.traffic = [];
    window.AppMockData.reportGroups = [];
    window.AppMockData.reportDetails = {};
    window.AppMockData.v3 = { version: "12.8.1", activeAlertCount: 0, highPriorityAlertCount: 0, latestAlerts: [] };
    window.AppMockData.recentAlerts = [];
    status.lastImportSync = null;
    window.AppTaskStore?.hydrate?.([], [], [], {});
  }
  function rememberImportSync(result) {
    status.lastImportSync = result?.riskTaskSync || result?.v104ImportTaskSync || result?.importDiagnostics || null;
    window.dispatchEvent(new CustomEvent("v125-import-sync", { detail: { result, sync: status.lastImportSync } }));
    return result;
  }
  function productFormatters() {
    return {
      money(value) { return value === null || value === undefined || value === "" || value === "—" || value === "未识别" ? "未识别" : String(value).startsWith("¥") ? String(value) : `¥${value}`; },
      percent(value) { return value === null || value === undefined || value === "" || value === "—" || value === "未识别" ? "未识别" : String(value).includes("%") ? String(value) : `${value}%`; },
    };
  }
  function normalizeTodoPayload(payload = {}) {
    const tasks = Array.isArray(payload.tasks) ? payload.tasks : [];
    const active = Array.isArray(payload.activeTasks) ? payload.activeTasks : tasks.filter((task) => !["已完成", "已归档", "已写入复盘"].includes(task.status));
    const events = Array.isArray(payload.events) ? payload.events : [];
    const counters = payload.counters && typeof payload.counters === "object" ? payload.counters : {};
    return { tasks, activeTasks: active, events, counters, payload };
  }

  const api = {
    status, failureSummary, getCurrentUserId, setCurrentUserId, currentUser, currentPermissions, can, productFormatters,
    dashboard: () => request("/api/modules/dashboard"),
    operatingUnit: () => request("/api/modules/operating-unit"),
    accounts: loadAccount,
    me: () => request("/api/accounts/me"),
    switchAccount: async (userId) => {
      const previousUserId = getCurrentUserId();
      const switched = await request("/api/accounts/switch", null, { method: "POST", body: { userId } });
      const nextUserId = switched?.currentUser?.id || userId || previousUserId;
      setCurrentUserId(nextUserId);
      account = switched?.account || (await loadAccount());
      await api.refreshTaskState().catch(() => null);
      window.dispatchEvent(new CustomEvent("mock-account-change", { detail: { account } }));
      return account;
    },
    updateUserRole: (userId, roleId) => applyAccountMutation(`/api/accounts/users/${encodeURIComponent(userId)}/role`, { roleId }),
    updateUserStores: (userId, storeIds) => applyAccountMutation(`/api/accounts/users/${encodeURIComponent(userId)}/stores`, { storeIds }),
    updateStoreAssignment: (storeId, primaryOperatorId, reviewerId = "U002") => applyAccountMutation(`/api/accounts/store-assignments/${encodeURIComponent(storeId)}`, { primaryOperatorId, reviewerId }),
    updateRolePermissions: (roleId, permissions) => applyAccountMutation(`/api/accounts/roles/${encodeURIComponent(roleId)}/permissions`, { permissions }),
    product: (params = {}) => request(`/api/modules/product${buildQuery(params)}`),
    competitor: () => request("/api/modules/competitor"),
    listing: () => request("/api/modules/listing"),
    traffic: () => request("/api/modules/traffic"),
    report: () => request("/api/modules/report"),
    trendCenter: (limit = 30) => request(`/api/trends/summary?limit=${encodeURIComponent(limit)}`),
    metricEvidence: (body = {}) => api.post("/api/trends/metric-evidence", null, body),
    taskSop: (body = {}) => api.post("/api/trends/task-sop", null, body),
    agents: () => request("/api/modules/agents"),
    moduleAgent: (module, id, mode = "analysis") => request(`/api/modules/agents/${encodeURIComponent(module)}/${encodeURIComponent(id)}?mode=${encodeURIComponent(mode)}`),
    cycleAgent: (target = "日报") => request(`/api/modules/agents/cycle/${encodeURIComponent(target)}`),
    createAgentTask: (module, id, draftIndex = 0, mode = "analysis") => api.post(`/api/modules/agents/${encodeURIComponent(module)}/${encodeURIComponent(id)}/tasks`, null, { draftIndex, mode }),
    generateTaskCandidates: (body = {}) => api.post("/api/modules/agents/tasks/generate", null, body),
    taskPlaybook: (taskId, preferredStyle = "") => request(`/api/modules/agents/tasks/${encodeURIComponent(taskId)}/playbook${preferredStyle ? `?preferred_style=${encodeURIComponent(preferredStyle)}` : ""}`),
    creativeAgent: (productId, body = {}) => api.post(`/api/modules/agents/creative/${encodeURIComponent(productId)}`, null, body),
    createCreativeTask: (productId, body = {}) => api.post(`/api/modules/agents/creative/${encodeURIComponent(productId)}/tasks`, null, body),
    feedbackFlywheel: () => request("/api/modules/feedback-flywheel"),
    feedbackCycle: (target = "日报", limit = 8) => request(`/api/modules/feedback-flywheel/cycle/${encodeURIComponent(target)}?limit=${encodeURIComponent(limit)}`),
    draftFeedbackCycle: (target = "日报", body = {}) => api.post(`/api/modules/feedback-flywheel/cycle/${encodeURIComponent(target)}/draft`, null, body),
    ragMemory: () => request("/api/modules/rag-memory"),
    ragCases: (params = {}) => { const query = new URLSearchParams(); if (params.status) query.set("status", params.status); if (params.level) query.set("level", params.level); if (params.limit) query.set("limit", params.limit); return request(`/api/modules/rag-memory/cases${query.toString() ? `?${query.toString()}` : ""}`); },
    ragSearch: (params = {}) => { const query = new URLSearchParams(); Object.entries(params || {}).forEach(([key, value]) => { if (value !== undefined && value !== null && value !== "") query.set(key, value); }); return request(`/api/modules/rag-memory/search${query.toString() ? `?${query.toString()}` : ""}`); },
    draftTaskMemory: (taskId, body = {}) => api.post(`/api/modules/rag-memory/feedback/tasks/${encodeURIComponent(taskId)}`, null, body),
    approveRagCase: (caseId, body = {}) => api.post(`/api/modules/rag-memory/cases/${encodeURIComponent(caseId)}/approve`, null, body),
    rejectRagCase: (caseId, body = {}) => api.post(`/api/modules/rag-memory/cases/${encodeURIComponent(caseId)}/reject`, null, body),
    v3Summary: () => request("/api/data/v3-summary"),
    v3Alerts: () => request("/api/data/alerts?active_only=true"),
    reportTemplates: () => request("/api/data/templates"),
    dataSourceConnections: () => optionalRequest("/api/data/source-connections", { sources: [], degraded: true, rule: "辅助数据源接口未接通，不阻塞数据主页面。" }),
    metricFactsSummary: () => request("/api/data/metric-facts/summary"),
    dataGapSummary: () => request("/api/data/data-gaps/summary"),
    importDiagnostics: (dataVersion = "") => request(`/api/data/import-diagnostics${dataVersion ? `?dataVersion=${encodeURIComponent(dataVersion)}` : ""}`),
    previewReportRows: (datasetName, rows, fieldMapping = {}, sourceSystem = "manual") => api.post("/api/data/preview", null, { datasetName, rows, fieldMapping, sourceSystem }),
    confirmReportImport: async (datasetName, rows, fieldMapping = {}, sourceSystem = "manual") => rememberImportSync(await api.post("/api/data/import/confirm", null, { datasetName, rows, fieldMapping, sourceSystem, autoCreateTasks: true })),
    uploadReportFile: async (file, datasetName = "auto", sourceSystem = "manual_upload") => rememberImportSync(await uploadRequest("/api/data/upload/confirm", file, { dataset_name: datasetName, source_system: sourceSystem, auto_create_tasks: "true" })),
    previewUploadFile: async (file, datasetName = "auto", sourceSystem = "manual_upload") => uploadRequest("/api/data/upload/preview", file, { dataset_name: datasetName, source_system: sourceSystem }),
    importMockAlerts: async () => rememberImportSync(await api.post("/api/data/import/mock-alerts", null, {})),
    syncDataSource: async (sourceId) => rememberImportSync(await api.post(`/api/data/source-connections/${encodeURIComponent(sourceId)}/sync`, null, {})),
    importReportRows: async (datasetName, rows) => rememberImportSync(await api.post("/api/data/import/report", null, { datasetName, rows, autoCreateTasks: true })),
    dbStatus: () => request("/api/system/db-status"),
    isolation: () => request("/api/system/isolation"),
    resetRuntimeData: async (includeAuditLogs = true) => { const result = await api.post(`/api/system/reset-runtime-data?confirm=true&include_audit_logs=${includeAuditLogs ? "true" : "false"}`, null, {}); clearClientRuntime(); return result; },
    resetLegacyRuntimeOnce: () => api.post("/api/system/reset-legacy-runtime-once", null, {}),
    refreshAfterDataImport: async (result = {}) => {
      rememberImportSync(result);
      const [products, competitors, listings, traffic, report, tasks] = await Promise.all([api.product(), api.competitor(), api.listing(), api.traffic(), api.report(), api.refreshTaskState()]);
      api.applyModuleData({ products, competitors, listings, traffic, report });
      window.dispatchEvent(new CustomEvent("v125-data-refresh", { detail: { result, tasks } }));
      return { products, competitors, listings, traffic, report, tasks };
    },
    todo: (params = {}) => { const query = new URLSearchParams(); if (params.scope) query.set("scope", params.scope); if (params.assigneeId) query.set("assignee_id", params.assigneeId); const suffix = query.toString() ? `?${query.toString()}` : ""; return request(`/api/modules/todo${suffix}`); },
    todoEvents: () => request("/api/modules/todo/events"),
    todoCounters: () => request("/api/modules/todo/counters"),
    lifecycleSummary: () => request("/api/modules/todo/lifecycle/summary"),
    refreshTaskState: async (params = {}) => {
      const payload = await api.todo(params);
      const normalized = normalizeTodoPayload(payload);
      window.AppTaskStore?.hydrate?.(normalized.tasks, [], normalized.events, normalized.counters);
      window.dispatchEvent(new CustomEvent("v1281-task-state-refresh", { detail: normalized }));
      return normalized;
    },
    log: () => request("/api/modules/log"),
    recapCandidates: (target = "") => request(`/api/modules/recap-candidates${target ? `?target=${encodeURIComponent(target)}` : ""}`),
    taskReport: (id) => request(`/api/modules/task-reports/tasks/${encodeURIComponent(id)}`),
    candidateReport: (module, id) => request(`/api/modules/task-reports/candidates/${encodeURIComponent(module)}/${encodeURIComponent(id)}`),
    alertReport: (id) => request(`/api/modules/task-reports/alerts/${encodeURIComponent(id)}`),
    post: (path, _fallback, body) => request(path, null, { method: "POST", body }),
    createProductTask: (id) => api.post(`/api/modules/product/${encodeURIComponent(id)}/tasks`, null, {}),
    createCompetitorTask: (id) => api.post(`/api/modules/competitor/${encodeURIComponent(id)}/tasks`, null, {}),
    createListingTask: (id) => api.post(`/api/modules/listing/${encodeURIComponent(id)}/tasks`, null, {}),
    createTrafficTask: (id) => api.post(`/api/modules/traffic/${encodeURIComponent(id)}/tasks`, null, {}),
    createReportTask: (id) => api.post(`/api/modules/report/${encodeURIComponent(id)}/tasks`, null, {}),
    splitTodo: (id, body = {}) => api.post(`/api/modules/todo/${id}/split`, null, body),
    assignTodo: (id, body = {}) => api.post(`/api/modules/todo/${id}/assign`, null, body),
    acceptTodo: (id, body = {}) => api.post(`/api/modules/todo/${id}/accept`, null, body),
    submitTodo: (id, body = {}) => api.post(`/api/modules/todo/${id}/submit`, null, body),
    submitEvidenceTodo: (id, body = {}) => api.post(`/api/modules/todo/${id}/submit-evidence`, null, body),
    reviewTodo: (id, body = {}) => api.post(`/api/modules/todo/${id}/review`, null, body),
    reviewEvidenceTodo: (id, body = {}) => api.post(`/api/modules/todo/${id}/review-evidence`, null, body),
    taskEvidence: (id) => request(`/api/modules/todo/${encodeURIComponent(id)}/evidence`),
    writeRecapTodo: (id, body = {}) => api.post(`/api/modules/todo/${id}/recap`, null, body),
    completeRecapTodo: (id, body = {}) => api.post(`/api/modules/todo/${id}/recap/complete`, null, body),
    completeTodo: (id) => api.post(`/api/modules/todo/${id}/complete`, null, {}),
    pinTodo: (id) => api.post(`/api/modules/todo/${id}/pin`, null, {}),
    reorderTodo: (id, direction) => api.post(`/api/modules/todo/${id}/reorder?direction=${encodeURIComponent(direction)}`, null, {}),
    resetTodo: () => api.post("/api/modules/todo/reset", null, {}),
    applyModuleData({ products, competitors, listings, traffic, report } = {}) {
      window.AppMockData.products = Array.isArray(products) ? products : [];
      window.AppMockData.competitors = Array.isArray(competitors) ? competitors : [];
      window.AppMockData.listings = Array.isArray(listings) ? listings : [];
      window.AppMockData.traffic = Array.isArray(traffic) ? traffic : [];
      window.AppMockData.reportGroups = Array.isArray(report?.reportGroups) ? report.reportGroups : [];
      window.AppMockData.reportDetails = report?.reportDetails || {};
      window.AppMockData.v3 = report?.v3 || null;
    },
    prefetch: async () => {
      const [accountResult, taskState] = await Promise.all([loadAccount(), api.refreshTaskState().catch(() => null)]);
      return { account: accountResult, taskState };
    },
    runtimeDiagnostics: () => request("/api/system/runtime-diagnostics"),
    backfillOperatingObjects: () => api.post("/api/system/backfill-operating-objects", null, {}),
  };

  window.AppApi = api;
})();
