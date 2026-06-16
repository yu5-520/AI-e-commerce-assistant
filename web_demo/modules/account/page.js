(function () {
  const s = (value) => AppShell.escape(value);
  let payload = null;

  function chips(items = []) {
    return `<div class="permission-chip-row">${items.map((item) => `<span>${s(item)}</span>`).join("")}</div>`;
  }

  function roleCard(role) {
    return `<article class="card"><div class="section-header"><h3>${s(role.name)}</h3><span class="status-badge">L${s(role.level)}</span></div><div class="role-note">范围：${s(role.scope)}</div><div class="role-note">${s(role.insightName || role.insightDepth)}</div>${chips(role.permissionNames || [])}</article>`;
  }

  function userRow(user) {
    return `<article class="report-card"><div class="section-header"><h3>${s(user.name)}</h3><span class="status-badge">${s(user.roleName)}</span></div><p>${s(user.scope)} · ${s((user.storeIds || []).join(" / "))}</p><small>${s((user.permissionNames || []).join("、"))}</small></article>`;
  }

  function storeRow(store) {
    return `<article class="report-card"><strong>${s(store.name)}</strong><p>${s(store.platform)} · ${s(store.id)}</p></article>`;
  }

  function sectionList(title, items = [], badge = "视角") {
    return `<section class="page-section"><div class="section-header"><h3>${s(title)}</h3><span class="status-badge">${s(badge)}</span></div><div class="report-card-list">${items.map((item, index) => `<article class="report-card"><strong>${index + 1}. ${s(item)}</strong></article>`).join("")}</div></section>`;
  }

  function roleSpecificSections(account) {
    const user = account.currentUser || {};
    const view = account.currentRoleView || {};
    const users = account.users || [];
    const stores = account.stores || [];
    if (user.roleId === "owner") {
      return `${sectionList("老板能看到的深层经营信息", user.managementInsights || [], user.insightName)}<section class="page-section"><div class="section-header"><h3>全部协作账号</h3><span class="status-badge">${users.length} 个账号</span></div><div class="report-card-list">${users.map(userRow).join("")}</div></section><section class="page-section"><div class="section-header"><h3>店群授权</h3><span class="status-badge">全部店群</span></div><div class="report-card-list">${stores.map(storeRow).join("")}</div></section>${sectionList("老板页面模块", view.sections || [])}`;
    }
    if (user.roleId === "manager") {
      const managedUsers = users.filter((item) => ["operator", "finance"].includes(item.roleId));
      return `${sectionList("店群总管能看到的管理信息", user.managementInsights || [], user.insightName)}<section class="page-section"><div class="section-header"><h3>我管理的账号</h3><span class="status-badge">${managedUsers.length} 个账号</span></div><div class="report-card-list">${managedUsers.map(userRow).join("")}</div></section>${sectionList("总管页面模块", view.sections || [])}`;
    }
    if (user.roleId === "operator") {
      return `${sectionList("运营只看到的执行信息", user.managementInsights || [], user.insightName)}${sectionList("可操作动作", user.allowedActions || [], "执行权限")}${sectionList("不可访问内容", user.hiddenFields || [], "已隐藏")}`;
    }
    if (user.roleId === "finance") {
      return `${sectionList("数据 / 财务能看到的经营信息", user.managementInsights || [], user.insightName)}${sectionList("可操作动作", user.allowedActions || [], "财务权限")}${sectionList("不可操作内容", user.hiddenFields || [], "已隐藏")}`;
    }
    return `${sectionList("只读账号能看到的摘要", user.managementInsights || [], user.insightName)}${sectionList("可查看范围", view.sections || [], "只读")}${sectionList("不可访问内容", user.hiddenFields || [], "已隐藏")}`;
  }

  window.AccountPage = {
    route: "accounts",
    title: "账号权限",
    async render() {
      payload = await AppApi.accounts();
      if (!payload) return `<section class="page-section"><h3>账号系统加载失败</h3><p>请确认 /api/accounts 已挂载。</p></section>`;
      const current = payload.currentUser || {};
      const view = payload.currentRoleView || {};
      const roles = payload.roles || [];
      const users = payload.users || [];
      const stores = payload.stores || [];
      return `<section class="report-hero"><div><p class="eyebrow">ACCOUNT SYSTEM · V2.1</p><h2>${s(view.headline || "企业协同账号系统")}</h2><p>${s(view.summary || "不同账号看到不同范围、按钮和经营深度。")}</p></div><div class="report-hero-side"><span>当前身份</span><strong>${s(current.roleName || "老板账号")}</strong><small>${s(current.name || "老板")}</small></div></section><section class="kpi-grid report-metrics">${[["账号角色", roles.length, "角色已分层"], ["协作账号", users.length, "可切换视角"], ["店铺范围", stores.length, current.scope || "按店群授权"], ["洞察深度", current.insightName || "已建模", current.insightDepth || "role"]].map(([a,b,c]) => AppShell.metricCard(a,b,c)).join("")}</section><section class="page-section"><div class="section-header"><h3>当前账号权限</h3><span class="status-badge">${s(current.roleName)}</span></div><div class="info-list"><div><span>数据范围</span><strong>${s(current.scope)}</strong></div><div><span>洞察深度</span><strong>${s(current.insightName)}</strong></div><div><span>可见模块</span><strong>${s((current.visibleModules || []).length)} 个</strong></div><div><span>操作权限</span><strong>${s((current.allowedActions || []).length)} 项</strong></div></div>${chips(current.permissionNames || [])}</section><section class="page-section"><div class="section-header"><h3>角色权限</h3><span class="status-badge">RBAC</span></div><div class="kpi-grid">${roles.map(roleCard).join("")}</div></section>${roleSpecificSections(payload)}`;
    },
  };
})();
