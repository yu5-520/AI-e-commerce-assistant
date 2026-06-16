(function () {
  let notice = "";
  const s = (value) => AppShell.escape(value);
  function taskState(item) {
    return item.hasActiveTask || AppTaskStore.findOpenTask({ suggestedTaskKey: item.suggestedTaskKey, activeTaskId: item.activeTaskId });
  }
  function row(item) {
    const existed = taskState(item);
    return `<article class="traffic-row"><div class="traffic-title-cell"><div class="traffic-thumb">${s(item.imageLabel)}</div><div class="traffic-title-block"><strong>${s(item.title)}</strong><small>${s(item.productId)} · ${s(item.platform)} · ${s(item.store)}</small><span>${s(item.channel)} · ${s(item.source)}</span></div></div><div class="traffic-metric-strip"><div class="traffic-number-cell"><span>曝光</span><strong>${s(item.exposure)}</strong><small>CTR ${s(item.ctr)}</small></div><div class="traffic-number-cell ${Number(item.roi) < 1.2 ? "danger" : "warning"}"><span>ROI</span><strong>${s(item.roi)}</strong><small>转化 ${s(item.conversion)}</small></div><div class="traffic-number-cell ${AppShell.statusClass(item.statusLevel)}"><span>退款率</span><strong>${s(item.refundRate)}</strong><small>${s(item.status)}</small></div></div><div class="traffic-actions"><button type="button" data-task="${s(item.id)}" class="${existed ? "ghost" : ""}">${existed ? "已在任务清单" : "加入任务清单"}</button></div></article>`;
  }
  window.TrafficPage = { route: "business-traffic", title: "流量", render() { return `<section class="traffic-toolbar"><div><p class="eyebrow">TRAFFIC TEST</p><h2>流量测试台</h2><p>流量模块只生成复盘和检查任务，不直接改预算、不直接投放。</p></div></section>${notice ? AppShell.notice("操作结果", notice) : ""}<section class="page-section traffic-list-section"><div class="section-header"><h3>流量测试</h3><span class="status-badge">${AppMockData.traffic.length} 个测试</span></div><div class="traffic-card-list">${AppMockData.traffic.map(row).join("")}</div></section>`; }, mount(ctx) { ctx.delegate("[data-task]", "click", async (_, node) => { notice = "任务提交中..."; AppRouter.schedule("traffic-task-start"); const result = await AppTaskActions.createTrafficTask(node.dataset.task); notice = result?.message || "流量任务已处理。"; AppRouter.schedule("traffic-task"); }); ctx.addCleanup(AppTaskStore.subscribe(() => AppRouter.schedule("task-store"))); } };
})();
