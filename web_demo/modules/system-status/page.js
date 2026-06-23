(function () {
  const s = (value) => AppShell.escape(value ?? "-");

  async function loadJson(path, fallback = null) {
    try {
      const response = await fetch(path, {
        method: "GET",
        headers: {
          Accept: "application/json",
          "X-Mock-User-Id": window.AppApi?.getCurrentUserId?.() || "U001",
        },
      });
      if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
      return await response.json();
    } catch (error) {
      console.warn(`[system-status] fallback for ${path}`, error);
      return fallback;
    }
  }

  function pill(text, tone = "neutral") {
    return `<span class="system-pill ${tone}">${s(text)}</span>`;
  }

  function boolTone(value) {
    return value ? "good" : "muted";
  }

  function mirrorCard(title, mirror) {
    const enabled = !!mirror?.enabled;
    const mode = mirror?.mode || "sqlite";
    const resources = Array.isArray(mirror?.resources) ? mirror.resources : (mirror?.mirroredResources || []);
    return `<article class="system-card mirror-card">
      <div class="system-card-head"><h3>${s(title)}</h3>${pill(enabled ? "可镜像" : "默认跳过", enabled ? "good" : "muted")}</div>
      <strong>${s(mode)}</strong>
      <p>${s(resources.join(" / ") || "未配置资源")}</p>
    </article>`;
  }

  function metric(label, value, tone = "neutral") {
    return `<article class="system-metric"><span>${s(label)}</span><strong>${s(value)}</strong>${pill(tone === "good" ? "正常" : tone === "warn" ? "关注" : "状态", tone)}</article>`;
  }

  function layerRow(layer) {
    return `<article class="system-layer-row">
      <div><strong>${s(layer?.name)}</strong><span>${s(layer?.target)}</span></div>
      ${pill(layer?.status || "unknown", "neutral")}
    </article>`;
  }

  function safeVersion(security, repository, architecture) {
    return security?.apiVersion || repository?.version || architecture?.version || "V5.3.7";
  }

  window.SystemStatusPage = {
    route: "system-status",
    title: "系统状态",
    async render() {
      const [security, repository, architecture] = await Promise.all([
        loadJson("/api/system/security", {}),
        loadJson("/api/system/repositories", {}),
        loadJson("/api/architecture/p0", {}),
      ]);

      const activeMode = repository?.activeMode || "sqlite";
      const apiVersion = safeVersion(security, repository, architecture);
      const layers = Array.isArray(architecture?.layers) ? architecture.layers : [];
      const mirrorBlocks = [
        ["任务", repository?.taskHybridMirror],
        ["导入与队列", repository?.importWorkerHybridMirror],
        ["审计与日志", repository?.auditTechHybridMirror],
        ["投影与数据", repository?.projectionDataHybridMirror],
        ["数据版本与预警", repository?.dataAlertWriteMirror],
      ];

      return `<section class="system-hero">
        <div><p class="eyebrow">SYSTEM STATUS · V5.3.7</p><h2>系统状态</h2><p>这里集中查看部署、数据库、Repository Mirror、P0 架构和运行模式。</p></div>
        <div class="system-hero-side"><span>当前模式</span><strong>${s(activeMode)}</strong><small>${s(apiVersion)}</small></div>
      </section>

      <section class="system-metric-grid">
        ${metric("API 版本", apiVersion, "good")}
        ${metric("Repository 模式", activeMode, activeMode === "sqlite" ? "warn" : "good")}
        ${metric("PostgreSQL Repository", repository?.postgresRepositoryEnabled ? "启用" : "未启用", boolTone(repository?.postgresRepositoryEnabled))}
        ${metric("运行态", architecture?.runtimeMode || "system-status", "neutral")}
      </section>

      <section class="page-section system-section"><div class="section-header"><h3>Repository Mirror</h3><button type="button" data-system-refresh>刷新</button></div><div class="system-card-grid">${mirrorBlocks.map(([title, mirror]) => mirrorCard(title, mirror)).join("")}</div></section>

      <section class="page-section system-section"><div class="section-header"><h3>运行边界</h3>${pill(security?.deploymentMode || "demo", "neutral")}</div><div class="system-card-grid">
        ${mirrorCard("安全响应头", { enabled: security?.securityHeaders?.enabled !== false, mode: security?.securityHeaders?.version || "enabled", resources: ["Security Headers"] })}
        ${mirrorCard("API 限流", { enabled: security?.apiRateLimit?.enabled !== false, mode: security?.apiRateLimit?.version || "enabled", resources: ["Rate Limit"] })}
        ${mirrorCard("Worker", { enabled: true, mode: security?.workerRuntime?.runtime || security?.workerRuntime?.mode || "sqlite", resources: ["Worker Runtime"] })}
        ${mirrorCard("LLM Gateway", { enabled: true, mode: security?.llmGateway?.version || "gateway", resources: ["Quota", "Cache", "Breaker"] })}
      </div></section>

      <section class="page-section system-section"><div class="section-header"><h3>P0 架构层</h3>${pill(architecture?.runtimeMode || "runtime", "neutral")}</div><div class="system-layer-list">${layers.map(layerRow).join("") || "<p>暂无架构层数据。</p>"}</div></section>`;
    },
    mount(ctx) {
      ctx.delegate("[data-system-refresh]", "click", () => AppRouter.schedule("system-status-refresh"));
    },
  };
})();
