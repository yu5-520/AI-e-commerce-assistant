(function () {
  const s = (value) => AppShell.escape(value ?? "-");

  async function loadJson(path, fallback = null) {
    try {
      const response = await fetch(path, { method: "GET", headers: { Accept: "application/json", "X-Mock-User-Id": window.AppApi?.getCurrentUserId?.() || "U001" } });
      if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
      return await response.json();
    } catch (error) {
      console.warn(`[system-status] fallback for ${path}`, error);
      return fallback;
    }
  }

  function pill(text, tone = "neutral") { return `<span class="system-pill ${tone}">${s(text)}</span>`; }
  function metric(label, value, tone = "neutral") { return `<article class="system-metric"><span>${s(label)}</span><strong>${s(value)}</strong>${pill(tone === "good" ? "正常" : tone === "warn" ? "关注" : tone === "danger" ? "阻断" : "状态", tone)}</article>`; }
  function layerRow(layer) { return `<article class="system-layer-row"><div><strong>${s(layer?.name)}</strong><span>${s(layer?.capability || layer?.target)}</span></div>${pill(layer?.status || "unknown", "neutral")}</article>`; }
  function flagRow(flag) { return `<article class="system-layer-row"><div><strong>${s(flag.name)}</strong><span>${s(flag.flagKey)} · ${s(flag.stage)} · ${s(flag.rolloutPercentage)}%</span></div>${pill(flag.enabledForContext ? "当前可用" : "当前不可用", flag.enabledForContext ? "good" : "warn")}</article>`; }
  function textRow(title, value, tone = "neutral") { return `<article class="system-layer-row"><div><strong>${s(title)}</strong><span>${s(value)}</span></div>${pill(tone, tone === "已挂载" || tone === "已固定" ? "good" : "neutral")}</article>`; }

  window.SystemStatusPage = {
    route: "system-status",
    title: "系统状态",
    async render() {
      const [health, security, repository, architecture, v7, v98, v99, v9, v10, v10Ready] = await Promise.all([
        loadJson("/api/health", {}), loadJson("/api/system/security", {}), loadJson("/api/system/repositories", {}), loadJson("/api/architecture/p0", {}), loadJson("/api/architecture/v7", {}), loadJson("/api/architecture/v9/ops-authorization", {}), loadJson("/api/architecture/v9/delivery-readiness", {}), loadJson("/api/architecture/v9/readiness", {}), loadJson("/api/architecture/v10/task-driven-product", {}), loadJson("/api/architecture/v10/readiness", {}),
      ]);
      const apiVersion = health?.version || v10Ready?.version || v10?.version || v9?.version || v99?.version || security?.apiVersion || repository?.version || architecture?.version || "10.8.0";
      const layers = v7?.controlPlane?.layers || architecture?.layers || [];
      const flags = v7?.tenantConfig?.featureFlags || [];
      const enabledFlags = flags.filter((flag) => flag.enabledForContext);
      const config = v7?.tenantConfig?.config || {};
      const v10Entries = v10Ready?.entries || { taskDrivenProduct: health?.v100Entry, readiness: health?.v100ReadinessEntry };
      const taskTypes = v10?.taskTypes || v10Ready?.taskTypes || [];
      const principles = v10?.principles || [];
      const minimalNav = v10?.minimalNavigation || v10Ready?.minimalNavigation || [];
      const collapsedRoutes = v10?.collapsedOperationRoutes || v10Ready?.collapsedOperationRoutes || [];
      const navRules = v10?.navigationCompressionRules || [];
      const layoutRules = v10?.frontendLayoutRules || v10Ready?.frontendLayoutRules || {};
      const uiRules = v10?.uiProductizationRules || v10Ready?.uiProductizationRules || [];
      const dashboardSections = v10?.dashboardWorkbenchSections || v10Ready?.dashboardWorkbenchSections || [];
      const dashboardRules = v10?.dashboardRules || v10Ready?.dashboardRules || [];
      const importTaskFlow = v10?.importTaskFlow || v10Ready?.importTaskFlow || [];
      const importRefresh = v10?.importRefreshContract || v10Ready?.importRefreshContract || {};
      const crossAccountFlow = v10?.crossAccountFlow || v10Ready?.crossAccountFlow || [];
      const roleViewRules = v10?.roleViewRules || v10Ready?.roleViewRules || {};
      const taskActionRules = v10?.taskActionRules || v10Ready?.taskActionRules || [];
      const operatingProfileRules = v10?.operatingProfileRules || v10Ready?.operatingProfileRules || [];
      const operatingProfileTagTypes = v10?.operatingProfileTagTypes || v10Ready?.operatingProfileTagTypes || [];
      const tagChangeTaskRules = v10?.tagChangeTaskRules || v10Ready?.tagChangeTaskRules || [];
      const tagChangeTaskFlow = v10?.tagChangeTaskFlow || v10Ready?.tagChangeTaskFlow || [];
      const entries = v9?.entries || { opsAuthorization: health?.v98Entry, deliveryReadiness: health?.v99Entry };
      const readinessAreas = Object.entries(v99?.readinessAreas || {});
      const deliveryStages = v99?.deliveryStages || [];
      const opsRoles = Object.keys(v98?.roles || {});
      const separationRules = v98?.separationRules || [];
      return `<section class="system-hero"><div><p class="eyebrow">SYSTEM STATUS · V10.8</p><h2>系统状态</h2><p>集中查看标签变化任务、Agent 经营档案、任务操作极简化和跨账号任务流转。</p></div><div class="system-hero-side"><span>当前版本</span><strong>${s(apiVersion)}</strong><small>${s(v10Ready?.status || "tag-change-tasks")}</small></div></section>
      <section class="system-metric-grid">
        ${metric("API 版本", apiVersion, apiVersion === "10.8.0" ? "good" : "warn")}
        ${metric("标签任务规则", tagChangeTaskRules.length, "good")}
        ${metric("标签任务流程", tagChangeTaskFlow.length, "good")}
        ${metric("经营档案规则", operatingProfileRules.length, "good")}
      </section>
      <section class="page-section system-section"><div class="section-header"><h3>V10.8 标签变化任务</h3>${pill(v10?.version || "10.8.0", "good")}</div><div class="system-layer-list">${tagChangeTaskRules.map((item) => textRow(item, "候选转任务规则", "已固定")).join("") || "<p>暂无标签变化任务规则。</p>"}${tagChangeTaskFlow.map((item) => textRow(item, "标签任务流程", "已固定")).join("")}</div></section>
      <section class="page-section system-section"><div class="section-header"><h3>V10.7 Agent 经营档案</h3>${pill(v10?.version || "10.8.0", "good")}</div><div class="system-layer-list">${operatingProfileRules.map((item) => textRow(item, "自动标签规则", "已固定")).join("") || "<p>暂无经营档案规则。</p>"}${operatingProfileTagTypes.map((item) => textRow(item, "Agent 标签类型", "已固定")).join("")}</div></section>
      <section class="page-section system-section"><div class="section-header"><h3>V10.6 任务操作极简化</h3>${pill(v10?.version || "10.8.0", "good")}</div><div class="system-layer-list">${taskActionRules.map((item) => textRow(item, "任务卡动作规则", "已固定")).join("") || "<p>暂无动作规则。</p>"}</div></section>
      <section class="page-section system-section"><div class="section-header"><h3>V10.5 跨账号任务流转</h3>${pill(v10?.version || "10.8.0", "good")}</div><div class="system-layer-list">${crossAccountFlow.map((item) => textRow(item, "自动流转规则", "已固定")).join("") || "<p>暂无跨账号规则。</p>"}${Object.entries(roleViewRules).map(([role, view]) => textRow(role, `${view.surface || "role"} · ${(view.actions || []).join(" / ")}`, "已固定")).join("")}</div></section>
      <section class="page-section system-section"><div class="section-header"><h3>V10.4 报表导入驱动任务</h3>${pill(v10?.version || "10.8.0", "good")}</div><div class="system-layer-list">${importTaskFlow.map((item) => textRow(item, "导入后端流程", "已固定")).join("")}${Object.entries(importRefresh).map(([name, value]) => textRow(name, Array.isArray(value) ? value.join(" / ") : value, "已固定")).join("")}</div></section>
      <section class="page-section system-section"><div class="section-header"><h3>V10.3 今日任务台</h3>${pill(v10?.version || "10.8.0", "good")}</div><div class="system-layer-list">${dashboardSections.map((item) => textRow(item, "总览任务台结构", "已固定")).join("")}${dashboardRules.map((item, index) => textRow(`任务台规则 ${index + 1}`, item, "已固定")).join("")}</div></section>
      <section class="page-section system-section"><div class="section-header"><h3>V10.2 产品化排版</h3>${pill(v10?.version || "10.8.0", "good")}</div><div class="system-layer-list">${Object.entries(layoutRules).map(([name, value]) => textRow(name, value, "已固定")).join("")}${uiRules.map((item, index) => textRow(`UI 规则 ${index + 1}`, item, "已固定")).join("")}</div></section>
      <section class="page-section system-section"><div class="section-header"><h3>V10.1 主导航压缩</h3>${pill(v10?.version || "10.8.0", "good")}</div><div class="system-layer-list">${minimalNav.map((item) => textRow(item, "主导航入口", "已固定")).join("")}${collapsedRoutes.map((item) => textRow(item, "折叠到经营模块", "已固定")).join("")}${navRules.slice(0, 5).map((item, index) => textRow(`规则 ${index + 1}`, item, "已固定")).join("")}</div></section>
      <section class="page-section system-section"><div class="section-header"><h3>V10 任务驱动产品</h3>${pill(v10?.version || "10.8.0", "good")}</div><div class="system-layer-list">${principles.map((item, index) => textRow(`原则 ${index + 1}`, item, "已固定")).join("")}${taskTypes.map((item) => textRow(item, "需要用户介入时以任务出现", "已固定")).join("")}</div></section>
      <section class="page-section system-section"><div class="section-header"><h3>V10 readiness 入口</h3>${pill(v10Ready?.status || "mounted", "good")}</div><div class="system-layer-list">${Object.entries(v10Entries || {}).map(([name, path]) => textRow(name, path, "已挂载")).join("") || "<p>暂无 V10 入口。</p>"}</div></section>
      <section class="page-section system-section"><div class="section-header"><h3>V9.9 交付验收</h3>${pill(v99?.version || "9.9.0", "good")}</div><div class="system-layer-list">${readinessAreas.map(([name, items]) => textRow(name, Array.isArray(items) ? items.join(" / ") : items, "已固定")).join("")}${deliveryStages.slice(0, 4).map((item) => textRow(item, "delivery stage", "已固定")).join("")}</div></section>
      <section class="page-section system-section"><div class="section-header"><h3>V9 readiness 入口</h3>${pill(v9?.status || "mounted", "good")}</div><div class="system-layer-list">${Object.entries(entries || {}).map(([name, path]) => textRow(name, path, "已挂载")).join("") || "<p>暂无 V9 入口。</p>"}</div></section>
      <section class="page-section system-section"><div class="section-header"><h3>V9.8 受托运维边界</h3>${pill(v98?.version || "9.8.0", "good")}</div><div class="system-layer-list">${opsRoles.map((role) => textRow(role, v98?.roles?.[role]?.type || "role", "已固定")).join("")}${separationRules.slice(0, 3).map((rule, index) => textRow(`边界规则 ${index + 1}`, rule, "已固定")).join("")}</div></section>
      <section class="page-section system-section"><div class="section-header"><h3>V7 控制面</h3>${pill(v7?.version || "runtime", "neutral")}</div><div class="system-layer-list">${layers.map(layerRow).join("") || "<p>暂无架构层数据。</p>"}</div></section>
      <section class="page-section system-section"><div class="section-header"><h3>功能开关</h3>${pill(`${enabledFlags.length}/${flags.length} 当前可用`, "good")}</div><div class="system-layer-list"><article class="system-layer-row"><div><strong>${s(config.edition || config.plan || "tenant")}</strong><span>${s((config.enabledModules || []).join(" / "))}</span></div>${pill(config.workflowMode || "workflow", "good")}</article>${flags.map(flagRow).join("") || "<p>暂无功能开关。</p>"}</div></section>`;
    },
    mount(ctx) { ctx.delegate("[data-system-refresh]", "click", () => AppRouter.schedule("system-status-refresh")); },
  };
})();
