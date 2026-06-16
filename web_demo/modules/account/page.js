(function () {
  const s = (value) => AppShell.escape(value);
  let payload = null;

  function roleCard(role) {
    return `<article class="card"><div class="section-header"><h3>${s(role.name)}</h3><span class="status-badge">L${s(role.level)}</span></div><p>${s(role.description)}</p><small>范围：${s(role.scope)}</small><div class="tag-row">${(role.permissions || []).slice(0, 5).map((item) => `<span>${s(item)}</span>`).join("")}</div></article>`;
  }

  function userRow(user) {
    return `<article class="report-card"><div class="section-header"><h3>${s(user.name)}</h3><span class="status-badge">${s(user.status)}</span></div><p>${s(user.roleName)} · ${s((user.storeIds || []).join(" / "))}</p><small>${s((user.permissionNames || []).join("、"))}</small></article>`;
  }

  function storeRow(store) {
    return `<article class="report-card"><strong>${s(store.name)}</strong><p>${s(store.platform)} · ${s(store.id)}</p></article>`;
  }

  window.AccountPage = {
    route: "accounts",
    title: "账号权限",
    async render() {
      payload = await AppApi.accounts();
      if (!payload) return `<section class="page-section"><h3>账号系统加载失败</h3><p>请确认 /api/accounts 已挂载。</p></section>`;
      const current = payload.currentUser || {};
      const roles = payload.roles || [];
      const users = payload.users || [];
      const stores = payload.stores || [];
      const flow = payload.taskFlow || [];
      return `<section class="report-hero"><div><p class="eyebrow">ACCOUNT SYSTEM · V2.0</p><h2>企业协同账号系统</h2><p>先用轻量账号上下文跑通角色、权限、店群范围和任务派发链路，后续再接真实登录、企业租户和审计存储。</p></div><div class="report-hero-side"><span>当前身份</span><strong>${s(current.roleName || "老板账号")}</strong><small>${s(current.name || "老板")}</small></div></section><section class="kpi-grid report-metrics">${[["账号角色", roles.length, "老板 / 总管 / 运营 / 财务 / 观察"], ["协作账号", users.length, "Mock 企业账号"], ["店铺范围", stores.length, "按店群授权"], ["权限边界", "已建模", "暂未接真实 SSO"]].map(([a,b,c]) => AppShell.metricCard(a,b,c)).join("")}</section><section class="page-section"><div class="section-header"><h3>角色权限</h3><span class="status-badge">RBAC</span></div><div class="kpi-grid">${roles.map(roleCard).join("")}</div></section><section class="page-section"><div class="section-header"><h3>账号列表</h3><span class="status-badge">${users.length} 个账号</span></div><div class="report-card-list">${users.map(userRow).join("")}</div></section><section class="page-section"><div class="section-header"><h3>店群范围</h3><span class="status-badge">授权范围</span></div><div class="report-card-list">${stores.map(storeRow).join("")}</div></section><section class="page-section"><div class="section-header"><h3>任务协同链路</h3><span class="status-badge">派发 / 提交 / 复核</span></div><div class="report-card-list">${flow.map((item, index) => `<article class="report-card"><strong>${index + 1}. ${s(item)}</strong></article>`).join("")}</div></section>`;
    },
  };
})();
