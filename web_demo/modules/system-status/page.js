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
      const [health, security, repository, architecture, v7, v98, v99, v9] = await Promise.all([
        loadJson("/api/health", {}),
        loadJson("/api/system/security", {}),
        loadJson("/api/system/repositories", {}),
        loadJson("/api/architecture/p0", {}),
        loadJson("/api/architecture/v7", {}),
        loadJson("/api/architecture/v9/ops-authorization", {}),
        loadJson("/api/architecture/v9/delivery-readiness", {}),
        loadJson("/api/architecture/v9/readiness", {}),
      ]);
      const activeMode = repository?.activeMode || "sqlite";
      const apiVersion = health?.version || v9?.version || v99?.version || security?.apiVersion || repository?.version || architecture?.version || "9.9.0";
      const layers = v7?.controlPlane?.layers || architecture?.layers || [];
      const flags = v7?.tenantConfig?.featureFlags || [];
      const enabledFlags = flags.filter((flag) => flag.enabledForContext);
      const config = v7?.tenantConfig?.config || {};
      const entries = v9?.entries || { opsAuthorization: health?.v98Entry, deliveryReadiness: health?.v99Entry };
      const readinessAreas = Object.entries(v99?.readinessAreas || {});
      const deliveryStages = v99?.deliveryStages || [];
      const opsRoles = Object.keys(v98?.roles || {});
      const separationRules = v98?.separationRules || [];
      return `<section class="system-hero"><div><p class="eyebrow">SYSTEM STATUS · V9.9</p><h2>系统状态</h2><p>集中查看运行版本、V9 交付验收、受托运维边界和 SaaS 控制面。</p></div><div class="system-hero-side"><span>当前版本</span><strong>${s(apiVersion)}</strong><small>${s(v9?.status || "readiness")}</small></div></section>
      <section class="system-metric-grid">
        ${metric("API 版本", apiVersion, apiVersion === "9.9.0" ? "good" : "warn")}
        ${metric("Repository 模式", activeMode, activeMode === "sqlite" ? "warn" : "good")}
        ${metric("V9 入口", Object.keys(entries || {}).length, "good")}
        ${metric("交付阶段", deliveryStages.length, "good")}
      </section>
      <section class="page-section system-section"><div class="section-header"><h3>V9.9 交付验收</h3>${pill(v99?.version || "9.9.0", "good")}</div><div class="system-layer-list">
        ${readinessAreas.map(([name, items]) => textRow(name, Array.isArray(items) ? items.join(" / ") : items, "已固定")).join("") || "<p>暂无 V9.9 readiness 数据。</p>"}
      </div></section>
      <section class="page-section system-section"><div class="section-header"><h3>V9 readiness 入口</h3>${pill(v9?.status || "mounted", "good")}</div><div class="system-layer-list">
        ${Object.entries(entries || {}).map(([name, path]) => textRow(name, path, "已挂载")).join("") || "<p>暂无 V9 入口。</p>"}
      </div></section>
      <section class="page-section system-section"><div class="section-header"><h3>V9.8 受托运维边界</h3>${pill(v98?.version || "9.8.0", "good")}</div><div class="system-layer-list">
        ${opsRoles.map((role) => textRow(role, v98?.roles?.[role]?.type || "role", "已固定")).join("") || "<p>暂无角色边界。</p>"}
        ${separationRules.slice(0, 5).map((rule, index) => textRow(`边界规则 ${index + 1}`, rule, "已固定")).join("")}
      </div></section>
      <section class="page-section system-section"><div class="section-header"><h3>V7 控制面</h3>${pill(v7?.version || "runtime", "neutral")}</div><div class="system-layer-list">${layers.map(layerRow).join("") || "<p>暂无架构层数据。</p>"}</div></section>
      <section class="page-section system-section"><div class="section-header"><h3>功能开关</h3>${pill(`${enabledFlags.length}/${flags.length} 当前可用`, "good")}</div><div class="system-layer-list">
        <article class="system-layer-row"><div><strong>${s(config.edition || config.plan || "tenant")}</strong><span>${s((config.enabledModules || []).join(" / "))}</span></div>${pill(config.workflowMode || "workflow", "good")}</article>
        ${flags.map(flagRow).join("") || "<p>暂无功能开关。</p>"}
      </div></section>`;
    },
    mount(ctx) { ctx.delegate("[data-system-refresh]", "click", () => AppRouter.schedule("system-status-refresh")); },
  };
})();
