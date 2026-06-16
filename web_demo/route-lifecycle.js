(function () {
  if (window.APP_ROUTE_LIFECYCLE?.version) return;

  const nativeAddEventListener = window.addEventListener.bind(window);
  const nativeRemoveEventListener = window.removeEventListener.bind(window);
  const NativeMutationObserver = window.MutationObserver;
  const hashListeners = [];
  const routeObservers = new Set();
  const routeHooks = {
    before: new Set(),
    after: new Set(),
  };

  let scheduled = false;
  let running = false;
  let transitionId = 0;
  let lastRoute = location.hash.replace("#", "") || "dashboard";

  function currentRoute() {
    return location.hash.replace("#", "") || "dashboard";
  }

  function safeCall(callback, event) {
    try {
      const result = callback.call(window, event);
      return result && typeof result.then === "function" ? result : Promise.resolve(result);
    } catch (error) {
      console.error("[route-lifecycle] listener error", error);
      return Promise.resolve();
    }
  }

  function notifyHooks(type, detail) {
    routeHooks[type].forEach((handler) => {
      try {
        handler(detail);
      } catch (error) {
        console.error(`[route-lifecycle] ${type} hook error`, error);
      }
    });
    window.dispatchEvent(new CustomEvent(`app-route-${type}`, { detail }));
  }

  function runRouteObservers(detail) {
    routeObservers.forEach((observer) => {
      if (!observer.active) return;
      try {
        observer.callback([], observer, detail);
      } catch (error) {
        console.error("[route-lifecycle] observer error", error);
      }
    });
  }

  async function flushRoute(reason = "route") {
    if (running) {
      schedule(reason);
      return;
    }
    running = true;
    scheduled = false;

    const route = currentRoute();
    const from = lastRoute;
    const id = ++transitionId;
    const detail = { id, route, from, reason, at: Date.now() };

    notifyHooks("before", detail);

    const event = new Event("hashchange");
    for (const listener of [...hashListeners]) {
      await safeCall(listener, event);
    }

    await new Promise((resolve) => requestAnimationFrame(resolve));
    runRouteObservers(detail);
    await new Promise((resolve) => requestAnimationFrame(resolve));

    lastRoute = route;
    notifyHooks("after", detail);
    running = false;

    if (scheduled) flushRoute("queued");
  }

  function schedule(reason = "route") {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => flushRoute(reason));
  }

  window.addEventListener = function patchedWindowAddEventListener(type, listener, options) {
    if (type === "hashchange" && typeof listener === "function") {
      if (!hashListeners.includes(listener)) hashListeners.push(listener);
      return;
    }
    return nativeAddEventListener(type, listener, options);
  };

  window.removeEventListener = function patchedWindowRemoveEventListener(type, listener, options) {
    if (type === "hashchange" && typeof listener === "function") {
      const index = hashListeners.indexOf(listener);
      if (index >= 0) hashListeners.splice(index, 1);
      return;
    }
    return nativeRemoveEventListener(type, listener, options);
  };

  if (NativeMutationObserver) {
    window.MutationObserver = class RouteLifecycleMutationObserver {
      constructor(callback) {
        this.callback = callback;
        this.active = false;
      }
      observe() {
        this.active = true;
        routeObservers.add(this);
      }
      disconnect() {
        this.active = false;
        routeObservers.delete(this);
      }
      takeRecords() {
        return [];
      }
    };
  }

  nativeAddEventListener("hashchange", () => schedule("hashchange"));
  nativeAddEventListener("load", () => schedule("load"));

  window.APP_ROUTE_LIFECYCLE = {
    version: "1.2.0",
    currentRoute,
    schedule,
    afterRoute(handler) {
      routeHooks.after.add(handler);
      return () => routeHooks.after.delete(handler);
    },
    beforeRoute(handler) {
      routeHooks.before.add(handler);
      return () => routeHooks.before.delete(handler);
    },
    runAfterRender(callback) {
      routeHooks.after.add(callback);
      callback({ id: transitionId, route: currentRoute(), from: lastRoute, reason: "manual", at: Date.now() });
      return () => routeHooks.after.delete(callback);
    },
  };
})();
