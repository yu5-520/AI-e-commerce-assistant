(async function () {
  const pages = [
    window.DashboardPage,
    window.AccountPage,
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

  function renderAccountSwitcher(account) {
    const select = document.getElementById("accountSwitcher");
    if (!select || !account?.users) return;
    const currentId = account.currentUser?.id || AppApi.getCurrentUserId();
    select.innerHTML = account.users
      .map((user) => `<option value="${AppShell.escape(user.id)}" ${user.id === currentId ? "selected" : ""}>${AppShell.escape(user.name)} · ${AppShell.escape(user.roleName)}</option>`)
      .join("");
    select.onchange = async () => {
      select.disabled = true;
      await AppApi.switchAccount(select.value);
      await AppApi.prefetch();
      renderAccountSwitcher(await AppApi.accounts());
      AppRouter.schedule("account-switch");
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
