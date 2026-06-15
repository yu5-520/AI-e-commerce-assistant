function patchDashboardTop() {
  const hero = document.querySelector(".hero-card.dashboard-hero");
  if (hero) {
    hero.classList.add("dashboard-hero-compact");
    const title = hero.querySelector("h2");
    if (title && title.textContent.includes("今日任务清单")) title.textContent = "任务清单";

    const eyebrow = hero.querySelector(".eyebrow");
    if (eyebrow) eyebrow.textContent = "TASK BOARD";

    const sideStrong = hero.querySelector(".hero-actions strong");
    if (sideStrong && sideStrong.textContent === "每天") {
      const pending = document.querySelector(".kpi-grid .card:nth-child(3) strong")?.textContent?.trim();
      sideStrong.textContent = pending ? `${pending} 项待确认` : "待确认";
    }
  }

  const metricTitles = document.querySelectorAll(".kpi-grid .card h3");
  metricTitles.forEach((title) => {
    if (title.textContent.trim() === "今日到期") title.textContent = "到期任务";
  });

  document.querySelectorAll(".card-desc").forEach((desc) => {
    if (desc.textContent.trim() === "需要今天先处理") desc.textContent = "需要先处理";
    if (desc.textContent.trim() === "有明确时间限制") desc.textContent = "有时间限制";
  });
}

const dashboardPatchObserver = new MutationObserver(() => patchDashboardTop());
dashboardPatchObserver.observe(document.body, { childList: true, subtree: true });
window.addEventListener("hashchange", () => setTimeout(patchDashboardTop, 0));
window.addEventListener("load", () => setTimeout(patchDashboardTop, 0));
setTimeout(patchDashboardTop, 0);
setTimeout(patchDashboardTop, 250);
setTimeout(patchDashboardTop, 1000);
