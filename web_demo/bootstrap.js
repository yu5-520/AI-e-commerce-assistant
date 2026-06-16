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
  ];

  pages.forEach((page) => AppRouter.register(page));

  if (window.AppApi?.prefetch) {
    await window.AppApi.prefetch();
    const badge = document.getElementById("apiModeBadge");
    if (badge) badge.textContent = "模块接口";
  }

  AppRouter.start();
})();
