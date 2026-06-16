(async function () {
  const pages = [
    window.DashboardPage,
    window.OperatingUnitPage,
    window.ReportPage,
    window.ProductPage,
    window.CompetitorPage,
    window.ListingPage,
    window.TrafficPage,
    window.TodoPage,
    window.LogPage,
    window.TaskReportPage,
  ];

  pages.forEach((page) => AppRouter.register(page));

  if (window.AppApi?.prefetch) {
    await window.AppApi.prefetch();
    const badge = document.getElementById("apiModeBadge");
    if (badge) {
      const usingServer = window.AppApi.status.source === "server";
      badge.textContent = usingServer ? "服务端接口" : "本地兜底";
      badge.title = window.AppApi.failureSummary?.() || "接口状态未知";
      badge.classList.toggle("warning", !usingServer);
    }
  }

  AppRouter.start();
})();
