(function () {
  const ACCOUNT_KEY = "ai_ecommerce_v237_current_user_id";
  const status = { source: "unknown", failures: [] };
  let account = null;

  function getCurrentUserId() {
    return localStorage.getItem(ACCOUNT_KEY) || "U001";
  }

  function setCurrentUserId(userId) {
    localStorage.setItem(ACCOUNT_KEY, userId || "U001");
  }

  function currentUser() {
    return account?.currentUser || null;
  }

  function currentPermissions() {
    return currentUser()?.permissions || [];
  }

  function can(permission) {
    return currentPermissions().includes(permission);
  }

  function failureSummary() {
    if (!status.failures.length) return "所有模块接口请求正常。";
    return status.failures.slice(-5).map((item) => `${item.path}: ${item.message}`).join("\n");
  }

  async function request(path, fallback, options = {}) {
    try {
      const response = await fetch(path, {
        method: options.method || "GET",
        headers: { Accept: "application/json", "Content-Type": "application/json", "X-Mock-User-Id": getCurrentUserId() },
        body: options.body ? JSON.stringify(options.body) : undefined,
      });
      if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
      if (status.source !== "fallback") status.source = "server";
      return await response.json();
    } catch (error) {
      status.source = "fallback";
      status.failures.push({ path, message: error.message, at: Date.now() });
      console.warn(`[api-client] fallback for ${path}`, error);
      return fallback;
    }
  }

  async function loadAccount() { account = await request("/api/accounts", account); return account; }
  async function applyAccountMutation(path, body) { const result = await request(path, null, { method: "POST", body }); account = result?.account || (await loadAccount()); window.dispatchEvent(new CustomEvent("mock-account-change", { detail: { account } })); return result; }

  const api = {
    status, failureSummary, getCurrentUserId, setCurrentUserId, currentUser, currentPermissions, can,
    dashboard: () => request("/api/modules/dashboard", null),
    operatingUnit: () => request("/api/modules/operating-unit", null),
    accounts: loadAccount,
    me: () => request("/api/accounts/me", null),
    switchAccount: async (userId) => { setCurrentUserId(userId); const switched = await request("/api/accounts/switch", null, { method: "POST", body: { userId } }); account = switched?.account || (await loadAccount()); window.dispatchEvent(new CustomEvent("mock-account-change", { detail: { account } })); return account; },
    updateUserRole: (userId, roleId) => applyAccountMutation(`/api/accounts/users/${encodeURIComponent(userId)}/role`, { roleId }),
    updateUserStores: (userId, storeIds) => applyAccountMutation(`/api/accounts/users/${encodeURIComponent(userId)}/stores`, { storeIds }),
    updateRolePermissions: (roleId, permissions) => applyAccountMutation(`/api/accounts/roles/${encodeURIComponent(roleId)}/permissions`, { permissions }),
    product: () => request("/api/modules/product", window.AppMockData.products),
    competitor: () => request("/api/modules/competitor", window.AppMockData.competitors),
    listing: () => request("/api/modules/listing", window.AppMockData.listings),
    traffic: () => request("/api/modules/traffic", window.AppMockData.traffic),
    report: () => request("/api/modules/report", { reportGroups: window.AppMockData.reportGroups, reportDetails: window.AppMockData.reportDetails }),
    todo: (params = {}) => { const query = new URLSearchParams(); if (params.scope) query.set("scope", params.scope); if (params.assigneeId) query.set("assignee_id", params.assigneeId); const suffix = query.toString() ? `?${query.toString()}` : ""; return request(`/api/modules/todo${suffix}`, { tasks: window.AppTaskStore?.listTasks?.() || [], activeTasks: window.AppTaskStore?.listActiveTasks?.() || [], viewer: currentUser() }); },
    log: () => request("/api/modules/log", window.AppTaskStore?.listLogs?.() || []),
    taskReport: (id) => request(`/api/modules/task-reports/tasks/${encodeURIComponent(id)}`, null),
    candidateReport: (module, id) => request(`/api/modules/task-reports/candidates/${encodeURIComponent(module)}/${encodeURIComponent(id)}`, null),
    post: (path, fallback, body) => request(path, fallback, { method: "POST", body }),
    createProductTask: (id) => api.post(`/api/modules/product/${id}/tasks`, null),
    createCompetitorTask: (id) => api.post(`/api/modules/competitor/${id}/tasks`, null),
    createListingTask: (id) => api.post(`/api/modules/listing/${id}/tasks`, null),
    createTrafficTask: (id) => api.post(`/api/modules/traffic/${id}/tasks`, null),
    createReportTask: (id) => api.post(`/api/modules/report/${id}/tasks`, null),
    assignTodo: (id, body = {}) => api.post(`/api/modules/todo/${id}/assign`, null, body),
    submitTodo: (id, body = {}) => api.post(`/api/modules/todo/${id}/submit`, null, body),
    reviewTodo: (id, body = {}) => api.post(`/api/modules/todo/${id}/review`, null, body),
    completeTodo: (id) => api.post(`/api/modules/todo/${id}/complete`, null),
    pinTodo: (id) => api.post(`/api/modules/todo/${id}/pin`, null),
    reorderTodo: (id, direction) => api.post(`/api/modules/todo/${id}/reorder?direction=${encodeURIComponent(direction)}`, null),
    resetTodo: () => api.post("/api/modules/todo/reset", null),
    applyModuleData({ products, competitors, listings, traffic, report } = {}) { if (Array.isArray(products)) window.AppMockData.products = products; if (Array.isArray(competitors)) window.AppMockData.competitors = competitors; if (Array.isArray(listings)) window.AppMockData.listings = listings; if (Array.isArray(traffic)) window.AppMockData.traffic = traffic; if (report?.reportGroups) window.AppMockData.reportGroups = report.reportGroups; if (report?.reportDetails) window.AppMockData.reportDetails = report.reportDetails; },
    async refreshModuleData() { const [products, competitors, listings, traffic, report] = await Promise.all([api.product(), api.competitor(), api.listing(), api.traffic(), api.report()]); api.applyModuleData({ products, competitors, listings, traffic, report }); return window.AppMockData; },
    async refreshTaskState() { const [todo, logs] = await Promise.all([api.todo(), api.log()]); window.AppTaskStore?.hydrate?.(todo?.tasks || [], Array.isArray(logs) ? logs : []); await api.refreshModuleData(); return { todo, logs }; },
    async prefetch() { await loadAccount(); const [products, competitors, listings, traffic, report, todo, logs] = await Promise.all([api.product(), api.competitor(), api.listing(), api.traffic(), api.report(), api.todo(), api.log()]); api.applyModuleData({ products, competitors, listings, traffic, report }); window.AppTaskStore?.hydrate?.(todo?.tasks || [], Array.isArray(logs) ? logs : []); return window.AppMockData; },
  };
  window.AppApi = api;
})();