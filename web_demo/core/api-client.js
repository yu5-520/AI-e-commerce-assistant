(function () {
  const status = { source: "unknown", failures: [] };

  function failureSummary() {
    if (!status.failures.length) return "所有模块接口请求正常。";
    return status.failures.slice(-5).map((item) => `${item.path}: ${item.message}`).join("\n");
  }

  async function request(path, fallback, options = {}) {
    try {
      const response = await fetch(path, {
        method: options.method || "GET",
        headers: { Accept: "application/json", "Content-Type": "application/json" },
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

  const api = {
    status,
    failureSummary,
    dashboard: () => request("/api/modules/dashboard", null),
    operatingUnit: () => request("/api/modules/operating-unit", null),
    product: () => request("/api/modules/product", window.AppMockData.products),
    competitor: () => request("/api/modules/competitor", window.AppMockData.competitors),
    listing: () => request("/api/modules/listing", window.AppMockData.listings),
    traffic: () => request("/api/modules/traffic", window.AppMockData.traffic),
    report: () => request("/api/modules/report", { reportGroups: window.AppMockData.reportGroups, reportDetails: window.AppMockData.reportDetails }),
    todo: () => request("/api/modules/todo", { tasks: window.AppTaskStore?.listTasks?.() || [], activeTasks: window.AppTaskStore?.listActiveTasks?.() || [] }),
    log: () => request("/api/modules/log", window.AppTaskStore?.listLogs?.() || []),
    post: (path, fallback, body) => request(path, fallback, { method: "POST", body }),
    createProductTask: (id) => api.post(`/api/modules/product/${id}/tasks`, null),
    createCompetitorTask: (id) => api.post(`/api/modules/competitor/${id}/tasks`, null),
    createListingTask: (id) => api.post(`/api/modules/listing/${id}/tasks`, null),
    createTrafficTask: (id) => api.post(`/api/modules/traffic/${id}/tasks`, null),
    createReportTask: (id) => api.post(`/api/modules/report/${id}/tasks`, null),
    completeTodo: (id) => api.post(`/api/modules/todo/${id}/complete`, null),
    pinTodo: (id) => api.post(`/api/modules/todo/${id}/pin`, null),
    reorderTodo: (id, direction) => api.post(`/api/modules/todo/${id}/reorder?direction=${encodeURIComponent(direction)}`, null),
    resetTodo: () => api.post("/api/modules/todo/reset", null),
    applyModuleData({ products, competitors, listings, traffic, report } = {}) {
      if (Array.isArray(products)) window.AppMockData.products = products;
      if (Array.isArray(competitors)) window.AppMockData.competitors = competitors;
      if (Array.isArray(listings)) window.AppMockData.listings = listings;
      if (Array.isArray(traffic)) window.AppMockData.traffic = traffic;
      if (report?.reportGroups) window.AppMockData.reportGroups = report.reportGroups;
      if (report?.reportDetails) window.AppMockData.reportDetails = report.reportDetails;
    },
    async refreshModuleData() {
      const [products, competitors, listings, traffic, report] = await Promise.all([
        api.product(),
        api.competitor(),
        api.listing(),
        api.traffic(),
        api.report(),
      ]);
      api.applyModuleData({ products, competitors, listings, traffic, report });
      return window.AppMockData;
    },
    async refreshTaskState() {
      const [todo, logs] = await Promise.all([api.todo(), api.log()]);
      window.AppTaskStore?.hydrate?.(todo?.tasks || [], Array.isArray(logs) ? logs : []);
      await api.refreshModuleData();
      return { todo, logs };
    },
    async prefetch() {
      const [products, competitors, listings, traffic, report, todo, logs] = await Promise.all([
        api.product(),
        api.competitor(),
        api.listing(),
        api.traffic(),
        api.report(),
        api.todo(),
        api.log(),
      ]);
      api.applyModuleData({ products, competitors, listings, traffic, report });
      window.AppTaskStore?.hydrate?.(todo?.tasks || [], Array.isArray(logs) ? logs : []);
      return window.AppMockData;
    },
  };

  window.AppApi = api;
})();
