(async function () {
  const V10_MAIN_NAV = ["dashboard", "data-check", "operating-unit", "business-actions", "business-report", "accounts", "system-status"];
  const OPERATOR_NAV = ["dashboard", "data-check", "operating-unit", "business-actions", "business-report"];
  const INTERNAL_TO_V10_NAV = new Map([
    ["store-overview", "operating-unit"], ["executive-cockpit", "dashboard"], ["people-overview", "business-actions"],
    ["task-command", "business-actions"], ["manager-tasks", "business-actions"], ["manager-dispatch", "business-actions"],
    ["manager-review", "business-actions"], ["manager-modules", "operating-unit"], ["manager-retrospective", "business-report"],
    ["manager-reports", "business-report"], ["business-products", "operating-unit"], ["business-competitors", "operating-unit"],
    ["business-listing", "operating-unit"], ["business-traffic", "operating-unit"], ["trend-center", "operating-unit"],
    ["weight-center", "operating-unit"], ["tenant-config", "system-status"], ["config-audit", "system-status"],
    ["release-governance", "system-status"], ["release-alerts", "system-status"], ["feedback-flywheel", "business-report"],
    ["task-report", "business-actions"], ["task-submit", "business-actions"],
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
  function setApiBadge() {
    const badge = document.getElementById("apiModeBadge");
    if (!badge) return;
    const source = window.AppApi?.status?.source;
    const ok = source === "server";
    badge.textContent = ok ? "后端正常" : source === "unknown" ? "接口检测中" : "接口异常";
    badge.title = window.AppApi?.failureSummary?.() || "接口状态未知";
    badge.classList.toggle("warning", !ok && source !== "unknown");
  }

  const pages = [window.DashboardPage, window.StoreOverviewPage, window.TaskCommandPage, window.ProfitBudgetPage, window.OrgEfficiencyPage, window.ReviewAuditPage, window.AccountPage, window.RoleConsolePage, window.SystemStatusPage, window.TenantConfigPage, window.ConfigAuditPage, window.ReleaseGovernancePage, window.ReleaseAlertsPage, window.WeightCenterPage, window.ManagerTasksPage, window.ManagerDispatchPage, window.ManagerReviewPage, window.ManagerTaskDetailPage, window.ManagerModulesPage, window.ManagerRetrospectivePage, window.ManagerReportsPage, window.OperatingUnitPage, window.ReportPage, window.DataVersionDetailPage, window.TrendCenterPage, window.ProductPage, window.CompetitorPage, window.ListingPage, window.TrafficPage, window.InventoryCenterPage, window.ServiceCenterPage, window.TodoPage, window.TaskReportPage, window.TaskSubmitPage, window.LogPage, window.FeedbackFlywheelPage];
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
      try {
        await AppApi.switchAccount(select.value);
        await AppApi.prefetch();
        const nextAccount = await AppApi.accounts();
        renderAccountSwitcher(nextAccount);
        const active = compressedRoute(location.hash.replace("#", "") || "dashboard");
        const allowed = new Set(visibleModulesFor(nextAccount));
        if (allowed.size && !allowed.has(active)) AppRouter.navigate("dashboard");
        else AppRouter.schedule("account-switch");
      } finally {
        setApiBadge();
        select.disabled = false;
      }
    };
  }

  window.addEventListener("api-client-error", setApiBadge);
  window.addEventListener("api-client-status", setApiBadge);
  if (window.AppApi?.prefetch) {
    try {
      await window.AppApi.prefetch();
      renderAccountSwitcher(await AppApi.accounts());
    } catch (error) {
      console.error("[bootstrap] initial server prefetch failed; local business fallback is disabled", error);
    } finally {
      setApiBadge();
    }
  }
  AppRouter.start();
})();
