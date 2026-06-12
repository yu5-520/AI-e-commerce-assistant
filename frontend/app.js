const root = document.documentElement;
const themeToggle = document.getElementById('themeToggle');
const modeButtons = document.querySelectorAll('.mode-card');
const modeName = document.getElementById('modeName');
const form = document.getElementById('operationForm');
const resultBox = document.getElementById('resultBox');
const sideItems = document.querySelectorAll('.side-item');

const membershipInput = document.getElementById('membershipInput');
const titleCountInput = document.getElementById('titleCountInput');
const imagePlanCountInput = document.getElementById('imagePlanCountInput');
const imageGenerateCountInput = document.getElementById('imageGenerateCountInput');

const CLIENT_ID_KEY = 'ai_ecommerce_client_id';
const LAST_RESULT_KEY = 'ai_ecommerce_last_result_id';
const clientId = getClientId();

const savedTheme = localStorage.getItem('theme') || 'light';
root.dataset.theme = savedTheme;
themeToggle.textContent = savedTheme === 'dark' ? '切换浅色' : '切换深色';

let currentMode = '自然流';
let currentResultId = null;
let recentResults = [];

const FREE_ALLOWED = {
  titleCount: ['3', '5'],
  imagePlanCount: ['1', '2'],
  imageGenerateCount: ['0', '1', '2'],
};

function getClientId() {
  let value = localStorage.getItem(CLIENT_ID_KEY);
  if (value) return value;
  const suffix = crypto?.randomUUID ? crypto.randomUUID() : `${Date.now()}_${Math.random().toString(16).slice(2)}`;
  value = `client_${suffix}`;
  localStorage.setItem(CLIENT_ID_KEY, value);
  return value;
}

function setTheme(nextTheme) {
  root.dataset.theme = nextTheme;
  localStorage.setItem('theme', nextTheme);
  themeToggle.textContent = nextTheme === 'dark' ? '切换浅色' : '切换深色';
}

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
    .replace(/可执行、可、可/g, '可')
    .replace(/\s+/g, ' ')
    .trim();
}

function setLoading(isLoading) {
  const button = form.querySelector('button[type="submit"]');
  button.disabled = isLoading;
  button.textContent = isLoading ? '生成中...' : '生成方案';
}

function rememberResult(payload) {
  if (!payload?.result_id) return;
  localStorage.setItem(LAST_RESULT_KEY, payload.result_id);
}

function renderRecentResults() {
  if (!recentResults.length) return '';
  return `
    <article class="result-card recent-card">
      <div class="recent-head">
        <h3>最近方案</h3>
        <span>${recentResults.length} 条</span>
      </div>
      <div class="recent-list">
        ${recentResults.map(item => `
          <button class="recent-item" data-load-result="${escapeHtml(item.result_id)}" type="button">
            <strong>${escapeHtml(item.product || '未填写商品')}</strong>
            <span>${escapeHtml(item.mode || '方案')} · ${escapeHtml(formatTime(item.created_at))}</span>
          </button>
        `).join('')}
      </div>
    </article>
  `;
}

function bindRecentButtons() {
  document.querySelectorAll('[data-load-result]').forEach(button => {
    button.addEventListener('click', () => loadResult(button.dataset.loadResult));
  });
}

function renderSystemMessage(title, message = '') {
  resultBox.innerHTML = `
    <article class="result-card muted">
      <h3>${escapeHtml(title)}</h3>
      ${message ? `<p>${escapeHtml(message)}</p>` : ''}
    </article>
    ${renderRecentResults()}
  `;
  bindRecentButtons();
}

