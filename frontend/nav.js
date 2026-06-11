const appLayout = document.getElementById('appLayout');
const sidebar = document.getElementById('sidebar');
const navToggle = document.getElementById('navToggle');
const sidebarScrim = document.getElementById('sidebarScrim');

const NAV_STATE_KEY = 'ai_ecommerce_nav_collapsed';
const TABLET_BREAKPOINT = 1180;

function isCompactViewport() {
  return window.innerWidth <= TABLET_BREAKPOINT;
}

function setNavButton(open) {
  if (!navToggle) return;
  navToggle.setAttribute('aria-expanded', String(open));
  navToggle.textContent = isCompactViewport() ? '菜单' : (open ? '收起导航' : '展开导航');
}

function openNav() {
  if (!appLayout) return;
  appLayout.classList.add('nav-open');
  appLayout.classList.remove('nav-collapsed');
  setNavButton(true);
}

function closeNav({ persist = true } = {}) {
  if (!appLayout) return;
  appLayout.classList.remove('nav-open');
  if (!isCompactViewport()) {
    appLayout.classList.add('nav-collapsed');
    if (persist) localStorage.setItem(NAV_STATE_KEY, 'true');
  }
  setNavButton(false);
}

function expandNav({ persist = true } = {}) {
  if (!appLayout) return;
  appLayout.classList.remove('nav-collapsed');
  appLayout.classList.add('nav-open');
  if (!isCompactViewport() && persist) localStorage.setItem(NAV_STATE_KEY, 'false');
  setNavButton(true);
}

function syncNavForViewport() {
  if (!appLayout) return;
  if (isCompactViewport()) {
    appLayout.classList.remove('nav-collapsed');
    appLayout.classList.remove('nav-open');
    setNavButton(false);
    return;
  }
  const shouldCollapse = localStorage.getItem(NAV_STATE_KEY) === 'true';
  appLayout.classList.toggle('nav-collapsed', shouldCollapse);
  appLayout.classList.toggle('nav-open', !shouldCollapse);
  setNavButton(!shouldCollapse);
}

navToggle?.addEventListener('click', () => {
  if (!appLayout) return;
  if (isCompactViewport()) {
    if (appLayout.classList.contains('nav-open')) closeNav({ persist: false });
    else openNav();
    return;
  }
  if (appLayout.classList.contains('nav-collapsed')) expandNav();
  else closeNav();
});

sidebarScrim?.addEventListener('click', () => closeNav({ persist: false }));

sidebar?.querySelectorAll('a').forEach(link => {
  link.addEventListener('click', () => {
    if (isCompactViewport()) closeNav({ persist: false });
  });
});

window.addEventListener('resize', syncNavForViewport);
syncNavForViewport();
