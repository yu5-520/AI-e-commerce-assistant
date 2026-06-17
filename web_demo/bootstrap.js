(async function () {
  const MANAGER_NAV = [
    "dashboard",
    "manager-tasks",
    "manager-dispatch",
    "manager-review",
    "manager-modules",
    "manager-retrospective",
    "manager-reports",
    "operating-unit",
    "business-report",
    "accounts",
  ];

  function loadStyle(href) {
    return new Promise((resolve) => {
      if ([...document.styleSheets].some((sheet) => sheet.href && sheet.href.includes(href.split("?")[0]))) return resolve();
      const link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = href;
      link.onload = resolve;
      link.onerror = resolve;
      document.head.appendChild(link);
    });
  }

  function loadScript(src) {
    return new Promise((resolve) => {
      if (document.querySelector(`script[src^="${src.split("?")[0]}"]`)) return resolve();
      const script = document.createElement("script");
      script.src = src;
      script.onload = resolve;
      script.onerror = resolve;
      document.body.appendChild(script);
    });
  }

  function visibleModulesFor(account) {
    const role = account?.currentUser?.roleId;
    if (role === "manager") return MANAGER_NAV;
    return account?.currentUser?.visibleModules || [];
  }

  await loadStyle("/web_demo/minimal-ui.css?v=3.0.8");
  await loadStyle("/web_demo/manager-module-hub.css?v=3.0.8");
  await loadStyle("/web_demo/alert-report.css?v=3.0.8");
  await loadStyle("/web_demo/task-evidence.css?v=3.0.8");
  await loadScript("/web_demo/modules/executive/org-responsibility-v304.js?v=3.0.8");
  await loadScript("/web_demo/modules/manager/manager-modules-v305.js?v=3.0.8");

  const pages = [
    window.DashboardPage,
    window.StoreOverviewPage,
    window.TaskCommandPage,
    window.ProfitBudgetPage,
    window.OrgEfficiencyPage,
    window.ReviewAuditPage,
    window.AccountPage,
    window.RoleConsolePage,
    window.ManagerTasksPage,
    window.ManagerDispatchPage,
    window.ManagerReviewPage,
    window.ManagerTaskDetailPage,
    window.ManagerModulesPage,
    window.ManagerRetrospectivePage,
    window.ManagerReportsPage,
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

  pages.filter(Boolean).forEach((page) => AppRouter.register(page));

  function applyNavigationScope(account) {
    const visible = new Set(visibleModulesFor(account));
    document.querySelectorAll(".nav a[data-route]").forEach((link) => {
      const allowed = !visible.size || visible.has(link.dataset.route);
      link.hidden = !allowed;
    });
  }

  function renderAccountSwitcher(account) {
    const select = document.getElementById("accountSwitcher");
    if (!select || !account?.users) return;
    const currentId = account.currentUser?.id || AppApi.getCurrentUserId();
    select.innerHTML = account.users
      .map((user) => `<option value="${AppShell.escape(user.id)}" ${user.id === currentId ? "selected" : ""}>${AppShell.escape(user.name)} · ${AppShell.escape(user.roleName)}</option>`)
      .join("");
    applyNavigationScope(account);
    select.onchange = async () => {
      select.disabled = true;
      await AppApi.switchAccount(select.value);
      await AppApi.prefetch();
      const nextAccount = await AppApi.accounts();
      renderAccountSwitcher(nextAccount);
      const active = location.hash.replace("#", "") || "dashboard";
      const allowed = new Set(visibleModulesFor(nextAccount));
      if (allowed.size && !allowed.has(active)) AppRouter.navigate("dashboard");
      else AppRouter.schedule("account-switch");
      select.disabled = false;
    };
  }

  if (window.AppApi?.prefetch) {
    await window.AppApi.prefetch();
    renderAccountSwitcher(await window.AppApi.accounts());
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
