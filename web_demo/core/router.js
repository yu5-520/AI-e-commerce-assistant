(function () {
  const routes = new Map();
  const aliases = new Map([
    ["risk-center", "store-overview"],
    ["executive-cockpit", "store-overview"],
    ["people-overview", "task-command"],
  ]);
  let current = null;
  let scheduled = false;
  let renderToken = 0;
  let pendingState = {};

  function rawRouteFromHash() { return location.hash.replace("#", "") || "dashboard"; }
  function routeFromHash() { return aliases.get(rawRouteFromHash()) || rawRouteFromHash(); }
  function errorView(error) {
    const message = error?.message || String(error || "接口异常");
    const last = window.AppApi?.status?.lastError;
    const path = last?.path || "当前页面接口";
    return `<section class="page-section"><div class="section-header"><h3>接口异常</h3><span class="status-badge">无本地兜底</span></div><p>后端接口没有返回可用数据，页面已停止展示本地模拟业务内容。</p><div class="product-notice"><strong>${AppShell.escape(path)}</strong><span>${AppShell.escape(message)}</span></div></section>`;
  }

  function createContext(route, token, state = {}) {
    const cleanup = [];
    return {
      route,
      token,
      state,
      isCurrent: () => token === renderToken && routeFromHash() === route,
      on(selector, type, handler, options) {
        document.querySelectorAll(selector).forEach((node) => {
          node.addEventListener(type, handler, options);
          cleanup.push(() => node.removeEventListener(type, handler, options));
        });
      },
      delegate(selector, type, handler, root = AppShell.view()) {
        if (!root) return;
        const wrapped = (event) => {
          const target = event.target.closest(selector);
          if (!target || !root.contains(target)) return;
          handler(event, target);
        };
        root.addEventListener(type, wrapped);
        cleanup.push(() => root.removeEventListener(type, wrapped));
      },
      addCleanup(fn) { if (typeof fn === "function") cleanup.push(fn); },
      cleanup() { while (cleanup.length) { try { cleanup.pop()(); } catch (error) { console.error("[router] cleanup error", error); } } },
    };
  }

  async function renderNow(reason = "route") {
    scheduled = false;
    const route = routes.has(routeFromHash()) ? routeFromHash() : "dashboard";
    const page = routes.get(route) || routes.get("dashboard");
    const token = ++renderToken;
    const state = pendingState || {};
    pendingState = {};
    if (current?.page?.unmount) { try { current.page.unmount(current.ctx); } catch (error) { console.error("[router] unmount error", error); } }
    current?.ctx?.cleanup?.();
    current = null;
    AppShell.setActive(route);
    AppShell.setTitle(page.title || "总览");
    const ctx = createContext(route, token, state);
    current = { route, page, ctx };
    try {
      const html = await page.render(ctx);
      if (!ctx.isCurrent()) return;
      AppShell.setView(html || "");
      if (page.mount) page.mount(ctx);
      window.dispatchEvent(new CustomEvent("app-route-mounted", { detail: { route, reason, token, state } }));
    } catch (error) {
      console.error("[router] render error", error);
      if (ctx.isCurrent()) AppShell.setView(errorView(error));
    }
  }

  function schedule(reason = "route", state = null) {
    if (state) pendingState = { ...pendingState, ...state };
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => renderNow(reason));
  }

  function register(page) {
    if (!page || !page.route) throw new Error("Route page requires route");
    routes.set(page.route, page);
  }

  function navigate(route, state = null) {
    if (!route) return;
    const target = aliases.get(route) || route;
    if (state) pendingState = { ...pendingState, ...state };
    if (routeFromHash() === target) schedule("same-route", state);
    else location.hash = target;
  }

  function start() {
    window.addEventListener("hashchange", () => schedule("hashchange"));
    document.getElementById("refreshBtn")?.addEventListener("click", () => schedule("refresh"));
    const target = routeFromHash();
    if (target !== rawRouteFromHash()) location.hash = target;
    else schedule("start");
  }

  window.AppRouter = { register, start, navigate, schedule, routeFromHash };
})();
