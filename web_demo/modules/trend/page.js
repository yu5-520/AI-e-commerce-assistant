(function () {
  let trendData = null;
  const s = (value) => AppShell.escape(value ?? "");
  const pct = (value) => {
    const number = Number(value || 0);
    if (!Number.isFinite(number)) return "-";
    return `${number > 0 ? "+" : ""}${(number * 100).toFixed(1)}%`;
  };
  const num = (value) => {
    const number = Number(value || 0);
    if (!Number.isFinite(number)) return s(value || "-");
    return Number.isInteger(number) ? String(number) : number.toFixed(2);
  };
  const directionText = (value) => value === "up" ? "上涨" : value === "down" ? "下滑" : "稳定";
  const riskClass = (value) => value === "高" ? "danger" : value === "中" ? "warning" : "good";

  function metricCards(summary = {}) {
    return `<section class="kpi-grid report-metrics">${[
      ["商品快照", summary.snapshotCount || 0, "导入后生成"],
      ["趋势指标", summary.trendCount || 0, "同品对比"],
      ["经营信号", summary.signalCount || 0, "趋势触发"],
      ["任务候选", summary.taskCandidateSignalCount || 0, "V6.2 接入"]
    ].map(([a,b,c]) => AppShell.metricCard(a,b,c)).join("")}</section>`;
  }

  function compactList(title, items = []) {
    return `<article class="page-section report-section"><div class="section-header"><h3>${s(title)}</h3><span class="status-badge">${s(items.length)} 项</span></div><div class="version-alert-list">${items.length ? items.map((item) => `<article class="version-alert-row"><strong>${s(item.name)}</strong><span>${s(item.count)} 个商品 / 快照</span><small>基于当前账号可见范围</small></article>`).join("") : `<div class="log-empty">暂无数据，导入两次以上同商品报表后会形成趋势。</div>`}</div></article>`;
  }

  function productList(items = []) {
    return `<section class="page-section report-section"><div class="section-header"><h3>单商品趋势对象</h3><span class="status-badge">${s(items.length)} 个</span></div><div class="report-card-list">${items.length ? items.map((item) => `<article class="report-card"><div><h3>${s(item.title || item.productId || item.product_id)}</h3><p>${s(item.platform || "未知平台")} · ${s(item.category || "未分类")}</p><div class="report-meta"><span>${s(item.productId || item.product_id)}</span><span>${s(item.storeName || item.storeId || "未绑定店铺")}</span><span>快照 ${s(item.snapshotCount || 0)}</span></div></div><div class="report-actions"><span class="status-badge">趋势对象</span></div></article>`).join("") : `<div class="log-empty">暂无商品快照。请先在报表中心导入包含商品 ID 的 ERP / CRM 数据。</div>`}</div></section>`;
  }

  function trendList(items = []) {
    return `<section class="page-section report-section"><div class="section-header"><h3>最新指标趋势</h3><span class="status-badge">${s(items.length)} 条</span></div><div class="version-alert-list">${items.length ? items.map((item) => `<article class="version-alert-row"><strong>${s(item.productId)} · ${s(item.metricLabel || item.metricName)}</strong><span>${s(directionText(item.trendDirection))} · ${num(item.previousValue)} → ${num(item.currentValue)} · ${pct(item.changeRate)}</span><small>${s(item.datasetName || "报表")} · ${s(item.dataVersion || "")}</small></article>`).join("") : `<div class="log-empty">同一商品至少导入两次后，系统会计算指标变化。</div>`}</div></section>`;
  }

  function signalList(items = []) {
    return `<section class="page-section report-section"><div class="section-header"><h3>经营信号</h3><span class="status-badge">${s(items.length)} 条</span></div><div class="report-card-list">${items.length ? items.map((item) => `<article class="report-card"><div><h3>${s(item.signalType)}</h3><p>${s(item.productId)} · ${s(item.metricLabel || item.sourceMetric)} · ${s(directionText(item.trendDirection))}</p><div class="report-meta"><span class="status-badge ${riskClass(item.riskLevel)}">${s(item.riskLevel)}风险</span><span>${s(item.taskCandidate ? "任务候选" : "观察信号")}</span><span>${pct(item.changeRate)}</span></div><p>${s(item.reason || "趋势中心记录该信号，后续接入风险分级任务。")}</p></div><div class="report-actions"><span class="status-badge">V6.1</span></div></article>`).join("") : `<div class="log-empty">暂无经营信号。导入新的同商品数据后会自动生成。</div>`}</div></section>`;
  }

  window.TrendCenterPage = {
    route: "trend-center",
    title: "趋势中心",
    async render() {
      trendData = await AppApi.trendCenter(50);
      const summary = trendData?.summary || {};
      return `<section class="report-hero report-hero-clean"><div><p class="eyebrow">TREND CENTER · V6.1</p><h2>动态数据趋势中心</h2></div><div class="report-hero-side"><span>当前阶段</span><strong>快照与信号</strong><small>V6.2 接风险分级任务</small></div></section>${metricCards(summary)}<section class="report-preview-grid">${compactList("总店铺趋势", trendData?.storeTrends || [])}${compactList("平台趋势", trendData?.platformTrends || [])}${compactList("平台类目趋势", trendData?.categoryTrends || [])}</section>${productList(trendData?.latestProducts || [])}${trendList(trendData?.latestTrends || [])}${signalList(trendData?.latestSignals || [])}`;
    },
    mount(ctx) {
      ctx.onRefresh = async () => {
        trendData = await AppApi.trendCenter(50);
        AppRouter.schedule("trend-refresh");
      };
    }
  };
})();