function normalizeProductResult(payload) {
  const productResult = payload.product_result || {};
  return {
    title: cleanText(productResult.title || `${payload.mode || currentMode}方案｜${payload.product || '未填写商品'}`),
    summary: cleanText(productResult.summary || '已生成一版可测试方案。'),
    generationConfig: productResult.generation_config || {},
    creditEstimate: productResult.image_generation_plan || {},
    titles: Array.isArray(productResult.titles) ? productResult.titles : [],
    imageDirections: Array.isArray(productResult.image_directions) ? productResult.image_directions : [],
    skuPlans: Array.isArray(productResult.sku_plans) ? productResult.sku_plans : [],
    priceAdvice: Array.isArray(productResult.price_advice) ? productResult.price_advice : [],
    activitySuggestions: Array.isArray(productResult.activity_suggestions) ? productResult.activity_suggestions : [],
    nextActions: Array.isArray(productResult.next_actions) ? productResult.next_actions : [],
    precisionTips: Array.isArray(productResult.precision_tips) ? productResult.precision_tips : [],
  };
}

function productItemButton(action, text, label = '已使用') {
  return `<button class="small-btn" data-feedback="${escapeHtml(action)}" data-item-text="${escapeHtml(text)}" type="button">${escapeHtml(label)}</button>`;
}

function copyButton(text) {
  return `<button class="small-btn ghost" data-copy="${escapeHtml(text)}" type="button">复制</button>`;
}

function renderTitleCards(titles) {
  if (!titles.length) return '';
  return `
    <section class="product-section">
      <div class="section-title"><h3>标题测试包</h3></div>
      <div class="copy-list">
        ${titles.map((item, index) => {
          const text = cleanText(item.text || item);
          const tag = cleanText(item.tag || '测试标题');
          const useCase = cleanText(item.use_case || '标题测试');
          return `
            <article class="copy-item">
              <div class="copy-index">${index + 1}</div>
              <div class="copy-content">
                <strong>${escapeHtml(text)}</strong>
                <p>${escapeHtml(tag)} · ${escapeHtml(useCase)}</p>
              </div>
              <div class="copy-actions">
                ${copyButton(text)}
                ${productItemButton('used_title', text)}
              </div>
            </article>
          `;
        }).join('')}
      </div>
    </section>
  `;
}

function renderImageDirections(items) {
  if (!items.length) return '';
  return `
    <section class="product-section">
      <div class="section-title"><h3>主图方向</h3></div>
      <div class="card-grid">
        ${items.map(item => {
          const name = cleanText(item.name || '主图方向');
          const mainText = cleanText(item.main_text || '主图大字');
          const subText = cleanText(item.sub_text || '副文案');
          const structure = cleanText(item.structure || '画面结构');
          const copyText = `${name}\n主图大字：${mainText}\n副文案：${subText}\n画面结构：${structure}`;
          return `
            <article class="product-card">
              <span class="card-kicker">${escapeHtml(name)}</span>
              <h4>${escapeHtml(mainText)}</h4>
              <p>${escapeHtml(subText)}</p>
              <div class="structure-box">${escapeHtml(structure)}</div>
              <div class="action-row">
                ${copyButton(copyText)}
                ${productItemButton('used_image_direction', copyText)}
              </div>
            </article>
          `;
        }).join('')}
      </div>
    </section>
  `;
}

function renderImageCreditPlan(plan) {
  if (!plan || !Number(plan.count)) return '';
  const text = `选择生成 ${plan.count} 张图片，预计消耗 ${plan.credits || 0} 积分。${plan.note || ''}`;
  return `
    <section class="product-section">
      <div class="section-title"><h3>图片积分</h3></div>
      <article class="credit-card">
        <strong>${escapeHtml(cleanText(text))}</strong>
      </article>
    </section>
  `;
}

function renderSkuPlans(items) {
  if (!items.length) return '';
  return `
    <section class="product-section">
      <div class="section-title"><h3>SKU 组合</h3></div>
      <div class="sku-table">
        <div class="sku-row sku-head"><span>SKU 类型</span><span>示例</span><span>作用</span><span>操作</span></div>
        ${items.map(item => {
          const type = cleanText(item.type || 'SKU');
          const example = cleanText(item.example || '规格示例');
          const purpose = cleanText(item.purpose || '作用');
          const copyText = `${type}：${example}｜${purpose}`;
          return `
            <div class="sku-row">
              <span>${escapeHtml(type)}</span>
              <span>${escapeHtml(example)}</span>
              <span>${escapeHtml(purpose)}</span>
              <span class="table-actions">${copyButton(copyText)}${productItemButton('used_sku', copyText)}</span>
            </div>
          `;
        }).join('')}
      </div>
    </section>
  `;
}

