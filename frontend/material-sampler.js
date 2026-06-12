(() => {
  const SCENE_WORDS = ['通勤', '骑行', '户外', '旅游', '防晒', '出游', '上班', '学生', '宝妈', '露营', '跑步'];
  const FUNCTION_WORDS = ['轻薄', '透气', '冰丝', '凉感', '速干', '防晒', '显瘦', '宽松', '不闷', '防紫外线', '收纳'];
  const PRICE_WORDS = ['低价', '券后', '活动价', '清仓', '高性价比', '限时', '多件装'];

  function escapeHtml(value) {
    return String(value || '')
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;');
  }

  function unique(items, limit = 12) {
    const out = [];
    items.forEach(item => {
      const text = String(item || '').trim();
      if (text && !out.includes(text)) out.push(text);
    });
    return out.slice(0, limit);
  }

  function tokenize(text) {
    return String(text || '').match(/[\u4e00-\u9fffA-Za-z0-9]{2,}/g) || [];
  }

  function removeStaleYears(text) {
    const currentYear = new Date().getFullYear();
    return String(text || '').replace(/\b(20\d{2})\b年?/g, (_, year) => Number(year) >= currentYear ? year : '').replace(/\s+/g, ' ').trim();
  }

  function pickTerms(material, product) {
    const cleaned = removeStaleYears(material);
    const banned = new Set([product, '拼多多', '商品', '标题', '新款', '爆款', '正品', '旗舰', '包邮', '现货', '2024', '2025']);
    const freq = new Map();
    tokenize(cleaned).forEach(word => {
      if (banned.has(word) || /^20\d{2}$/.test(word)) return;
      freq.set(word, (freq.get(word) || 0) + 1);
    });
    const dynamic = [...freq.entries()].sort((a, b) => b[1] - a[1]).map(([word]) => word);
    return unique([
      ...dynamic,
      ...FUNCTION_WORDS.filter(word => cleaned.includes(word)),
      ...SCENE_WORDS.filter(word => cleaned.includes(word)),
      ...PRICE_WORDS.filter(word => cleaned.includes(word)),
    ], 18);
  }

  function currentSeason() {
    const month = new Date().getMonth() + 1;
    if ([3, 4, 5].includes(month)) return '春季';
    if ([6, 7, 8].includes(month)) return '夏季';
    if ([9, 10, 11].includes(month)) return '秋季';
    return '冬季';
  }

  function buildObservation() {
    const product = document.getElementById('productInput')?.value?.trim() || '商品';
    const mode = document.getElementById('modeName')?.textContent?.trim() || '自然流';
    const material = document.getElementById('marketMaterialInput')?.value || '';
    const terms = pickTerms(material, product);
    const season = currentSeason();
    const searchTasks = [
      `拼多多 ${product} ${season} 热门标题`,
      `${product} ${season} 主图卖点`,
      `${product} 价格带 SKU 组合`,
      mode === '强付费' ? `${product} 投放素材 点击率 卖点` : mode === '爆品打造' ? `${product} 爆品 对标 价格带` : `${product} 自然搜索 长尾词`,
    ];
    const nextSampling = material.trim() ? [] : ['补充 3-5 条当前竞品标题', '补充 1-2 个主图大字或卖点词', '补充同价位商品的价格表达'];
    return {
      product,
      mode,
      season,
      terms,
      searchTasks,
      nextSampling,
      structures: ['商品词 + 当季词 + 功能词 + 场景词', '商品词 + 人群词 + 功能词 + 价格感', '商品词 + 材质/体验词 + 痛点词 + 场景词'],
      sampleCount: material.split('\n').map(line => line.trim()).filter(Boolean).length,
    };
  }

  function renderPanel(observation) {
    const panel = document.getElementById('materialSamplerPanel');
    if (!panel) return;
    const thirdTitle = observation.nextSampling.length ? '下一步采样' : '建议搜索词';
    const thirdItems = observation.nextSampling.length ? observation.nextSampling : observation.searchTasks;
    panel.classList.add('active');
    panel.innerHTML = `
      <h3>素材采样预览</h3>
      <p>${escapeHtml(observation.product)} · ${escapeHtml(observation.mode)} · ${escapeHtml(observation.season)} · ${observation.sampleCount} 条素材</p>
      <div class="material-sampler-grid">
        <article class="material-sampler-card">
          <strong>可用词感</strong>
          <div class="material-sampler-pills">${observation.terms.length ? observation.terms.map(term => `<span class="material-sampler-pill">${escapeHtml(term)}</span>`).join('') : '<small>等待素材补充</small>'}</div>
        </article>
        <article class="material-sampler-card">
          <strong>标题结构</strong>
          ${observation.structures.map(item => `<span>${escapeHtml(item)}</span>`).join('')}
        </article>
        <article class="material-sampler-card">
          <strong>${escapeHtml(thirdTitle)}</strong>
          ${thirdItems.slice(0, 4).map(item => `<span>${escapeHtml(item)}</span>`).join('')}
        </article>
      </div>
    `;
  }

  function mountSampler() {
    const materialInput = document.getElementById('marketMaterialInput');
    if (!materialInput || document.getElementById('materialSamplerButton')) return;
    const row = document.createElement('div');
    row.className = 'material-sampler-row';
    row.innerHTML = '<button id="materialSamplerButton" class="small-btn" type="button">观察素材</button><span class="muted-text">先看词感，再生成方案</span>';
    const panel = document.createElement('div');
    panel.id = 'materialSamplerPanel';
    panel.className = 'material-sampler-panel';
    materialInput.closest('label')?.insertAdjacentElement('afterend', row);
    row.insertAdjacentElement('afterend', panel);
    document.getElementById('materialSamplerButton')?.addEventListener('click', () => renderPanel(buildObservation()));
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mountSampler);
  else mountSampler();
})();
