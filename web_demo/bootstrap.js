(async function () {
  const pages = [
    window.DashboardPage,
    window.ExecutiveCockpitPage,
    window.RiskCenterPage,
    window.TaskCommandPage,
    window.ProfitBudgetPage,
    window.OrgEfficiencyPage,
    window.ReviewAuditPage,
    window.AccountPage,
    window.RoleConsolePage,
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

  function applyNavigationScope(account) {
    const visible = new Set(account?.currentUser?.visibleModules || []);
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
      const allowed = new Set(nextAccount?.currentUser?.visibleModules || []);
      if (allowed.size && !allowed.has(active)) AppRouter.navigate("accounts");
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