function renderSimpleList(title, items, action) {
  if (!items.length) return '';
  return `
    <section class="product-section">
      <div class="section-title"><h3>${escapeHtml(title)}</h3></div>
      <div class="simple-list">
        ${items.map(item => {
          const label = typeof item === 'string' ? '' : cleanText(item.label || '建议');
          const value = typeof item === 'string' ? cleanText(item) : cleanText(item.value || item.text || '');
          const copyText = label ? `${label}：${value}` : value;
          return `
            <article class="simple-item">
              <div>${label ? `<strong>${escapeHtml(label)}</strong>` : ''}<p>${escapeHtml(value)}</p></div>
              <div class="copy-actions">${copyButton(copyText)}${productItemButton(action, copyText, '已完成')}</div>
            </article>
          `;
        }).join('')}
      </div>
    </section>
  `;
}

function renderConfigSummary(config) {
  const applied = config?.applied || {};
  const membership = config?.membership === 'vip' ? 'VIP 版' : '普通版';
  if (!applied.title_count) return '';
  return `<p class="config-summary">${membership} · 标题 ${applied.title_count} 条 · 主图 ${applied.image_plan_count} 个 · 图片 ${applied.image_generate_count} 张</p>`;
}

function renderResult(payload) {
  currentResultId = payload.result_id || null;
  rememberResult(payload);
  const product = normalizeProductResult(payload);
  resultBox.innerHTML = `
    <article class="result-card product-result">
      <div class="product-head">
        <div>
          <h3>${escapeHtml(product.title)}</h3>
          ${product.summary ? `<p>${escapeHtml(product.summary)}</p>` : ''}
          ${renderConfigSummary(product.generationConfig)}
        </div>
        <span class="saved-pill">已保存</span>
      </div>
      ${renderTitleCards(product.titles)}
      ${renderImageDirections(product.imageDirections)}
      ${renderImageCreditPlan(product.creditEstimate)}
      ${renderSkuPlans(product.skuPlans)}
      ${renderSimpleList('价格与活动', [...product.priceAdvice, ...product.activitySuggestions], 'used_activity')}
      ${renderSimpleList('下一步操作', product.nextActions, 'done_next_action')}
      ${renderSimpleList('补充信息', product.precisionTips, 'precision_tip')}
    </article>
    <article class="result-card usage-record">
      <h3>使用记录</h3>
      <p id="feedbackStatus" class="feedback-status">等待操作。</p>
    </article>
    ${renderRecentResults()}
  `;

  document.querySelectorAll('[data-copy]').forEach(button => {
    button.addEventListener('click', () => copyToClipboard(button.dataset.copy));
  });
  document.querySelectorAll('[data-feedback]').forEach(button => {
    button.addEventListener('click', () => sendFeedback(button.dataset.feedback, button.dataset.itemText || ''));
  });
  bindRecentButtons();
}

async function copyToClipboard(text) {
  const status = document.getElementById('feedbackStatus');
  try {
    await navigator.clipboard.writeText(text);
    if (status) status.textContent = '已复制。';
  } catch {
    if (status) status.textContent = '复制失败，请手动复制。';
  }
}

function getGenerationConfig() {
  return {
    membership: membershipInput?.value || 'free',
    title_count: Number(titleCountInput?.value || 3),
    image_plan_count: Number(imagePlanCountInput?.value || 1),
    image_generate_count: Number(imageGenerateCountInput?.value || 0),
  };
}

function optionAllowed(select, allowedValues) {
  if (!select) return;
  Array.from(select.options).forEach(option => {
    const locked = !allowedValues.includes(option.value);
    option.disabled = locked;
    option.textContent = option.textContent.replace('（需VIP）', '') + (locked ? '（需VIP）' : '');
  });
  if (!allowedValues.includes(select.value)) {
    select.value = allowedValues[allowedValues.length - 1];
  }
}

