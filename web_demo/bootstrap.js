(function () {
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
  AppRouter.start();
})();
