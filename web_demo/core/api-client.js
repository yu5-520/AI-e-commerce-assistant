(function () {
  async function request(path, fallback) {
    try {
      const response = await fetch(path, { headers: { Accept: "application/json" } });
      if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
      return await response.json();
    } catch (error) {
      console.warn(`[api-client] fallback for ${path}`, error);
      return fallback;
    }
  }

  const api = {
    dashboard: () => request("/api/modules/dashboard", null),
    operatingUnit: () => request("/api/modules/operating-unit", null),
    product: () => request("/api/modules/product", window.AppMockData.products),
    competitor: () => request("/api/modules/competitor", window.AppMockData.competitors),
    listing: () => request("/api/modules/listing", window.AppMockData.listings),
    traffic: () => request("/api/modules/traffic", window.AppMockData.traffic),
    report: () => request("/api/modules/report", { reportGroups: window.AppMockData.reportGroups, reportDetails: window.AppMockData.reportDetails }),
    todo: () => request("/api/modules/todo", null),
    log: () => request("/api/modules/log", []),
    async prefetch() {
      const [products, competitors, listings, traffic, report] = await Promise.all([
        api.product(),
        api.competitor(),
        api.listing(),
        api.traffic(),
        api.report(),
      ]);
      if (Array.isArray(products)) window.AppMockData.products = products;
      if (Array.isArray(competitors)) window.AppMockData.competitors = competitors;
      if (Array.isArray(listings)) window.AppMockData.listings = listings;
      if (Array.isArray(traffic)) window.AppMockData.traffic = traffic;
      if (report?.reportGroups) window.AppMockData.reportGroups = report.reportGroups;
      if (report?.reportDetails) window.AppMockData.reportDetails = report.reportDetails;
      return window.AppMockData;
    },
  };

  window.AppApi = api;
})();