function updateMembershipLimits() {
  const isVip = membershipInput?.value === 'vip';
  if (!isVip) {
    optionAllowed(titleCountInput, FREE_ALLOWED.titleCount);
    optionAllowed(imagePlanCountInput, FREE_ALLOWED.imagePlanCount);
    optionAllowed(imageGenerateCountInput, FREE_ALLOWED.imageGenerateCount);
  } else {
    optionAllowed(titleCountInput, ['3', '5', '10', '15']);
    optionAllowed(imagePlanCountInput, ['1', '2', '3', '5']);
    optionAllowed(imageGenerateCountInput, ['0', '1', '2', '3', '5']);
  }
}

function formatTime(value) {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
}

async function refreshRecentResults({ rerender = false } = {}) {
  try {
    const response = await fetch(`/api/results?client_id=${encodeURIComponent(clientId)}`);
    const data = await response.json();
    if (response.ok && data.ok && Array.isArray(data.results)) {
      recentResults = data.results;
    }
  } catch {
    recentResults = [];
  }
  if (rerender) {
    if (currentResultId) {
      const lastId = currentResultId;
      await loadResult(lastId, { quiet: true });
    } else {
      renderSystemMessage('等待生成方案');
    }
  }
}

async function loadResult(resultId, { quiet = false } = {}) {
  if (!resultId) return;
  try {
    const response = await fetch(`/api/results/${encodeURIComponent(resultId)}?client_id=${encodeURIComponent(clientId)}`);
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.error || 'result_not_found');
    renderResult(data);
  } catch {
    if (!quiet) renderSystemMessage('方案读取失败', '请重新生成。');
  }
}

async function restoreLastResult() {
  await refreshRecentResults();
  const lastId = localStorage.getItem(LAST_RESULT_KEY);
  if (lastId) {
    await loadResult(lastId, { quiet: true });
    if (currentResultId) return;
  }
  renderSystemMessage('等待生成方案');
}

async function generateOperation() {
  const product = document.getElementById('productInput').value;
  const detail = document.getElementById('detailInput').value;
  const cost = document.getElementById('costInput').value;
  const price = document.getElementById('priceInput').value;
  const stock = document.getElementById('stockInput').value;
  const generationConfig = getGenerationConfig();

  setLoading(true);
  renderSystemMessage('正在生成方案');

  try {
    const response = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ client_id: clientId, mode: currentMode, product, detail, cost, price, stock, ...generationConfig })
    });
    const data = await response.json();
    if (!response.ok || !data.ok) {
      throw new Error(data.error || 'generate_failed');
    }
    await refreshRecentResults();
    renderResult(data);
    await refreshRecentResults({ rerender: true });
  } catch (error) {
    renderSystemMessage('生成失败，请稍后再试。');
  } finally {
    setLoading(false);
  }
}

async function sendFeedback(action, itemText = '') {
  const status = document.getElementById('feedbackStatus');
  if (!currentResultId) {
    if (status) status.textContent = '请先生成方案。';
    return;
  }
  if (status) status.textContent = '已记录。';
  try {
    const response = await fetch('/api/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ client_id: clientId, result_id: currentResultId, action, item_text: itemText, section: 'product_result_card' })
    });
    const data = await response.json();
    if (!response.ok || !data.ok) {
      throw new Error(data.error || 'feedback_failed');
    }
    if (status) status.textContent = '已记录。';
  } catch (error) {
    if (status) status.textContent = '记录失败，请稍后再试。';
  }
}

themeToggle.addEventListener('click', () => {
  setTheme(root.dataset.theme === 'dark' ? 'light' : 'dark');
});

modeButtons.forEach(button => {
  button.addEventListener('click', () => {
    modeButtons.forEach(item => item.classList.remove('selected'));
    button.classList.add('selected');
    currentMode = button.dataset.mode;
    modeName.textContent = currentMode;
  });
});

sideItems.forEach(item => {
  item.addEventListener('click', () => {
    sideItems.forEach(link => link.classList.remove('active'));
    item.classList.add('active');
  });
});

membershipInput?.addEventListener('change', updateMembershipLimits);
updateMembershipLimits();
restoreLastResult();

form.addEventListener('submit', event => {
  event.preventDefault();
  generateOperation();
});
