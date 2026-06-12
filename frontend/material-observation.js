(() => {
  let lastPayload = null;

  function escapeHtml(value) {
    return String(value || '')
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;');
  }

  function cleanText(value) {
    return String(value || '')
      .replace(/result_id|backflow|llm_status|fallback|debug|api|POST|GET|后端|接口|回流|全量堆叠/gi, '')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function renderPills(items) {
    if (!Array.isArray(items) || !items.length) return '<span class="muted-text">暂无</span>';
    return items.slice(0, 18).map(item => `<span class="observation-pill">${escapeHtml(cleanText(item))}</span>`).join('');
  }

  function renderObservation(observation) {
    if (!observation || !Object.keys(observation).length) return '';
    const status = observation.status || '素材观察';
    const usableTerms = observation.usable_terms || [];
    const structures = observation.title_structures || [];
    const searchTasks = observation.search_tasks || [];
    const nextSampling = observation.next_sampling || [];
    const sampleCount = observation.sample_count || 0;
    const thirdTitle = nextSampling.length ? '下一步采样' : '建议搜索词';
    const thirdItems = (nextSampling.length ? nextSampling : searchTasks).slice(0, 4);
    return `
      <section class="product-section observation-section" data-material-observation="true">
        <div class="section-title">
          <h3>素材观察</h3>
          <span>${escapeHtml(status)} · ${sampleCount} 条素材</span>
        </div>
        <div class="observation-grid">
          <article class="observation-card">
            <strong>可用词感</strong>
            <div class="observation-pills">${renderPills(usableTerms)}</div>
          </article>
          <article class="observation-card">
            <strong>标题结构</strong>
            <div class="observation-list">${structures.slice(0, 3).map(item => `<p>${escapeHtml(cleanText(item))}</p>`).join('') || '<p>等待更多素材</p>'}</div>
          </article>
          <article class="observation-card">
            <strong>${escapeHtml(thirdTitle)}</strong>
            <div class="observation-list">${thirdItems.map(item => `<p>${escapeHtml(cleanText(item))}</p>`).join('') || '<p>等待更多素材</p>'}</div>
          </article>
        </div>
      </section>
    `;
  }

  function injectObservation() {
    const observation = lastPayload?.product_result?.material_observation;
    if (!observation) return;
    const productResult = document.querySelector('.product-result');
    if (!productResult || productResult.querySelector('[data-material-observation="true"]')) return;
    const productHead = productResult.querySelector('.product-head');
    if (!productHead) return;
    productHead.insertAdjacentHTML('afterend', renderObservation(observation));
  }

  const originalFetch = window.fetch.bind(window);
  window.fetch = async (...args) => {
    const response = await originalFetch(...args);
    const url = String(args[0] || '');
    if (url.includes('/api/generate') || url.includes('/api/results/')) {
      response.clone().json().then(data => {
        if (data?.product_result?.material_observation) {
          lastPayload = data;
          setTimeout(injectObservation, 0);
          setTimeout(injectObservation, 60);
          setTimeout(injectObservation, 180);
        }
      }).catch(() => {});
    }
    return response;
  };

  const observer = new MutationObserver(() => injectObservation());
  observer.observe(document.documentElement, { childList: true, subtree: true });
})();
