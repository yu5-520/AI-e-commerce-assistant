(function () {
  const s = (value) => AppShell.escape(value);
  const label = (value) => String(value || "").replaceAll("任务指挥", "人员总览").replaceAll("利润预算", "供投财务");

  function chips(items = []) {
    return `<div class="permission-chip-row">${items.map((item) => `<span>${s(label(item))}</span>`).join("")}</div>`;
  }

  function rolePermissionCard(role, permissions) {
    const selected = new Set(role.permissions || []);
    return `<article class="report-card"><div class="section-header"><h3>${s(role.name)}</h3><span class="status-badge">L${s(role.level)}</span></div><div class="permission-chip-row">${permissions.map((permission) => `<button type="button" class="secondary" data-permission="${s(role.id)}:${s(permission.id)}" aria-pressed="${selected.has(permission.id)}">${selected.has(permission.id) ? "✓ " : ""}${s(label(permission.name))}</button>`).join("")}</div></article>`;
  }

  function userControlCard(user, roles, stores) {
    return `<article class="report-card"><div class="section-header"><h3>${s(user.name)}</h3><span class="status-badge">${s(user.roleName)}</span></div><div class="permission-chip-row">${roles.map((role) => `<button type="button" class="secondary" data-role-change="${s(user.id)}:${s(role.id)}">${s(role.name)}</button>`).join("")}</div><div class="permission-chip-row">${stores.map((store) => `<button type="button" class="secondary" data-store-toggle="${s(user.id)}:${s(store.id)}">${(user.storeIds || []).includes(store.id) ? "✓ " : ""}${s(store.name)}</button>`).join("")}</div></article>`;
  }

  window.AccountPage = {
    route: "accounts",
    title: "账号权限",
    async render() {
      const payload = await AppApi.accounts();
      if (!payload) return `<section class="page-section"><h3>账号系统加载失败</h3></section>`;
      const current = payload.currentUser || {};
      const view = payload.currentRoleView || {};
      const actions = (current.allowedActions || []).map(label);
      const sections = (view.sections || []).map(label);
      return `<section class="report-hero"><div><p class="eyebrow">ACCOUNT · V2.3.4</p><h2>${s(label(view.headline || "账号中心"))}</h2><p>${s(label(view.summary || "账号页只展示当前身份、范围和权限入口；组织结构和权限治理已下沉到组织效率。"))}</p></div><div class="report-hero-side"><span>当前身份</span><strong>${s(current.roleName)}</strong><small>${s(current.name)}</small></div></section><section class="kpi-grid report-metrics">${[["当前角色", current.roleName, current.insightName], ["数据范围", current.scope, "按角色授权"], ["可见模块", (current.visibleModules || []).length, "动态导航"], ["操作权限", actions.length, "按钮级控制"]].map(([a,b,c]) => AppShell.metricCard(a,b,c)).join("")}</section><section class="page-section"><div class="section-header"><h3>我的权限摘要</h3><button type="button" data-org-efficiency>组织效率管理</button></div>${chips(current.permissionNames || [])}<div class="info-list"><div><span>可操作</span><strong>${s(actions.join(" / "))}</strong></div><div><span>不可访问</span><strong>${s((current.hiddenFields || []).join(" / ") || "无")}</strong></div></div></section><section class="page-section"><div class="section-header"><h3>我的功能入口</h3><span class="status-badge">${s(current.insightName)}</span></div><div class="report-card-list">${sections.map((item) => `<article class="report-card"><strong>${s(item)}</strong></article>`).join("")}</div></section>`;
    },
    mount(ctx) { ctx.delegate("[data-org-efficiency]", "click", () => AppRouter.navigate("org-efficiency")); },
  };

  window.RoleConsolePage = {
    route: "role-console",
    title: "角色权限控制台",
    async render() {
      const payload = await AppApi.accounts();
      if (!payload) return `<section class="page-section"><h3>控制台加载失败</h3></section>`;
      const user = payload.currentUser || {};
      if (!AppApi.can("manage_roles")) return `<section class="report-hero"><div><p class="eyebrow">ROLE CONSOLE</p><h2>无权限访问</h2><p>当前账号只能查看自己的权限摘要，不能调整角色、店铺范围或权限模板。</p></div><div class="report-hero-side"><span>当前身份</span><strong>${s(user.roleName)}</strong><small>${s(user.name)}</small></div></section>`;
      const roles = payload.roles || [];
      const users = payload.users || [];
      const stores = payload.stores || [];
      const permissions = payload.permissions || [];
      const logs = payload.roleChangeLogs || [];
      return `<section class="report-hero"><div><p class="eyebrow">ROLE CONSOLE · LEGACY</p><h2>角色权限控制台</h2><p>该入口保留兼容；日常组织结构、职位关系和权限治理请进入组织效率。</p></div><div class="report-hero-side"><span>管理者</span><strong>${s(user.roleName)}</strong><small>${s(user.name)}</small></div></section><section class="page-section"><div class="section-header"><h3>账号升降级 / 店铺授权</h3><span class="status-badge">${users.length} 个账号</span></div><div class="report-card-list">${users.map((item) => userControlCard(item, roles, stores)).join("")}</div></section><section class="page-section"><div class="section-header"><h3>角色权限模板</h3><span class="status-badge">可切换</span></div><div class="report-card-list">${roles.map((role) => rolePermissionCard(role, permissions)).join("")}</div></section><section class="page-section"><div class="section-header"><h3>变更记录</h3><span class="status-badge">${logs.length} 条</span></div><div class="report-card-list">${logs.length ? logs.map((item) => `<article class="report-card"><strong>${s(item.type)}</strong><p>${s(JSON.stringify(item))}</p></article>`).join("") : `<article class="report-card"><strong>暂无变更</strong><p>调整角色、店铺或权限后会记录在这里。</p></article>`}</div></section>`;
    },
    mount(ctx) {
      ctx.delegate("[data-role-change]", "click", async (_, node) => { const [userId, roleId] = node.dataset.roleChange.split(":"); await AppApi.updateUserRole(userId, roleId); await AppApi.prefetch(); AppRouter.schedule("role-change"); });
      ctx.delegate("[data-store-toggle]", "click", async (_, node) => { const [userId, storeId] = node.dataset.storeToggle.split(":"); const account = await AppApi.accounts(); const user = (account.users || []).find((item) => item.id === userId); const current = new Set(user?.storeIds || []); current.has(storeId) ? current.delete(storeId) : current.add(storeId); await AppApi.updateUserStores(userId, Array.from(current)); await AppApi.prefetch(); AppRouter.schedule("store-toggle"); });
      ctx.delegate("[data-permission]", "click", async (_, node) => { const [roleId, permissionId] = node.dataset.permission.split(":"); const account = await AppApi.accounts(); const role = (account.roles || []).find((item) => item.id === roleId); const current = new Set(role?.permissions || []); current.has(permissionId) ? current.delete(permissionId) : current.add(permissionId); await AppApi.updateRolePermissions(roleId, Array.from(current)); await AppApi.prefetch(); AppRouter.schedule("permission-toggle"); });
    },
  };
})();
