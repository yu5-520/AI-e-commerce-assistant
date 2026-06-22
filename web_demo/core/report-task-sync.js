(function () {
  if (!window.AppApi) return;
  const api = window.AppApi;
  const originalConfirm = api.confirmReportImport;
  const originalMockAlerts = api.importMockAlerts;
  const userId = () => api.getCurrentUserId?.() || "U001";

  async function syncReportTasks() {
    try {
      const response = await fetch("/api/data/report-tasks/sync-current", {
        method: "POST",
        headers: { Accept: "application/json", "Content-Type": "application/json", "X-Mock-User-Id": userId() },
        body: JSON.stringify({ source: "report_ui_auto_sync" }),
      });
      if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
      return await response.json();
    } catch (error) {
      console.warn("[report-task-sync] sync fallback", error);
      return { version: "5.1.6", mode: "report_task_sync_failed", syncedTaskCount: 0, error: error.message };
    }
  }

  api.syncReportTasks = syncReportTasks;

  api.confirmReportImport = async function (...args) {
    const result = await originalConfirm.apply(api, args);
    const sync = await syncReportTasks();
    return { ...(result || {}), taskRepositorySync: sync };
  };

  api.importMockAlerts = async function (...args) {
    const result = await originalMockAlerts.apply(api, args);
    const sync = await syncReportTasks();
    return { ...(result || {}), taskRepositorySync: sync };
  };
})();
