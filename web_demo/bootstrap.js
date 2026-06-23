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
    "data-check",
    "trend-center",
    "feedback-flywheel",
    "business-report",
    "system-status",
    "accounts",
  ];

  const FEEDBACK_ROLES = new Set(["owner", "manager"]);
  const SYSTEM_STATUS_ROLES = new Set(["owner", "manager"]);
  const TREND_ROLES = new Set(["owner", "manager", "operator", "finance"]);

  function visibleModulesFor(account) {
    const role = account?.currentUser?.roleId;
    const base = role === "manager" ? MANAGER_NAV : (account?.currentUser?.visibleModules || []);
    const next = [...base];
    if (TREND_ROLES.has(role)) next.push("trend-center");
    if (FEEDBACK_ROLES.has(role)) next.push("feedback-flywheel");
    if (SYSTEM_STATUS_ROLES.has(role)) next.push("system-status");
    return Array.from(new Set(next));
  }

  const pages = [
    window.DashboardPage,
    window.StoreOverviewPage,
    window.TaskCommandPage,
    window.ProfitBudgetPage,
    window.OrgEfficiencyPage,
    window.ReviewAuditPage,
    window.AccountPage,
    window.RoleConsolePage,
    window.SystemStatusPage,
    window.ManagerTasksPage,
    window.ManagerDispatchPage,
    window.ManagerReviewPage,
    window.ManagerTaskDetailPage,
    window.ManagerModulesPage,
    window.ManagerRetrospectivePage,
    window.ManagerReportsPage,
    window.OperatingUnitPage,
    window.ReportPage,
    window.DataVersionDetailPage,
    window.TrendCenterPage,
    window.ProductPage,
    window.CompetitorPage,
    window.ListingPage,
    window.TrafficPage,
    window.InventoryCenterPage,
    window.ServiceCenterPage,
    window.TodoPage,
    window.LogPage,
    window.FeedbackFlywheelPage,
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