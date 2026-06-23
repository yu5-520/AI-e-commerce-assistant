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

  window.SystemStatusPage = {
    route: "system-status",
    title: "系统状态",
    async render() {
      const [security, repository, architecture, v7] = await Promise.all([
        loadJson("/api/system/security", {}),
        loadJson("/api/system/repositories", {}),
        loadJson("/api/architecture/p0", {}),
        loadJson("/api/architecture/v7", {}),
      ]);
      const activeMode = repository?.activeMode || "sqlite";
      const apiVersion = v7?.version || security?.apiVersion || repository?.version || architecture?.version || "V7.1.0";
      const layers = v7?.controlPlane?.layers || architecture?.layers || [];
      const flags = v7?.tenantConfig?.featureFlags || [];
      const enabledFlags = flags.filter((flag) => flag.enabledForContext);
      const config = v7?.tenantConfig?.config || {};
      return `<section class="system-hero"><div><p class="eyebrow">SYSTEM STATUS · V7.1</p><h2>系统状态</h2><p>集中查看 SaaS 控制面、租户配置、功能开关和运行模式。</p></div><div class="system-hero-side"><span>当前模式</span><strong>${s(activeMode)}</strong><small>${s(apiVersion)}</small></div></section>
      <section class="system-metric-grid">
        ${metric("API 版本", apiVersion, "good")}
        ${metric("Repository 模式", activeMode, activeMode === "sqlite" ? "warn" : "good")}
        ${metric("租户模块", (config.enabledModules || []).length, "good")}
        ${metric("功能开关", `${enabledFlags.length}/${flags.length}`, "good")}
      </section>
      <section class="page-section system-section"><div class="section-header"><h3>V7.1 租户配置</h3>${pill(v7?.tenantConfig?.roleId || "role", "neutral")}</div><div class="system-layer-list">
        <article class="system-layer-row"><div><strong>${s(config.edition || config.plan || "tenant")}</strong><span>${s((config.enabledModules || []).join(" / "))}</span></div>${pill(config.workflowMode || "workflow", "good")}</article>
      </div></section>
      <section class="page-section system-section"><div class="section-header"><h3>功能开关</h3>${pill(`${enabledFlags.length}/${flags.length} 当前可用`, "good")}</div><div class="system-layer-list">${flags.map(flagRow).join("") || "<p>暂无功能开关。</p>"}</div></section>
      <section class="page-section system-section"><div class="section-header"><h3>V7 控制面</h3>${pill(v7?.version || "runtime", "neutral")}</div><div class="system-layer-list">${layers.map(layerRow).join("") || "<p>暂无架构层数据。</p>"}</div></section>`;
    },
    mount(ctx) { ctx.delegate("[data-system-refresh]", "click", () => AppRouter.schedule("system-status-refresh")); },
  };
})();