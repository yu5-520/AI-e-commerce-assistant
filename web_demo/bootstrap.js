(async function () {
  const V10_MAIN_NAV = ["dashboard", "data-check", "operating-unit", "business-actions", "business-report", "accounts", "system-status"];
  const OPERATOR_NAV = ["dashboard", "data-check", "operating-unit", "business-actions", "business-report"];
  const INTERNAL_TO_V10_NAV = new Map([
    ["store-overview", "operating-unit"],
    ["executive-cockpit", "dashboard"],
    ["people-overview", "business-actions"],
    ["task-command", "business-actions"],
    ["manager-tasks", "business-actions"],
    ["manager-dispatch", "business-actions"],
    ["manager-review", "business-actions"],
    ["manager-modules", "operating-unit"],
    ["manager-retrospective", "business-report"],
    ["manager-reports", "business-report"],
    ["business-products", "operating-unit"],
    ["business-competitors", "operating-unit"],
    ["business-listing", "operating-unit"],
    ["business-traffic", "operating-unit"],
    ["trend-center", "operating-unit"],
    ["weight-center", "operating-unit"],
    ["tenant-config", "system-status"],
    ["config-audit", "system-status"],
    ["release-governance", "system-status"],
    ["release-alerts", "system-status"],
    ["feedback-flywheel", "business-report"],
  ]);

  function compressedRoute(route) { return INTERNAL_TO_V10_NAV.get(route) || route; }

  function visibleModulesFor(account) {
    const role = account?.currentUser?.roleId;
    if (role === "operator") return OPERATOR_NAV;
    if (["owner", "manager", "finance", "observer"].includes(role)) return V10_MAIN_NAV;
    const base = account?.currentUser?.visibleModules || V10_MAIN_NAV;
    const compressed = base.map(compressedRoute).filter((route) => V10_MAIN_NAV.includes(route));
    return Array.from(new Set(compressed.length ? compressed : V10_MAIN_NAV));
  }

  const pages = [window.DashboardPage, window.StoreOverviewPage, window.TaskCommandPage, window.ProfitBudgetPage, window.OrgEfficiencyPage, window.ReviewAuditPage, window.AccountPage, window.RoleConsolePage, window.SystemStatusPage, window.TenantConfigPage, window.ConfigAuditPage, window.ReleaseGovernancePage, window.ReleaseAlertsPage, window.WeightCenterPage, window.ManagerTasksPage, window.ManagerDispatchPage, window.ManagerReviewPage, window.ManagerTaskDetailPage, window.ManagerModulesPage, window.ManagerRetrospectivePage, window.ManagerReportsPage, window.OperatingUnitPage, window.ReportPage, window.DataVersionDetailPage, window.TrendCenterPage, window.ProductPage, window.CompetitorPage, window.ListingPage, window.TrafficPage, window.InventoryCenterPage, window.ServiceCenterPage, window.TodoPage, window.LogPage, window.FeedbackFlywheelPage, window.TaskReportPage];

  pages.filter(Boolean).forEach((page) => AppRouter.register(page));

  function applyNavigationScope(account) {
    const visible = new Set(visibleModulesFor(account));
    document.querySelectorAll(".nav a[data-route]").forEach((link) => { link.hidden = !!visible.size && !visible.has(link.dataset.route); });
  }

  function renderAccountSwitcher(account) {
    const select = document.getElementById("accountSwitcher");
    if (!select || !account?.users) return;
    const currentId = account.currentUser?.id || AppApi.getCurrentUserId();
    select.innerHTML = account.users.map((user) => `<option value="${AppShell.escape(user.id)}" ${user.id === currentId ? "selected" : ""}>${AppShell.escape(user.name)} · ${AppShell.escape(user.roleName)}</option>`).join("");
    applyNavigationScope(account);
    select.onchange = async () => {
      select.disabled = true;
      await AppApi.switchAccount(select.value);
      await AppApi.prefetch();
      const nextAccount = await AppApi.accounts();
      renderAccountSwitcher(nextAccount);
      const active = compressedRoute(location.hash.replace("#", "") || "dashboard");
      const allowed = new Set(visibleModulesFor(nextAccount));
      if (allowed.size && !allowed.has(active)) AppRouter.navigate("dashboard");
      else AppRouter.schedule("account-switch");
      select.disabled = false;
    };
  }

  if (window.AppApi?.prefetch) {
    await window.AppApi.prefetch();
    renderAccountSwitcher(await AppApi.accounts());
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
